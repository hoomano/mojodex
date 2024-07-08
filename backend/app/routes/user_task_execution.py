import os
from flask import request
from flask_restful import Resource
from app import db, authenticate, time_manager
from mojodex_core.entities.user_task import UserTask
from mojodex_core.entities.user_workflow_execution import UserWorkflowExecution
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *
from mojodex_core.entities.user_task_execution import UserTaskExecution as DBUserTaskExecution
from models.session_creator import SessionCreator
from sqlalchemy import func, and_, or_, text
from sqlalchemy.sql.functions import coalesce

from models.purchase_manager import PurchaseManager
from datetime import datetime, timezone

class UserTaskExecution(Resource):

    def __init__(self):
        UserTaskExecution.method_decorators = [authenticate(methods=["PUT", "GET", "DELETE"])]
        self.session_creator = SessionCreator()
        self.purchase_manager = PurchaseManager()

    def put(self, user_id):
        if not request.is_json:
            log_error(f"Error creating UserTaskExecution : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        # data
        try:
            timestamp = request.json["datetime"]
            user_task_pk = request.json["user_task_pk"]
            platform = request.json["platform"] if "platform" in request.json else "webapp"
        except KeyError as e:
            log_error(f"Error creating UserTaskExecution : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            # Check if user has enough credits to create this task
            purchase_manager = PurchaseManager()
            purchase = purchase_manager.purchase_for_new_task(user_task_pk)
            if purchase is None:
                return {"error": "no_purchase"}, 402

            session_creation = self.session_creator.create_session(user_id, platform, "form")
            if "error" in session_creation[0]:
                return session_creation
            session_id = session_creation[0]["session_id"]

            user_task: UserTask = db.session.query(UserTask).get(user_task_pk)
            if user_task is None:
                log_error(f"Error creating UserTaskExecution : UserTask {user_task_pk} not found")
                return {"error": f"UserTask {user_task_pk} not found"}, 400

            empty_json_input_values = []

            json_input = user_task.task.get_json_input_in_language(user_task.user.language_code)
            
            for input in json_input:
                # append input to empty_json_input_values but with additional field "value" without editing json_input
                new_input = input.copy()
                new_input["value"] = None
                empty_json_input_values.append(new_input)

            
            task_execution: DBUserTaskExecution = DBUserTaskExecution(user_task_fk=user_task_pk,
                                                 json_input_values=empty_json_input_values, session_id=session_id)
            if "user_task_execution_fk" in request.json:
                task_execution.predefined_action_from_user_task_execution_fk = request.json["user_task_execution_fk"]
            db.session.add(task_execution)
            db.session.flush()
            db.session.refresh(task_execution)

            db.session.commit()

            def recover_text_edit_actions(user_task_pk):
                try:
                    # Subquery for user_language_code
                    user_lang_subquery = (
                        db.session.query(
                            MdTextEditActionDisplayedData.text_edit_action_fk.label("text_edit_action_fk"),
                            MdTextEditActionDisplayedData.name.label("user_lang_name"),
                            MdTextEditActionDisplayedData.description.label("user_lang_description"),
                        )
                        .join(MdUser, MdUser.user_id == user_id)
                        .filter(MdTextEditActionDisplayedData.language_code == MdUser.language_code)
                        .subquery()
                    )

                    # Subquery for 'en'
                    en_subquery = (
                        db.session.query(
                            MdTextEditActionDisplayedData.text_edit_action_fk.label("text_edit_action_fk"),
                            MdTextEditActionDisplayedData.name.label("en_name"),
                            MdTextEditActionDisplayedData.description.label("en_description"),
                        )
                        .filter(MdTextEditActionDisplayedData.language_code == "en")
                        .subquery()
                    )

                    # Main query
                    text_edit_actions = (
                        db.session.query(
                            MdTextEditAction.text_edit_action_pk,
                            coalesce(user_lang_subquery.c.user_lang_name, en_subquery.c.en_name).label(
                                "name"
                            ),
                            coalesce(user_lang_subquery.c.user_lang_description, en_subquery.c.en_description).label(
                                "description"
                            ),
                            MdTextEditAction.emoji,
                        )
                        .outerjoin(user_lang_subquery, MdTextEditAction.text_edit_action_pk == user_lang_subquery.c.text_edit_action_fk)
                        .outerjoin(en_subquery, MdTextEditAction.text_edit_action_pk == en_subquery.c.text_edit_action_fk)
                        .join(
                            MdTextEditActionTextTypeAssociation,
                            MdTextEditActionTextTypeAssociation.text_edit_action_fk == MdTextEditAction.text_edit_action_pk,
                        )
                        .join(
                            MdTextType,
                            MdTextType.text_type_pk == MdTextEditActionTextTypeAssociation.text_type_fk,
                        )
                        .join(
                            MdTask,
                            MdTask.output_text_type_fk == MdTextType.text_type_pk,
                        )
                        .join(
                            MdUserTask,
                            MdUserTask.task_fk == MdTask.task_pk,
                        )
                        .filter(
                            MdUserTask.user_task_pk == user_task_pk,
                        )
                    ).all()

                    actions = [text_edit_action._asdict() for text_edit_action in text_edit_actions]

                    return actions

                except Exception as e:
                    raise Exception(f"recover_text_edit_actions: {e}")

            predefined_actions_data = [predefined_action._asdict() for predefined_action in task_execution.predefined_actions]
            predefined_actions = [{**predefined_action.displayed_data, "task_pk": predefined_action.task_fk} for predefined_action in predefined_actions_data]

            
            return {**{"user_task_execution_pk": task_execution.user_task_execution_pk,
                     "json_input": json_input,
                     "actions": predefined_actions,
                     "text_edit_actions" : recover_text_edit_actions(user_task_pk=user_task_pk)
                     }, **session_creation[0]}, 200 # append session_creation to returned dict
        except Exception as e:
            db.session.rollback()
            log_error(f"Error creating UserTaskExecution : {e}")
            return {"error": f"{e}"}, 500

    # end of task
    def post(self):
        error_message= "Error ending UserTaskExecution : "
        try:
            secret = request.headers['Authorization']
            if secret != os.environ["PURCHASE_UPDATER_SOCKETIO_SECRET"]:
                log_error(f"{error_message}: Authentication error : Wrong secret")
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"{error_message} : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        if not request.is_json:
            log_error(f"{error_message} : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        # data
        try:
            timestamp = request.json["datetime"]
            user_task_execution_pk = request.json["user_task_execution_pk"]
        except KeyError as e:
            log_error(f"{error_message} : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            user_task_execution = db.session.query(MdUserTaskExecution) \
                .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk) \
                .first()
            if user_task_execution is None:
                log_error(
                    f"{error_message} : UserTaskExecution {user_task_execution_pk} not found ")
                return {"error": f"UserTaskExecution  {user_task_execution_pk} not found"}, 400

            user_task_execution.end_date = datetime.now()

            purchase = self.purchase_manager.associate_purchase_to_user_task_execution(user_task_execution_pk)
            if purchase:
                # check if purchase is all consumed
                consumed = self.purchase_manager.purchase_is_all_consumed(purchase.purchase_pk)
                if consumed:
                    self.purchase_manager.deactivate_purchase(purchase)
            db.session.commit()
            return {"user_task_execution_pk": user_task_execution_pk}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"{error_message} : {e}")
            return {"error": f"{e}"}, 500

    def get(self, user_id):

        try:
            timestamp = request.args["datetime"]
        except KeyError as e:
            log_error(f"Error getting user_task_executions : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        try:

            def recover_text_edit_actions(user_task_pk):
                try:
                    # Subquery for user_language_code
                    user_lang_subquery = (
                        db.session.query(
                            MdTextEditActionDisplayedData.text_edit_action_fk.label("text_edit_action_fk"),
                            MdTextEditActionDisplayedData.name.label("user_lang_name"),
                            MdTextEditActionDisplayedData.description.label("user_lang_description"),
                        )
                        .join(MdUser, MdUser.user_id == user_id)
                        .filter(MdTextEditActionDisplayedData.language_code == MdUser.language_code)
                        .subquery()
                    )

                    # Subquery for 'en'
                    en_subquery = (
                        db.session.query(
                            MdTextEditActionDisplayedData.text_edit_action_fk.label("text_edit_action_fk"),
                            MdTextEditActionDisplayedData.name.label("en_name"),
                            MdTextEditActionDisplayedData.description.label("en_description"),
                        )
                        .filter(MdTextEditActionDisplayedData.language_code == "en")
                        .subquery()
                    )

                    # Main query
                    text_edit_actions = (
                        db.session.query(
                            MdTextEditAction.text_edit_action_pk,
                            coalesce(user_lang_subquery.c.user_lang_name, en_subquery.c.en_name).label(
                                "name"
                            ),
                            coalesce(user_lang_subquery.c.user_lang_description, en_subquery.c.en_description).label(
                                "description"
                            ),
                            MdTextEditAction.emoji,
                        )
                        .outerjoin(user_lang_subquery, MdTextEditAction.text_edit_action_pk == user_lang_subquery.c.text_edit_action_fk)
                        .outerjoin(en_subquery, MdTextEditAction.text_edit_action_pk == en_subquery.c.text_edit_action_fk)
                        .join(
                            MdTextEditActionTextTypeAssociation,
                            MdTextEditActionTextTypeAssociation.text_edit_action_fk == MdTextEditAction.text_edit_action_pk,
                        )
                        .join(
                            MdTextType,
                            MdTextType.text_type_pk == MdTextEditActionTextTypeAssociation.text_type_fk,
                        )
                        .join(
                            MdTask,
                            MdTask.output_text_type_fk == MdTextType.text_type_pk,
                        )
                        .join(
                            MdUserTask,
                            MdUserTask.task_fk == MdTask.task_pk,
                        )
                        .filter(
                            MdUserTask.user_task_pk == user_task_pk,
                        )
                    ).all()

                    actions = [text_edit_action._asdict() for text_edit_action in text_edit_actions]

                    return actions

                except Exception as e:
                    raise Exception(f"recover_text_edit_actions: {e}")

            def get_n_todos(user_task_execution_pk):
                # count the number of todos for a user_task_execution_pk
                return (db.session.query(func.count(MdTodo.todo_pk))
                        .filter(MdTodo.user_task_execution_fk == user_task_execution_pk)
                        .filter(MdTodo.deleted_by_user.is_(None))
                        .scalar()
                        )

            def get_n_todos_not_read(user_task_execution_pk):
                now_utc = datetime.now(timezone.utc).date()
                # Subquery to get the latest todo_scheduling for each todo
                latest_todo_scheduling = db.session.query(
                    MdTodoScheduling.todo_fk,
                    func.max(MdTodoScheduling.scheduled_date).label('latest_scheduled_date')) \
                    .group_by(MdTodoScheduling.todo_fk) \
                    .subquery()
                # count the number of todos not read for a user_task_execution_pk
                return (db.session.query(func.count(MdTodo.todo_pk))
                        .join(MdUserTaskExecution,
                              MdTodo.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk)
                        .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk)
                        .join(MdUser, MdUserTask.user_id == MdUser.user_id)
                        .join(latest_todo_scheduling, MdTodo.todo_pk == latest_todo_scheduling.c.todo_fk)
                        .filter((latest_todo_scheduling.c.latest_scheduled_date - text(
                    'md_user.timezone_offset * interval \'1 minute\'')) >= now_utc)
                        .filter(MdTodo.user_task_execution_fk == user_task_execution_pk)
                        .filter(MdTodo.deleted_by_user.is_(None))
                        .filter(MdTodo.read_by_user.is_(None))
                        .filter(MdTodo.completed.is_(None))
                        .scalar()
                        )

          
            if "user_task_execution_pk" in request.args:
                user_task_execution_pk = int(request.args["user_task_execution_pk"])
                produced_text_subquery = db.session.query(MdProducedText.produced_text_pk,
                                                          MdProducedText.user_task_execution_fk.label(
                                                              'user_task_execution_fk'),
                                                          MdProducedTextVersion.title.label('produced_text_title'),
                                                          MdProducedTextVersion.production.label(
                                                              'produced_text_production'),
                                                          MdProducedTextVersion.produced_text_version_pk.label(
                                                              'produced_text_version_pk'),
                                                          func.row_number().over(
                                                              partition_by=MdProducedText.user_task_execution_fk,
                                                              order_by=MdProducedTextVersion.creation_date.asc()).label(
                                                              'row_number')) \
                    .join(MdProducedTextVersion,
                          MdProducedTextVersion.produced_text_fk == MdProducedText.produced_text_pk) \
                    .subquery()
                
                highest_row_number_subquery = db.session.query(
                    produced_text_subquery.c.user_task_execution_fk,
                    func.max(produced_text_subquery.c.row_number).label('max_row_number')
                ).group_by(produced_text_subquery.c.user_task_execution_fk).subquery()

                result =( db.session.query(
                        DBUserTaskExecution,
                        MdTask,
                        MdTaskDisplayedData,
                        produced_text_subquery.c.produced_text_pk.label("produced_text_pk"),
                        produced_text_subquery.c.produced_text_title.label("produced_text_title"),
                        produced_text_subquery.c.produced_text_production.label("produced_text_production"),
                        produced_text_subquery.c.produced_text_version_pk.label("produced_text_version_pk"),
                        produced_text_subquery.c.row_number.label("produced_text_version_index"),
                        MdUser.timezone_offset,
                        MdUser.language_code
                    ).join(MdUserTask, MdUserTask.user_task_pk == DBUserTaskExecution.user_task_fk)
                    .join(MdUser, MdUser.user_id == MdUserTask.user_id)
                    .join(MdTask, MdTask.task_pk == MdUserTask.task_fk)
                    .join(MdTaskDisplayedData, MdTaskDisplayedData.task_fk == MdTask.task_pk)
                    .outerjoin(highest_row_number_subquery,
                        highest_row_number_subquery.c.user_task_execution_fk == DBUserTaskExecution.user_task_execution_pk)
                    .outerjoin(produced_text_subquery,
                            and_(
                                produced_text_subquery.c.user_task_execution_fk == DBUserTaskExecution.user_task_execution_pk,
                                produced_text_subquery.c.row_number == highest_row_number_subquery.c.max_row_number))
                    .filter(DBUserTaskExecution.user_task_execution_pk == user_task_execution_pk)
                    .filter(MdUser.user_id == user_id)
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
                    .group_by(DBUserTaskExecution.user_task_execution_pk, MdTask.task_pk,
                              MdTaskDisplayedData.task_displayed_data_pk,
                              produced_text_subquery.c.produced_text_pk, produced_text_subquery.c.produced_text_title,
                              produced_text_subquery.c.produced_text_production,
                              produced_text_subquery.c.produced_text_version_pk,
                              produced_text_subquery.c.row_number,
                              MdUser.timezone_offset,
                              MdUser.language_code
                              )
                    .first())._asdict()
                if result["MdTask"].type == "workflow":
                    workflow_execution = db.session.query(UserWorkflowExecution).get(result["UserTaskExecution"].user_task_execution_pk)
                else:
                    workflow_execution = None

                return {
                    "user_task_execution_pk": result["UserTaskExecution"].user_task_execution_pk,
                    "start_date": time_manager.backend_date_to_user_date(result["UserTaskExecution"].start_date,
                                                                         result["timezone_offset"]).isoformat() if
                    result["UserTaskExecution"].start_date and result["timezone_offset"] else None,
                    "end_date": time_manager.backend_date_to_user_date(result["UserTaskExecution"].end_date,
                                                                       result["timezone_offset"]).isoformat() if result[
                                                                                                                     "UserTaskExecution"].end_date and
                                                                                                                 result[
                                                                                                                     "timezone_offset"] else None,
                    "deleted_by_user": result["UserTaskExecution"].deleted_by_user is not None,
                    "title": result["UserTaskExecution"].title,
                    "summary": result["UserTaskExecution"].summary,
                    "session_id": result["UserTaskExecution"].session_id,
                    "json_inputs_values": None if all(input.get('value') is None for input in result["UserTaskExecution"].json_input_values) else result["UserTaskExecution"].json_input_values,
                    "icon": result["MdTask"].icon,
                    "task_name": result["MdTaskDisplayedData"].name_for_user,
                    "task_type": result["MdTask"].type,
                    "result_chat_enabled": result["MdTask"].result_chat_enabled,
                    "actions": result['UserTaskExecution'].predefined_actions,
                    "user_task_pk": result["UserTaskExecution"].user_task_fk,
                    "n_todos": get_n_todos(result["UserTaskExecution"].user_task_execution_pk),
                    "n_not_read_todos": get_n_todos_not_read(result["UserTaskExecution"].user_task_execution_pk),
                    "produced_text_pk": result["produced_text_pk"],
                    "produced_text_title": result["produced_text_title"],
                    "produced_text_production": result["produced_text_production"],
                    "produced_text_version_pk": result["produced_text_version_pk"],
                    "produced_text_version_index": result["produced_text_version_index"],
                    "text_edit_actions": recover_text_edit_actions(
                        result["UserTaskExecution"].user_task_fk),
                    "working_on_todos": result["UserTaskExecution"].todos_extracted is None,
                    "step_executions": workflow_execution.get_steps_execution_json() if result["MdTask"].type == "workflow" else None,
                    "steps": workflow_execution.task.get_json_steps_with_translation(result["language_code"]) if result["MdTask"].type == "workflow" else None
                }, 200

            n_user_task_executions = min(50,
                                         int(request.args[
                                                 "n_user_task_executions"])) if "n_user_task_executions" in request.args else 50
            offset = int(request.args["offset"]) if "offset" in request.args else 0

            produced_text_subquery = db.session.query(MdProducedText.produced_text_pk,
                                                      MdProducedText.user_task_execution_fk.label(
                                                          'user_task_execution_fk'),
                                                      MdProducedTextVersion.title.label('produced_text_title'),
                                                      MdProducedTextVersion.production.label(
                                                          'produced_text_production'),
                                                      MdProducedTextVersion.produced_text_version_pk.label(
                                                          'produced_text_version_pk'),
                                                      func.row_number().over(
                                                              partition_by=MdProducedText.user_task_execution_fk,
                                                              order_by=MdProducedTextVersion.creation_date.asc()).label(
                                                              'row_number')) \
                .join(MdProducedTextVersion, MdProducedTextVersion.produced_text_fk == MdProducedText.produced_text_pk) \
                .subquery()
            
            highest_row_number_subquery = db.session.query(
                    produced_text_subquery.c.user_task_execution_fk,
                    func.max(produced_text_subquery.c.row_number).label('max_row_number')
                ).group_by(produced_text_subquery.c.user_task_execution_fk).subquery()


            # Subquery to retrieve the tasks in the user_language_code
            user_lang_subquery = (
                db.session.query(
                    MdTaskDisplayedData.task_fk.label("task_fk"),
                    MdTaskDisplayedData.name_for_user.label("user_lang_name_for_user"),
                )
                .join(MdUser, MdUser.user_id == user_id)
                .filter(MdTaskDisplayedData.language_code == MdUser.language_code)
                .subquery()
            )

            # Subquery to retrieve the tasks in 'en'
            en_subquery = (
                db.session.query(
                    MdTaskDisplayedData.task_fk.label("task_fk"),
                    MdTaskDisplayedData.name_for_user.label("en_name_for_user"),
                )
                .filter(MdTaskDisplayedData.language_code == "en")
                .subquery()
            )
          
            result = (
                db.session.query(
                    DBUserTaskExecution,
                    MdTask,
                    coalesce(
                        user_lang_subquery.c.user_lang_name_for_user, 
                        en_subquery.c.en_name_for_user
                    ).label("name_for_user"),
                    produced_text_subquery.c.produced_text_pk.label("produced_text_pk"),
                    produced_text_subquery.c.produced_text_title.label("produced_text_title"),
                    produced_text_subquery.c.produced_text_production.label("produced_text_production"),
                    produced_text_subquery.c.produced_text_version_pk.label("produced_text_version_pk"),
                    produced_text_subquery.c.row_number.label("produced_text_version_index"),
                    MdUser.timezone_offset,
                    MdUser.language_code
                )
                .distinct(DBUserTaskExecution.user_task_execution_pk)
                .join(MdUserTask, MdUserTask.user_task_pk == DBUserTaskExecution.user_task_fk)
                .join(MdUser, MdUser.user_id == MdUserTask.user_id)
                .join(MdTask, MdTask.task_pk == MdUserTask.task_fk)
                .outerjoin(user_lang_subquery, MdTask.task_pk == user_lang_subquery.c.task_fk)
                .outerjoin(en_subquery, MdTask.task_pk == en_subquery.c.task_fk)
                 .outerjoin(highest_row_number_subquery,
                        highest_row_number_subquery.c.user_task_execution_fk == DBUserTaskExecution.user_task_execution_pk)
                    .outerjoin(produced_text_subquery,
                            and_(
                                produced_text_subquery.c.user_task_execution_fk == DBUserTaskExecution.user_task_execution_pk,
                                produced_text_subquery.c.row_number == highest_row_number_subquery.c.max_row_number))
                .filter(MdUserTask.user_id == user_id)
                .filter(DBUserTaskExecution.start_date.isnot(None))
                .filter(DBUserTaskExecution.deleted_by_user.is_(None)))

            if "search_filter" in request.args:
                search_filter = request.args["search_filter"]
                if search_filter:
                    result = result.filter(or_(produced_text_subquery.c.produced_text_title.ilike(f"%{search_filter}%"),
                                               produced_text_subquery.c.produced_text_production.ilike(
                                                   f"%{search_filter}%")))

            if "user_task_pks" in request.args:
                search_user_tasks_filter = request.args["user_task_pks"]
                if search_user_tasks_filter:
                    search_user_tasks_filter_list = search_user_tasks_filter.split(";")
                    result = result.filter(MdUserTask.user_task_pk.in_(search_user_tasks_filter_list))

            result = (result.group_by(DBUserTaskExecution.user_task_execution_pk, MdTask.task_pk,
                                      user_lang_subquery.c.user_lang_name_for_user,
                                      en_subquery.c.en_name_for_user,
                                      produced_text_subquery.c.produced_text_pk,
                                      produced_text_subquery.c.produced_text_title,
                                      produced_text_subquery.c.produced_text_production,
                                      produced_text_subquery.c.produced_text_version_pk,
                                        produced_text_subquery.c.row_number,
                                      MdUser.timezone_offset,
                                      MdUser.language_code
                                      )
                      .order_by(DBUserTaskExecution.user_task_execution_pk.desc())
                      .limit(n_user_task_executions)
                      .offset(offset)
                      .all())

            result = [row._asdict() for row in result]

            def get_workflow_specific_data(row):
                workflow_execution = db.session.query(UserWorkflowExecution).get(row["UserTaskExecution"].user_task_execution_pk)
                return {
                    "steps": workflow_execution.task.get_json_steps_with_translation(row["language_code"]),
                    "step_executions": workflow_execution.get_steps_execution_json()
                }
            
          

            results_list = [{
                "user_task_execution_pk": row["UserTaskExecution"].user_task_execution_pk,
                "start_date": time_manager.backend_date_to_user_date(row["UserTaskExecution"].start_date,
                                                                     row["timezone_offset"]).isoformat() if row[
                                                                                                                "UserTaskExecution"].start_date and
                                                                                                            row[
                                                                                                                "timezone_offset"] else None,
                "end_date": time_manager.backend_date_to_user_date(row["UserTaskExecution"].end_date,
                                                                   row["timezone_offset"]).isoformat() if row[
                                                                                                              "UserTaskExecution"].end_date and
                                                                                                          row[
                                                                                                              "timezone_offset"] else None,
                "title": row["UserTaskExecution"].title,
                "summary": row["UserTaskExecution"].summary,
                "session_id": row["UserTaskExecution"].session_id,
               "json_inputs_values": None if all(input.get('value') is None for input in row["UserTaskExecution"].json_input_values) else row["UserTaskExecution"].json_input_values,
                "icon": row["MdTask"].icon,
                "task_name": row["name_for_user"],
                "task_type": row["MdTask"].type,
                "result_chat_enabled": row["MdTask"].result_chat_enabled,
                "actions": row['UserTaskExecution'].predefined_actions,
                "user_task_pk": row["UserTaskExecution"].user_task_fk,
                "n_todos": get_n_todos(row["UserTaskExecution"].user_task_execution_pk),
                "n_not_read_todos": get_n_todos_not_read(row["UserTaskExecution"].user_task_execution_pk),
                "produced_text_pk": row["produced_text_pk"],
                "produced_text_title": row["produced_text_title"],
                "produced_text_production": row["produced_text_production"],
                "produced_text_version_pk": row["produced_text_version_pk"],
                "produced_text_version_index": row["produced_text_version_index"],
                "text_edit_actions": recover_text_edit_actions(row["UserTaskExecution"].user_task_fk),
                "working_on_todos": row["UserTaskExecution"].todos_extracted is None,
                **(get_workflow_specific_data(row) if row["MdTask"].type == "workflow" else {})
            } for row in result]

            return {"user_task_executions": results_list}, 200

        except Exception as e:
            log_error(f"Error getting user_task_executions : {e}")
            return {"error": f"Error getting user_task_executions : {e}"}, 400

    # deleting user_task_execution
    def delete(self, user_id):

        try:
            timestamp = request.args["datetime"]
            user_task_execution_pk = request.args["user_task_execution_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            # Check user_task_execution exists for this user
            user_task_execution = db.session.query(MdUserTaskExecution) \
                .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk) \
                .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                .join(MdUser, MdUserTask.user_id == MdUser.user_id) \
                .filter(MdUser.user_id == user_id) \
                .first()
            if user_task_execution is None:
                return {"error": "User task execution not found"}, 404

            user_task_execution.deleted_by_user = datetime.now()
            db.session.commit()
            return {"user_task_execution_pk": user_task_execution_pk}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error deleting user_task_execution : {e}")
            return {"error": f"Error deleting user_task_execution : {e}"}, 400
