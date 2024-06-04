from models.assistant.models.instruct_task import InstructTask
from mojodex_core.entities import MdUser, MdTask, MdUserTask


class User:

    def __init__(self, user_id, db_session):
        self.user_id = user_id
        self.db_session = db_session
        self.db_object = self._get_db_object(user_id)

    def _get_db_object(self, user_id):
        try:
            return self.db_session.query(MdUser).filter(MdUser.user_id == user_id).first()
        except Exception as e:
            raise Exception(f"_get_db_object :: {e}")

    @property
    def company_knowledge(self):
        try:
            return self.db_object.company_description
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: company_knowledge :: {e}")

    @property
    def username(self):
        try:
            return self.db_object.name
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: username :: {e}")

    @property
    def language_code(self):
        try:
            return self.db_object.language_code
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: language_code :: {e}")

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
