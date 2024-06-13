from mojodex_core.entities.db_base_entities import MdUser, MdTask, MdUserTask
from sqlalchemy.orm import object_session

class User(MdUser):

    @property
    def available_instruct_tasks(self):
        try:
            session = object_session(self)
            user_tasks = session.query(MdTask). \
                join(MdUserTask, MdTask.task_pk == MdUserTask.task_fk). \
                filter(MdUserTask.user_id == self.user_id). \
                filter(MdTask.type == "instruct"). \
                filter(MdUserTask.enabled == True).all()
            return [task.name_for_system for task in user_tasks]
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: available_tasks :: {e}")