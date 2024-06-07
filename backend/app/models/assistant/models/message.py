from mojodex_core.entities import MdMessage
from sqlalchemy.orm.attributes import flag_modified

class Message:

    def __init__(self, message_pk, db_session):
        self.message_pk = message_pk
        self.db_session = db_session
        self.db_object = self._get_db_object(message_pk)

    def _get_db_object(self, message_pk):
        try:
            return self.db_session.query(MdMessage).filter(MdMessage.message_pk == message_pk).first()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: _get_db_object :: {e}")

    @property
    def user_task_execution_pk(self):
        try:
            return self.db_object.message['user_task_execution_pk']
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: user_task_execution_pk :: {e}")

    @user_task_execution_pk.setter
    def user_task_execution_pk(self, user_task_execution_pk):
        try:
            new_message = self.db_object.message
            new_message['user_task_execution_pk'] = user_task_execution_pk
            self.db_object.message = new_message
            flag_modified(self.db_object, "message")
            self.db_session.commit()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: user_task_execution_pk :: {e}")