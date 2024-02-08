class UserTaskExecution:

    logger_prefix = "UserTaskExecution::"
    def __init__(self, session_id, user_task_execution_pk, task_name, task_definition, json_input_values, task_result, user_id):
        try:
            self.session_id = session_id
            self.user_task_execution_pk = user_task_execution_pk
            self.task_name = task_name
            self.task_definition = task_definition
            self.json_input_values = json_input_values
            self.task_result = task_result
            self.user_id=user_id
        except Exception as e:
            raise Exception(f"{UserTaskExecution.logger_prefix} __init__ :: {e}")