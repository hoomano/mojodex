from mojodex_core.entities.abstract_entities.abstract_entity import AbstractEntity
from mojodex_core.entities.db_base_entities import MdUserTask
from sqlalchemy.orm import object_session
from mojodex_core.entities.user import User
from mojodex_core.entities.abstract_entities.task import Task
from abc import ABC, abstractmethod


class UserTask(MdUserTask, ABC, metaclass=AbstractEntity):
    """UserTask entity class is an abstract class.
    It should be instanciated as an InstructUserTask or UserWorkflow.
    
    This is true for default constructor usage but also when retrieving data from the database: `db.session.query(InstructUserTask).all()`"""

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
        """
        task property is abstract and should be implemented in the child class to retrieve either an InstructTask or Workflow entity.
        Implementation will look like:

        ```
        try:
            session = object_session(self)
            return session.query(Task).filter(Task.task_pk == self.task_fk).first()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: task :: {e}")
        ```

        replacing `Task` by `InstructTask` or `Workflow` depending on the child class.
        """
        raise NotImplementedError

    @property
    def json_input_in_user_language(self):
        try:
            return self.task.get_json_input_in_language(self.user.language_code)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: json_input_in_user_language :: {e}")