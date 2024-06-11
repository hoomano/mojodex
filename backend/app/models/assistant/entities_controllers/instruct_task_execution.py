from datetime import datetime
from jinja2 import Template
from models.produced_text_managers.instruct_task_produced_text_manager import InstructTaskProducedTextManager
from models.assistant.entities_controllers.assistant_user_controller import AssistantUserController

from mojodex_core.entities_controllers.instruct_task import InstructTask
from mojodex_core.entities_controllers.user_task_execution import UserTaskExecution
from mojodex_core.entities import MdUserTaskExecution, MdUserTask


class InstructTaskExecution(UserTaskExecution):
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

            user_task = self._get_user_task(db_session, user_task_execution_pk)
            user = user if user else AssistantUserController(user_task.user_id, db_session)
            super().__init__(user_task_execution_pk, db_session, task, user, session)

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} __init__ :: {e}")

    def _get_user_task(self, db_session, user_task_execution_pk):
        try:
            return db_session.query(MdUserTask).join(MdUserTaskExecution, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk).filter(
                MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk).first()
        except Exception as e:
            raise Exception(f"_get_user_task :: {e}")

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



