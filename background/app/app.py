from gevent import monkey


monkey.patch_all()


from mojodex_core.mail import mojo_mail_client


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

from models.documents.document_manager import DocumentManager
document_manager = DocumentManager()

from http_routes import HttpRouteManager
HttpRouteManager(api)


@app.route("/")
def index():
    message = "Welcome to Mojodex Background Service."
    return message


if __name__ == '__main__':
    app.run()
