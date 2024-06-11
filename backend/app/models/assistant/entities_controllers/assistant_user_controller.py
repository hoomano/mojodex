from mojodex_core.entities import MdTask, MdUserTask
from mojodex_core.entities_controllers.instruct_task import InstructTask
from mojodex_core.entities_controllers.user import User


class AssistantUserController(User):

    def __init__(self, user_id, db_session):
        super().__init__(user_id, db_session)


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
