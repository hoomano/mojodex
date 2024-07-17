import os
from flask import request
from flask_restful import Resource
from app import db, authenticate
from mojodex_core.entities.instruct_user_task_execution import InstructTaskExecution
from mojodex_core.entities.user_task import UserTask
from mojodex_core.entities.user_workflow_execution import UserWorkflowExecution
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import MdProducedText, MdTask, MdTaskDisplayedData, MdUser, MdUserTask, MdUserTaskExecution, MdProducedTextVersion
from mojodex_core.entities.user_task_execution import UserTaskExecution as UserTaskExecutionEntity
from models.session_creator import SessionCreator
from sqlalchemy import func, and_, or_
from models.purchase_manager import PurchaseManager
from datetime import datetime
from sqlalchemy.sql.functions import coalesce

# This class is used to create, get and delete UserTaskExecution
# Once created, the UserTaskExecution is "run" ==> see UserTaskExecutionRun
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

            
            task_execution: UserTaskExecutionEntity = UserTaskExecutionEntity(user_task_fk=user_task_pk,
                                                 json_input_values=empty_json_input_values, session_id=session_id)
            if "user_task_execution_fk" in request.json:
                task_execution.predefined_action_from_user_task_execution_fk = request.json["user_task_execution_fk"]
            db.session.add(task_execution)
            db.session.flush()
            db.session.refresh(task_execution)

            db.session.commit()


            return {**{"user_task_execution_pk": task_execution.user_task_execution_pk,
                     "json_input": json_input,
                     "actions": task_execution.user_task.predefined_actions,
                     "text_edit_actions" : task_execution.user_task.text_edit_actions,
                     }, **session_creation[0]}, 200 # append session_creation to returned dict
        except Exception as e:
            db.session.rollback()
            log_error(f"Error creating UserTaskExecution : {e}")
            return {"error": f"{e}"}, 500

    # end of task
    # Used by backend/app/user_task_execution_purchase_updater.py
    # TODO > should be refacto to trigger on database event to update purchase status
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
        

    def _retrieve_specific_user_task_execution(self, user_task_execution_pk, user_id):
        try:
            user_task_execution: UserTaskExecutionEntity = (db.session.query(UserTaskExecutionEntity)
                .filter(UserTaskExecutionEntity.user_task_execution_pk == user_task_execution_pk)
                .join(MdUserTask, MdUserTask.user_task_pk == UserTaskExecutionEntity.user_task_fk)
                .filter(MdUserTask.user_id == user_id)
                .first())
            
            # Need to query the right implementation table to get access to the specialised "to_json" method
            return db.session.query(UserWorkflowExecution if user_task_execution.task.type == "workflow" else InstructTaskExecution).get(user_task_execution.user_task_execution_pk)
        except Exception as e:
            raise Exception(f"_retrieve_specific_user_task_execution: {e}")

    def _retrieve_list_of_user_task_executions(self, user_id, n_user_task_executions, offset, search_filter=None, search_user_tasks_filter_list=None):
        try:
            # Subquery to get the last produced text versions for each user_task_execution
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
                
                # Subquery to get the highest row number for each user_task_execution
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
            
                result = (db.session.query(UserTaskExecutionEntity, 
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
                                        MdUser.language_code)
                    .distinct(UserTaskExecutionEntity.user_task_execution_pk)
                    .join(MdUserTask, MdUserTask.user_task_pk == UserTaskExecutionEntity.user_task_fk)
                    .join(MdUser, MdUser.user_id == MdUserTask.user_id)
                    .join(MdTask, MdTask.task_pk == MdUserTask.task_fk)
                    .outerjoin(user_lang_subquery, MdTask.task_pk == user_lang_subquery.c.task_fk)
                    .outerjoin(en_subquery, MdTask.task_pk == en_subquery.c.task_fk)
                    .outerjoin(highest_row_number_subquery,
                            highest_row_number_subquery.c.user_task_execution_fk == UserTaskExecutionEntity.user_task_execution_pk)
                    .outerjoin(produced_text_subquery,
                                and_(
                                    produced_text_subquery.c.user_task_execution_fk == UserTaskExecutionEntity.user_task_execution_pk,
                                    produced_text_subquery.c.row_number == highest_row_number_subquery.c.max_row_number))
                    .filter(MdUserTask.user_id == user_id)
                    .filter(UserTaskExecutionEntity.start_date.isnot(None))
                    .filter(UserTaskExecutionEntity.deleted_by_user.is_(None)))


                if search_filter:
                    result = result.filter(UserTaskExecutionEntity.title.ilike(f"%{search_filter}%"))

                if search_user_tasks_filter_list:
                    result = result.filter(MdUserTask.user_task_pk.in_(search_user_tasks_filter_list))

                result = (result.group_by(UserTaskExecutionEntity.user_task_execution_pk, MdTask.task_pk,
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
                      .order_by(UserTaskExecutionEntity.user_task_execution_pk.desc())
                      .limit(n_user_task_executions)
                      .offset(offset)
                      .all())

                return [row._asdict() for row in result]
        except Exception as e:
            raise Exception(f"_retrieve_list_of_user_task_executions: {e}")

    def get(self, user_id):
        """
        Used both to retrieve a single user_task_execution and a list of user_task_executions
        In the case of getting a list of user_task_executions or a specific user_task_execution, it's used by both:
        - the webapp to display the list of past user_task_executions
        - the mobile app to display the list of past user_task_executions AND store each user_task_execution in the local memory to avoid reloading them each time
        """
        try:
            timestamp = request.args["datetime"]
        except KeyError as e:
            log_error(f"Error getting user_task_executions : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        try:
            # Return a specific user_task_execution
            if "user_task_execution_pk" in request.args:
                user_task_execution_pk = int(request.args["user_task_execution_pk"])
                user_task_execution = self._retrieve_specific_user_task_execution(user_task_execution_pk, user_id)
                return user_task_execution.to_json(), 200
            
            # Else, return a list of user_task_executions
            else:
                # Return a list of user_task_executions
                n_user_task_executions = min(50, int(request.args["n_user_task_executions"])) if "n_user_task_executions" in request.args else 50
                offset = int(request.args["offset"]) if "offset" in request.args else 0
                search_filter = request.args["search_filter"] if "search_filter" in request.args else None
                search_user_tasks_filter = request.args["user_task_pks"] if "user_task_pks" in request.args else None
                search_user_tasks_filter_list =  search_user_tasks_filter.split(";") if search_user_tasks_filter else None
                rows = self._retrieve_list_of_user_task_executions(user_id, n_user_task_executions, offset, search_filter=search_filter, search_user_tasks_filter_list=search_user_tasks_filter_list)
                
                
                results_list = [{
                    "user_task_execution_pk": row["UserTaskExecution"].user_task_execution_pk,
                    "start_date": row["UserTaskExecution"].start_date_user_timezone.isoformat(),
                    "end_date": row["UserTaskExecution"].end_date_user_timezone.isoformat() if row["UserTaskExecution"].end_date else None,
                    "title": row["UserTaskExecution"].title,
                    "summary": row["UserTaskExecution"].summary,
                    "session_id": row["UserTaskExecution"].session_id,
                    "json_inputs_values": None if all(input.get('value') is None for input in row["UserTaskExecution"].json_input_values) else row["UserTaskExecution"].json_input_values,
                    "icon": row["MdTask"].icon,
                    "task_name": row["name_for_user"],
                    "task_type": row["MdTask"].type,
                    "result_chat_enabled": row["MdTask"].result_chat_enabled,
                    "actions": row["UserTaskExecution"].user_task.predefined_actions,
                    "user_task_pk": row["UserTaskExecution"].user_task_fk,
                    "n_todos":row["UserTaskExecution"].n_todos,
                    "n_not_read_todos": row["UserTaskExecution"].n_todos_not_read,
                    "produced_text_pk": row["produced_text_pk"],
                    "produced_text_title": row["produced_text_title"],
                    "produced_text_production": row["produced_text_production"],
                    "produced_text_version_pk": row["produced_text_version_pk"],
                    "produced_text_version_index": row["produced_text_version_index"],
                    "text_edit_actions": row["UserTaskExecution"].user_task.text_edit_actions,
                    "working_on_todos": row["UserTaskExecution"].todos_extracted is None
                } for row in rows]

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
                .filter(MdUserTask.user_id == user_id) \
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
