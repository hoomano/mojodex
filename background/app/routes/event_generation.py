import os
from sqlalchemy import extract, text
from models.events.events_generator import EventsGenerator
from flask import request
from flask_restful import Resource
from app import executor, db
from models.events.todo_daily_emails_generator import TodoDailyEmailsGenerator
from models.events.calendar_suggestion_notifications_generator import CalendarSuggestionNotificationsGenerator
from mojodex_core.entities.db_base_entities import MdCalendarSuggestion, MdUser
from datetime import datetime

class EventsGeneration(Resource):
    def post(self):
        try:
            timestamp = request.json['datetime']
            event_type = request.json['event_type']
            n_events = min(50, int(request.json["n_events"])) if "n_events" in request.json else 50
            offset = int(request.json["offset"]) if "offset" in request.json else 0
        except Exception:
            return {"error": "invalid inputs"}, 400

        try:
            kwargs = {}
            if event_type == 'todo_daily_emails':
                user_ids_query_result = db.session.query(MdUser.user_id) \
                    .filter(MdUser.timezone_offset != None) \
                    .filter(extract("hour", text('NOW() - md_user.timezone_offset * interval \'1 minute\'')) >= int(os.environ.get('DAILY_TODO_EMAIL_TIME', 8))) \
                    .filter(extract("hour", text('NOW() - md_user.timezone_offset * interval \'1 minute\'')) < int(os.environ.get('DAILY_TODO_EMAIL_TIME', 8))+1) \
                    .filter(extract("dow", text('NOW() - md_user.timezone_offset * interval \'1 minute\'')) != int(0)) \
                    .filter(extract("dow", text('NOW() - md_user.timezone_offset * interval \'1 minute\'')) != int(6)) \
                    .filter(MdUser.todo_email_reception == True) \
                    .order_by(MdUser.user_id) \
                    .offset(offset) \
                    .limit(n_events) \
                    .all()
                user_ids = [result[0] for result in user_ids_query_result]
                events_generator_class = TodoDailyEmailsGenerator

            elif event_type == 'calendar_suggestion_notifications':
                since_date = request.json['since_date']
                since_date = datetime.fromisoformat(since_date)
                until_date = request.json['until_date']
                until_date = datetime.fromisoformat(until_date)
                results = db.session.query(MdCalendarSuggestion.user_id) \
                    .filter(MdCalendarSuggestion.reminder_date.isnot(None)) \
                    .filter(MdCalendarSuggestion.reminder == True) \
                    .filter(MdCalendarSuggestion.reminder_date.between(since_date, until_date)) \
                    .order_by(MdCalendarSuggestion.calendar_suggestion_pk) \
                    .offset(offset) \
                    .limit(n_events) \
                    .all()
                user_ids = [result[0] for result in results]
                events_generator_class = CalendarSuggestionNotificationsGenerator
                kwargs = {"since_date": since_date, "until_date": until_date}
            else:
                raise Exception(f"Unknown event type {event_type}")
            
            def generate_events(user_ids, events_generator_class, **kwargs):
                for user_id in user_ids:
                    events_generator: EventsGenerator = events_generator_class(user_id, **kwargs)
                    events_generator.generate_events()

            executor.submit(generate_events, user_ids, events_generator_class, **kwargs)
        
            return {"user_ids": user_ids}, 200
            
        except Exception as e:
            return {"error": f"Error generating events : {e}"}, 404
