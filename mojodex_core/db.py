from functools import wraps
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
except Exception as e:
    logging.warning(f"Error initializing db_session :: {e}")



def with_db_session(func):
    """
    Decorator function to open a db session, run the function, then close the db session.

    Args:
        func (function): The function to be wrapped.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            db_session = Session(engine)
            func(self, *args, db_session=db_session, **kwargs)
            db_session.close()
        except Exception as e:
            raise Exception(f"with_db_session :: {e}")

    return wrapper