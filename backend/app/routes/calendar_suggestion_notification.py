import os


import requests
from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.entities.user import User
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *
from datetime import datetime

class CalendarSuggestionNotifications(Resource):

    def post(self):
        error_message = "Error sending calendar_suggestion notifications"
        if not request.is_json:
            log_error(f"{error_message} : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_SCHEDULER_SECRET"]:
                log_error(f"{error_message} : Authentication error : Wrong secret", notify_admin=True)
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"{error_message} : Missing Authorization secret in headers", notify_admin=True)
            return {"error": f"Missing Authorization secret in headers"}, 403

        try:
            timestamp = request.json['datetime']
            since_date = request.json['since_date']
            since_date = datetime.fromisoformat(since_date)
            until_date = request.json['until_date']
            until_date = datetime.fromisoformat(until_date)
            n_notifications = min(50, int(request.json["n_notifications"])) if "n_notifications" in request.json else 50
            offset = int(request.json["offset"]) if "offset" in request.json else 0

        except Exception as e:
            log_error(f"{error_message} : {e}", notify_admin=True)
            return {"error": f"Missing datetime in body"}, 400

        try:

            # Get all calendar_suggestion_pks with notification_time_utc is not none and between since_date and until_date
            results = db.session.query(MdCalendarSuggestion, User, MdTask) \
                .join(User, User.user_id == MdCalendarSuggestion.user_id) \
                .join(MdTask, MdTask.task_pk == MdCalendarSuggestion.proposed_task_fk) \
                .filter(MdCalendarSuggestion.reminder_date.isnot(None)) \
                .filter(MdCalendarSuggestion.reminder == True) \
                .filter(MdCalendarSuggestion.reminder_date.between(since_date, until_date)) \
                .order_by(MdCalendarSuggestion.calendar_suggestion_pk) \
                .offset(offset) \
                .limit(n_notifications) \
                .all()

            notification_data = [{"user_id": calendar_suggestion.user_id,
                                  "suggestion_text": calendar_suggestion.suggestion_text,
                                  "task_pk": calendar_suggestion.proposed_task_fk,
                                  "task_name": task.name_for_system,
                                  "datetime_context": user.datetime_context,
                                  "user_name": user.name,
                                  "user_company_description": user.company_description,
                                  "user_goal": user.goal
                                  } for calendar_suggestion, user, task in results]


            # send backend for preparing email text
            uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/events_generation"
            pload = {'datetime': datetime.now().isoformat(), 'event_type': 'calendar_suggestion_notifications',
                     'data': notification_data}
            internal_request = requests.post(uri, json=pload)
            if internal_request.status_code != 200:
                log_error(f"Error while calling background events_generation : {internal_request.json()}")

            return {"calendar_suggestion_pks": [calendar_suggestion.calendar_suggestion_pk for calendar_suggestion, user, task in results]}, 200

        except Exception as e:
            log_error(f"{error_message} : {e}", notify_admin=True)
            return {"error": f"{error_message} : {e}"}, 409
