from entity_factory import EntityFactory

# Replace this with your actual database URL
DATABASE_URL = f"postgresql+psycopg2://assistant_db_user:password@localhost:5432/your_assistant_db"
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
engine = create_engine(DATABASE_URL)

SessionMaker = sessionmaker(bind=engine)
session = SessionMaker()
factory = EntityFactory(session)

user = factory.get_entity('MdUser', "14f919cf95a70935c6c70f4a89ef5fec")
print(user.email)
print(user.get_greeting())

task = factory.get_entity('MdTask', 1)
print(task.name_for_system)

#new_task = factory.add_entity('MdTask', name_for_system="New Task", type="instruct")
#print(new_task.task_pk)
#print(f"Created User: {new_user.id} - {new_user.name}")  # Output: Created User: <new_user_id> - John Doe