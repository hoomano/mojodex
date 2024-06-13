from mojodex_core.entities.db_base_entities import MdMessage
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm import object_session

class Message(MdMessage):


    @property
    def user_task_execution_pk(self):
        try:
            return self.message['user_task_execution_pk']
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: user_task_execution_pk :: {e}")

    @user_task_execution_pk.setter
    def user_task_execution_pk(self, user_task_execution_pk):
        try:
            session = object_session(self)
            new_message = self.db_object.message
            new_message['user_task_execution_pk'] = user_task_execution_pk
            self.message = new_message
            flag_modified(self.db_object, "message")
            session.commit()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: user_task_execution_pk :: {e}")