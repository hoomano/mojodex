from functools import cached_property
from mojodex_core.entities.user_task import UserTask
from mojodex_core.entities.instruct_task import InstructTask
from sqlalchemy.orm import object_session



class InstructUserTask(UserTask):

    @cached_property
    def task(self):
        try:
            session = object_session(self)
            return session.query(InstructTask).filter(InstructTask.task_pk == self.task_fk).first()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: task :: {e}")