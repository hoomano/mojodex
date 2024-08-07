from gevent import monkey
monkey.patch_all()

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
import jwt

from datetime import datetime
from mojodex_core.entities.db_base_entities import *

from mojodex_backend_logger import MojodexBackendLogger


main_logger = MojodexBackendLogger("main_logger")

from placeholder_generator import PlaceholderGenerator

placeholder_generator = PlaceholderGenerator()

from translator import Translator

translator = Translator()

from timing_logger import TimingLogger

timing_logger = TimingLogger("/data/timing_logs.log")




def generate_session_id(user_id):
    random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    clear_string = f"{random_string}_mojodex_{user_id}_{datetime.now().isoformat()}"
    encoded_string = hashlib.md5(clear_string.encode())
    return encoded_string.hexdigest()


from socketio_message_sender import SocketioMessageSender

socketio_message_sender = SocketioMessageSender()

from http_routes import *

HttpRouteManager(api)

from models.assistant.session_controller import SessionController

from user_task_execution_purchase_updater import UserTaskExecutionPurchaseUpdater

userTaskExecutionPurchaseUpdater = UserTaskExecutionPurchaseUpdater()

from mojodex_core.logging_handler import log_error

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
    session = SessionController(session_id)

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


@server_socket.on('disconnect')
def handle_message():
    try:
        main_logger.info(f"Someone disconnected : {request.sid}")
    except Exception:
        pass  # If log does not work, it's not a big deal, won't crash an exception


if __name__ == '__main__':
    server_socket.run(app)
