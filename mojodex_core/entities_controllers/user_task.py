from mojodex_core.entities import MdUserTask
from mojodex_core.entities_controllers.entity_controller import EntityController


class UserTask(EntityController):

    def __init__(self, user_task_pk, db_session):
        super().__init__(MdUserTask, user_task_pk, db_session)

    @property
    def user_task_pk(self):
        try:
            return self.pk
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: user_task_pk :: {e}")

    @property
    def task_fk(self):
        try:
            return self.db_object.task_fk
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: task_fk :: {e}")

    @property
    def user_id(self):
        try:
            return self.db_object.user_id
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: user_id :: {e}")