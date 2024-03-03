from flask import request
from flask_restful import Resource
from app import db, executor
from mojodex_core.entities import *

from background_logger import BackgroundLogger


from models.cortex.reschedule_todo_cortex import RescheduleTodoCortex


class RescheduleTodo(Resource):
    logger_prefix = "RescheduleTodo::"

    def __init__(self):
        self.logger = BackgroundLogger(f"{RescheduleTodo.logger_prefix}")

    def post(self):
        try:
            self.logger.debug(f"POST /reschedule_todo")
            timestamp = request.json['datetime']
            todo_pk = request.json['todo_pk']
        except Exception:
            return {"error": "invalid inputs"}, 400

        try:
            # check user_task_execution exists
            self.logger.debug(f"🟢 POST /reschedule_todo - todo_pk {todo_pk}")
            todo = db.session.query(MdTodo).filter(MdTodo.todo_pk == todo_pk).first()
            self.logger.debug(f"🟢 POST /reschedule_todo - todo retrieved from db")
            if todo is None:
                return {"error": "todo not found"}, 404

            reschedule_todos_cortex = RescheduleTodoCortex(todo)
            self.logger.debug(f"🟢 POST /reschedule_todo - reschedule_todos_cortex created")
            def run_reschedule_todos_cortex(cortex):
                try:
                    cortex.reschedule_todo()
                except Exception as err:
                    print("🔴" + str(err))

            executor.submit(run_reschedule_todos_cortex, reschedule_todos_cortex)
            return {"success": "Process started"}, 200
        except Exception as e:
            return {"error": f"Error in reschedule todos route : {e}"}, 404


