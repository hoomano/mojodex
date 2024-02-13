from app import db
from db_models import MdUserTaskExecution, MdTask, MdUserTask, MdProducedText, MdProducedTextVersion


class UserTaskExecution:

    logger_prefix = "UserTaskExecution::"
    def __init__(self, user_task_execution_pk):
        try:
            self.user_task_execution_pk = user_task_execution_pk
            self.__get_info()
        except Exception as e:
            raise Exception(f"{UserTaskExecution.logger_prefix} __init__ :: {e}")

    def __get_info(self):
        try:
            results = db.session.query(MdUserTaskExecution, MdTask, MdUserTask.user_id)\
                .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk)\
                .join(MdTask, MdUserTask.task_fk == MdTask.task_pk)\
                .filter(MdUserTaskExecution.user_task_execution_pk == self.user_task_execution_pk)\
                .first()
            if results is None:
                raise Exception(f"{UserTaskExecution.logger_prefix} __get_info :: user_task_execution_pk {self.user_task_execution_pk} not found")
            self.session_id = results.MdUserTaskExecution.session_id
            self.task_name = results.MdTask.name_for_system
            self.task_definition = results.MdTask.definition_for_system
            self.json_input_values = results.MdUserTaskExecution.json_input_values
            # if values from json_input_values are all null, json_input_values = null
            if all([json_input_value["value"] is None for json_input_value in self.json_input_values]):
                self.json_input_values = None

            self.user_id = results.user_id
            self.user_task_fk = results.MdUserTaskExecution.user_task_fk

            task_result = db.session.query(MdProducedTextVersion.production) \
                .join(MdProducedText, MdProducedTextVersion.produced_text_fk == MdProducedText.produced_text_pk) \
                .join(MdUserTaskExecution,MdProducedText.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk) \
                .filter(MdUserTaskExecution.user_task_execution_pk == self.user_task_execution_pk) \
                .order_by(MdProducedTextVersion.creation_date.desc()) \
                .first()

            self.task_result = task_result[0] if task_result else None

        except Exception as e:
            raise Exception(f"{UserTaskExecution.logger_prefix} __get_info :: {e}")