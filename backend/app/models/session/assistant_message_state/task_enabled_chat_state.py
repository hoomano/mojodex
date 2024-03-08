from models.session.assistant_message_state.chat_state import ChatState
from app import db
from mojodex_core.entities import MdTask, MdUserTask, MdUserTaskExecution, MdTaskDisplayedData, MdProducedText, MdUser
from sqlalchemy import or_, func


class TaskEnabledChatState(ChatState):
    logger_prefix = "TaskEnabledChatState :: "

    def __init__(self, running_user_task_execution_pk):
        try:
            super().__init__()
            if running_user_task_execution_pk:
                self.__set_task_and_execution(running_user_task_execution_pk)
            else:
                self.running_task = None
                self.running_user_task_execution = None
                self.running_task_displayed_data = None
                self.running_user_task = None
        except Exception as e:
            raise Exception(f"{TaskEnabledChatState.logger_prefix} __init__ :: {e}")

    def get_produced_text_done(self):
        try:
            if self.running_user_task_execution is None:
                return False
            return db.session.query(MdProducedText).filter(
                MdProducedText.user_task_execution_fk == self.running_user_task_execution.user_task_execution_pk).count() > 1
        except Exception as e:
            raise Exception(f"{TaskEnabledChatState.logger_prefix} get_produced_text_done :: {e}")
        
    def __set_task_and_execution(self, user_task_execution_pk):
        try:
            self.running_task, self.running_user_task, self.running_user_task_execution = db.session.query(MdTask, MdUserTask, MdUserTaskExecution) \
                .join(MdUserTask, MdUserTask.task_fk == MdTask.task_pk) \
                .join(MdUserTaskExecution, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk) \
                .first()
            
            self.running_task_displayed_data = (
                db.session
                .query(
                    MdTaskDisplayedData,
                )
                .join(MdTask,
                    MdTask.task_pk == MdTaskDisplayedData.task_fk)
                .join(
                    MdUserTask, 
                    MdUserTask.task_fk == MdTask.task_pk
                )
                .join(
                    MdUser, 
                    MdUser.user_id == MdUserTask.user_id
                )
                .filter(
                    MdTaskDisplayedData.task_fk == self.running_task.task_pk
                )
                .filter(
                    or_(
                        MdTaskDisplayedData.language_code == MdUser.language_code,
                        MdTaskDisplayedData.language_code == 'en'
                    )
                )
                .order_by(
                    # Sort by user's language first otherwise by english
                    func.nullif(MdTaskDisplayedData.language_code, 'en').asc()
                )
                .first())
        except Exception as e:
            raise Exception(f"__set_task_and_execution :: {e}")

