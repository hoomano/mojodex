from models.assistant.models.instruct_task import InstructTask
from mojodex_core.entities import MdUser, MdTask, MdUserTask


class User(MdUser):

    """def _get_db_object(self, user_id):
        try:
            user_data = self.db_session.query(User).filter(User.user_id == user_id).first()
            return {key: getattr(user_data, key) for key in user_data.__dict__ if not key.startswith('_')}
        except Exception as e:
            raise Exception(f"_get_db_object :: {e}")"""



    @property
    def available_instruct_tasks(self):
        try:
            user_tasks = self.db_session.query(MdTask). \
                join(MdUserTask, MdTask.task_pk == MdUserTask.task_fk). \
                filter(MdUserTask.user_id == self.user_id). \
                filter(MdTask.type == "instruct"). \
                filter(MdUserTask.enabled == True).all()
            return [InstructTask(task.task_pk, self.db_session) for task in user_tasks]
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: available_tasks :: {e}")



