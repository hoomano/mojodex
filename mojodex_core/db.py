import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

from mojodex_core.entities import MdError

Base = declarative_base()

connection_string = f"postgresql+psycopg2://{os.environ['DBUSER']}:{os.environ['DBPASS']}@{os.environ['DBHOST']}:5432/{os.environ['DBNAME']}"

engine = create_engine(connection_string)
Base.metadata.create_all(engine)
db_session = Session(engine)

# print(db_session.query(MdError).first())



class MySession(Session):
    # override init and destructor to print when session is created and destroyed
    def __init__(self):
        super().__init__(engine)

        