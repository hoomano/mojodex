from models.todos.todos_creator import TodosCreator
from flask import request
from flask_restful import Resource
from app import db, executor
from mojodex_core.entities.db_base_entities import MdUserTaskExecution

class ExtractTodos(Resource):

    def post(self):
        try:
            timestamp = request.json['datetime']
            user_task_execution_pk = request.json['user_task_execution_pk']
        except Exception:
            return {"error": "invalid inputs"}, 400

        try:
            # check user_task_execution exists
            user_task_execution = db.session.query(MdUserTaskExecution).filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk).first()
            if user_task_execution is None:
                return {"error": "user_task_execution not found"}, 404

            todos_creator = TodosCreator(user_task_execution_pk)

            executor.submit(todos_creator.extract_and_save)
            return {"success": "Process started"}, 200
        except Exception as e:
            return {"error": f"Error in extract todos route : {e}"}, 404


