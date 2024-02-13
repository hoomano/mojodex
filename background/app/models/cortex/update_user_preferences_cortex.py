
from app import db, language_retriever, conversation_retriever
from db_models import *

from models.user_task_execution import UserTaskExecution
from models.knowledge.knowledge_collector import KnowledgeCollector

from background_logger import BackgroundLogger


from models.user_preferences.user_preferences_manager import UserPreferencesManager


class UpdateUserPreferencesCortex:
    logger_prefix = "UpdateUserPreferencesCortex"

    def __init__(self, user_task_execution):
        try:
            self.logger = BackgroundLogger(
                f"{UpdateUserPreferencesCortex.logger_prefix} - user_task_execution_pk {user_task_execution.user_task_execution_pk}")
            self.logger.debug(f"__init__")

            self.user_task_execution = UserTaskExecution(user_task_execution.user_task_execution_pk)

            self.user = db.session.query(MdUser).join(MdUserTask, MdUserTask.user_id == MdUser.user_id).filter(
                MdUserTask.user_task_pk == self.user_task_execution.user_task_fk).first()

            self.knowledge_collector = KnowledgeCollector(self.user.name, self.user.timezone_offset, self.user.summary, self.user.company_description, self.user.goal)

            self.conversation = conversation_retriever.get_conversation_as_string(self.user_task_execution.session_id, agent_key='YOU', user_key='USER', with_tags=False)

            self.existing_tags = self.__get_existing_tags()


        except Exception as e:
            raise Exception(f"__init__ :: {e}")



    def update_user_preferences(self):
        try:
            self.logger.debug(f"update_user_preferences")
            user_preferences_manager = UserPreferencesManager(self.user.user_id, self.user.name, self.knowledge_collector)
            user_preferences_manager.update(self.user_task_execution.task_name, self.user_task_execution.task_definition,
                                            self.user_task_execution.json_input_values, self.conversation, self.existing_tags)
        except Exception as e:
            self.logger.error(f"update_user_preferences :: {e}")


    def __get_existing_tags(self):
        try:
            self.logger.debug(f"__get_existing_tags")
            existing_tags = db.session.query(MdTag).all()
            return [tag.label for tag in existing_tags]
        except Exception as e:
            raise Exception(f"__get_existing_tags :: {e}")