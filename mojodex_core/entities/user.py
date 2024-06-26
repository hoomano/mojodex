from datetime import datetime, timedelta

from mojodex_core.entities.db_base_entities import MdUser, MdTask, MdUserTask
from sqlalchemy.orm import object_session

from mojodex_core.entities.instruct_task import InstructTask
from mojodex_core.llm_engine.mpt import MPT


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

    @property
    def local_datetime(self):
        try:
            timestamp = datetime.utcnow()
            if self.timezone_offset:
                timestamp -= timedelta(minutes=self.timezone_offset)
            return timestamp
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: local_datetime :: {e}")

    @property
    def datetime_context(self):
        try:
            return MPT("mojodex_core/instructions/global_context.mpt", weekday=self.local_datetime.strftime("%A"),
                   datetime=self.local_datetime.strftime("%d %B %Y"),
                   time=self.local_datetime.strftime("%H:%M")).prompt
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: datetime_context :: {e}")