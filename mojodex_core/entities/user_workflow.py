from mojodex_core.entities.user_task import UserTask
from sqlalchemy.orm import object_session

from mojodex_core.entities.workflow import Workflow


class UserWorkflow(UserTask):

    @property
    def task(self):
        try:
            session = object_session(self)
            return session.query(Workflow).filter(Workflow.task_pk == self.task_fk).first()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: task :: {e}")