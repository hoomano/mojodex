from mojodex_core.entities.task import Task
from sqlalchemy.orm import object_session

from mojodex_core.entities.workflow_step import WorkflowStep


class Workflow(Task):

    @property
    def steps(self):
        try:
            session = object_session(self)
            return session.query(WorkflowStep) \
                .filter(WorkflowStep.task_fk == self.db_object.task_pk) \
                .order_by(WorkflowStep.rank.asc()).all()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: steps :: {e}")
