from gevent import monkey

monkey.patch_all()


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
# Read the .env file to check which LLM engine to use
llm_engine = os.environ.get("LLM_ENGINE", "openai")

if llm_engine == "openai":
    from llm_api.mojodex_background_openai import MojodexBackgroundOpenAI, OpenAIConf
    # check the .env file to see which LLM_API_PROVIDER is set
    if os.environ.get("LLM_API_PROVIDER") == "azure":
        llm_conf = OpenAIConf.gpt4_turbo_conf
    else:
        llm_conf = OpenAIConf.gpt4_turbo_conf

    llm = MojodexBackgroundOpenAI
elif llm_engine == "mistral":
    from llm_api.mojodex_background_mistralai import MojodexMistralAI, MistralAIConf
    # check the .env file to see which LLM_API_PROVIDER is set
    if os.environ.get("LLM_API_PROVIDER") == "azure":
        llm_conf = MistralAIConf.azure_mistral_large_conf
    else:
        llm_conf = MistralAIConf.mistral_large_conf
    llm = MojodexMistralAI
else:
    raise Exception(f"Unknown LLM engine: {llm_engine}")

# Setup the embedder
embedding_engine = os.environ.get("EMBEDDING_ENGINE", "openai")
if embedding_engine == "openai":
    embedder = MojodexBackgroundOpenAI
    embedding_conf = OpenAIConf.embedding_conf
else:
    raise Exception(f"Unknown embedding engine: {embedding_engine}")


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

from mojodex_core.costs_manager.tokens_costs_manager import TokensCostsManager
from mojodex_core.costs_manager.serp_api_costs_manager import SerpAPICostsManager
from mojodex_core.costs_manager.news_api_costs_manager import NewsAPICostsManager
tokens_costs_manager = TokensCostsManager()
serp_api_costs_manager = SerpAPICostsManager()
news_api_costs_manager = NewsAPICostsManager()


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
