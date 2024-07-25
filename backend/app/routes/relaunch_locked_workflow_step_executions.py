
import os
from sqlalchemy.orm.attributes import flag_modified
import pytz
from flask import request
from flask_restful import Resource

from models.workflows.workflow_process_controller import WorkflowProcessController
from mojodex_core.authentication import authenticate_with_scheduler_secret
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import MdUserTaskExecution, MdUserWorkflowStepExecution, MdUserWorkflowStepExecutionResult
from app import db, server_socket
from datetime import datetime, timedelta
class RelaunchLockedWorkflowStepExecutions(Resource):


    def __init__(self):
        RelaunchLockedWorkflowStepExecutions.method_decorators = [authenticate_with_scheduler_secret(methods=["POST"])]

    def post(self):
        error_message = "Error relaunching locked workflow step executions"
        if not request.is_json:
            log_error(f"{error_message} : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        try:
            timestamp = request.json['datetime']
        except KeyError:
            log_error(f"{error_message} : Missing datetime in body", notify_admin=True)
            return {"error": f"Missing datetime in body"}, 400
        
        try:
            utc = pytz.UTC
            current_time = datetime.now(utc)
            thirty_mins_ago = current_time - timedelta(minutes=30)
            # find every user_workflow_step_execution that is locked => locked = no result and no error with creation_date > 30 minutes ago
           
            locked_steps = db.session.query(MdUserWorkflowStepExecution)\
                .outerjoin(MdUserWorkflowStepExecutionResult, MdUserWorkflowStepExecution.user_workflow_step_execution_pk == MdUserWorkflowStepExecutionResult.user_workflow_step_execution_fk)\
                .filter(MdUserWorkflowStepExecution.error_status.is_(None))\
                .filter(MdUserWorkflowStepExecution.creation_date < thirty_mins_ago)\
                .filter(MdUserWorkflowStepExecutionResult.user_workflow_step_execution_fk.is_(None))\
                .join(MdUserTaskExecution, MdUserWorkflowStepExecution.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk)\
                .filter(MdUserTaskExecution.deleted_by_user.is_(None))\
                .all()
            
            user_workflow_step_executions_pk = [step.user_workflow_step_execution_pk for step in locked_steps]
            # mark these steps as error
            for step in locked_steps:
                step.error_status = {"datetime": current_time.isoformat(), "message": "Step was locked for more than 2 hours."}
                flag_modified(step, "error_status")
                db.session.flush()
            db.session.commit()

            # relaunch these steps
            for step in locked_steps:
                workflow_process_controller = WorkflowProcessController(step.user_task_execution_fk)
                server_socket.start_background_task(workflow_process_controller.run)

            # Normally, flask_socketio will close db.session automatically after the request is done 
            # (https://flask.palletsprojects.com/en/2.3.x/patterns/sqlalchemy/) "Flask will automatically remove database sessions at the end of the request or when the application shuts down."
            # But if may not the case because of the background task launched in this route, errors like `QueuePool limit of size 5 overflow 10 reached` may happen in the backend logs and cause issues.
            # That's why here we explicitely call `db.session.close()` to close the session manually.
            db.session.close()
            return {"user_workflow_step_executions_pk": user_workflow_step_executions_pk}, 200

        except Exception as e:
            db.session.rollback()
            log_error(f"{error_message} : {e}", notify_admin=True)
            db.session.close()
            return {"error": f"{e}"}, 500