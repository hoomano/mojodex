from flask import request
from flask_restful import Resource
from app import db, server_socket
from mojodex_core.authentication import authenticate
from models.workflows.workflow_process_controller import WorkflowProcessController
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *

class UserWorkflowStepExecution(Resource):

    def __init__(self):
        UserWorkflowStepExecution.method_decorators = [authenticate()]

    def post(self, user_id):
        """Route to validate a step"""
        error_message = "Error while validating step"
        if not request.json:
            return {"error": "Missing JSON body"}, 400
        try:
            timestamp = request.json['datetime']
            user_workflow_step_execution_pk = request.json['user_workflow_step_execution_pk']
            validated = request.json['validated'] # boolean
        except KeyError as e:
            return {"error": f"Missing parameter : {e}"}, 400
        
        try:
            user_task_execution = db.session.query(MdUserTaskExecution)\
                .join(MdUserTask, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk)\
                .join(MdUserWorkflowStepExecution, MdUserWorkflowStepExecution.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk)\
                .filter(MdUserWorkflowStepExecution.user_workflow_step_execution_pk == user_workflow_step_execution_pk)\
                .filter(MdUserTask.user_id == user_id)\
                .first()
            if not user_task_execution:
                return {"error": "Workflow execution not found for this user"}, 404
            workflow_process_controller = WorkflowProcessController(user_task_execution.user_task_execution_pk)
            if validated:
                workflow_process_controller.validate_step_execution(user_workflow_step_execution_pk)
                server_socket.start_background_task(workflow_process_controller.run)
            else:
                workflow_process_controller.add_state_message()
                
            # Normally, flask_socketio will close db.session automatically after the request is done 
            # (https://flask.palletsprojects.com/en/2.3.x/patterns/sqlalchemy/) "Flask will automatically remove database sessions at the end of the request or when the application shuts down."
            # But if may not the case because of the background task launched in this route, errors like `QueuePool limit of size 5 overflow 10 reached` may happen in the backend logs and cause issues.
            # That's why here we explicitely call `db.session.close()` to close the session manually.
            db.session.close()
            return {"message": "Step validated"}, 200
        except Exception as e:
            db.session.rollback()
            log_error(e)
            db.session.close()
            return {"error": f"{error_message}: {e}"}, 500
        
    def put(self, user_id):
        """Route to relaunch workflow after a step failed in error"""
        error_message = "Error while relaunching workflow after a step failed in error"
        if not request.json:
            return {"error": "Missing JSON body"}, 400
        try:
            timestamp = request.json['datetime']
            user_workflow_step_execution_pk = request.json['user_workflow_step_execution_pk']
        except KeyError as e:
            return {"error": f"Missing parameter : {e}"}, 400
        
        try:
            user_task_execution = db.session.query(MdUserTaskExecution)\
                .join(MdUserTask, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk)\
                .join(MdUserWorkflowStepExecution, MdUserWorkflowStepExecution.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk)\
                .filter(MdUserWorkflowStepExecution.user_workflow_step_execution_pk == user_workflow_step_execution_pk)\
                .filter(MdUserTask.user_id == user_id)\
                .first()
            if not user_task_execution:
                return {"error": "Workflow execution not found for this user"}, 404
            
            workflow_process_controller = WorkflowProcessController(user_task_execution.user_task_execution_pk)
        
            server_socket.start_background_task(workflow_process_controller.run)

            # Normally, flask_socketio will close db.session automatically after the request is done 
            # (https://flask.palletsprojects.com/en/2.3.x/patterns/sqlalchemy/) "Flask will automatically remove database sessions at the end of the request or when the application shuts down."
            # But if may not the case because of the background task launched in this route, errors like `QueuePool limit of size 5 overflow 10 reached` may happen in the backend logs and cause issues.
            # That's why here we explicitely call `db.session.close()` to close the session manually.
            db.session.close()
            return {"message": "Workflow relaunched"}, 200
        except Exception as e:
            db.session.rollback()
            log_error(e)
            db.session.close()
            return {"error": f"{error_message}: {e}"}, 500
        
    