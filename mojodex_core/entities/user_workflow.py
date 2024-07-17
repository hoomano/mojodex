from functools import cached_property
from mojodex_core.entities.user_task import UserTask
from sqlalchemy.orm import object_session

from mojodex_core.entities.workflow import Workflow


class UserWorkflow(UserTask):

    @cached_property
    def task(self):
        try:
            session = object_session(self)
            return session.query(Workflow).get(self.task_fk)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: task :: {e}")
        
    @cached_property
    def steps_as_json(self):
        """
        Returns steps of the workflows as json in user's language
        """
        try:
            return self.task.get_json_steps_with_translation(self.user.language_code)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_json_steps :: {e}")