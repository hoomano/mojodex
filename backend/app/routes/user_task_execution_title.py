import os
from flask import request
from flask_restful import Resource
from app import db, authenticate
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *


class UserTaskExecutionTitle(Resource):

    def __init__(self):
        UserTaskExecutionTitle.method_decorators = [authenticate()]

    # updating user_summary
    def post(self, user_id):
        if not request.is_json:
            return {"error": "Invalid request"}, 400

        try:
            timestamp = request.json["datetime"]
            title = request.json["title"]
            user_task_execution_pk = request.json["user_task_execution_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            # find user_task_execution
            user_task_execution = db.session.query(MdUserTaskExecution)\
                .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk)\
                .join(MdUserTask, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk)\
                .filter(MdUserTask.user_id == user_id)\
                .first()
            if user_task_execution is None:
                return {"error": f"Invalid user_task_execution_pk: {user_task_execution_pk}"}, 400

            # update user_task_execution title
            user_task_execution.title = title

            db.session.commit()

            return {"success": True}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error updating user_task_execution title : {e}")
            return {"error": f"Error updating user_task_execution title : {e}"}, 400