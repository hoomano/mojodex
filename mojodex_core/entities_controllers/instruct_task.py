from mojodex_core.entities_controllers.task import Task
from mojodex_core.db import Session

class InstructTask(Task):

    def __init__(self, task_pk: int, db_session: Session):
        super().__init__(task_pk, db_session)

    @property
    def infos_to_extract(self):
        try:
            return self.db_object.infos_to_extract
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: infos_to_extract :: {e}")

    @property
    def output_format_instruction_title(self):
        try:
            return self.db_object.output_format_instruction_title
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: output_format_instruction_title :: {e}")

    @property
    def output_format_instruction_draft(self):
        try:
            return self.db_object.output_format_instruction_draft
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: output_format_instruction_draft :: {e}")

    @property
    def final_instruction(self):
        try:
            return self.db_object.final_instruction
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: final_instruction :: {e}")
