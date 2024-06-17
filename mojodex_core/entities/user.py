from mojodex_core.entities.db_base_entities import MdUser, MdTask, MdUserTask
from sqlalchemy.orm import object_session

from mojodex_core.entities.instruct_task import InstructTask


class User(MdUser):

    @property
    def available_instruct_tasks(self):
        try:
            session = object_session(self)
            return session.query(InstructTask). \
                join(MdUserTask, InstructTask.task_pk == MdUserTask.task_fk). \
                filter(MdUserTask.user_id == self.user_id). \
                filter(InstructTask.type == "instruct"). \
                filter(MdUserTask.enabled == True).all()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: available_tasks :: {e}")