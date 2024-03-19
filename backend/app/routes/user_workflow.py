from flask import request
from flask_restful import Resource
from app import db, authenticate, log_error
from mojodex_core.entities import *
from sqlalchemy import and_, or_, func
from sqlalchemy.sql.functions import coalesce
from packaging import version


class UserWorkflow(Resource):

    def __init__(self):
        UserWorkflow.method_decorators = [authenticate()]

    def get(self, user_id):
        error_message = "Error getting user_workflows"
        try:
            timestamp = request.args["datetime"]
            platform = request.args["platform"] if "platform" in request.args else "webapp" # for the moment default to webapp if nothing is passed
            app_version =  version.parse(request.args["version"]) if "version" in request.args else version.parse("0.0.0") # for the moment default to 0.0.0 if nothing is passed
        except KeyError as e:
            log_error(f"{error_message}: Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            if "user_workflow_pk" in request.args:
                user_workflow_pk = int(request.args["user_workflow_pk"])

                # get user_workflow info
                result = db.session.query(MdUserWorkflow, MdWorkflow)\
                    .join(MdWorkflow, MdWorkflow.workflow_pk == MdUserWorkflow.workflow_fk)\
                    .filter(MdUserWorkflow.user_workflow_pk == user_workflow_pk)\
                    .filter(MdUserWorkflow.user_id == user_id)\
                    .first()
                
                if not result:
                    return {"error": "Workflow not found for this user"}, 404
                
                user_workflow, workflow = result
                return {
                    "user_workflow_pk": user_workflow.user_workflow_pk,
                    "workflow_pk": workflow.workflow_pk,
                    "name": workflow.name,
                    "icon": workflow.icon,
                    "description": workflow.description,
                    "inputs_spec": workflow.json_inputs_spec,
                }, 200
                

            # get user_workflows
            n_user_workflows = min(50, int(request.args["n_user_workflows"])) if "n_user_workflows" in request.args else 50
            offset = int(request.args["offset"]) if "offset" in request.args else 0

            results = db.session.query(MdUserWorkflow, MdWorkflow)\
                .join(MdWorkflow, MdWorkflow.workflow_pk == MdUserWorkflow.workflow_fk)\
                .filter(MdUserWorkflow.user_id == user_id)\
                .order_by(MdUserWorkflow.workflow_fk)\
                .limit(n_user_workflows)\
                .offset(offset)\
                .all()
            
            return {'user_workflows': [{
                "user_workflow_pk": user_workflow.user_workflow_pk,
                "workflow_pk": workflow.workflow_pk,
                "name": workflow.name,
                "icon": workflow.icon,
                "description": workflow.description,
                "inputs_spec": workflow.json_inputs_spec,
            } for user_workflow, workflow in results]}, 200
            
        except Exception as e:
            db.session.rollback()
            log_error(f"{error_message} : {e}")
            return {"error": f"{e}"}, 404

