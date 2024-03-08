from models.session.assistant_message_state.task_enabled_chat_state import TaskEnabledChatState
from app import db
from db_models import MdTask, MdTaskDisplayedData, MdUserTask, MdUserTaskExecution, MdMessage
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime

class GeneralChatState(TaskEnabledChatState):
    logger_prefix = "GeneralChatState :: "

    def __init__(self, running_user_task_execution_pk):
        try:
            super().__init__(running_user_task_execution_pk)
            self.running_task_set = False
        except Exception as e:
            raise Exception(f"{GeneralChatState.logger_prefix} __init__ :: {e}")

    def set_running_task(self, task_pk, session_id):
        try:
            self.running_task_set = True
            if task_pk is not None:
                self.running_task, self.running_task_displayed_data, self.running_user_task = db.session.query(MdTask, MdTaskDisplayedData, MdUserTask)\
                    .join(MdTaskDisplayedData, MdTask.task_pk == MdTaskDisplayedData.task_fk)\
                    .join(MdUserTask, MdTask.task_pk == MdUserTask.task_fk)\
                    .filter(MdTask.task_pk == task_pk).first()
                # create user_task_execution
                self.__create_user_task_execution(session_id)
                self.__associate_previous_user_message(session_id)
            else:
                self.running_task, self.running_task_displayed_data, self.running_user_task, self.running_user_task_execution = None, None, None, None
        except Exception as e:
            raise Exception(f"{GeneralChatState.logger_prefix} set_running_task :: {e}")
        
    def __get_empty_json_input_values(self):
        try:
            empty_json_input_values = []
            for input in self.running_task_displayed_data.json_input:
                input["value"] = None
                empty_json_input_values.append(input)
            return empty_json_input_values
        except Exception as e:
            raise Exception(f"__get_empty_json_input_values :: {e}")
        
    def __create_user_task_execution(self, session_id):
        try:
            empty_json_input_values = self.__get_empty_json_input_values()
           
            task_execution = MdUserTaskExecution(user_task_fk=self.running_user_task.user_task_pk, start_date=datetime.now(),
                                                 json_input_values=empty_json_input_values, session_id=session_id)
            db.session.add(task_execution)
            db.session.commit()
            self.running_user_task_execution = task_execution
        except Exception as e:
            raise Exception(f"__create_user_task_execution :: {e}")

    def __associate_previous_user_message(self, session_id):
        try:
            from models.session.session import Session as SessionModel
            previous_user_message = db.session.query(MdMessage).filter(MdMessage.session_id == session_id).filter(
                MdMessage.sender == SessionModel.user_message_key).order_by(MdMessage.message_date.desc()).first()
            if previous_user_message:
                new_message = previous_user_message.message

                new_message['user_task_execution_pk'] = self.running_user_task_execution.user_task_execution_pk
                previous_user_message.message = new_message
                flag_modified(previous_user_message, "message")
                db.session.commit() 
        except Exception as e:
            raise Exception(f"__associate_previous_user_message :: {e}")
        