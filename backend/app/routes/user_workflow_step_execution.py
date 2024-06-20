from datetime import datetime
from flask import request
from flask_restful import Resource
from app import db, authenticate, server_socket

from models.workflows.workflow_process_controller import WorkflowProcessController
from mojodex_core.entities.user_workflow_step_execution import UserWorkflowStepExecution as UserWorkflowStepExecutionEntity
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *
from jinja2 import Template

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
            platform = request.json['platform']
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
                
            return {"message": "Step validated"}, 200
        except Exception as e:
            log_error(e)
            return {"error": f"{error_message}: {e}"}, 500
        
    def put(self, user_id):
        """Route to relaunch workflow after a step failed in error"""
        error_message = "Error while relaunching workflow after a step failed in error"
        if not request.json:
            return {"error": "Missing JSON body"}, 400
        try:
            timestamp = request.json['datetime']
            user_workflow_step_execution_pk = request.json['user_workflow_step_execution_pk']
            platform = request.json['platform']
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

            return {"message": "Workflow relaunched"}, 200
        except Exception as e:
            log_error(e)
            return {"error": f"{error_message}: {e}"}, 500
        
    