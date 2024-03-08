from flask import request
from flask_restful import Resource
from app import db, executor
from mojodex_core.entities import *

from background_logger import BackgroundLogger

from models.cortex.extract_todos_cortex import ExtractTodosCortex


class ExtractTodos(Resource):
    logger_prefix = "ExtractTodos::"

    def __init__(self):
        self.logger = BackgroundLogger(f"{ExtractTodos.logger_prefix}")

    def post(self):
        try:
            self.logger.debug(f"POST /extract_todos")
            timestamp = request.json['datetime']
            user_task_execution_pk = request.json['user_task_execution_pk']
        except Exception:
            return {"error": "invalid inputs"}, 400

        try:
            # check user_task_execution exists
            self.logger.debug(f"🟢 POST /extract_todos - user_task_execution_pk {user_task_execution_pk}")
            user_task_execution = db.session.query(MdUserTaskExecution).filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk).first()
            self.logger.debug(f"🟢 POST /extract_todos - user_task_execution retrieved from db")
            if user_task_execution is None:
                return {"error": "user_task_execution not found"}, 404

            extract_todos_cortex = ExtractTodosCortex(user_task_execution)
            self.logger.debug(f"🟢 POST /extract_todos - extract_todos_cortex created")
            def run_extract_todos_cortex(cortex):
                try:
                    cortex.extract_todos()
                except Exception as err:
                    print("🔴" + str(err))

            executor.submit(run_extract_todos_cortex, extract_todos_cortex)
            return {"success": "Process started"}, 200
        except Exception as e:
            return {"error": f"Error in extract todos route : {e}"}, 404


