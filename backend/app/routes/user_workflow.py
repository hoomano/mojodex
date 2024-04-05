import os
from flask import request
from flask_restful import Resource
from app import db, authenticate
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import *
from sqlalchemy import and_, or_, func
from sqlalchemy.sql.functions import coalesce
from packaging import version


class UserWorkflow(Resource):

    def __init__(self):
        UserWorkflow.method_decorators = [authenticate(methods=["GET"])]

    def _get_workflow_steps_in_user_language(self, workflow_pk, user_id):
        # Subquery for user_language_code
        user_lang_subquery = (
            db.session.query(
                MdWorkflowStepDisplayedData.workflow_step_fk.label("workflow_step_fk"),
                MdWorkflowStepDisplayedData.name_for_user.label("user_lang_name_for_user"),
                MdWorkflowStepDisplayedData.definition_for_user.label("user_lang_definition_for_user"),
            )
            .join(MdUser, MdUser.user_id == user_id)
            .filter(MdWorkflowStepDisplayedData.language_code == MdUser.language_code)
            .subquery()
        )

        # Subquery for 'en'
        en_subquery = (
            db.session.query(
                MdWorkflowStepDisplayedData.workflow_step_fk.label("workflow_step_fk"),
                MdWorkflowStepDisplayedData.name_for_user.label("en_name_for_user"),
                MdWorkflowStepDisplayedData.definition_for_user.label("en_definition_for_user"),
            )
            .filter(MdWorkflowStepDisplayedData.language_code == "en")
            .subquery()
        )

        steps = db.session.query(MdWorkflowStep, coalesce(
            user_lang_subquery.c.user_lang_name_for_user,
            en_subquery.c.en_name_for_user).label(
            "name_for_user"),
                                 coalesce(
                                     user_lang_subquery.c.user_lang_definition_for_user,
                                     en_subquery.c.en_definition_for_user).label(
                                     "definition_for_user")) \
            .outerjoin(user_lang_subquery, MdWorkflowStep.workflow_step_pk == user_lang_subquery.c.workflow_step_fk) \
            .outerjoin(en_subquery, MdWorkflowStep.workflow_step_pk == en_subquery.c.workflow_step_fk) \
            .filter(MdWorkflowStep.workflow_fk == workflow_pk) \
            .order_by(MdWorkflowStep.rank) \
            .all()

        return [{
            'workflow_step_pk': step.workflow_step_pk,
            'step_name_for_user': name_for_user,
            'step_definition_for_user': definition_for_user
        } for step, name_for_user, definition_for_user in steps
        ]

    def get(self, user_id):
        error_message = "Error getting user_workflows"
        try:
            timestamp = request.args["datetime"]
            platform = request.args[
                "platform"] if "platform" in request.args else "webapp"  # for the moment default to webapp if nothing is passed
            app_version = version.parse(request.args["version"]) if "version" in request.args else version.parse(
                "0.0.0")  # for the moment default to 0.0.0 if nothing is passed
        except KeyError as e:
            log_error(f"{error_message}: Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            if "user_workflow_pk" in request.args:
                user_workflow_pk = int(request.args["user_workflow_pk"])

                # get user_workflow info
                result = db.session.query(MdUserWorkflow, MdWorkflow, MdWorkflowDisplayedData) \
                    .join(MdWorkflow, MdWorkflow.workflow_pk == MdUserWorkflow.workflow_fk) \
                    .join(MdWorkflowDisplayedData, MdWorkflowDisplayedData.workflow_fk == MdWorkflow.workflow_pk) \
                    .join(MdUser, MdUser.user_id == MdUserWorkflow.user_id) \
                    .filter(MdUserWorkflow.user_id == user_id) \
                    .filter(MdUserWorkflow.user_workflow_pk == user_workflow_pk) \
                    .filter(or_(
                        MdWorkflowDisplayedData.language_code == MdUser.language_code,
                        MdWorkflowDisplayedData.language_code == 'en'
                    )) \
                    .order_by(
                    # Sort by user's language first otherwise by english
                    func.nullif(MdWorkflowDisplayedData.language_code, 'en').asc()
                    ) \
                    .first()

                if not result:
                    log_error(f"Workflow with user_workflow_pk {user_workflow_pk} not found for this user")
                    return {"error": f"Workflow with user_workflow_pk {user_workflow_pk} not found for this user"}, 404

                user_workflow, workflow, workflow_displayed_data = result
                return {
                    "user_workflow_pk": user_workflow.user_workflow_pk,
                    "workflow_pk": workflow.workflow_pk,
                    "name": workflow_displayed_data.name_for_user,
                    "icon": workflow.icon,
                    "steps": self._get_workflow_steps_in_user_language(workflow.workflow_pk, user_id),
                    "definition": workflow_displayed_data.definition_for_user
                }, 200

            # get user_workflows
            n_user_workflows = min(50,
                                   int(request.args["n_user_workflows"])) if "n_user_workflows" in request.args else 50
            offset = int(request.args["offset"]) if "offset" in request.args else 0

            # Subquery for user_language_code
            user_lang_subquery = (
                db.session.query(
                    MdWorkflowDisplayedData.workflow_fk.label("workflow_fk"),
                    MdWorkflowDisplayedData.name_for_user.label("user_lang_name_for_user"),
                    MdWorkflowDisplayedData.definition_for_user.label("user_lang_definition_for_user"),
                )
                .join(MdUser, MdUser.user_id == user_id)
                .filter(MdWorkflowDisplayedData.language_code == MdUser.language_code)
                .subquery()
            )

            # Subquery for 'en'
            en_subquery = (
                db.session.query(
                    MdWorkflowDisplayedData.workflow_fk.label("workflow_fk"),
                    MdWorkflowDisplayedData.name_for_user.label("en_name_for_user"),
                    MdWorkflowDisplayedData.definition_for_user.label("en_definition_for_user"),
                )
                .filter(MdWorkflowDisplayedData.language_code == "en")
                .subquery()
            )

            results = db.session.query(MdUserWorkflow, MdWorkflow, coalesce(
                user_lang_subquery.c.user_lang_name_for_user,
                en_subquery.c.en_name_for_user).label(
                "name_for_user"),
                                       coalesce(
                                           user_lang_subquery.c.user_lang_definition_for_user,
                                           en_subquery.c.en_definition_for_user).label(
                                           "definition_for_user")) \
                .join(MdWorkflow, MdWorkflow.workflow_pk == MdUserWorkflow.workflow_fk) \
                .outerjoin(user_lang_subquery, MdWorkflow.workflow_pk == user_lang_subquery.c.workflow_fk) \
                .outerjoin(en_subquery, MdWorkflow.workflow_pk == en_subquery.c.workflow_fk) \
                .filter(MdUserWorkflow.user_id == user_id) \
                .order_by(MdUserWorkflow.workflow_fk) \
                .limit(n_user_workflows) \
                .offset(offset) \
                .all()

            return {'user_workflows': [{
                "user_workflow_pk": user_workflow.user_workflow_pk,
                "workflow_pk": workflow.workflow_pk,
                "name_for_user": name_for_user,
                "icon": workflow.icon,
                "definition_for_user": definition_for_user,
                "steps": self._get_workflow_steps_in_user_language(workflow.workflow_pk, user_id)
            } for user_workflow, workflow, name_for_user, definition_for_user in results]}, 200

        except Exception as e:
            db.session.rollback()
            log_error(f"{error_message} : {e}")
            return {"error": f"{e}"}, 404

    def put(self):
        if not request.is_json:
            return {"error": "Request must be JSON"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["BACKOFFICE_SECRET"]:
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            return {"error": f"Missing Authorization secret in headers"}, 403

        try:
            timestamp = request.json["datetime"]
            user_id = request.json['user_id']
            workflow_pk = request.json["workflow_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            # ensure this does not already exist
            user_workflow = db.session.query(MdUserWorkflow).filter(
                and_(MdUserWorkflow.user_id == user_id, MdUserWorkflow.workflow_fk == workflow_pk)).first()
            if user_workflow:
                return {"error": "User workflow already exists"}, 400

            user_workflow = MdUserWorkflow(user_id=user_id, workflow_fk=workflow_pk)
            db.session.add(user_workflow)
            db.session.commit()
            return {"user_workflow_pk": user_workflow.user_workflow_pk}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error while creating user_workflow: {e}"}, 500
