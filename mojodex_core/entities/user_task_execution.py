from mojodex_core.entities.user_task import UserTask
from mojodex_core.entities.db_base_entities import MdProducedTextVersion, MdUserTaskExecution, MdProducedText
from sqlalchemy.orm import object_session
from mojodex_core.entities.session import Session


class UserTaskExecution(MdUserTaskExecution):
    """UserTaskExecution entity class that contains all the common properties and methods of an InstructUserTaskExecution or UserWorkflowExecution.
    """


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
    def user_task(self):
        """ contains the common informations of a UserTask, either from an Instruct or Workflow.
        """
        try:
            session = object_session(self)
            return session.query(UserTask).filter(UserTask.user_task_pk == self.user_task_fk).first()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: user_task :: {e}")

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

    @property
    def last_produced_text_version(self):
        try:
            session = object_session(self)
            return session.query(MdProducedTextVersion).\
                join(MdProducedText, MdProducedTextVersion.produced_text_fk == MdProducedText.produced_text_pk).\
                filter(MdProducedText.user_task_execution_fk == self.user_task_execution_pk).\
                order_by(MdProducedTextVersion.creation_date.desc()).first()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: produced_text :: {e}")
        
    @property
    def derives_from_a_previous_user_task_execution(self) -> bool:
        """On mobile app, some tasks can display "predefined_actions" at the end of the execution. 
        Those are other task the user can launch to chain task executions on a same subject.

        Returns True if the current UserTaskExecution is the result of a predefined_action launched from a previous UserTaskExecution.
        """
        return self.predefined_action_from_user_task_execution_fk is not None

    @property
    def previous_related_user_task_executions(self) -> list:
        """On mobile app, some tasks can display "predefined_actions" at the end of the execution. 
        Those are other task the user can launch to chain task executions on a same subject.

        This methods retrieves the previous related user task execution of this chain, if any.
        """
        try:
            session = object_session(self)
            previous_related_user_task_execution = []
            user_task_execution = self
            while user_task_execution and user_task_execution.derives_from_a_previous_user_task_execution:
                user_task_execution = session.query(UserTaskExecution) \
                    .filter(UserTaskExecution.user_task_execution_pk == user_task_execution.predefined_action_from_user_task_execution_fk) \
                    .first()
                if user_task_execution:
                    previous_related_user_task_execution.append(user_task_execution)
            return previous_related_user_task_execution
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: previous_related_user_task_execution :: {e}")
        
    @property
    def predefined_actions(self):
        try:
            return self.task.get_predefined_actions_in_language(self.user.language_code)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: predefined_actions :: {e}")