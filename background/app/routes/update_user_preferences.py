from flask import request
from flask_restful import Resource
from app import db, executor
from db_models import *

from background_logger import BackgroundLogger

from models.cortex.update_user_preferences_cortex import UpdateUserPreferencesCortex


class UpdateUserPreferences(Resource):
    logger_prefix = "UpdateUserPreferences::"

    def __init__(self):
        self.logger = BackgroundLogger(f"{UpdateUserPreferences.logger_prefix}")

    def post(self):
        try:
            self.logger.debug(f"POST /update_user_preferences")
            timestamp = request.json['datetime']
            user_task_execution_pk = request.json['user_task_execution_pk']
        except Exception:
            return {"error": "invalid inputs"}, 400

        try:
            # check user_task_execution exists
            user_task_execution = db.session.query(MdUserTaskExecution).filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk).first()
            if user_task_execution is None:
                return {"error": "user_task_execution not found"}, 404

            update_user_preferences_cortex = UpdateUserPreferencesCortex(user_task_execution)
            def run_update_user_preferences_cortex(cortex):
                try:
                    cortex.update_user_preferences()
                except Exception as err:
                    print("🔴" + str(err))

            executor.submit(run_update_user_preferences_cortex, update_user_preferences_cortex)
            return {"success": "Process started"}, 200
        except Exception as e:
            return {"error": f"Error in update user preferences route : {e}"}, 404


