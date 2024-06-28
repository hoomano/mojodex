from jinja2 import Template
from sqlalchemy.orm import object_session
from mojodex_core.entities.abstract_entities.user_task_execution import UserTaskExecution
from mojodex_core.entities.instruct_user_task import InstructUserTask
from mojodex_core.produced_text_managers.task_produced_text_manager import TaskProducedTextManager


class InstructTaskExecution(UserTaskExecution):
    task_specific_instructions_prompt = "mojodex_core/prompts/tasks/task_specific_instructions.txt"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    @property
    def user_task(self):
        try:
            session = object_session(self)
            return session.query(InstructUserTask).get(self.user_task_fk)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}:: user_task :: {e}")

    @property
    def instructions(self):
        try:
            with open(self.task_specific_instructions_prompt, 'r') as f:
                template = Template(f.read())
            return template.render(task=self.task,
                                   user_task_inputs=self.json_input_values,
                                   title_start_tag=TaskProducedTextManager.title_tag_manager.start_tag,
                                   title_end_tag=TaskProducedTextManager.title_tag_manager.end_tag,
                                   draft_start_tag=TaskProducedTextManager.draft_tag_manager.start_tag,
                                   draft_end_tag=TaskProducedTextManager.draft_tag_manager.end_tag,
                                   )
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: instructions :: {e}")
