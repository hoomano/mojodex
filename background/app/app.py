from gevent import monkey

monkey.patch_all()

from mojodex_core.llm_engine.llm import LLM
from mojodex_core.llm_engine.embedding_provider import EmbeddingProvider

from datetime import datetime

from flask import Flask
from flask_restful import Api
import os
from flask_sqlalchemy import SQLAlchemy
from concurrent.futures import ThreadPoolExecutor
# Configure the logger
import logging
logging.basicConfig(level=logging.ERROR) # Else we get logs from all packages
import jinja2
env = jinja2.Environment()
env.policies['json.dumps_kwargs'] = {'sort_keys': False}

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=5)

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
engine_container = db.get_engine(app)

from background_logger import BackgroundLogger

# Setup the LLM Engine
llm, llm_conf, llm_backup_conf = LLM.get_main_llm_provider()

# Setup the embedder
embedder, embedding_conf = EmbeddingProvider.get_embedding_provider()

main_logger = BackgroundLogger("main_logger")

try:
    from mojodex_core.email_sender import MojoAwsMail
    mojo_mail_client = MojoAwsMail(
        sender_name=os.environ['SENDER_NAME'], sender_email=os.environ['SENDER_EMAIL'], region="eu-west-3")
except Exception as e:
    main_logger.error(f"Error while initializing MojoAwsMail : {e}")
    mojo_mail_client = None

admin_email_receivers = os.environ["ADMIN_EMAIL_RECEIVERS"].split(
    ",") if "ADMIN_EMAIL_RECEIVERS" in os.environ else []
technical_email_receivers = os.environ["TECHNICAL_EMAIL_RECEIVERS"].split(
    ",") if "TECHNICAL_EMAIL_RECEIVERS" in os.environ else []


def send_admin_error_email(error_message):
    try:
        mojo_mail_client.send_mail(subject=f"MOJODEX BACKGROUND ERROR - {os.environ['ENVIRONMENT']}",
                                   recipients=technical_email_receivers,
                                   text=error_message)
    except Exception as e:
        main_logger.error(f"Error while sending admin email : {e}")



from models.documents.document_manager import DocumentManager
document_manager = DocumentManager()

from language_retriever import LanguageRetriever
language_retriever = LanguageRetriever()

from conversation_retriever import ConversationRetriever
conversation_retriever = ConversationRetriever()


def on_json_error(result, function_name, retries):
    error_path = f"/data/{function_name}_{datetime.now().isoformat()}.txt"
    with open(error_path, "w") as f:
        f.write(result)
    raise Exception(
        f"{function_name} - incorrect JSON: aborting after {retries} retries...  data available in {error_path}")

from http_routes import HttpRouteManager
HttpRouteManager(api)


@app.route("/")
def index():
    message = "Welcome to Mojodex Backend Service."
    return message


if __name__ == '__main__':
    app.run()
