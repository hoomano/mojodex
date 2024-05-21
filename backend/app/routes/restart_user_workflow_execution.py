from datetime import datetime
from models.workflows.workflow_execution import WorkflowExecution
from flask import request
from flask_restful import Resource
from app import db, authenticate, server_socket
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import MdUserTaskExecution, MdTask, MdUserTask
from sqlalchemy.orm.attributes import flag_modified

class RestartUserWorkflowExecution(Resource):

    def __init__(self):
        RestartUserWorkflowExecution.method_decorators = [authenticate()]

    def post(self, user_id):
        """Route to restart a workflow execution by changing initial data and restarting the workflow"""
        error_message = "Error while restarting workflow"
        try:
            timestamp = request.form['datetime']
            user_task_execution_pk = request.form['user_task_execution_pk']
            new_inputs = request.form['inputs']
            platform = request.form['platform']
        except KeyError as e:
            return {"error": f"Missing parameter : {e}"}, 400
        
        try:
            result = db.session.query(MdUserTaskExecution, MdTask) \
                .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                .join(MdTask, MdTask.task_pk == MdUserTask.task_fk) \
                .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk) \
                .filter(MdUserTask.user_id == user_id) \
                .first()
            if result is None:
                log_error(
                    f"{error_message} : UserTaskExecution {user_task_execution_pk} not found for user {user_id}")
                return {"error": f"UserTaskExecution  {user_task_execution_pk} not found for this user"}, 400

            user_task_execution, task = result
            if task.type != "workflow":
                log_error(f"{error_message} : Task {task.task_pk} is not a workflow")
                return {"error": "Task is not a workflow"}, 400

            json_input_values = self.user_task_execution_inputs_manager.construct_inputs_from_request(user_task_execution.json_input_values,
                                                                                    new_inputs, request.files, user_id,
                                                                                    user_task_execution.session_id)
            user_task_execution.json_input_values = json_input_values
            flag_modified(user_task_execution, "json_input_values")
            db.session.commit()

            # Invalidate current step
            workflow_execution = WorkflowExecution(user_task_execution_pk)
            server_socket.start_background_task(workflow_execution.restart)

            return {"message": "Workflow restarted"}, 200
        except Exception as e:
            log_error(e)
            return {"error": f"{error_message}: {e}"}, 500
        
  