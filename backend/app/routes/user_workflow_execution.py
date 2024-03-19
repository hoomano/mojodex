from datetime import datetime
from models.session_creator import SessionCreator
from models.workflows.workflow import WorkflowExecution
from flask import request
from flask_restful import Resource
from app import db, authenticate, log_error, server_socket
from mojodex_core.entities import *


class UserWorkflowExecution(Resource):
    def __init__(self):
        UserWorkflowExecution.method_decorators = [authenticate()]
        self.session_creator = SessionCreator()

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
        if not request.json:
            return {"error": "Missing JSON body"}, 400
        try:
            timestamp = request.json['datetime']
            user_workflow_pk = request.json['user_workflow_pk']
            platform = request.json['platform']
        except KeyError as e:
            return {"error": f"Missing parameter : {e}"}, 400
        
        try:
            user_workflow = db.session.query(MdUserWorkflow)\
                .filter(MdUserWorkflow.user_workflow_pk == user_workflow_pk)\
                .filter(MdUserWorkflow.user_id == user_id)\
                .first()
            if not user_workflow:
                return {"error": "Workflow not found for this user"}, 404
            
            # create session
            session_creation = self.session_creator.create_session(user_id, platform, "form")
            if "error" in session_creation[0]:
               return session_creation
            session_id = session_creation[0]["session_id"]
            
            db_workflow_execution = MdUserWorkflowExecution(
                user_workflow_fk=user_workflow_pk,
                session_id=session_id
            )
            db.session.add(db_workflow_execution)
            db.session.commit()
            workflow_execution = WorkflowExecution(db_workflow_execution.user_workflow_execution_pk)
            
            return workflow_execution.to_json(), 200
        except Exception as e:
            db.session.rollback()
            log_error(e)
            return {"error": f"{error_message}: {e}"}, 500
        
    
    def post(self, user_id):
        """Run workflow execution"""
        error_message = "Error while running workflow execution"
        if not request.json:
            return {"error": "Missing JSON body"}, 400
        
        try:
            timestamp = request.json['datetime']
            user_workflow_execution_pk = request.json['user_workflow_execution_pk']
            initial_parameters = request.json['initial_parameters']
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

            # ensure initial_parameters is a json
            if not isinstance(initial_parameters, dict):
                return {"error": "initial_parameters must be a json"}, 400
            workflow_execution.initial_parameters = initial_parameters
            workflow_execution.start_date = datetime.now()
            #workflow_execution.run() # TODO: run must be done asynchronously in a dedicated thread
            server_socket.start_background_task(workflow_execution.run)
            return {"user_workflow_execution_pk": user_workflow_execution_pk}, 200
        except Exception as e:
            log_error(e)
            return {"error": f"{error_message}: {e}"}, 500
        