from sqlalchemy import extract, func, text
from models.todos.todos_rescheduler import TodosRescheduler
from flask import request
from flask_restful import Resource
from app import db, executor
from mojodex_core.entities.db_base_entities import MdTodo, MdTodoScheduling, MdUser, MdUserTask, MdUserTaskExecution
from datetime import datetime, timedelta, timezone

class RescheduleTodo(Resource):
    def post(self):
        try:
            timestamp = request.json['datetime']
        except Exception:
            return {"error": "invalid inputs"}, 400

        try:
            
            # find all users for which it is 1am in their timezone
            # find all of those users todo that last scheduled date is yesterday and completed is null and deleted_by_user is null
            offset = 0
            n_todos = 50
            todo_pks = []
            results = []

            while len(results) == 50 or offset == 0:
                yesterday = datetime.now(timezone.utc) - timedelta(days=1)

                latest_todo_scheduling = db.session.query(MdTodoScheduling.todo_fk, func.max(MdTodoScheduling.scheduled_date).label('scheduled_date')) \
                    .group_by(MdTodoScheduling.todo_fk) \
                    .subquery()

                # no reschedule while user is on week-end to avoid sending emails to inform about rescheduling on week-end
                results = db.session.query(MdTodo) \
                    .join(latest_todo_scheduling, MdTodo.todo_pk == latest_todo_scheduling.c.todo_fk) \
                    .join(MdUserTaskExecution, MdTodo.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk) \
                    .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                    .join(MdUser, MdUserTask.user_id == MdUser.user_id) \
                    .filter(latest_todo_scheduling.c.scheduled_date < yesterday) \
                    .filter(MdTodo.deleted_by_user.is_(None)) \
                    .filter(MdTodo.deleted_by_mojo.is_(None)) \
                    .filter(MdTodo.completed.is_(None)) \
                    .filter(extract("hour", text('NOW() - md_user.timezone_offset * interval \'1 minute\'')) >= int(1)) \
                    .filter(extract("hour", text('NOW() - md_user.timezone_offset * interval \'1 minute\'')) < int(1) + 1) \
                    .filter(extract("dow", text('NOW() - md_user.timezone_offset * interval \'1 minute\'')) != int(0)) \
                    .filter(extract("dow", text('NOW() - md_user.timezone_offset * interval \'1 minute\'')) != int(6)) \
                    .all()

                todo_pks += [todo.todo_pk for todo in results]
                offset += n_todos


            def reschedule_todos_by_batches(todo_pks):
                for todo_pk in todo_pks:
                    todos_rescheduler = TodosRescheduler(todo_pk)
                    todos_rescheduler.reschedule_and_save()

            executor.submit(reschedule_todos_by_batches, todo_pks)
            
            return {"todo_pks": todo_pks}, 200
        except Exception as e:
            return {"error": f"Error in reschedule todos route : {e}"}, 404


