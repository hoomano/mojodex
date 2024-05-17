from flask import request
from flask_restful import Resource
from app import db, authenticate
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import MdUserWorkflowStepExecutionResult, MdUserTaskExecution, MdUserWorkflowStepExecution, MdUserTask


class UserWorkflowStepExecutionResult(Resource):

    def __init__(self):
        UserWorkflowStepExecutionResult.method_decorators = [authenticate()]

     
    def put(self, user_id):
        """Route to edit a previous version of step result"""
        error_message = "Error while saving new step result"
        if not request.json:
            return {"error": "Missing JSON body"}, 400
        try:
            timestamp = request.json['datetime']
            user_workflow_step_execution_pk = request.json['user_workflow_step_execution_pk']
            new_result = request.json['result']
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
            
            step_result = MdUserWorkflowStepExecutionResult(
                user_workflow_step_execution_fk=user_workflow_step_execution_pk,
                result=new_result,
                author='user')
            db.session.add(step_result)
            db.session.commit()
            
            return {"new_result": new_result}, 200
        except Exception as e:
            log_error(e)
            db.session.rollback()
            return {"error": f"{error_message}: {e}"}, 500
        
    