from jinja2 import Template
from models.produced_text_managers.instruct_task_produced_text_manager import InstructTaskProducedTextManager
from sqlalchemy.orm import object_session

from mojodex_core.entities.user_task_execution import UserTaskExecution

from mojodex_core.entities.instruct_user_task import InstructUserTask


class InstructTaskExecution(UserTaskExecution):
    task_specific_instructions_prompt = "mojodex_core/prompts/tasks/task_specific_instructions.txt"


    @property
    def user_task(self):
        try:
            session = object_session(self)
            return session.query(InstructUserTask).filter(InstructUserTask.user_task_pk == self.user_task_fk).first()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}")

    @property
    def instructions(self):
        try:
            with open(self.task_specific_instructions_prompt, 'r') as f:
                template = Template(f.read())
            return template.render(task=self.task,
                                   user_task_inputs=self.json_input_values,
                                   # TODO
                                   #title_start_tag=InstructTaskProducedTextManager.title_start_tag,
                                   #title_end_tag=InstructTaskProducedTextManager.title_end_tag,
                                   #draft_start_tag=InstructTaskProducedTextManager.draft_start_tag,
                                   #draft_end_tag=InstructTaskProducedTextManager.draft_end_tag,
                                   # task_tool_associations=task_tool_associations
                                   )
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: instructions :: {e}")
