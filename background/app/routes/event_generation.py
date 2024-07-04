from flask import request
from flask_restful import Resource
from app import executor
from models.events.todo_daily_emails_generator import TodoDailyEmailsGenerator
from models.events.calendar_suggestion_notifications_generator import CalendarSuggestionNotificationsGenerator


class EventsGeneration(Resource):
    def post(self):
        try:
            timestamp = request.json['datetime']
            event_type = request.json['event_type']
            data = request.json['data']
        except Exception:
            return {"error": "invalid inputs"}, 400

        try:
            if event_type == 'todo_daily_emails':
                events_generator = TodoDailyEmailsGenerator()
            elif event_type == 'calendar_suggestion_notifications':
                events_generator = CalendarSuggestionNotificationsGenerator()
            else:
                raise Exception(f"Unknown event type {event_type}")

            executor.submit(events_generator.generate_events, data)
            return {"success": "Process started"}, 200
        except Exception as e:
            return {"error": f"Error generating events : {e}"}, 404
