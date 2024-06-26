from functools import wraps
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import logging

class MojodexCoreDB:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MojodexCoreDB, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        
        try:
            connection_string = f"postgresql+psycopg2://{os.environ['DBUSER']}:{os.environ['DBPASS']}@{os.environ['DBHOST']}:5432/{os.environ['DBNAME']}"
            self.engine = create_engine(connection_string)
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
            db_session = Session(MojodexCoreDB().engine)
            result = func(self, *args, db_session=db_session, **kwargs)
            db_session.close()
            return result
        except Exception as e:
            raise Exception(f"with_db_session :: {e}")

    return wrapper