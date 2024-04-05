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
            # Get the platform_pk based on the platform name passed
            md_platform = db.session.query(MdPlatform).filter(MdPlatform.name == platform).first()
            if md_platform is None:
                log_error(f"{error_message} : the platform '{platform}' is invalid")
                return {"error": f"{error_message} : the platform '{platform}' is invalid"}, 404
            else:
                platform_pk = md_platform.platform_pk

            if "user_workflow_pk" in request.args:
                user_workflow_pk = int(request.args["user_workflow_pk"])

                # get user_workflow info
                result = db.session.query(MdUserWorkflow, MdWorkflow, MdWorkflowDisplayedData) \
                    .join(MdWorkflow, MdWorkflow.workflow_pk == MdUserWorkflow.workflow_fk) \
                    .join(MdWorkflowDisplayedData, MdWorkflowDisplayedData.workflow_fk == MdWorkflow.workflow_pk) \
                    .join(MdUser, MdUser.user_id == MdUserWorkflow.user_id) \
                    .join(
                        MdWorkflowPlatformAssociation,
                        MdWorkflowPlatformAssociation.workflow_fk == MdWorkflow.workflow_pk
                         ) \
                    .filter(MdUserWorkflow.user_id == user_id) \
                    .filter(MdUserWorkflow.enabled == True )\
                    .filter(MdUserWorkflow.user_workflow_pk == user_workflow_pk) \
                    .filter(
                        MdWorkflowPlatformAssociation.platform_fk == platform_pk
                     ) \
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
                    "definition": workflow_displayed_data.definition_for_user,
                    "enabled": True
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
                .join(
                MdWorkflowPlatformAssociation,
                MdWorkflowPlatformAssociation.workflow_fk == MdWorkflow.workflow_pk) \
                .outerjoin(user_lang_subquery, MdWorkflow.workflow_pk == user_lang_subquery.c.workflow_fk) \
                .outerjoin(en_subquery, MdWorkflow.workflow_pk == en_subquery.c.workflow_fk) \
                .filter(MdUserWorkflow.enabled == True)\
                .filter(MdUserWorkflow.user_id == user_id) \
                .filter(MdWorkflowPlatformAssociation.platform_fk == platform_pk) \
                .order_by(MdUserWorkflow.workflow_fk) \
                .limit(n_user_workflows) \
                .offset(offset) \
                .all()

            response = {'user_workflows': [{
                "user_workflow_pk": user_workflow.user_workflow_pk,
                "workflow_pk": workflow.workflow_pk,
                "name_for_user": name_for_user,
                "icon": workflow.icon,
                "definition_for_user": definition_for_user,
                "steps": self._get_workflow_steps_in_user_language(workflow.workflow_pk, user_id),
                "enabled": True
            } for user_workflow, workflow, name_for_user, definition_for_user in results]}

            # other workflows that are not enabled for this user but:
            # - he used to have it enabled in a previous purchase (user_workflow exists and enabled = False in this case)
            # - he never had it enabled (user_workflow does not exist in this case) and workflow.visible_for_teasing is true
            if len(response["user_workflows"]) < n_user_workflows:
                total_user_workflows = db.session.query(MdUserWorkflow) \
                    .filter(MdUserWorkflow.enabled == True) \
                    .filter(MdUserWorkflow.user_id == user_id).count()

                disabled_workflows_offset = max(0, offset - total_user_workflows)
                # Fetch the disabled workflows or workflows not in the md_user_workflow table for this user
                # outerjoin: join all workflow with associated user_workflow of this user, even if there is no user_workflow (=null)
                # filter on whether the user_workflow is disabled or the user_workflow is null (workflow_fk = null)
                disabled_workflows_query = (
                    db.session
                    .query(
                        MdWorkflow,
                        MdUserWorkflow,
                        coalesce(
                            user_lang_subquery.c.user_lang_name_for_user,
                            en_subquery.c.en_name_for_user).label(
                            "name_for_user"),
                        coalesce(
                            user_lang_subquery.c.user_lang_definition_for_user,
                            en_subquery.c.en_definition_for_user).label(
                            "definition_for_user")
                    )
                    .outerjoin(
                        MdUserWorkflow,
                        and_(
                            MdUserWorkflow.workflow_fk == MdWorkflow.workflow_pk,
                            MdUserWorkflow.user_id == user_id
                        )
                    )
                    .join(
                        MdWorkflowPlatformAssociation,
                        MdWorkflowPlatformAssociation.workflow_fk == MdWorkflow.workflow_pk
                    )
                    .outerjoin(user_lang_subquery, MdWorkflow.workflow_pk == user_lang_subquery.c.workflow_fk)
                    .outerjoin(en_subquery, MdWorkflow.workflow_pk == en_subquery.c.workflow_fk)
                    .filter(
                        and_(
                            MdWorkflowPlatformAssociation.platform_fk == platform_pk,
                            or_(
                                MdUserWorkflow.enabled != True,
                                and_(
                                    MdUserWorkflow.workflow_fk.is_(None),
                                    MdWorkflow.visible_for_teasing == True
                                )
                            )
                        )
                    )).order_by(MdWorkflow.workflow_pk).limit(
                    n_user_workflows - len(response["user_workflows"])).offset(disabled_workflows_offset).all()

                disabled_workflows_list = [
                    {
                        "user_workflow_pk": user_workflow.user_workflow_pk if user_workflow else None,
                        "workflow_pk": workflow.workflow_pk,
                        "name_for_user": name_for_user,
                        "definition_for_user": definition_for_user,
                        "icon": workflow.icon,
                        "steps": self._get_workflow_steps_in_user_language(workflow.workflow_pk, user_id),
                        "enabled": False
                    } for workflow, user_workflow, name_for_user, definition_for_user in disabled_workflows_query
                ]

                response["user_workflows"] += disabled_workflows_list

            return response, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"{error_message} : {e}")
            return {"error": f"{e}"}, 404
