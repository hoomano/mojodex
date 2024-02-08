import os
from flask import request
from flask_restful import Resource
from app import db, authenticate, log_error, executor, time_manager
from db_models import *
from datetime import datetime
from models.session_creator import SessionCreator
from sqlalchemy import func, and_, or_, text
from sqlalchemy.sql.functions import coalesce

from models.purchase_manager import PurchaseManager


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
            empty_json_input_values = []

            # get task in user's language or english if not translated
            md_displayed_data = (
                db.session
                .query(
                    MdTaskDisplayedData,
                )
                .join(
                    MdTask,
                    MdTask.task_pk == MdTaskDisplayedData.task_fk
                )
                .join(
                    MdUserTask, 
                    MdUserTask.task_fk == MdTask.task_pk
                )
                .join(
                    MdUser,
                    MdUser.user_id == user_id
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
                .filter(MdUserTask.user_task_pk == user_task_pk)
            .first())

            json_input = md_displayed_data.json_input


            # get predefined actions translated in english
            predefined_actions_data_en = (
                db.session
                .query(
                    MdPredefinedActionDisplayedData.task_predefined_action_association_fk.label("task_predefined_action_association_fk"),
                    MdPredefinedActionDisplayedData.displayed_data.label("displayed_data_en"),
                )
                .filter(MdPredefinedActionDisplayedData.language_code == 'en')
            ).subquery()

            # get predefined actions translated in user's language
            predefined_actions_data_user_lang = (
                db.session
                .query(
                    MdPredefinedActionDisplayedData.task_predefined_action_association_fk.label("task_predefined_action_association_fk"),
                    MdPredefinedActionDisplayedData.displayed_data.label("displayed_data_user_lang"),
                )
                .join(
                    MdUser,
                    MdUser.user_id == user_id
                )
                .filter(MdPredefinedActionDisplayedData.language_code == MdUser.language_code)
            ).subquery()

            # get predefined actions translated in user's language or english if not translated
            predefined_actions_data = (
                db.session
                .query(
                    MdTaskPredefinedActionAssociation.predefined_action_fk.label("task_fk"),
                    coalesce(
                        predefined_actions_data_user_lang.c.displayed_data_user_lang, 
                        predefined_actions_data_en.c.displayed_data_en
                    ).label("displayed_data"),
                )
                .outerjoin(
                    predefined_actions_data_user_lang, 
                    predefined_actions_data_user_lang.c.task_predefined_action_association_fk == MdTaskPredefinedActionAssociation.task_predefined_action_association_pk
                )
                .outerjoin(
                    predefined_actions_data_en,
                    predefined_actions_data_en.c.task_predefined_action_association_fk == MdTaskPredefinedActionAssociation.task_predefined_action_association_pk
                )
                .join(
                    MdUserTask,
                    MdUserTask.user_task_pk == user_task_pk
                )
                .filter(
                    MdTaskPredefinedActionAssociation.task_fk == MdUserTask.task_fk
                )
            ).all()
            predefined_actions_data = [predefined_action._asdict() for predefined_action in predefined_actions_data]

            predefined_actions = []
            for predefined_action in predefined_actions_data:
                action = predefined_action["displayed_data"]
                action["task_pk"] = predefined_action["task_fk"]
                predefined_actions.append(action)

            for input in json_input:
                # append input to empty_json_input_values but with additional field "value" without editing json_input
                new_input = input.copy()
                new_input["value"] = None
                empty_json_input_values.append(new_input)
            task_execution = MdUserTaskExecution(user_task_fk=user_task_pk,
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
            log_error(f"Error getting followups : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        try:

            def get_task_tool_executions(user_task_execution_pk):
                try:
                    query_sub = db.session.query(
                        MdTaskToolQuery.task_tool_execution_fk,
                        MdTaskToolQuery.task_tool_query_pk.label("task_tool_query_pks"),
                        func.array_agg(MdTaskToolQuery.query).label("queries"),
                        func.array_agg(MdTaskToolQuery.result).label("results")
                    ).group_by(MdTaskToolQuery.task_tool_execution_fk, MdTaskToolQuery.task_tool_query_pk).subquery()

                    aggregated_sub = db.session.query(
                        query_sub.c.task_tool_execution_fk,
                        func.array_agg(query_sub.c.task_tool_query_pks).label("agg_task_tool_query_pks"),
                        func.array_agg(query_sub.c.queries).label("agg_queries"),
                        func.array_agg(query_sub.c.results).label("agg_results")
                    ).group_by(query_sub.c.task_tool_execution_fk).subquery()

                    results = db.session.query(
                        MdTaskToolExecution.task_tool_execution_pk,
                        MdTool.name.label("tool_name"),
                        aggregated_sub.c.agg_task_tool_query_pks.label("ttq_pk"),
                        aggregated_sub.c.agg_queries.label("qs"),
                        aggregated_sub.c.agg_results.label("rs")
                    ).join(
                        MdTaskToolAssociation,
                        MdTaskToolExecution.task_tool_association_fk == MdTaskToolAssociation.task_tool_association_pk
                    ).join(
                        MdTool,
                        MdTaskToolAssociation.tool_fk == MdTool.tool_pk
                    ).outerjoin(
                        aggregated_sub,
                        MdTaskToolExecution.task_tool_execution_pk == aggregated_sub.c.task_tool_execution_fk
                    ).filter(
                        MdTaskToolExecution.user_task_execution_fk == user_task_execution_pk
                    ).all()

                    results = [result._asdict() for result in results]

                    results_list = [{
                        "task_tool_execution_pk": row["task_tool_execution_pk"],
                        "tool_name": row["tool_name"],
                        "queries": [{"query": q, "result": r, "task_tool_query_pk": ttq_pk}
                                    for ttq_pk, qs, rs in zip(row["ttq_pk"], row["qs"], row["rs"])
                                    for q, r in zip(qs, rs)
                                    ] if row["ttq_pk"] else []
                    } for row in results]

                    return results_list
                except Exception as e:
                    raise Exception(f"__get_task_tool_executions: {e}")

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
                now_utc = datetime.utcnow().date()
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

            def get_predefined_actions(task_pk):

                # Subquery to retrieve the predefined actions in the user_language_code
                predefined_actions_data_user_lang = (
                    db.session
                    .query(
                        MdPredefinedActionDisplayedData.task_predefined_action_association_fk.label(
                            "task_predefined_action_association_fk"),
                        MdPredefinedActionDisplayedData.displayed_data.label("displayed_data_user_lang"),
                    )
                    .join(
                        MdUser,
                        MdUser.user_id == user_id
                    )
                    .filter(MdPredefinedActionDisplayedData.language_code == MdUser.language_code)
                ).subquery()

                # Subquery to retrieve the predefined actions in 'en
                predefined_actions_data_en = (
                    db.session
                    .query(
                        MdPredefinedActionDisplayedData.task_predefined_action_association_fk.label(
                            "task_predefined_action_association_fk"),
                        MdPredefinedActionDisplayedData.displayed_data.label("displayed_data_en"),
                    )
                    .filter(MdPredefinedActionDisplayedData.language_code == 'en')
                ).subquery()

                result = db.session.query(
                    func.json_build_object(
                        "task_pk",
                        MdTaskPredefinedActionAssociation.predefined_action_fk,
                        "displayed_data",
                        coalesce(
                            predefined_actions_data_user_lang.c.displayed_data_user_lang,
                            predefined_actions_data_en.c.displayed_data_en
                        )
                    )) \
                    .filter(MdTaskPredefinedActionAssociation.task_fk == task_pk) \
                    .outerjoin(
                    predefined_actions_data_user_lang,
                    predefined_actions_data_user_lang.c.task_predefined_action_association_fk == MdTaskPredefinedActionAssociation.task_predefined_action_association_pk
                ) \
                    .outerjoin(
                    predefined_actions_data_en,
                    predefined_actions_data_en.c.task_predefined_action_association_fk == MdTaskPredefinedActionAssociation.task_predefined_action_association_pk
                ).all()

                result = [predefined_action[0] for predefined_action in
                          result]  # {task_pk: 12, displayed_data: {name: followup_email, button_text: Send follow-up email, message_prefix: Prepare follow-up email for this lead to engage them.}}
                # remove displayed_data depth
                result = [predefined_action["displayed_data"].update({"task_pk": predefined_action["task_pk"]}) or
                          predefined_action["displayed_data"] for predefined_action in result]
                return result

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
                                                              order_by=MdProducedTextVersion.creation_date.desc()).label(
                                                              'row_number')) \
                    .join(MdProducedTextVersion,
                          MdProducedTextVersion.produced_text_fk == MdProducedText.produced_text_pk) \
                    .subquery()

                result =( db.session.query(
                        MdUserTaskExecution,
                        MdTask,
                        MdTaskDisplayedData,
                        produced_text_subquery.c.produced_text_pk.label("produced_text_pk"),
                        produced_text_subquery.c.produced_text_title.label("produced_text_title"),
                        produced_text_subquery.c.produced_text_production.label("produced_text_production"),
                        produced_text_subquery.c.produced_text_version_pk.label("produced_text_version_pk"),
                        MdUser.timezone_offset
                    ).join(MdUserTask, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk)
                    .join(MdUser, MdUser.user_id == MdUserTask.user_id)
                    .join(MdTask, MdTask.task_pk == MdUserTask.task_fk)
                    .join(MdTaskDisplayedData, MdTaskDisplayedData.task_fk == MdTask.task_pk)
                    .outerjoin(produced_text_subquery,
                               and_(
                                   produced_text_subquery.c.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk,
                                   produced_text_subquery.c.row_number == 1))
                    .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk)
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
                    .group_by(MdUserTaskExecution.user_task_execution_pk, MdTask.task_pk,
                              MdTaskDisplayedData.task_displayed_data_pk,
                              produced_text_subquery.c.produced_text_pk, produced_text_subquery.c.produced_text_title,
                              produced_text_subquery.c.produced_text_production,
                              produced_text_subquery.c.produced_text_version_pk,
                              MdUser.timezone_offset
                              )
                    .first())._asdict()

                return {
                    "user_task_execution_pk": result["MdUserTaskExecution"].user_task_execution_pk,
                    "start_date": time_manager.backend_date_to_user_date(result["MdUserTaskExecution"].start_date,
                                                                         result["timezone_offset"]).isoformat() if
                    result["MdUserTaskExecution"].start_date and result["timezone_offset"] else None,
                    "end_date": time_manager.backend_date_to_user_date(result["MdUserTaskExecution"].end_date,
                                                                       result["timezone_offset"]).isoformat() if result[
                                                                                                                     "MdUserTaskExecution"].end_date and
                                                                                                                 result[
                                                                                                                     "timezone_offset"] else None,
                    "deleted_by_user": result["MdUserTaskExecution"].deleted_by_user is not None,
                    "title": result["MdUserTaskExecution"].title,
                    "summary": result["MdUserTaskExecution"].summary,
                    "session_id": result["MdUserTaskExecution"].session_id,
                    "icon": result["MdTask"].icon,
                    "task_name": result["MdTaskDisplayedData"].name_for_user,
                    "actions": get_predefined_actions(result["MdTask"].task_pk),
                    "user_task_pk": result["MdUserTaskExecution"].user_task_fk,
                    "n_todos": get_n_todos(result["MdUserTaskExecution"].user_task_execution_pk),
                    "n_not_read_todos": get_n_todos_not_read(result["MdUserTaskExecution"].user_task_execution_pk),
                    "produced_text_pk": result["produced_text_pk"],
                    "produced_text_title": result["produced_text_title"],
                    "produced_text_production": result["produced_text_production"],
                    "produced_text_version_pk": result["produced_text_version_pk"],
                    "task_tool_executions": get_task_tool_executions(
                        result["MdUserTaskExecution"].user_task_execution_pk),
                    "text_edit_actions": recover_text_edit_actions(
                        result["MdUserTaskExecution"].user_task_fk),
                    "working_on_todos": result["MdUserTaskExecution"].todos_extracted is None
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
                                                          order_by=MdProducedTextVersion.creation_date.desc()).label(
                                                          'row_number')) \
                .join(MdProducedTextVersion, MdProducedTextVersion.produced_text_fk == MdProducedText.produced_text_pk) \
                .subquery()


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
                    MdUserTaskExecution,
                    MdTask,
                    coalesce(
                        user_lang_subquery.c.user_lang_name_for_user, 
                        en_subquery.c.en_name_for_user
                    ).label("name_for_user"),
                    produced_text_subquery.c.produced_text_pk.label("produced_text_pk"),
                    produced_text_subquery.c.produced_text_title.label("produced_text_title"),
                    produced_text_subquery.c.produced_text_production.label("produced_text_production"),
                    produced_text_subquery.c.produced_text_version_pk.label("produced_text_version_pk"),
                    MdUser.timezone_offset
                )
                .distinct(MdUserTaskExecution.user_task_execution_pk)
                .join(MdUserTask, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk)
                .join(MdUser, MdUser.user_id == MdUserTask.user_id)
                .join(MdTask, MdTask.task_pk == MdUserTask.task_fk)
                .outerjoin(user_lang_subquery, MdTask.task_pk == user_lang_subquery.c.task_fk)
                .outerjoin(en_subquery, MdTask.task_pk == en_subquery.c.task_fk)
                .outerjoin(produced_text_subquery, and_(
                    produced_text_subquery.c.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk,
                    produced_text_subquery.c.row_number == 1))
                .filter(MdUserTask.user_id == user_id)
                .filter(MdUserTaskExecution.start_date.isnot(None))
                .filter(MdUserTaskExecution.deleted_by_user.is_(None)))

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

            result = (result.group_by(MdUserTaskExecution.user_task_execution_pk, MdTask.task_pk,
                                      user_lang_subquery.c.user_lang_name_for_user,
                                      en_subquery.c.en_name_for_user,
                                      produced_text_subquery.c.produced_text_pk,
                                      produced_text_subquery.c.produced_text_title,
                                      produced_text_subquery.c.produced_text_production,
                                      produced_text_subquery.c.produced_text_version_pk,
                                      MdUser.timezone_offset
                                      )
                      .order_by(MdUserTaskExecution.user_task_execution_pk.desc())
                      .limit(n_user_task_executions)
                      .offset(offset)
                      .all())

            result = [row._asdict() for row in result]

            results_list = [{
                "user_task_execution_pk": row["MdUserTaskExecution"].user_task_execution_pk,
                "start_date": time_manager.backend_date_to_user_date(row["MdUserTaskExecution"].start_date,
                                                                     row["timezone_offset"]).isoformat() if row[
                                                                                                                "MdUserTaskExecution"].start_date and
                                                                                                            row[
                                                                                                                "timezone_offset"] else None,
                "end_date": time_manager.backend_date_to_user_date(row["MdUserTaskExecution"].end_date,
                                                                   row["timezone_offset"]).isoformat() if row[
                                                                                                              "MdUserTaskExecution"].end_date and
                                                                                                          row[
                                                                                                              "timezone_offset"] else None,
                "title": row["MdUserTaskExecution"].title,
                "summary": row["MdUserTaskExecution"].summary,
                "session_id": row["MdUserTaskExecution"].session_id,
                "icon": row["MdTask"].icon,
                "task_name": row["name_for_user"],
                "actions": get_predefined_actions(row["MdTask"].task_pk),
                "user_task_pk": row["MdUserTaskExecution"].user_task_fk,
                "n_todos": get_n_todos(row["MdUserTaskExecution"].user_task_execution_pk),
                "n_not_read_todos": get_n_todos_not_read(row["MdUserTaskExecution"].user_task_execution_pk),
                "produced_text_pk": row["produced_text_pk"],
                "produced_text_title": row["produced_text_title"],
                "produced_text_production": row["produced_text_production"],
                "produced_text_version_pk": row["produced_text_version_pk"],
                "task_tool_executions": get_task_tool_executions(row["MdUserTaskExecution"].user_task_execution_pk),
                "text_edit_actions": recover_text_edit_actions(row["MdUserTaskExecution"].user_task_fk),
                "working_on_todos": row["MdUserTaskExecution"].todos_extracted is None
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
