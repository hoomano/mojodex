from app import db, language_retriever, conversation_retriever
from db_models import *
from models.user_task_execution import UserTaskExecution
from models.knowledge.knowledge_collector import KnowledgeCollector

from models.user_task_execution_summarizer import UserTaskExecutionSummarizer

from background_logger import BackgroundLogger


class UserTaskExecutionTitleAndSummaryCortex:
    logger_prefix = "UserTaskExecutionTitleAndSummaryCortex::"

    def __init__(self, user_task_execution):
        try:
            self.logger = BackgroundLogger(
                f"{UserTaskExecutionTitleAndSummaryCortex.logger_prefix} - user_task_execution_pk {user_task_execution.user_task_execution_pk}")
            self.logger.debug(f"__init__")
            
            self.user_task_execution = UserTaskExecution(user_task_execution.user_task_execution_pk)
            self.user = self._get_user()
           

            self.user_summary = self.user.summary
            self.user_messages_conversation = conversation_retriever._get_user_messages_as_conversation(self.user_task_execution.session_id)
            self.company = db.session.query(MdCompany).join(MdUser, MdUser.company_fk == MdCompany.company_pk).filter(
                MdUser.user_id == self.user.user_id).first()

            self.knowledge_collector = KnowledgeCollector(self.user.name, self.user.timezone_offset, self.user_summary, self.user.company_description, self.user.goal)
        except Exception as e:
            self.logger.error(f"__init__ :: {e}")

    def manage_user_task_execution_title_and_summary(self):
        try:
            self.logger.info("manage_user_task_execution_title_and_summary")
            self._summarize_task()
        except Exception as e:
            self.logger.error(f"manage_user_task_execution_title_and_summary: {e}")

    def _summarize_task(self):
        try:
            self.logger.info("_summarize_task")
            user_task_execution_summarizer = UserTaskExecutionSummarizer(self.knowledge_collector,
                                                                         self.user_task_execution, self.user_messages_conversation)
        except Exception as e:
            raise Exception(f"summarize_task: {e}")

    def _get_task_info(self, user_task_execution):
        try:
            user_task_pk, task_name_for_system, task_definition_for_system, task_input_values = db.session.query(
                MdUserTask.user_task_pk, MdTask.name_for_system, MdTask.definition_for_system,
                MdUserTaskExecution.json_input_values) \
                .join(MdUserTask, MdUserTask.task_fk == MdTask.task_pk) \
                .join(MdUserTaskExecution, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk) \
                .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution.user_task_execution_pk) \
                .first()

            return user_task_pk, task_name_for_system, task_definition_for_system, task_input_values
        except Exception as e:
            raise Exception(f"{UserTaskExecutionTitleAndSummaryCortex.logger_prefix} _get_task_info: {e}")

    def _get_user(self):
        try:
            user = db.session.query(MdUser).join(MdUserTask, MdUserTask.user_id == MdUser.user_id).filter(
                MdUserTask.user_task_pk == self.user_task_execution.user_task_fk).first()
            return user
        except Exception as e:
            raise Exception(f"_get_user: {e}")


