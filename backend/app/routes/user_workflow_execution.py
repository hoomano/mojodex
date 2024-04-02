from datetime import datetime
from models.session_creator import SessionCreator
from models.workflows.workflow import WorkflowExecution
from flask import request
from flask_restful import Resource
from app import db, authenticate, server_socket
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import *
from sqlalchemy.orm.attributes import flag_modified

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
            result = db.session.query(MdUserWorkflow, MdWorkflow)\
                .join(MdWorkflow, MdWorkflow.workflow_pk == MdUserWorkflow.workflow_fk)\
                .filter(MdUserWorkflow.user_workflow_pk == user_workflow_pk)\
                .filter(MdUserWorkflow.user_id == user_id)\
                .first()
            if not result:
                return {"error": "Workflow not found for this user"}, 404
            
            user_workflow, workflow = result
            
            # create session
            session_creation = self.session_creator.create_session(user_id, platform, "form")
            if "error" in session_creation[0]:
               return session_creation
            session_id = session_creation[0]["session_id"]

            empty_json_input_values = []
            for input in workflow.json_inputs_spec:
                # append input to empty_json_input_values but with additional field "value" without editing json_input
                new_input = input.copy()
                new_input["value"] = input["default_value"] # todo: remove default_value and change by none
                empty_json_input_values.append(new_input)
            
            db_workflow_execution = MdUserWorkflowExecution(
                user_workflow_fk=user_workflow_pk,
                session_id=session_id,
                json_inputs=empty_json_input_values
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
            json_inputs = request.json['json_inputs']
        except KeyError as e:
            return {"error": f"Missing parameter : {e}"}, 400
        
        try:
            db_workflow_execution = db.session.query(MdUserWorkflowExecution)\
                .join(MdUserWorkflow, MdUserWorkflow.user_workflow_pk == MdUserWorkflowExecution.user_workflow_fk)\
                .filter(MdUserWorkflowExecution.user_workflow_execution_pk == user_workflow_execution_pk)\
                .filter(MdUserWorkflow.user_id == user_id)\
                .first()
            if not db_workflow_execution:
                return {"error": "Workflow execution not found for this user"}, 404
            
            # ensure json_inputs is a list
            # TODO: also ensure it contains input_name and value
            if not isinstance(json_inputs, list):
                return {"error": "json_inputs must be a list"}, 400
            db_workflow_execution.json_inputs = json_inputs
            flag_modified(db_workflow_execution, "json_inputs")
            db_workflow_execution.start_date = datetime.now()
            db.session.commit()

            workflow_execution = WorkflowExecution(user_workflow_execution_pk)

            server_socket.start_background_task(workflow_execution.run)
            return {"user_workflow_execution_pk": user_workflow_execution_pk}, 200
        except Exception as e:
            log_error(e)
            return {"error": f"{error_message}: {e}"}, 500
        