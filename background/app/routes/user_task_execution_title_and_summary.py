from flask import request
from flask_restful import Resource

from mojodex_core.entities import *

from models.cortex.user_task_execution_title_and_summary_cortex import UserTaskExecutionTitleAndSummaryCortex

from background_logger import BackgroundLogger


class UserTaskExecutionTitleAndSummary(Resource):
    logger_prefix = "UserTaskExecutionTitleAndSummary::"

    def __init__(self):
        self.logger = BackgroundLogger(f"{UserTaskExecutionTitleAndSummary.logger_prefix}")

    def post(self):
        try:
            self.logger.info(f"POST /user_task_execution_title_and_summary")
            timestamp = request.json['datetime']
            user_task_execution_pk = request.json['user_task_execution_pk']
        except Exception:
            return {"error": "invalid inputs"}, 400

        try:
            from app import db, executor
            self.logger.info(f"🟢 POST /user_task_execution_title_and_summary - user_task_execution_pk {user_task_execution_pk}")
            # check user_task_execution exists
            user_task_execution = db.session.query(MdUserTaskExecution).filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk).first()
            self.logger.info(f"🟢 POST /user_task_execution_title_and_summary - user_task_execution retrieved from db")
            if user_task_execution is None:
                return {"error": "user_task_execution not found"}, 404
            user_task_execution_title_and_summary_cortex = UserTaskExecutionTitleAndSummaryCortex(user_task_execution)
            def run_user_task_execution_title_and_summary_cortex(cortex):
                try:
                    print(f"🟢 run_user_task_execution_title_and_summary_cortex")
                    cortex.manage_user_task_execution_title_and_summary()
                except Exception as err:
                    print("🔴" + str(err))

            executor.submit(run_user_task_execution_title_and_summary_cortex, user_task_execution_title_and_summary_cortex)
            return {"success": "Process started"}, 200
        except Exception as e:
            return {"error": f"Error in manage_user_task_execution_title_and_summary : {e}"}, 404


