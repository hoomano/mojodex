import os
from datetime import datetime
import requests
from flask import request
from flask_restful import Resource
from app import db, log_error
from mojodex_core.entities import *
from sqlalchemy import func, text, extract


class DailyNotifications(Resource):

    def post(self):
        if not request.is_json:
            log_error(f"Error sending daily notifications : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_SCHEDULER_SECRET"]:
                log_error(f"Error sending daily notifications : Authentication error : Wrong secret", notify_admin=True)
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"Error sending daily notifications : Missing Authorization secret in headers", notify_admin=True)
            return {"error": f"Missing Authorization secret in headers"}, 403

        try:
            timestamp = request.json['datetime']
            n_notifications = min(50, int(request.json["n_notifications"])) if "n_notifications" in request.json else 50
            offset = int(request.json["offset"]) if "offset" in request.json else 0
        except Exception as e:
            log_error(f"Error sending daily notifications : {e}", notify_admin=True)
            return {"error": f"Missing datetime in body"}, 400

        try:
            # today_morning = today at 00:00:00
            today_morning = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            todos_subquery = (db.session.query(
                MdUserTask.user_id.label('user_id'),
                MdUserTaskExecution.user_task_fk,
                func.array_agg(MdTodo.description).label('today_new_todos_desc'))
                              .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk)
                              .join(MdTodo, MdTodo.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk)
                              .join(MdUser, MdUser.user_id == MdUserTask.user_id)
                              .filter(func.timezone(
                text(f'md_user.timezone_offset * interval \'1 minute\''), MdTodo.creation_date) >= today_morning)
                              .group_by(MdUserTaskExecution.user_task_fk, MdUserTask.user_id)
                              ).subquery()

            results = db.session.query(MdUser.user_id, MdUser.name, MdUser.company_description, MdUser.timezone_offset,
                               MdUser.goal,
                               MdUser.language_code,
                               todos_subquery.c.today_new_todos_desc.label("today_new_todos_desc")
                               ).outerjoin(todos_subquery, MdUser.user_id == todos_subquery.c.user_id).filter(
                MdUser.timezone_offset != None) \
                .filter(extract("hour", text('NOW() - md_user.timezone_offset * interval \'1 minute\'')) >= int(
                os.environ.get('DAILY_NOTIF_TIME', 14))) \
                .filter(extract("hour", text('NOW() - md_user.timezone_offset * interval \'1 minute\'')) < int(
                os.environ.get('DAILY_NOTIF_TIME', 14)) + 1) \
                .filter(todos_subquery.c.today_new_todos_desc.isnot(None)) \
                .order_by(
                MdUser.user_id).offset(offset).limit(n_notifications).all()

            results = [result._asdict() for result in results]

            users = [{'user_id': row["user_id"],
                      'user_name': row["name"],
                      'user_company_description': row["company_description"],
                      'user_timezone_offset': row["timezone_offset"],
                      'user_goal': row["goal"],
                      'language': row["language_code"] if row["language_code"] else "en",
                      'new_todos_today': row["today_new_todos_desc"]
                      } for row in results]


            # send backend for preparing email text
            uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/events_generation"
            pload = {'datetime': datetime.now().isoformat(), 'event_type': 'daily_notifications', 'data': users}
            internal_request = requests.post(uri, json=pload)
            if internal_request.status_code != 200:
                log_error(f"Error while calling background events_generation : {internal_request.json()}")

            # return list of user_ids
            return {"user_ids": [user["user_id"] for user in users]}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error sending daily notifications : {e}", notify_admin=True)
            return {"error": f"Error sending daily notifications : {e}"}, 500
