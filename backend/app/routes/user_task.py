from flask import request
from flask_restful import Resource
from app import db, authenticate
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import *
from sqlalchemy import and_, or_, func
from sqlalchemy.sql.functions import coalesce
from packaging import version
class UserTask(Resource):


    def __init__(self):
        UserTask.method_decorators = [authenticate()]

    def get(self, user_id):

        try:
            timestamp = request.args["datetime"]
            platform = request.args["platform"] if "platform" in request.args else "webapp" # for the moment default to webapp if nothing is passed
            app_version =  version.parse(request.args["version"]) if "version" in request.args else version.parse("0.0.0") # for the moment default to 0.0.0 if nothing is passed
        except KeyError as e:
            log_error(f"Error getting user_tasks : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            # Get the platform_pk based on the platform name passed
            md_platform = db.session.query(MdPlatform).filter(MdPlatform.name == platform).first()
            if md_platform is None:
                log_error(f"Error getting user_tasks : the platform '{platform}' is invalid")
                return {"error": f"the platform '{platform}' is invalid"}, 404
            else:
                platform_pk = md_platform.platform_pk

            if "user_task_pk" in request.args:
                user_task_pk = int(request.args["user_task_pk"])

                # get task in user's language or english if not translated
                result = (
                    db.session
                    .query(
                        MdUserTask,
                        MdTask,
                        MdTaskDisplayedData
                    )
                    .join(
                        MdTask, 
                        MdTask.task_pk == MdUserTask.task_fk
                    )
                    .join(
                        MdTaskPlatformAssociation,
                        MdTaskPlatformAssociation.task_fk == MdTask.task_pk
                    )
                    .join(
                        MdTaskDisplayedData,
                        MdTaskDisplayedData.task_fk == MdTask.task_pk
                    )
                    .join(
                        MdUser,
                        MdUser.user_id == MdUserTask.user_id
                    )
                    .filter(
                        MdUserTask.user_id == user_id
                    )
                    .filter(
                        MdUserTask.enabled == True
                    )
                    .filter(
                        MdUserTask.user_task_pk == user_task_pk,
                    )
                    .filter(
                        MdTaskPlatformAssociation.platform_fk == platform_pk
                    )
                    .filter(
                        or_(
                            MdTaskDisplayedData.language_code == MdUser.language_code,
                            MdTaskDisplayedData.language_code == 'en'
                        )
                    )
                    .order_by(
                        # Sort by user's language first otherwise by english
                        func.nullif(MdTaskDisplayedData.language_code, 'en').asc()
                    )
                ).first()

                if result is None:
                    log_error(f"Error getting user_task : UserTask with user_task_pk {user_task_pk} does not exist for this user")
                    return {"error": f"Invalid user_task_pk: {user_task_pk} for this user"}, 400
                user_task, task, task_displayed_data = result

                return {"user_task_pk": user_task.user_task_pk,
                        "task_pk": task.task_pk,
                        "user_task_name": task_displayed_data.name_for_user,
                        "user_task_description": task_displayed_data.definition_for_user,
                        "user_task_icon": task.icon,
                        "task_name": task_displayed_data.name_for_user,
                        "task_description": task_displayed_data.definition_for_user,
                        "task_icon": task.icon,
                        "enabled": True
                        }, 200

            # if no produced_text_pk is provided, return n_produced_texts first produced_texts
            n_user_tasks = min(50, int(request.args["n_user_tasks"])) if "n_user_tasks" in request.args else 50
            offset = int(request.args["offset"]) if "offset" in request.args else 0

            # Subquery for user_language_code
            user_lang_subquery = (
                db.session.query(
                    MdTaskDisplayedData.task_fk.label("task_fk"),
                    MdTaskDisplayedData.name_for_user.label("user_lang_name_for_user"),
                    MdTaskDisplayedData.definition_for_user.label("user_lang_definition_for_user"),
                )
                .join(MdUser, MdUser.user_id == user_id)
                .filter(MdTaskDisplayedData.language_code == MdUser.language_code)
                .subquery()
            )

            # Subquery for 'en'
            en_subquery = (
                db.session.query(
                    MdTaskDisplayedData.task_fk.label("task_fk"),
                    MdTaskDisplayedData.name_for_user.label("en_name_for_user"),
                    MdTaskDisplayedData.definition_for_user.label("en_definition_for_user"),
                )
                .filter(MdTaskDisplayedData.language_code == "en")
                .subquery()
            )

            response = (
                db.session.
                query(
                    MdUserTask,
                    MdTask,
                    coalesce(
                        user_lang_subquery.c.user_lang_name_for_user, 
                        en_subquery.c.en_name_for_user).label(
                            "name_for_user"),
                    coalesce(
                        user_lang_subquery.c.user_lang_definition_for_user,
                        en_subquery.c.en_definition_for_user).label(
                            "definition_for_user")
                )
                .join(
                    MdTask,
                    MdUserTask.task_fk == MdTask.task_pk
                )
                .join(
                    MdTaskPlatformAssociation,
                    MdTaskPlatformAssociation.task_fk == MdTask.task_pk
                )
                .outerjoin(user_lang_subquery, MdTask.task_pk == user_lang_subquery.c.task_fk)
                .outerjoin(en_subquery, MdTask.task_pk == en_subquery.c.task_fk)
                .filter(
                    MdUserTask.enabled == True
                )
                .filter(
                    MdUserTask.user_id == user_id
                )
                .filter(
                    MdTaskPlatformAssociation.platform_fk == platform_pk
                )).order_by(MdUserTask.task_fk).limit(n_user_tasks).offset(offset).all()

            response = {
                "user_tasks":
                    [{
                        "user_task_pk": user_task.user_task_pk,
                        "task_pk": task.task_pk,
                        "task_name": name_for_user,
                        "task_description": description_for_user,
                        "task_icon": task.icon,
                        "enabled": True
                        } for user_task, task, name_for_user, description_for_user in response]
            }
     

            # other tasks that are not enabled for this user but:
            # - he used to have it enabled in a previous purchase (user_task exists and enabled = False in this case)
            # - he never had it enabled (user_task does not exist in this case) and task.visible_for_teasing is true
            if len(response["user_tasks"]) < n_user_tasks:
                total_user_tasks = db.session.query(MdUserTask) \
                .filter(MdUserTask.enabled == True) \
                .filter(MdUserTask.user_id == user_id).count()

                disabled_tasks_offset = max(0, offset - total_user_tasks)
                # Fetch the disabled tasks or tasks not in the md_user_task table for this user
                # outerjoin: join all task with associated user_task of this user, even if there is no user_task (=null)
                # filter on whether the user_task is disabled or the user_task is null (task_fk = null)
                disabled_tasks_query = (
                    db.session
                    .query(
                        MdTask, 
                        MdUserTask,
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
                        MdUserTask, 
                        and_(
                            MdUserTask.task_fk == MdTask.task_pk, 
                            MdUserTask.user_id == user_id
                        )
                    )
                    .join(
                        MdTaskPlatformAssociation,
                        MdTaskPlatformAssociation.task_fk == MdTask.task_pk
                    )
                    .outerjoin(user_lang_subquery, MdTask.task_pk == user_lang_subquery.c.task_fk)
                    .outerjoin(en_subquery, MdTask.task_pk == en_subquery.c.task_fk)
                    .filter(
                        and_(
                            MdTaskPlatformAssociation.platform_fk == platform_pk,
                            or_(
                                MdUserTask.enabled != True, 
                                and_(
                                    MdUserTask.task_fk.is_(None),
                                    MdTask.visible_for_teasing == True
                                )
                            ) 
                        )
                    )).order_by(MdTask.task_pk).limit(
                    n_user_tasks - len(response["user_tasks"])).offset(disabled_tasks_offset).all()

                disabled_tasks_list = [
                    {
                        "user_task_pk": user_task.user_task_pk if user_task else None,
                        "task_pk": task.task_pk,
                        "task_name": name_for_user,
                        "task_description": description_for_user,
                        "task_icon": task.icon,
                        "enabled": False
                        } for task, user_task, name_for_user, description_for_user in disabled_tasks_query
                ]

                response["user_tasks"] += disabled_tasks_list

            return response, 200

        except Exception as e:
            db.session.rollback()
            log_error(f"Error getting user_tasks : {e}")
            return {"error": f"{e}"}, 404

