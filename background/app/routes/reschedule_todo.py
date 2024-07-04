from models.todos.todos_rescheduler import TodosRescheduler
from flask import request
from flask_restful import Resource
from app import db, executor
from mojodex_core.entities.db_base_entities import MdTodo


class RescheduleTodo(Resource):
    def post(self):
        try:
            timestamp = request.json['datetime']
            todo_pk = request.json['todo_pk']
        except Exception:
            return {"error": "invalid inputs"}, 400

        try:
            # check user_task_execution exists
            todo = db.session.query(MdTodo).filter(MdTodo.todo_pk == todo_pk).first()
            if todo is None:
                return {"error": "todo not found"}, 404

            todos_rescheduler = TodosRescheduler(todo_pk)

            executor.submit(todos_rescheduler.reschedule_and_save)
            return {"success": "Process started"}, 200
        except Exception as e:
            return {"error": f"Error in reschedule todos route : {e}"}, 404


