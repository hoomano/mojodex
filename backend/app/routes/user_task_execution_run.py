from datetime import datetime
import json

from models.user_task_execution_inputs_manager import UserTaskExecutionInputsManager
from flask import request
from flask_restful import Resource
from app import db, authenticate, server_socket
from models.workflows.workflow_execution import WorkflowExecution
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import MdUserTaskExecution, MdTask, MdUserTask
from sqlalchemy.orm.attributes import flag_modified
from packaging import version

class UserTaskExecutionRun(Resource):
    logger_prefix = "UserTaskExecutionRun"
    image_type = "image"

    def __init__(self):
        UserTaskExecutionRun.method_decorators = [authenticate()]
        self.user_task_execution_inputs_manager = UserTaskExecutionInputsManager()

    # post
    # This route is used to start a task_execution from a Form (webapp)
    def post(self, user_id):
        error_message = "Error launching UserTaskExecutionRun"

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

            json_input_values = self.user_task_execution_inputs_manager.construct_inputs_from_request(user_task_execution.json_input_values,
                                                                                    inputs, request.files, user_id,
                                                                                    user_task_execution.session_id)
            user_task_execution.json_input_values = json_input_values
            flag_modified(user_task_execution, "json_input_values")
            db.session.commit()

            user_task_execution.start_date = datetime.now()
            db.session.commit()

            if task.type =="instruct":
                # Launch the process
                from models.assistant.session import Session as SessionModel
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
