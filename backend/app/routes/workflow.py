from flask import request
from flask_restful import Resource
from app import db
import os
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import *
from models.workflows.steps_library import steps_class


class Workflow(Resource):
    logger_prefix = "Route :: Workflow :: "

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
            platforms = request.json["platforms"]
            name_for_system = request.json['name_for_system']
            icon = request.json['icon']
            definition_for_system = request.json['definition_for_system']
            workflow_displayed_data = request.json["workflow_displayed_data"]
            steps = request.json['steps']
            output_type = request.json["output_type"].strip().lower()
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
            # ensure output_type is in md_text_type
            db_output_type = \
            db.session.query(MdTextType.text_type_pk).filter(MdTextType.name == output_type).first()
            if not db_output_type:
                # add text_type to md_text_type
                text_type = MdTextType(name=output_type)
                db.session.add(text_type)
                db.session.flush()
                db.session.refresh(text_type)
                output_type_pk = text_type.text_type_pk
            else:
                output_type_pk = db_output_type[0]
            # ensure platform is a list
            if not isinstance(platforms, list):
                return {"error": f"'platforms' must be a list"}, 400
            # get platform_pk of each platform based on platform name
            platform_pks = []
            for platform_name in platforms:
                md_platform = db.session.query(MdPlatform).filter(MdPlatform.name == platform_name).first()
                if md_platform is None:
                    return {"error": f"Platform '{platform_name}' is an invalid platform"}, 400
                else:
                    platform_pks.append(md_platform.platform_pk)

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
                definition_for_system=definition_for_system,
                output_text_type_fk=output_type_pk
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
                return {"error": "Steps must be a list of string"}, 400

            for step_index in range(len(steps)):
                step = steps[step_index]
                # check step is a dict
                if not isinstance(step, dict):
                    return {"error": "Step must be a dict"}, 400
                if "name_for_system" not in step:
                    return {"error": "Step must contain 'name_for_system'"}, 400
                step_name_for_system = step["name_for_system"]
                # ensure key exists in steps_class
                if step_name_for_system not in steps_class:
                    return {"error": f"Step {step_name_for_system} not found in steps library"}, 400

                db_step = MdWorkflowStep(
                    name_for_system=step_name_for_system,
                    workflow_fk=db_workflow.workflow_pk,
                    rank=step_index + 1
                )
                db.session.add(db_step)
                db.session.flush()

                if "step_displayed_data" not in step:
                    return {"error": f"Step {step_name_for_system} must contain 'step_displayed_data'"}, 400
                step_displayed_data = step["step_displayed_data"]

                # check content of step_displayed_data
                if not isinstance(step_displayed_data, list):
                    return {"error": f"Step_displayed_data for step {step_name_for_system} must be a list of dict"}, 400
                for translation in step_displayed_data:
                    if not isinstance(translation, dict):
                        return {"error": f"Step_displayed_data for step {step_name_for_system} must be a list of dict"}, 400
                    if "language_code" not in translation:
                        return {"error": f"Step_displayed_data for step {step_name_for_system} must contain 'language_code'"}, 400
                    step_language_code = translation["language_code"]
                    if "name_for_user" not in translation:
                        return {"error": f"Step_displayed_data for step {step_name_for_system} - language {step_language_code} must contain 'name_for_user'"}, 400
                    step_name_for_user = translation["name_for_user"]
                    if "definition_for_user" not in translation:
                        return {"error": f"Step_displayed_data for step {step_name_for_system} - language {step_language_code} must contain 'definition_for_user'"}, 400
                    step_definition_for_user = translation["definition_for_user"]

                    # add step_displayed_data to db
                    db_step_displayed_data = MdWorkflowStepDisplayedData(
                        workflow_step_fk=db_step.workflow_step_pk,
                        language_code=step_language_code,
                        name_for_user=step_name_for_user,
                        definition_for_user=step_definition_for_user
                    )
                    db.session.add(db_step_displayed_data)
                    db.session.flush()

            # add workflow_platform_association
            for platform_pk in platform_pks:
                workflow_platform_association = MdWorkflowPlatformAssociation(
                    workflow_fk=db_workflow.workflow_pk,
                    platform_fk=platform_pk
                )
                db.session.add(workflow_platform_association)
            db.session.commit()
            return {"workflow_pk": db_workflow.workflow_pk}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"{self.logger_prefix} - Error while creating workflow: {e}")
            return {"error": f"Error while creating workflow: {e}"}, 500

    def _get_workflow_steps(self, workflow_pk):
        try:
            steps = db.session.query(MdWorkflowStep) \
                .filter(MdWorkflowStep.workflow_fk == workflow_pk) \
                .order_by(MdWorkflowStep.rank) \
                .all()
            steps_json = []
            for step in steps:
                step_translations = db.session.query(MdWorkflowStepDisplayedData).filter(
                    MdWorkflowStepDisplayedData.workflow_step_fk == step.workflow_step_pk).all()
                step_displayed_data = [
                    {
                        "language_code": translation.language_code,
                        "name_for_user": translation.name_for_user,
                        "definition_for_user": translation.definition_for_user
                    } for translation in step_translations]

                steps_json.append({
                    "step_pk": step.workflow_step_pk,
                    "name_for_system": step.name_for_system,
                    "rank": step.rank,
                    "step_displayed_data": step_displayed_data
                })
            return steps_json
        except Exception as e:
            raise Exception(f"Error getting workflow steps : {e}")

    def get(self):
        try:
            secret = request.headers['Authorization']
            if secret != os.environ["BACKOFFICE_SECRET"]:
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"{self.logger_prefix} - Error getting workflow json : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        # data
        try:
            timestamp = request.args["datetime"]
            workflow_pk = int(request.args["workflow_pk"])
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            result = db.session.query(MdWorkflow, MdTextType) \
                .filter(MdWorkflow.workflow_pk == workflow_pk) \
                .join(MdTextType, MdTextType.text_type_pk == MdWorkflow.output_text_type_fk) \
                .first()
            if result is None:
                return {"error": f"Workflow with pk {workflow_pk} not found"}, 404
            workflow, output_type = result
            workflow_translations = db.session.query(MdWorkflowDisplayedData).filter(
                MdWorkflowDisplayedData.workflow_fk == workflow_pk).all()
            workflow_displayed_data = [
                {
                    "language_code": translation.language_code,
                    "name_for_user": translation.name_for_user,
                    "definition_for_user": translation.definition_for_user,
                    "json_inputs_spec": translation.json_inputs_spec
                } for translation in workflow_translations]

            platforms = (
                db.session
                .query(
                    MdPlatform
                )
                .join(
                    MdWorkflowPlatformAssociation,
                    MdWorkflowPlatformAssociation.platform_fk == MdPlatform.platform_pk
                )
                .filter(
                    MdWorkflowPlatformAssociation.workflow_fk == workflow_pk
                )
                .all())

            platforms = [platform.name for platform in platforms]

            workflow_json = {
                "workflow_pk": workflow_pk,
                "platforms": platforms,
                "workflow_displayed_data": workflow_displayed_data,
                "name_for_system": workflow.name_for_system,
                "definition_for_system": workflow.definition_for_system,
                "icon": workflow.icon,
                "output_type": output_type.name,
                "steps": self._get_workflow_steps(workflow_pk)
            }

            return workflow_json, 200

        except Exception as e:
            log_error(f"{self.logger_prefix} Error getting workflow json : {e}")
            db.session.rollback()
            return {"error": f"Error getting workflow json : {e}"}, 500
