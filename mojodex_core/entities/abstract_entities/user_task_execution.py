from abc import ABC, abstractmethod
from mojodex_core.entities.abstract_entities.abstract_entity import AbstractEntity
from mojodex_core.entities.db_base_entities import MdUserTaskExecution, MdProducedText
from sqlalchemy.orm import object_session
from mojodex_core.entities.session import Session


class UserTaskExecution(MdUserTaskExecution, ABC, metaclass=AbstractEntity):
    """UserTaskExecution entity class is an abstract class.
    It should be instanciated as an InstructUserTaskExecution or UserWorkflowExecution.
    
    This is true for default constructor usage but also when retrieving data from the database: `db.session.query(InstructUserTaskExecution).all()`"""


    @property
    def produced_text_done(self):
        try:
            session = object_session(self)
            return session.query(MdProducedText).filter(MdProducedText.user_task_execution_fk == self.user_task_execution_pk).count() >= 1
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: produced_text_done :: {e}")

    @property
    def has_images_inputs(self):
        try:
            for input in self.json_input_values:
                if input["type"] in ["image", "multiple_images"]:
                    return True
            return False
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}:: has_images_inputs :: {e}")

    @property
    def images_input_names(self):
        try:
            input_images = []
            for task_input in self.json_input_values:
                if task_input["type"] == "image":
                    input_images.append(task_input["value"])
                elif task_input["type"] == "multiple_images":
                    input_images += task_input["value"]
            return input_images
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}:: images_input_names :: {e}")

    @property
    def task_name_in_user_language(self):
        try:
            return self.task.get_name_in_language(self.user.language_code)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_task_name_in_user_language :: {e}")

    @property
    @abstractmethod
    def user_task(self):
        """
        task property is abstract and should be implemented in the child class to retrieve either an InstructTask or Workflow entity.
        Implementation will look like:

        ```
        try:
            session = object_session(self)
            return session.query(UserTask).filter(UserTask.user_task_pk == self.user_task_fk).first()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: user_task :: {e}")
        ```

        replacing `Task` by `InstructTask` or `Workflow` depending on the child class.
        """
        raise NotImplementedError
        

    @property
    def user(self):
        try:
            return self.user_task.user
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: user :: {e}")

    @property
    def task(self):
        try:
            return self.user_task.task
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: task :: {e}")

    @property
    def session(self):
        try:
            session = object_session(self)
            return session.query(Session).filter(Session.session_id == self.session_id).first()
        except Exception as e:
            raise Exception(f"{self.__class__} :: session :: {e}")

