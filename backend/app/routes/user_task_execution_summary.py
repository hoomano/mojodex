import os
from flask import request
from flask_restful import Resource
from app import db, log_error, server_socket
from mojodex_core.entities import *

class UserTaskExecutionSummary(Resource):

    # updating user_summary
    def post(self):
        if not request.is_json:
            return {"error": "Invalid request"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                log_error(f"Error updating UserTaskExecution summary : Authentication error : Wrong secret")
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"Error updating user summary : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        # data
        try:
            timestamp = request.json["datetime"]
            title = request.json["title"]
            summary = request.json["summary"]
            user_task_execution_pk = request.json["user_task_execution_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            # find user_task_execution
            user_task_execution = db.session.query(MdUserTaskExecution)\
                .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk)\
                .first()
            if user_task_execution is None:
                return {"error": f"Invalid user_task_execution_pk: {user_task_execution_pk}"}, 400

            # update user_task_execution summary
            user_task_execution.title = title
            user_task_execution.summary = summary

            # if session as started in form mode, it takes the same title as the user_task_execution
            session = db.session.query(MdSession).filter(MdSession.session_id == user_task_execution.session_id).first()
            if session.starting_mode == "form":
                session.title = title

            db.session.commit()

            server_socket.emit('user_task_execution_title', {"title": title, "session_id": user_task_execution.session_id},
                               to=user_task_execution.session_id)

            return {"success": True}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error updating user_task_execution summary : {e}")
            return {"error": f"Error updating user_task_execution summary : {e}"}, 400