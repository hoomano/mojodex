from datetime import datetime
from models.workflows.workflow_execution import WorkflowExecution
from flask import request
from flask_restful import Resource
from app import db, authenticate, server_socket
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import *
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
            
            workflow_execution = WorkflowExecution(user_task_execution.user_task_execution_pk)
            if validated:
                workflow_execution.validate_step_execution(user_workflow_step_execution_pk)
                server_socket.start_background_task(workflow_execution.run)
            else:
                # # todo => set a status rejected ?
                # add new message to db
                current_step_in_validation = workflow_execution.get_step_execution_from_pk(user_workflow_step_execution_pk)
                with open("mojodex_core/prompts/workflows/state.txt", "r") as file:
                    template = Template(file.read())
                    text = template.render(
                        before_checkpoint_validated_steps_executions=workflow_execution.get_before_checkpoint_validated_steps_executions(current_step_in_validation),
                        after_checkpoint_validated_steps_executions=workflow_execution.get_after_checkpoint_validated_steps_executions(current_step_in_validation),
                        current_step=current_step_in_validation,
                        )
                    
                system_message = MdMessage(
                                session_id=user_task_execution.session_id, sender='system', event_name='worflow_step_execution_rejection', message={'text': text},
                                creation_date=datetime.now(), message_date=datetime.now()
                )
                db.session.add(system_message)
                db.session.commit()
                
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
            
            workflow_execution = WorkflowExecution(user_task_execution.user_task_execution_pk)
        
            server_socket.start_background_task(workflow_execution.run)

            return {"message": "Workflow relaunched"}, 200
        except Exception as e:
            log_error(e)
            return {"error": f"{error_message}: {e}"}, 500
        
    