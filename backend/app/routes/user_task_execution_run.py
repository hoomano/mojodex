
import json

from models.user_task_execution_inputs_manager import UserTaskExecutionInputsManager
from flask import request
from flask_restful import Resource
from app import db, server_socket
from mojodex_core.authentication import authenticate
from models.workflows.workflow_process_controller import WorkflowProcessController
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import MdUserTaskExecution, MdTask, MdUserTask
from sqlalchemy.orm.attributes import flag_modified
from packaging import version
from datetime import datetime

# This route is used to start a task_execution from a Form (webapp)
# Note: From mobile app, there is no form, so the user_task_execution is started from a message
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

            # Manage the inputs received from the form, this is generically done and managed before the execution of the task (instruct or workflow) itself
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
                from models.assistant.session_controller import SessionController
                session = SessionController(user_task_execution.session_id)

                def launch_process(session, app_version, platform, user_task_execution_pk, use_message_placeholder, use_draft_placeholder):
                    session.process_form_input( app_version, platform, user_task_execution_pk, use_message_placeholder=use_message_placeholder, use_draft_placeholder=use_draft_placeholder)
                    return

                server_socket.start_background_task(launch_process, session, app_version, platform, user_task_execution_pk, use_message_placeholder, use_draft_placeholder)
            else:
                workflow_execution = WorkflowProcessController(user_task_execution_pk)
                server_socket.start_background_task(workflow_execution.run)


            # Normally, flask_socketio will close db.session automatically after the request is done 
            # (https://flask.palletsprojects.com/en/2.3.x/patterns/sqlalchemy/) "Flask will automatically remove database sessions at the end of the request or when the application shuts down."
            # But if may not the case because of the background task launched in this route, errors like `QueuePool limit of size 5 overflow 10 reached` may happen in the backend logs and cause issues.
            # That's why here we explicitely call `db.session.close()` to close the session manually.
            db.session.close()

            return {"success": "ok"}, 200

        except Exception as e:
            db.session.rollback()
            log_error(f"{error_message} : {e}")
            db.session.close()
            return {"error": f"{e}"}, 500
