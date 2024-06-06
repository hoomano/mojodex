from datetime import datetime
from jinja2 import Template
from models.produced_text_managers.instruct_task_produced_text_manager import InstructTaskProducedTextManager
from models.assistant.models.chat_session import ChatSession
from models.assistant.models.instruct_task import InstructTask
from models.assistant.models.user import User
from mojodex_core.entities import MdUserTaskExecution, MdUserTask


class InstructTaskExecution:
    task_specific_instructions_prompt = "mojodex_core/prompts/tasks/task_specific_instructions.txt"

    @classmethod
    def create_from_user_task(cls, user, task_pk, session, db_session):
        try:
            task = InstructTask(task_pk, db_session)
            empty_json_input_values = task.get_json_input_in_language(user.language_code)

            user_task_pk = db_session.query(MdUserTask.user_task_pk).filter(MdUserTask.user_id == user.user_id).filter(
                MdUserTask.task_fk == task_pk).first()[0]

            task_execution = MdUserTaskExecution(user_task_fk=user_task_pk,
                                                 start_date=datetime.now(),
                                                 json_input_values=empty_json_input_values,
                                                 session_id=session.session_id)
            db_session.add(task_execution)
            db_session.commit()

            return cls(user_task_execution_pk=task_execution.user_task_execution_pk, db_session=db_session, user=user,
                       session=session)
        except Exception as e:
            raise Exception(f"{cls.__name__} :: create_user_task_execution :: {e}")

    def __init__(self, user_task_execution_pk, db_session, user=None, task=None, session=None):
        try:
            self.db_session = db_session
            self.user_task_execution_pk = user_task_execution_pk
            self.db_object = self._get_db_object(user_task_execution_pk)
            user_task = self._get_user_task()
            self.user = user if user else User(user_task.user_id, self.db_session)
            self.task = task if task else InstructTask(user_task.task_fk, self.db_session)
            self.session = session if session else ChatSession(self.db_object.session_id, self.db_session)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} __init__ :: {e}")

    def _get_db_object(self, user_task_execution_pk):
        try:
            return self.db_session.query(MdUserTaskExecution).filter(
                MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk).first()
        except Exception as e:
            raise Exception(f"_get_db_object :: {e}")

    def _get_user_task(self):
        try:
            return self.db_session.query(MdUserTask).filter(
                MdUserTask.user_task_pk == self.db_object.user_task_fk).first()
        except Exception as e:
            raise Exception(f"_get_user_task :: {e}")

    @property
    def produced_text_done(self):
        try:
            pass
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}")

    @property
    def user_task_inputs(self):
        try:
            return self.db_object.json_input_values
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: user_task_inputs :: {e}")

    @property
    def instructions(self):
        try:
            with open(self.task_specific_instructions_prompt, 'r') as f:
                template = Template(f.read())
            return template.render(task=self.task,
                                   user_task_inputs=self.user_task_inputs,
                                   title_start_tag=InstructTaskProducedTextManager.title_start_tag,
                                   title_end_tag=InstructTaskProducedTextManager.title_end_tag,
                                   draft_start_tag=InstructTaskProducedTextManager.draft_start_tag,
                                   draft_end_tag=InstructTaskProducedTextManager.draft_end_tag,
                                   # task_tool_associations=task_tool_associations
                                   )
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: instructions :: {e}")

    @property
    def has_images_inputs(self):
        try:
            for input in self.user_task_inputs:
                if input["type"] == "image":
                    return True
            return False
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}:: has_images_inputs :: {e}")

    @property
    def images_input_names(self):
        try:
            input_images = [input["value"] for input in self.user_task_inputs if input["type"] == "image"]
            return input_images
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}:: images_input_names :: {e}")

    @property
    def task_name_in_user_language(self):
        try:
            return self.task.get_task_name_in_language(self.user.language_code)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_task_name_in_user_language :: {e}")
