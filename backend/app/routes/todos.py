import os
from datetime import datetime

from flask import request
from flask_restful import Resource
from app import db, authenticate, log_error
from mojodex_core.entities import *
from sqlalchemy import func, text


class Todos(Resource):
    MAX_TODOS = 50

    def __init__(self):
        Todos.method_decorators = [authenticate(methods=["POST", "GET", "DELETE"])]

    # adding new todo
    def put(self):
        if not request.is_json:
            return {"error": "Invalid request"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                log_error(f"Error creating new todo : Authentication error : Wrong secret")
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"Error creating new todo : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        # data
        try:
            timestamp = request.json["datetime"]
            description = request.json["description"]
            due_date = request.json["due_date"]
            try:
                due_date = datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                return {"error": f"Invalid due_date {due_date}"}, 400
            user_task_execution_fk = request.json["user_task_execution_fk"]

        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            # create new todo
            new_todo = MdTodo(
                creation_date=timestamp,
                description=description,
                user_task_execution_fk=user_task_execution_fk
            )
            db.session.add(new_todo)
            db.session.flush()
            db.session.refresh(new_todo)

            # create todo_scheduling
            new_todo_scheduling = MdTodoScheduling(
                todo_fk=new_todo.todo_pk,
                scheduled_date=due_date
            )

            db.session.add(new_todo_scheduling)
            db.session.commit()

            return {"todo_pk": new_todo.todo_pk}, 200

        except Exception as e:
            db.session.rollback()
            log_error(f"Error creating new todo : {e}")
            return {"error": f"Error creating new todo : {e}"}, 400

    # marking todo as done or as read
    def post(self, user_id):
        if not request.is_json:
            return {"error": "Invalid request"}, 400

        try:
            timestamp = request.json["datetime"]
            mark_as_read = request.json["mark_as_read"] if "mark_as_read" in request.json else False
            mark_as_done = request.json["mark_as_done"] if "mark_as_done" in request.json else False
            # check one and only one of mark_as_read and mark_as_done is True
            if sum([mark_as_read, mark_as_done]) == 0 or sum([mark_as_read, mark_as_done]) == 2:
                return {"error": "mark_as_read and mark_as_done are False. Set just one of them as True"}, 400
            # if mark as done, ensure there is a todo_pk
            if mark_as_done and "todo_pk" not in request.json:
                return {"error": "Missing field todo_pk"}, 400
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            if "todo_pk" in request.json:
                todo_pk = request.json["todo_pk"]
                # check todo exists for this user
                todo = db.session.query(MdTodo)\
                    .filter(MdTodo.todo_pk == todo_pk)\
                    .join(MdUserTaskExecution, MdTodo.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk)\
                    .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk)\
                    .join(MdUser, MdUserTask.user_id == MdUser.user_id)\
                    .filter(MdUser.user_id == user_id)\
                    .first()
                if todo is None:
                    return {"error": "Todo not found"}, 404

                if mark_as_read:
                    todo.read_by_user = datetime.now()
                elif mark_as_done:
                    if todo.completed:
                        return {"error": "Todo already done, can't do it again."}, 400
                    else:
                        todo.completed = datetime.now()
                db.session.commit()
                return {"todo_pk": todo_pk}, 200

            if "user_task_execution_pk" in request.json and mark_as_read:
                user_task_execution_pk = request.json["user_task_execution_pk"]
                # check user_task_execution_pk exists for this user
                user_task_execution = db.session.query(MdUserTaskExecution) \
                    .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                    .join(MdUser, MdUserTask.user_id == MdUser.user_id) \
                    .filter(MdUser.user_id == user_id) \
                    .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk) \
                    .first()
                if user_task_execution is None:
                    return {"error": "user_task_execution_pk not found"}, 404

                if mark_as_read:
                    todos = db.session.query(MdTodo)\
                        .filter(MdTodo.user_task_execution_fk == user_task_execution_pk)\
                        .filter(MdTodo.read_by_user.is_(None))\
                        .all()
                    for todo in todos:
                        todo.read_by_user = datetime.now()
                db.session.commit()
                return {"user_task_execution_pk": user_task_execution_pk}, 200


            # mark all todos related to an user as read
            if mark_as_read :
                all_user_todos = (
                    db.session.query(MdTodo)
                    .join(MdUserTaskExecution, MdTodo.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk)
                    .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk)
                    .join(MdUser, MdUserTask.user_id == MdUser.user_id)
                    .filter(MdUser.user_id == user_id)
                    .filter(MdTodo.read_by_user.is_(None))
                    .all())

                for todo in all_user_todos:
                    todo.read_by_user = datetime.now()
                db.session.commit()

                return {"todo_pks": [todo.todo_pk for todo in all_user_todos]}, 200

            else:
                return {"error": f"Invalid request - {request.json}"}, 400

        except Exception as e:
            db.session.rollback()
            log_error(f"Error marking todo as done : {e}")
            return {"error": f"Error marking todo as done : {e}"}, 400


    # deleting todo
    def delete(self, user_id):

        try:
            timestamp = request.args["datetime"]
            todo_pk = request.args["todo_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            # Check todo exists for this user
            todo = db.session.query(MdTodo) \
                .filter(MdTodo.todo_pk == todo_pk) \
                .join(MdUserTaskExecution, MdTodo.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk) \
                .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                .join(MdUser, MdUserTask.user_id == MdUser.user_id) \
                .filter(MdUser.user_id == user_id) \
                .first()
            if todo is None:
                return {"error": "Todo not found"}, 404

            todo.deleted_by_user = datetime.now()
            db.session.commit()
            return {"todo_pk": todo_pk}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error deleting todo : {e}")
            return {"error": f"Error deleting todo : {e}"}, 400


    # get todos
    def get(self, user_id):

        try:
            timestamp = request.args["datetime"]
            n_todos = min(Todos.MAX_TODOS, int(request.args[
                                                           "n_todos"])) if "n_todos" in request.args else Todos.MAX_TODOS
            offset = int(request.args["offset"]) if "offset" in request.args else 0

        except KeyError as e:
            return {"error": f"Missing {e} in args"}, 400

        try:
            # Subquery to get the latest todo_scheduling for each todo
            latest_todo_scheduling = db.session.query(
                MdTodoScheduling.todo_fk,
                func.max(MdTodoScheduling.scheduled_date).label('latest_scheduled_date'))\
                .group_by(MdTodoScheduling.todo_fk)\
                .subquery()
            # Get the current date in UTC
            now_utc = datetime.utcnow().date()
            if "user_task_execution_fk" in request.args:
                user_task_execution_pk = request.args["user_task_execution_fk"]
                # ensure user_task_execution_pk exists for this user
                user_task_execution = db.session.query(MdUserTaskExecution) \
                    .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                    .join(MdUser, MdUserTask.user_id == MdUser.user_id) \
                    .filter(MdUser.user_id == user_id) \
                    .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk) \
                    .first()
                if user_task_execution is None:
                    return {"error": "user_task_execution_pk not found"}, 404
                results = db.session.query(MdTodo, latest_todo_scheduling.c.latest_scheduled_date) \
                    .join(latest_todo_scheduling, MdTodo.todo_pk == latest_todo_scheduling.c.todo_fk) \
                    .join(MdUserTaskExecution, MdTodo.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk) \
                    .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                    .join(MdUser, MdUserTask.user_id == MdUser.user_id) \
                    .filter(MdTodo.user_task_execution_fk == user_task_execution_pk) \
                    .filter(MdTodo.deleted_by_user.is_(None)) \
                    .order_by(latest_todo_scheduling.c.latest_scheduled_date.asc()) \
                    .offset(offset) \
                    .limit(n_todos) \
                    .all()
            else:
                # get not completed todos and scheduled_date >= today in user timezone

                results = db.session.query(MdTodo, latest_todo_scheduling.c.latest_scheduled_date) \
                    .join(MdUserTaskExecution, MdTodo.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk) \
                    .join(latest_todo_scheduling, MdTodo.todo_pk == latest_todo_scheduling.c.todo_fk) \
                    .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                    .join(MdUser, MdUserTask.user_id == MdUser.user_id) \
                    .filter(MdUser.user_id == user_id) \
                    .filter(MdTodo.deleted_by_user.is_(None)) \
                    .filter(MdTodo.completed.is_(None)) \
                    .filter((latest_todo_scheduling.c.latest_scheduled_date - text('md_user.timezone_offset * interval \'1 minute\'')) >= now_utc) \
                    .order_by(latest_todo_scheduling.c.latest_scheduled_date.asc()) \
                    .offset(offset) \
                    .limit(n_todos) \
                    .all()

            all_user_todos = db.session.query(MdTodo) \
                .join(MdUserTaskExecution,
                      MdTodo.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk) \
                .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                .join(MdUser, MdUserTask.user_id == MdUser.user_id) \
                .filter(MdUser.user_id == user_id)

            # Has user done todos before? This is to change display message on front if todo-list is empty
            user_has_never_done_todo = all_user_todos.count() == 0

            # Check for the number of todos not read
            n_todos_not_read = all_user_todos \
                .join(latest_todo_scheduling, MdTodo.todo_pk == latest_todo_scheduling.c.todo_fk) \
                .filter((latest_todo_scheduling.c.latest_scheduled_date - text(
                'md_user.timezone_offset * interval \'1 minute\'')) >= now_utc) \
                .filter(MdTodo.read_by_user.is_(None))\
                .filter(MdTodo.completed.is_(None)) \
                .filter(MdTodo.deleted_by_user.is_(None)) \
                .count()

            # Check if the user has had a todo before
            if not results:
                return {
                    "todos": [], 
                    "user_has_never_done_todo": user_has_never_done_todo,
                    "n_todos_not_read": n_todos_not_read
                    }, 200

            return {"todos": [{
                "todo_pk": todo.todo_pk,
                "user_task_execution_fk": todo.user_task_execution_fk,
                "description": todo.description,
                "scheduled_date": scheduled_date.isoformat(),
                "completed": todo.completed.isoformat() if todo.completed else None,
                "creation_date": todo.creation_date.isoformat(),
                "read_by_user": todo.read_by_user.isoformat() if todo.read_by_user else None
            } for todo, scheduled_date in results
            ],
                "user_has_never_done_todo": user_has_never_done_todo,
                "n_todos_not_read": n_todos_not_read
            }, 200

        except Exception as e:
            db.session.rollback()
            log_error(f"Error getting todos : {e}")
            return {"error": f"Error getting todos : {e}"}, 400

