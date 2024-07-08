import time
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

connection_string = f"postgresql+psycopg2://assistant_db_user:password@localhost:5432/your_assistant_db"

engine = create_engine(connection_string)
Base.metadata.create_all(engine)
db_session = Session(engine)



class MySession(Session):
    # override init and destructor to print when assistant is created and destroyed
    def __init__(self):
        print("🟢 Session created")
        super().__init__(engine)

    def __del__(self):
        print("🔴 MySession destroyed")

class Car:
    def __init__(self, model):
        self.model = model
        print(f'🟢 {self.model} has been created')

    def __del__(self):
        print(f'🔴 {self.model} has been deleted')


class Person:
    def __init__(self, name, car_model):
        self.name = name
        self.car = Car(car_model)
        self.session = MySession()
        print(f'🟢 {self.name} has been created')

    def __del__(self):
        print(f'🔴 {self.name} has been deleted')


person = Person('John', 'Toyota')
del person
time.sleep(20)

