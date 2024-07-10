import os
from flask import request
from flask_restful import Resource
from app import db, authenticate
from mojodex_core.entities.instruct_user_task_execution import InstructTaskExecution
from mojodex_core.entities.user_task import UserTask
from mojodex_core.entities.user_workflow_execution import UserWorkflowExecution
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import MdProducedText, MdUserTask, MdUserTaskExecution, MdProducedTextVersion
from mojodex_core.entities.user_task_execution import UserTaskExecution as DBUserTaskExecution
from models.session_creator import SessionCreator
from sqlalchemy import func, and_, or_
from models.purchase_manager import PurchaseManager
from datetime import datetime

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

            # Subquery to get the last produced text versions
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

          
            if "user_task_execution_pk" in request.args:
                user_task_execution_pk = int(request.args["user_task_execution_pk"])
               
                user_task_execution: DBUserTaskExecution = (db.session.query(DBUserTaskExecution)
                    .filter(DBUserTaskExecution.user_task_execution_pk == user_task_execution_pk)
                    .join(MdUserTask, MdUserTask.user_task_pk == DBUserTaskExecution.user_task_fk)
                    .filter(MdUserTask.user_id == user_id)
                    .group_by(DBUserTaskExecution.user_task_execution_pk)
                    .first())
                
                return db.session.query(UserWorkflowExecution if user_task_execution.task.type == "workflow" else InstructTaskExecution).get(user_task_execution.user_task_execution_pk).to_json(), 200

            n_user_task_executions = min(50,
                                         int(request.args[
                                                 "n_user_task_executions"])) if "n_user_task_executions" in request.args else 50
            offset = int(request.args["offset"]) if "offset" in request.args else 0

          
            result = (db.session.query(DBUserTaskExecution)
                .distinct(DBUserTaskExecution.user_task_execution_pk)
                .join(MdUserTask, MdUserTask.user_task_pk == DBUserTaskExecution.user_task_fk)
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

            user_task_executions:  list[DBUserTaskExecution] = (result.group_by(DBUserTaskExecution.user_task_execution_pk)
                      .order_by(DBUserTaskExecution.user_task_execution_pk.desc())
                      .limit(n_user_task_executions)
                      .offset(offset)
                      .all())

            return {"user_task_executions": [db.session.query(UserWorkflowExecution if user_task_execution.task.type == "workflow" else InstructTaskExecution).get(user_task_execution.user_task_execution_pk).to_json() 
                                             for user_task_execution in user_task_executions]}, 200

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
