import os

import requests
from flask import request
from flask_restful import Resource
from models.session import Session as SessionModel
from app import db, authenticate, log_error
from mojodex_core.entities import *
from datetime import datetime


class TaskToolExecution(Resource):

    def __init__(self):
        TaskToolExecution.method_decorators = [authenticate()]

    # The user gave their validation for the tool usage
    def post(self, user_id):
        if not request.is_json:
            log_error(f"Error launching TaskToolExecution : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        # data
        try:
            timestamp = request.json["datetime"]
            task_tool_execution_pk = request.json["task_tool_execution_pk"]
        except KeyError as e:
            log_error(f"Error launching TaskToolExecution : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            # Check task_tool_execution exists for this user
            task_tool_execution = db.session.query(MdTaskToolExecution) \
                .join(MdUserTaskExecution, MdTaskToolExecution.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk) \
                .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                .filter(MdTaskToolExecution.task_tool_execution_pk == task_tool_execution_pk) \
                .filter(MdUserTask.user_id == user_id) \
                .first()
            if task_tool_execution is None:
                log_error(
                    f"Error launching TaskToolExecution : TaskToolExecution {task_tool_execution_pk} not found for user {user_id}")
                return {"error": f"TaskToolExecution  {task_tool_execution_pk} not found for this user"}, 400

            # Update task_tool_execution
            task_tool_execution.user_validation = datetime.now()
            db.session.flush()

            session_id = db.session.query(MdUserTaskExecution.session_id) \
                .join(MdTaskToolExecution, MdTaskToolExecution.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk) \
                .filter(MdTaskToolExecution.task_tool_execution_pk == task_tool_execution_pk) \
                .first()[0]

            message = {'text':"OK"}
            user_message = MdMessage(session_id=session_id, sender=SessionModel.user_message_key, event_name='user_message',
                                message=message,
                                creation_date=datetime.now(), message_date=datetime.now())
            db.session.add(user_message)
            db.session.flush()
            db.session.refresh(user_message)
            message["message_pk"] = user_message.message_pk
            user_message.message = message


            # Call background for launching execution
            uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/task_tool_execution"
            pload = {'datetime': datetime.now().isoformat(), 'task_tool_execution_pk': task_tool_execution_pk}
            internal_request = requests.post(uri, json=pload)
            if internal_request.status_code != 200:
                log_error(f"Error while calling background task_tool_execution_pk : {internal_request.json()}")
                return {"error": f"Error while calling background task_tool_execution_pk : {internal_request.json()}"}, 500

            db.session.commit()
            return {"message": "TaskToolExecution launched", "message_pk": user_message.message_pk}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error launching TaskToolExecution : {e}")
            return {"error": f"{e}"}, 500
