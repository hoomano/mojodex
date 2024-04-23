import base64
from datetime import datetime
import json
import os

from models.user_images_file_manager import UserImagesFileManager
from flask import request
from flask_restful import Resource
from app import db, authenticate, server_socket
from models.workflows.workflow_execution import WorkflowExecution
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import *
from sqlalchemy.orm.attributes import flag_modified
from packaging import version
from werkzeug.utils import secure_filename

class UserTaskExecutionRun(Resource):
    logger_prefix = "UserTaskExecutionRun"
    image_type = "image"

    def __init__(self):
        UserTaskExecutionRun.method_decorators = [authenticate()]
        self.user_image_file_manager = UserImagesFileManager()


    # post
    # This route is used to start a task_execution from a Form (webapp)
    def post(self, user_id):
        error_message = "Error launching UserTaskExecutionRun"
        print(f"🟢 {request.headers.get('Content-Type')}")

        # data
        try:
            if request.is_json: # USED UNTIL VERSION 0.4.11
                timestamp = request.json["datetime"]
                user_task_execution_pk = request.json["user_task_execution_pk"]
                platform = request.json["platform"] if "platform" in request.json else "webapp"
                app_version = version.parse(request.json["version"]) if "version" in request.json else version.parse("0.0.0")
                inputs = request.json["inputs"]
                use_message_placeholder = request.json['use_message_placeholder'] if (
                    'use_message_placeholder' in request.json) else False
                use_draft_placeholder = request.json['use_draft_placeholder'] if (
                        'use_draft_placeholder' in request.json) else False
            else:
                timestamp = request.form["datetime"]
                user_task_execution_pk = request.form["user_task_execution_pk"]
                platform = request.form["platform"] if "platform" in request.form else "webapp"
                app_version = version.parse(request.form["version"]) if "version" in request.form else version.parse("0.0.0")
                inputs = json.loads(request.form["inputs"])
                use_message_placeholder = request.form['use_message_placeholder'] if (
                    'use_message_placeholder' in request.form) else False
                use_draft_placeholder = request.form['use_draft_placeholder'] if (
                        'use_draft_placeholder' in request.form) else False
        except KeyError as e:
            log_error(f"{error_message} : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            result = db.session.query(MdUserTaskExecution, MdTask) \
                .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                .join(MdTask, MdTask.task_pk == MdUserTask.task_fk) \
                .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk) \
                .filter(MdUserTask.user_id == user_id) \
                .first()
            if result is None:
                log_error(
                    f"{error_message} : UserTaskExecution {user_task_execution_pk} not found for user {user_id}")
                return {"error": f"UserTaskExecution  {user_task_execution_pk} not found for this user"}, 400

            user_task_execution, task = result

            # ensure inputs is a list of dicts and each dict has the required fields (input_name and input_value)
            if not isinstance(inputs, list):
                return {"error": "inputs must be a list"}, 400
            
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

            for image_input in request.files:
                # look for corresponding input in json_input_values
                for input in json_input_values:
                    if input["input_name"] == image_input:
                        filename = secure_filename(request.files[image_input].filename)
                        input['value'] = filename
                        self.user_image_file_manager.store_image_file(request.files[image_input], filename, user_id, user_task_execution.session_id)

            user_task_execution.json_input_values = json_input_values
            flag_modified(user_task_execution, "json_input_values")
            db.session.commit()

            user_task_execution.start_date = datetime.now()
            db.session.commit()

            if task.type =="instruct":
                # Launch the process
                from models.session.session import Session as SessionModel
                session = SessionModel(user_task_execution.session_id)

                def launch_process(session, app_version, platform, user_task_execution_pk, use_message_placeholder, use_draft_placeholder):
                    session.process_form_input( app_version, platform, user_task_execution_pk, use_message_placeholder=use_message_placeholder, use_draft_placeholder=use_draft_placeholder)
                    return

                server_socket.start_background_task(launch_process, session, app_version, platform, user_task_execution_pk, use_message_placeholder, use_draft_placeholder)
            else:
                workflow_execution = WorkflowExecution(user_task_execution_pk)
                server_socket.start_background_task(workflow_execution.run)

            return {"success": "ok"}, 200

        except Exception as e:
            db.session.rollback()
            log_error(f"{error_message} : {e}")
            return {"error": f"{e}"}, 500
