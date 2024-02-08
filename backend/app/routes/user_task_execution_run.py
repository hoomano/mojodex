import os
from datetime import datetime

from flask import request
from flask_restful import Resource
from app import db, authenticate, log_error, server_socket, executor, main_logger
from db_models import *
from sqlalchemy.orm.attributes import flag_modified
from models.tasks.task_manager import TaskManager
from models.session import Session
from models.voice_generator import VoiceGenerator
from packaging import version

class UserTaskExecutionRun(Resource):
    logger_prefix = "UserTaskExecutionRun"

    def __init__(self):
        UserTaskExecutionRun.method_decorators = [authenticate()]

    # post
    # This route is used to start a task_execution from a Form (webapp)
    def post(self, user_id):
        error_message = "Error launching UserTaskExecutionRun"
        if not request.is_json:
            log_error(f"{error_message} : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        # data
        try:
            timestamp = request.json["datetime"]
            user_task_execution_pk = request.json["user_task_execution_pk"]
            platform = request.json["platform"] if "platform" in request.json else "webapp"
            app_version = version.parse(request.json["version"]) if "version" in request.json else version.parse("0.0.0")
        except KeyError as e:
            log_error(f"{error_message} : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            user_task_execution = db.session.query(MdUserTaskExecution) \
                .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk) \
                .filter(MdUserTask.user_id == user_id) \
                .first()
            if user_task_execution is None:
                log_error(
                    f"{error_message} : UserTaskExecution {user_task_execution_pk} not found for user {user_id}")
                return {"error": f"UserTaskExecution  {user_task_execution_pk} not found for this user"}, 400

            # ensure inputs is a list of dicts and each dict has the required fields (input_name and input_value)
            if "inputs" in request.json:
                inputs = request.json["inputs"]
                if not isinstance(inputs, list):
                    return {"error": "inputs must be a JSON string or a list"}, 400
                json_input_values = user_task_execution.json_input_values
                for filled_input in inputs:
                    # check format
                    if not isinstance(filled_input, dict):
                        raise KeyError("inputs must be a list of dicts")
                    if "input_name" not in filled_input or "input_value" not in filled_input:
                        raise KeyError("inputs must be a list of dicts with keys input_name and input_value")
                    # look for corresponding input in json_input_values
                    for input in json_input_values:
                        if input["input_name"] == filled_input["input_name"]:
                            input["value"] = filled_input["input_value"]
                user_task_execution.json_input_values = json_input_values
                flag_modified(user_task_execution, "json_input_values")
                db.session.commit()

            task, user = (
                db.session
                .query(
                    MdTask,
                    MdUser
                    )
                .join(
                    MdUserTask, 
                    MdUserTask.task_fk == MdTask.task_pk
                )
                .join(
                    MdUser, 
                    MdUser.user_id == MdUserTask.user_id
                )
                .filter(
                    MdUserTask.user_task_pk == user_task_execution.user_task_fk
                )
                .filter(
                    MdUserTask.enabled == True
                )
                .first())

            if task is None:
                return {"error": "Task not found or disabled"}, 400

            if 'SPEECH_KEY' in os.environ and 'SPEECH_REGION' in os.environ:
                try:
                    voice_generator = VoiceGenerator() if platform == "mobile" else None
                except Exception as e:
                    voice_generator = None
                    main_logger.error(f"{UserTaskExecutionRun.logger_prefix}:: Can't initialize voice generator")
            else:
                voice_generator = None


            user_storage = os.path.join(Session.sessions_storage, user.user_id)
            if not os.path.exists(user_storage):
                os.makedirs(user_storage, exist_ok=True)
            session_storage = os.path.join(user_storage, user_task_execution.session_id)
            if not os.path.exists(session_storage):
                os.makedirs(session_storage, exist_ok=True)
            mojo_messages_audio_storage = os.path.join(session_storage, "mojo_messages_audios")
            if not os.path.exists(mojo_messages_audio_storage):
                os.makedirs(mojo_messages_audio_storage, exist_ok=True)

            user_task_execution.start_date = datetime.now()
            db.session.flush()
            db.session.refresh(user_task_execution)
            db.session.commit()

            task_manager = TaskManager(user, user_task_execution.session_id, platform, voice_generator,
                                       mojo_messages_audio_storage,
                                       task=task,
                                       user_task_execution=user_task_execution)

            def browse_missing_info_callback(app_version, task_manager, use_message_placeholder, use_draft_placeholder, tag_proper_nouns):
                task_manager.start_task_from_form(app_version, use_message_placeholder=use_message_placeholder, use_draft_placeholder=use_draft_placeholder, tag_proper_nouns=tag_proper_nouns)
                return

            use_message_placeholder = request.json['use_message_placeholder'] if (
                        'use_message_placeholder' in request.json) else False
            use_draft_placeholder = request.json['use_draft_placeholder'] if ('use_draft_placeholder' in request.json) else False

            server_socket.start_background_task(browse_missing_info_callback, app_version, task_manager, use_message_placeholder, use_draft_placeholder, platform=="mobile")

            return {"success": "ok"}, 200

        except Exception as e:
            db.session.rollback()
            log_error(f"{error_message} : {e}")
            return {"error": f"{e}"}, 500
