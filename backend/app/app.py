from gevent import monkey

monkey.patch_all()


from mojodex_core.llm_engine.llm import LLM
from mojodex_core.llm_engine.embedding_provider import EmbeddingProvider
from mojodex_core.stt.stt import STT

import hashlib
import random
import string
from packaging import version

from flask import Flask
from flask_socketio import SocketIO, join_room, ConnectionRefusedError, emit
from flask_restful import Api
import os
from flask_sqlalchemy import SQLAlchemy
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=5)

app = Flask(__name__)

app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", False)
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
app.config["TIME_ZONE"] = os.environ.get("FLASK_TIME_ZONE", "UTC")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_size": int(os.environ.get("FLASK_POOL_SIZE", 25)),
    "max_overflow": int(os.environ.get("FLASK_MAX_OVERFLOW", 1)),
}
app.config[
    "SQLALCHEMY_DATABASE_URI"] = f"postgresql+psycopg2://{os.environ['DBUSER']}:{os.environ['DBPASS']}@{os.environ['DBHOST']}:5432/{os.environ['DBNAME']}"

db = SQLAlchemy(app)
api = Api(app)

server_socket = SocketIO(app, ping_timeout=40, ping_interval=15, logger=False, engineio_logger=False,
                         cors_allowed_origins="*", )

from flask_restful import request
from functools import wraps
import jwt

from datetime import datetime
from mojodex_core.entities import *

from mojodex_backend_logger import MojodexBackendLogger

# Setup the LLM Engine
llm, llm_conf, llm_backup_conf = LLM.get_main_llm_provider()

# Setup the embedder
embedder, embedding_conf = EmbeddingProvider.get_embedding_provider()

# Setup the STT engine
stt, stt_conf = STT.get_stt()

main_logger = MojodexBackendLogger("main_logger")

# TODO: setup dedicated email conf file for multiple providers management
try:
    from mojodex_core.email_sender import MojoAwsMail
    mojo_mail_client = MojoAwsMail(sender_name=os.environ['SENDER_NAME'], sender_email=os.environ['SENDER_EMAIL'],
                                   region="eu-west-3")
except Exception as e:
    main_logger.info(f"No email client available.")
    mojo_mail_client = None


def send_admin_email(subject, recipients, text):
    try:
        if mojo_mail_client:
            mojo_mail_client.send_mail(subject=subject,
                                       recipients=recipients,
                                       text=text)
    except Exception as e:
        main_logger.error(f"Error while sending admin email : {e}")


admin_email_receivers = os.environ["ADMIN_EMAIL_RECEIVERS"].split(",") if "ADMIN_EMAIL_RECEIVERS" in os.environ else []
technical_email_receivers = os.environ["TECHNICAL_EMAIL_RECEIVERS"].split(",") if "TECHNICAL_EMAIL_RECEIVERS" in os.environ else []


def log_error(error_message, session_id=None, notify_admin=False):
    try:
        main_logger.error(error_message)
        error = MdError(session_id=session_id, message=str(error_message),
                        creation_date=datetime.now())
        db.session.add(error)
        db.session.commit()
        if notify_admin:
            send_admin_email(subject=f"MOJODEX ERROR - {os.environ['ENVIRONMENT']}",
                             recipients=technical_email_receivers,
                             text=str(error_message))
    except Exception as e:
        db.session.rollback()
        main_logger.error(f"Error while logging error : {e}")



from placeholder_generator import PlaceholderGenerator

placeholder_generator = PlaceholderGenerator()

from translator import Translator

translator = Translator()

from time_manager import TimeManager

time_manager = TimeManager()

from models.documents.document_manager import DocumentManager

document_manager = DocumentManager()

from timing_logger import TimingLogger

timing_logger = TimingLogger("/data/timing_logs.log")


def authenticate_function(token):
    try:
        payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=os.environ["ENCODING_ALGORITHM"])
        user_id = payload["sub"].split(os.environ['TOKEN_SECRET_SPLITTER'])[0]
        return True, user_id
    except KeyError:
        return {"error": "Authorization key required"}, 403
    except jwt.ExpiredSignatureError:
        return {"error": "Token expired."}, 403
    except jwt.InvalidTokenError:
        return {"error": "Invalid token."}, 403


def authenticate(methods=["PUT", "POST", "DELETE", "GET"]):
    methods = [name.lower() for name in methods]

    def authenticate_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            if func.__name__ not in methods:
                return func(*args, **kwargs)
            try:
                token = request.headers['Authorization']
                auth = authenticate_function(token)
                if auth[0] is not True:
                    return auth
                else:
                    kwargs["user_id"] = auth[1]
            except Exception as e:
                return {"error": f"Authentication error : {e}"}, 403

            return func(*args, **kwargs)

        return wrapper

    return authenticate_wrapper


