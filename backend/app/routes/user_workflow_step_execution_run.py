from datetime import datetime
from models.workflows.workflow import WorkflowExecution
from flask import request
from flask_restful import Resource
from app import db, authenticate, log_error, server_socket
from mojodex_core.entities import *
from jinja2 import Template

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
            platform = request.json['platform']
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
                server_socket.start_background_task(workflow_execution.run)
            else:
                # # todo => set a status rejected ?
                # add new message to db
                with open("/data/prompts/workflows/state.txt", "r") as file:
                    text = Template(file.read())
                    text = text.render(
                        before_checkpoint_steps_executions=workflow_execution.before_checkpoint_steps_executions,
                        after_checkpoint_to_current_steps_executions=workflow_execution.after_checkpoint_to_current_steps_executions,
                        current_step=workflow_execution.current_step_execution,
                        )
                    
                system_message = MdMessage(
                                session_id=user_workflow_execution.session_id, sender='system', event_name='worflow_step_run_rejection', message={'text': text},
                                creation_date=datetime.now(), message_date=datetime.now()
                )
                db.session.add(system_message)
                db.session.commit()
                workflow_execution.invalidate_current_run()
                from models.session.session import Session as SessionModel
                session = SessionModel(user_workflow_execution.session_id)
                server_socket.start_background_task(session.process_workflow_step_run_rejection, platform, user_workflow_execution.user_workflow_execution_pk)
           
            return {"message": "Step validated"}, 200
        except Exception as e:
            log_error(e)
            return {"error": f"{error_message}: {e}"}, 500