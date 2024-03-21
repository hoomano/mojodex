import os
from datetime import datetime, timedelta
import requests
from flask import request
from flask_restful import Resource
from app import db, authenticate
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import *
from sqlalchemy import func, text, extract


class TodosScheduling(Resource):


    # adding new todo scheduling
    def put(self):
        if not request.is_json:
            return {"error": "Invalid request"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                log_error(f"Error creating new todo scheduling: Authentication error : Wrong secret")
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"Error creating new todo scheduling: Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        # data
        try:
            timestamp = request.json["datetime"]
            todo_fk = request.json["todo_fk"]
            argument = request.json["argument"]
            reschedule_date = request.json["reschedule_date"] if "reschedule_date" in request.json else None
            if reschedule_date:
                try:
                    reschedule_date = datetime.strptime(reschedule_date, "%Y-%m-%d")
                except ValueError:
                    return {"error": f"Invalid due_date {reschedule_date}"}, 400

        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            if reschedule_date:
                # create todo_scheduling
                new_todo_scheduling = MdTodoScheduling(
                    todo_fk=todo_fk,
                    scheduled_date=reschedule_date,
                    reschedule_justification=argument
                )

                db.session.add(new_todo_scheduling)
                db.session.commit()
                return {"todo_pk": todo_fk, "todo_scheduling_pk": new_todo_scheduling.todo_scheduling_pk}, 200

            # get md_todo
            todo = db.session.query(MdTodo).filter(MdTodo.todo_pk == todo_fk).first()
            if not todo:
                return {"error": f"Todo {todo_fk} not found"}, 404
            todo.deleted_by_mojo = datetime.now()
            todo.deletion_justification = argument
            db.session.commit()

            return {"todo_pk": todo_fk}, 200

        except Exception as e:
            db.session.rollback()
            log_error(f"Error creating new todo scheduling: {e}")
            return {"error": f"Error creating new todo scheduling: {e}"}, 400


    # reschedule todo route for scheduler
    def post(self):
        if not request.is_json:
            log_error(f"Error running reschedule todos : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_SCHEDULER_SECRET"]:
                log_error(f"Error running reschedule todos : Authentication error : Wrong secret", notify_admin=True)
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"Error running reschedule todos : Missing Authorization secret in headers", notify_admin=True)
            return {"error": f"Missing Authorization secret in headers"}, 403

        try:
            timestamp = request.json['datetime']
        except KeyError:
            log_error(f"Error running reschedule todos : Missing datetime in body", notify_admin=True)
            return {"error": f"Missing datetime in body"}, 400

        try:

            # find all users for which it is 1am in their timezone
            # find all of those users todo that last scheduled date is yesterday and completed is null and deleted_by_user is null
            offset = 0
            n_todos = 50
            todo_pks = []
            results = []

            while len(results) == 50 or offset == 0:
                yesterday = datetime.utcnow() - timedelta(days=1)

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
                    .filter(extract("hour", text('NOW() - md_user.timezone_offset * interval \'1 minute\'')) >= int(
                    1)) \
                    .filter(extract("hour", text('NOW() - md_user.timezone_offset * interval \'1 minute\'')) < int(
                    1) + 1) \
                    .filter(extract("dow", text('NOW() - md_user.timezone_offset * interval \'1 minute\'')) != int(0)) \
                    .filter(extract("dow", text('NOW() - md_user.timezone_offset * interval \'1 minute\'')) != int(6)) \
                    .all()

                todo_pks += [todo.todo_pk for todo in results]
                offset += n_todos

            def reschedule_todo(todo_pk):
                # call background backend /reschedule_todo
                uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/reschedule_todo"
                pload = {"datetime": datetime.now().isoformat(), "todo_pk": todo_pk}
                internal_request = requests.post(uri, json=pload)
                if internal_request.status_code != 200:
                    log_error(f"Error while calling background extract_todos : {internal_request.text}")
                    # We won't return an error to the user, because the task has been ended but the background process failed

            for todo_pk in todo_pks:
                reschedule_todo(todo_pk)

            return {"todo_pks": todo_pks}, 200

        except Exception as e:
            log_error(f"Error running extract todos : {e}", notify_admin=True)
            return {"error": f"Error running extract todos : {e}"}, 500