from push_notification_sender import PushNotificationSender
try:
    push_notification_sender = PushNotificationSender()
except Exception as e:
    main_logger.error(f"Can't initialize NotificationSender : {e}")
    push_notification_sender = None



def generate_session_id(user_id):
    random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    clear_string = f"{random_string}_mojodex_{user_id}_{datetime.now().isoformat()}"
    encoded_string = hashlib.md5(clear_string.encode())
    return encoded_string.hexdigest()


def on_json_error(result, function_name, retries):
    error_path = f"/data/{function_name}_{datetime.now().isoformat()}.txt"
    with open(error_path, "w") as f:
        f.write(result)
    raise Exception(
        f"{function_name} - incorrect JSON : aborting after {retries} retries...  data available in {error_path}")


from socketio_message_sender import SocketioMessageSender

socketio_message_sender = SocketioMessageSender()

from http_routes import *

HttpRouteManager(api)

from models.session.session import Session as SessionModel

from user_task_execution_purchase_updater import UserTaskExecutionPurchaseUpdater

userTaskExecutionPurchaseUpdater = UserTaskExecutionPurchaseUpdater()


@app.route("/")
def index():
    message = f"Welcome to Mojodex Backend Service."
    return message


def resume_session(session_id):
    # get session from db
    session_db = db.session.query(MdSession).filter(MdSession.session_id == session_id).first()
    if session_db is None:
        main_logger.error(f"Session {session_id} not found in db", None)
        emit('error', f"Session {session_id} not found")
        return
    join_room(session_id)
    userTaskExecutionPurchaseUpdater.join_room(session_id)
    session = SessionModel(session_id)

    return session


@server_socket.on('connect')
def handle_message(data):
    try:
        if 'secret' in data and data['secret'] == os.environ["PURCHASE_UPDATER_SOCKETIO_SECRET"]:
            return # ok
        token = data['token']
        payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=os.environ["ENCODING_ALGORITHM"])
        payload_split = payload["sub"].split(os.environ['TOKEN_SECRET_SPLITTER'])
        if payload_split:
            user_id = payload_split[0]
            join_room(f"mojo_events_{user_id}")
        if not userTaskExecutionPurchaseUpdater.is_connected and not userTaskExecutionPurchaseUpdater.connecting:
            userTaskExecutionPurchaseUpdater.connect()
    except KeyError as e:
        main_logger.error(f'Someone tried to connect without a token : {e}')
        raise ConnectionRefusedError("Missing token")
    except jwt.ExpiredSignatureError:
        main_logger.error('Someone tried to connect with expired token')
        raise ConnectionRefusedError("Expired token")
    except jwt.InvalidTokenError:
        main_logger.error('Someone tried to connect with invalid token')
        raise ConnectionRefusedError("Invalid token")
    except Exception as e:
        main_logger.error(f'Someone tried to connect but something wrong happened during authentication : {e}')
        raise ConnectionRefusedError(str(e))


@server_socket.on('start_session')
def handle_message(data):
    try:
        session_id = data["session_id"]
        app_version = version.parse(data["version"])
        resume_session(session_id)
    except KeyError as e:
        message = {"error": str(e), "session_id": data.get("session_id")}
        emit('error', message)
        log_error(message, session_id=data.get("session_id"))


@server_socket.on('manage_session_events')
def handle_message(data):
    try:
        # check secret
        if data["secret"] != os.environ["PURCHASE_UPDATER_SOCKETIO_SECRET"]:
            raise Exception("Invalid secret")
        join_room(data["room"])
    except Exception as e:
        log_error(f"Error while managing session events : {e}")


def socketio_event_callback(event_name, data):
    try:
        if "session_id" in data:
            session_id = data["session_id"]
            app_version = version.parse(data["version"])
            session = resume_session(session_id)
        else:
            message = {"error": "No session_id provided", "session_id": data.get("session_id")}
            emit('error', message)
            return
        session.process_chat_message(data)
    except Exception as e:
        message = {"error": str(e), "session_id": data.get("session_id")}
        emit('error', message)


@server_socket.on('user_message')
def handle_message(data):
    emit("user_message_reception", {"success": "User message has been received", "session_id": data.get("session_id")})
    socketio_event_callback('user_message', data)


@server_socket.on('disconnect')
def handle_message():
    try:
        main_logger.info(f"Someone disconnected : {request.sid}")
    except Exception:
        pass  # If log does not work, it's not a big deal, won't crash an exception


if __name__ == '__main__':
    server_socket.run(app)
