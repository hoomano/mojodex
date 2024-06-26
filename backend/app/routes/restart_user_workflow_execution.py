import json
from models.user_task_execution_inputs_manager import UserTaskExecutionInputsManager
from flask import request
from flask_restful import Resource
from app import db, authenticate, server_socket

from models.workflows.workflow_process_controller import WorkflowProcessController
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import MdUserTaskExecution, MdTask, MdUserTask
from sqlalchemy.orm.attributes import flag_modified

class RestartUserWorkflowExecution(Resource):

    def __init__(self):
        RestartUserWorkflowExecution.method_decorators = [authenticate()]
        self.user_task_execution_inputs_manager = UserTaskExecutionInputsManager()

    def post(self, user_id):
        """Route to restart a workflow execution by changing initial data and restarting the workflow"""
        error_message = "Error while restarting workflow"
        try:
            timestamp = request.form['datetime']
            user_task_execution_pk = request.form['user_task_execution_pk']
            new_inputs = json.loads(request.form["inputs"])
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
            workflow_process_controller = WorkflowProcessController(user_task_execution_pk)
            server_socket.start_background_task(workflow_process_controller.restart)

            # Normally, flask_socketio will close db.session automatically after the request is done 
            # (https://flask.palletsprojects.com/en/2.3.x/patterns/sqlalchemy/) "Flask will automatically remove database sessions at the end of the request or when the application shuts down."
            # But if may not the case because of the background task launched in this route, errors like `QueuePool limit of size 5 overflow 10 reached` may happen in the backend logs and cause issues.
            # That's why here we explicitely call `db.session.close()` to close the session manually.
            db.session.close()

            return {"message": "Workflow restarted"}, 200
        except Exception as e:
            log_error(e)
            return {"error": f"{error_message}: {e}"}, 500
        
  