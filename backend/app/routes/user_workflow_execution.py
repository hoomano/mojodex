from models.workflows.workflow import WorkflowExecution
from flask import request
from flask_restful import Resource
from app import db, authenticate, log_error
from mojodex_core.entities import *


class UserWorkflowExecution(Resource):
    def __init__(self):
        UserWorkflowExecution.method_decorators = [authenticate()]

    def get(self, user_id):
        """Get the json describing workflow's state"""
        error_message = "Error while getting workflow execution"
        try:
            timestamp = request.args['datetime']
            user_workflow_execution_pk = request.args['user_workflow_execution_pk']
        except KeyError as e:
            return {"error": f"Missing parameter : {e}"}, 400
        
        try:
            user_workflow_execution = db.session.query(MdUserWorkflowExecution)\
                .join(MdUserWorkflow, MdUserWorkflow.user_workflow_pk == MdUserWorkflowExecution.user_workflow_fk)\
                .filter(MdUserWorkflowExecution.user_workflow_execution_pk == user_workflow_execution_pk)\
                .filter(MdUserWorkflow.user_id == user_id)\
                .first()
            if not user_workflow_execution:
                return {"error": "Workflow execution not found for this user"}, 404
            
            workflow_execution = WorkflowExecution(user_workflow_execution_pk)

            return workflow_execution.to_json(), 200
        except Exception as e:
            log_error(e)
            return {"error": f"{error_message}: {e}"}, 500
        
    
    def put(self, user_id):
        """Create new user_workflow_execution"""
        error_message = "Error while creating workflow execution"
        try:
            timestamp = request.json['datetime']
            user_workflow_pk = request.json['user_workflow_pk']
        except KeyError as e:
            return {"error": f"Missing parameter : {e}"}, 400
        
        try:
            user_workflow = db.session.query(MdUserWorkflow)\
                .filter(MdUserWorkflow.user_workflow_pk == user_workflow_pk)\
                .filter(MdUserWorkflow.user_id == user_id)\
                .first()
            if not user_workflow:
                return {"error": "Workflow not found for this user"}, 404
            
            db_workflow_execution = MdUserWorkflowExecution(
                user_workflow_fk=user_workflow_pk
            )
            db.session.add(db_workflow_execution)
            db.session.commit()
            return {"user_workflow_execution_pk": db_workflow_execution.user_workflow_execution_pk}, 200
        except Exception as e:
            log_error(e)
            return {"error": f"{error_message}: {e}"}, 500
        
    
    # todo: post for starting a workflow execution