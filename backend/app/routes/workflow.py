from flask import request
from flask_restful import Resource
from app import db
import os
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import *
from models.workflows.steps_library import steps_class


class Workflow(Resource):

    def put(self):
        """Create new workflow"""
        if not request.is_json:
            return {"error": "Request must be JSON"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["BACKOFFICE_SECRET"]:
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            return {"error": f"Missing Authorization secret in headers"}, 403

        try:
            timestamp = request.json['datetime']
            name_for_system = request.json['name_for_system']
            icon = request.json['icon']
            definition_for_system = request.json['definition_for_system']
            workflow_displayed_data = request.json["workflow_displayed_data"]
            steps = request.json['steps']
        except KeyError as e:
            return {"error": f"Missing parameter : {e}"}, 400

        try:
            # ensure there is no space and no upper case in name_for system
            if " " in name_for_system:
                return {
                    "error": f"name_for_system must not contain spaces but underscores. Example : 'answer_to_prospect'"}, 400
            if name_for_system != name_for_system.lower():
                return {
                    "error": f"name_for_system must be in lower case and use underscores. Example : 'answer_to_prospect'"}, 400

            # ensure that displayed_data is a list
            if not isinstance(workflow_displayed_data, list):
                return {
                    "error": f"workflow_displayed_data must be a list of dict specifying the corresponding language_code"}, 400
            else:
                for translation in workflow_displayed_data:
                    if "language_code" not in translation:
                        return {"error": f"language_code undefined, specify the corresponding language_code"}, 400
                    language_code = translation["language_code"]

                    if "name_for_user" not in translation:
                        return {"error": f"name_for_user missing for language_code '{language_code}'"}, 400

                    if "definition_for_user" not in translation:
                        return {"error": f"definition_for_user missing for language_code '{language_code}'"}, 400

                    if "json_inputs_spec" not in translation:
                        return {"error": f"json_input missing for language_code '{language_code}'"}, 400
                    else:
                        json_inputs_spec = translation["json_inputs_spec"]
                        # ensure json_inputs_spec is a list and each elements are dict
                        if not isinstance(json_inputs_spec, list):
                            return {
                                "error": f"json_inputs_spec for language_code '{language_code}' must be a list of dict"}, 400
                        for item in json_inputs_spec:
                            if not isinstance(item, dict):
                                return {
                                    "error": f"json_inputs_spec for language_code '{language_code}' must be a list of dict"}, 400
                            if "input_name_for_system" not in item:
                                return {
                                    "error": f"json_inputs_spec for language_code '{language_code}' must contain 'input_name'"}, 400
                            if "type" not in item:
                                return {
                                    "error": f"json_inputs_spec for language_code '{language_code}' must contain 'type'"}, 400
                            if "input_name_for_user" not in item:
                                return {
                                    "error": f"json_inputs_spec for language_code '{language_code}' must contain 'description_for_user'"}, 400

            db_workflow = MdWorkflow(
                name_for_system=name_for_system,
                icon=icon,
                definition_for_system=definition_for_system
            )
            db.session.add(db_workflow)
            db.session.flush()

            for translation in workflow_displayed_data:
                # SAVE TRANSLATIONS
                workflow_displayed_data = MdWorkflowDisplayedData(
                    workflow_fk=db_workflow.workflow_pk,
                    language_code=translation["language_code"],
                    name_for_user=translation["name_for_user"],
                    definition_for_user=translation["definition_for_user"],
                    json_inputs_spec=translation["json_inputs_spec"]
                )
                db.session.add(workflow_displayed_data)
                db.session.flush()

            # ensure steps is a list
            if not isinstance(steps, list):
                return {"error": "Steps should be a list of string"}, 400

            for step_index in range(len(steps)):
                step = steps[step_index]
                # check step is a string
                if not isinstance(step, str):
                    return {"error": "Step should be a string"}, 400
                # check if step exists in db
                db_step = db.session.query(MdWorkflowStep) \
                    .filter(MdWorkflowStep.name == step) \
                    .filter(MdWorkflowStep.workflow_fk == db_workflow.workflow_pk) \
                    .first()
                if not db_step:
                    # ensure key exists in steps_class 
                    if not step in steps_class:
                        return {"error": f"Step {step} not found in steps library"}, 400
                    db_step = MdWorkflowStep(
                        name=step,
                        workflow_fk=db_workflow.workflow_pk,
                        rank=step_index + 1
                    )
                    db.session.add(db_step)
                    db.session.flush()

            db.session.commit()
            return {"workflow_pk": db_workflow.workflow_pk}, 200
        except Exception as e:
            db.session.rollback()
            log_error(e)
            return {"error": f"Error while creating workflow: {e}"}, 500

    def get(self):
        try:
            secret = request.headers['Authorization']
            if secret != os.environ["BACKOFFICE_SECRET"]:
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"Error getting workflow json : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        # data
        try:
            timestamp = request.args["datetime"]
            workflow_pk = int(request.args["workflow_pk"])
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            workflow = db.session.query(MdWorkflow) \
                .filter(MdWorkflow.workflow_pk == workflow_pk) \
                .first()
            if workflow is None:
                return {"error": f"Workflow with pk {workflow_pk} not found"}, 404

            workflow_translations = db.session.query(MdWorkflowDisplayedData).filter(
                MdWorkflowDisplayedData.workflow_fk == workflow_pk).all()
            workflow_displayed_data = [
                {
                    "language_code": translation.language_code,
                    "name_for_user": translation.name_for_user,
                    "definition_for_user": translation.definition_for_user,
                    "json_inputs_spec": translation.json_inputs_spec
                } for translation in workflow_translations]

            workflow_json = {
                "workflow_pk": workflow_pk,
                "workflow_displayed_data": workflow_displayed_data,
                "name_for_system": workflow.name_for_system,
                "definition_for_system": workflow.definition_for_system,
                "icon": workflow.icon
            }

            return workflow_json, 200

        except Exception as e:
            log_error(f"Error getting workflow json : {e}")
            db.session.rollback()
            return {"error": f"Error getting workflow json : {e}"}, 500
