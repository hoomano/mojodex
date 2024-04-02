import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
import logging


try:
    Base = declarative_base()

    connection_string = f"postgresql+psycopg2://{os.environ['DBUSER']}:{os.environ['DBPASS']}@{os.environ['DBHOST']}:5432/{os.environ['DBNAME']}"
    engine = create_engine(connection_string)
    Base.metadata.create_all(engine)
    db_session = Session(engine)
except Exception as e:
    logging.warning(f"Error initializing db_session :: {e}")

