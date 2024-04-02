
import os
from datetime import datetime

import requests
from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import *
from sqlalchemy import func, text, extract, and_

from mojodex_backend_logger import MojodexBackendLogger



class TodoDailyEmails(Resource):
    logger_prefix = "TodoDailyEmails::"
    todo_daily_email_type="todo_daily_email"


    def __init__(self):
        self.logger = MojodexBackendLogger(TodoDailyEmails.logger_prefix)

    def post(self):
        if not request.is_json:
            log_error(f"Error sending todo daily emails : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        try:
           secret = request.headers['Authorization']
           if secret != os.environ["MOJODEX_SCHEDULER_SECRET"]:
               log_error(f"Error sending todo daily emails : Authentication error : Wrong secret", notify_admin=True)
               return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
           log_error(f"Error sending todo daily emails : Missing Authorization secret in headers", notify_admin=True)
           return {"error": f"Missing Authorization secret in headers"}, 403

        try:
            timestamp = request.json['datetime']
            n_emails = min(50, int(request.json["n_emails"])) if "n_emails" in request.json else 50
            offset = int(request.json["offset"]) if "offset" in request.json else 0

        except KeyError:
            log_error(f"Error sending todo daily emails : Missing datetime in body", notify_admin=True)
            return {"error": f"Missing datetime in body"}, 400

        try:

            today = func.date_trunc('day', func.now())

            # Subquery to check if the last scheduled date is today
            last_scheduled_today = db.session.query(
                MdTodoScheduling.todo_fk,
                func.max(MdTodoScheduling.scheduled_date).label('latest_scheduled_date')) \
                .filter(MdTodoScheduling.scheduled_date == today) \
                .group_by(MdTodoScheduling.todo_fk) \
                .subquery()

            # Subquery to get last produced_text_version
            produced_text_subquery = db.session.query(MdProducedText.produced_text_pk,
                                              MdProducedText.user_task_execution_fk.label('user_task_execution_fk'),
                                              MdProducedTextVersion.title.label('produced_text_title'),
                                              MdProducedTextVersion.production.label('produced_text_production'),
                                              MdProducedTextVersion.produced_text_version_pk.label(
                                                  'produced_text_version_pk'),
                                              func.row_number().over(
                                                  partition_by=MdProducedText.user_task_execution_fk,
                                                  order_by=MdProducedTextVersion.creation_date.desc()).label(
                                                  'row_number')) \
                .join(MdProducedTextVersion,
                      MdProducedTextVersion.produced_text_fk == MdProducedText.produced_text_pk) \
                .subquery()

            todos_today = db.session.query(
                MdTodo.todo_pk, 
                MdTodo.description, 
                MdUser.user_id, 
                produced_text_subquery.c.produced_text_title.label("latest_produced_text_version_title")
                ) \
                .join(last_scheduled_today, last_scheduled_today.c.todo_fk == MdTodo.todo_pk) \
                .join(MdUserTaskExecution, MdUserTaskExecution.user_task_execution_pk == MdTodo.user_task_execution_fk) \
                .join(MdUserTask, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk) \
                .join(MdUser, MdUser.user_id == MdUserTask.user_id) \
                .outerjoin(produced_text_subquery,
                           and_(
                               produced_text_subquery.c.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk,
                               produced_text_subquery.c.row_number == 1)) \
                .filter(MdUser.todo_email_reception == True) \
                .filter(MdTodo.deleted_by_mojo.is_(None)) \
                .filter(MdTodo.deleted_by_user.is_(None)) \
                .filter(MdTodo.completed.is_(None)) \
                .all()

            todos_today = [todo_today._asdict() for todo_today in todos_today]

            # filter on MdTodoScheduling.creation_date's day is today's day
            rescheduled_todos_today = db.session.query(
                MdTodo.todo_pk,
                MdTodo.description,
                MdTodoScheduling.reschedule_justification,
                MdTodoScheduling.scheduled_date,
                MdUser.user_id,
                produced_text_subquery.c.produced_text_title.label("latest_produced_text_version_title")
                ) \
                .join(MdTodoScheduling, MdTodoScheduling.todo_fk == MdTodo.todo_pk) \
                .join(MdUserTaskExecution, MdUserTaskExecution.user_task_execution_pk == MdTodo.user_task_execution_fk) \
                .join(MdUserTask, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk) \
                .join(MdUser, MdUser.user_id == MdUserTask.user_id) \
                .outerjoin(produced_text_subquery,
                           and_(
                               produced_text_subquery.c.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk,
                               produced_text_subquery.c.row_number == 1)) \
                .filter(
                and_(
                    extract("day", MdTodoScheduling.creation_date) == extract("day", today),
                    extract("month", MdTodoScheduling.creation_date) == extract("month", today),
                    extract("year", MdTodoScheduling.creation_date) == extract("year", today),
                )
            ) \
                .filter(MdUser.todo_email_reception == True) \
                .filter(MdTodoScheduling.reschedule_justification.isnot(None)) \
                .all()

            rescheduled_todos_today = [{
                "todo_pk" : rescheduled_todo_today.todo_pk,
                "description" : rescheduled_todo_today.description,
                "reschedule_justification" : rescheduled_todo_today.reschedule_justification,
                "scheduled_date" : rescheduled_todo_today.scheduled_date.isoformat(),
                "user_id" : rescheduled_todo_today.user_id,
                "latest_produced_text_version_title" : rescheduled_todo_today.latest_produced_text_version_title
                } for rescheduled_todo_today in rescheduled_todos_today]

            # Subquery for todos deleted by mojo today
            deleted_todos_today = db.session.query(
                MdTodo.todo_pk, 
                MdTodo.description, 
                MdTodo.deletion_justification,
                MdUser.user_id, 
                produced_text_subquery.c.produced_text_title.label("latest_produced_text_version_title")
                ) \
                .filter(
                and_(
                    extract("day", MdTodo.deleted_by_mojo) == extract("day", today),
                    extract("month", MdTodo.deleted_by_mojo) == extract("month", today),
                    extract("year", MdTodo.deleted_by_mojo) == extract("year", today),
                )
            ) \
                .join(MdUserTaskExecution, MdUserTaskExecution.user_task_execution_pk == MdTodo.user_task_execution_fk) \
                .join(MdUserTask, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk) \
                .join(MdUser, MdUser.user_id == MdUserTask.user_id) \
                .outerjoin(produced_text_subquery,
                           and_(
                               produced_text_subquery.c.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk,
                               produced_text_subquery.c.row_number == 1)) \
                .filter(MdUser.todo_email_reception == True) \
                .all()

            deleted_todos_today = [deleted_todo_today._asdict() for deleted_todo_today in deleted_todos_today]

            # Users whose timezone is not null and whose hour is between 8 and 9 am and who are not on weekends
            base_user_query = db.session.query(MdUser) \
                .filter(MdUser.timezone_offset != None) \
                .filter(extract("hour", text('NOW() - md_user.timezone_offset * interval \'1 minute\'')) >= int(os.environ.get('DAILY_TODO_EMAIL_TIME', 8))) \
                .filter(extract("hour", text('NOW() - md_user.timezone_offset * interval \'1 minute\'')) < int(os.environ.get('DAILY_TODO_EMAIL_TIME', 8))+1) \
                .filter(extract("dow", text('NOW() - md_user.timezone_offset * interval \'1 minute\'')) != int(0)) \
                .filter(extract("dow", text('NOW() - md_user.timezone_offset * interval \'1 minute\'')) != int(6)) \
                .filter(MdUser.todo_email_reception == True) \
                .order_by(MdUser.user_id) \
                .offset(offset).limit(n_emails) \
                .all()

            users = []
            for user in base_user_query:
                users_todos_today = [
                    todo_today for todo_today in todos_today 
                    if todo_today["user_id"] == user.user_id and todo_today["todo_pk"] is not None
                ]
                users_rescheduled_todos = [
                    rescheduled_todo_today for rescheduled_todo_today in rescheduled_todos_today 
                    if rescheduled_todo_today["user_id"] == user.user_id and rescheduled_todo_today["todo_pk"] is not None
                ]
                users_deleted_todos = [
                    deleted_todo_today for deleted_todo_today in deleted_todos_today 
                    if deleted_todo_today["user_id"] == user.user_id and deleted_todo_today["todo_pk"] is not None
                ]
                if users_todos_today or users_rescheduled_todos or users_deleted_todos:
                    users.append({
                        "user_id": user.user_id,
                        "email": user.email,
                        "username": user.name,
                        "user_timezone_offset": user.timezone_offset,
                        "company_description": user.company_description,
                        "goal": user.goal,
                        "language": user.language_code,
                        "today_todo_list": users_todos_today,
                        "rescheduled_todos": users_rescheduled_todos,
                        "deleted_todos": users_deleted_todos
                    })

            # send backend for preparing email text
            uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/events_generation"
            pload = {'datetime': datetime.now().isoformat(), 'event_type': 'todo_daily_emails', 'data': users}
            internal_request = requests.post(uri, json=pload)
            if internal_request.status_code != 200:
                log_error(f"Error while calling background events_generation : {internal_request.json()}")

            # return list of user_ids
            return {"user_ids": [user.user_id for user in base_user_query]}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error sending daily emails : {e}", notify_admin=True)
            return {"error": f"Error sending daily emails : {e}"}, 500
