from mojodex_core.entities.db_base_entities import MdUserTask, MdTaskDisplayedData
from sqlalchemy.orm import object_session

from mojodex_core.entities.user import User

from mojodex_core.entities.task import Task
from abc import ABC, abstractmethod


class UserTask(MdUserTask, ABC):

    @property
    def user(self):
        try:
            session = object_session(self)
            return session.query(User).filter(User.user_id == self.user_id).first()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: user :: {e}")

    @property
    @abstractmethod
    def task(self):
        try:
            session = object_session(self)
            return session.query(Task).filter(Task.task_pk == self.task_fk).first()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: task :: {e}")

    @property
    def json_input_in_user_language(self):
        try:
            return self.task.get_json_input_in_language(self.user.language_code)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: json_input_in_user_language :: {e}")