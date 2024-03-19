from models.workflows.workflow import WorkflowExecution
from flask import request
from flask_restful import Resource
from app import db, authenticate, log_error, server_socket
from mojodex_core.entities import *


class UserWorkflowStepExecutionRun(Resource):

    def __init__(self):
        UserWorkflowStepExecutionRun.method_decorators = [authenticate()]

    def post(self, user_id):
        """Route to validate a step"""
        error_message = "Error while validating step"
        if not request.json:
            return {"error": "Missing JSON body"}, 400
        try:
            timestamp = request.json['datetime']
            user_workflow_step_execution_run_pk = request.json['user_workflow_step_execution_run_pk']
            validated = request.json['validated'] # boolean
        except KeyError as e:
            return {"error": f"Missing parameter : {e}"}, 400
        
        try:
            user_workflow_execution = db.session.query(MdUserWorkflowExecution)\
                .join(MdUserWorkflow, MdUserWorkflow.user_workflow_pk == MdUserWorkflowExecution.user_workflow_fk)\
                .join(MdUserWorkflowStepExecution, MdUserWorkflowStepExecution.user_workflow_execution_fk == MdUserWorkflowExecution.user_workflow_execution_pk)\
                .join(MdUserWorkflowStepExecutionRun, MdUserWorkflowStepExecutionRun.user_workflow_step_execution_fk == MdUserWorkflowStepExecution.user_workflow_step_execution_pk)\
                .filter(MdUserWorkflowStepExecutionRun.user_workflow_step_execution_run_pk == user_workflow_step_execution_run_pk)\
                .filter(MdUserWorkflow.user_id == user_id)\
                .first()
            if not user_workflow_execution:
                return {"error": "Workflow execution not found for this user"}, 404
            
            workflow_execution = WorkflowExecution(user_workflow_execution.user_workflow_execution_pk)
            if validated:
                workflow_execution.validate_current_run()
            else:
                workflow_execution.invalidate_current_run()
            server_socket.start_background_task(workflow_execution.run)
            #workflow_execution.run()
            return {"message": "Step validated"}, 200
        except Exception as e:
            log_error(e)
            return {"error": f"{error_message}: {e}"}, 500