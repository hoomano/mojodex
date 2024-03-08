from flask import request
from flask_restful import Resource
from app import db, executor
from mojodex_core.entities import *

from models.events.daily_notifications_generator import DailyNotificationsGenerator
from models.events.daily_emails_generator import DailyEmailsGenerator

from models.knowledge.knowledge_collector import KnowledgeCollector

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
            if event_type == 'daily_notifications':
                events_generator = DailyNotificationsGenerator()
            elif event_type == 'daily_emails':
                events_generator = DailyEmailsGenerator()
            elif event_type == 'todo_daily_emails':
                events_generator = TodoDailyEmailsGenerator()
            elif event_type == 'calendar_suggestion_notifications':
                events_generator = CalendarSuggestionNotificationsGenerator()
            else:
                raise Exception(f"Unknown event type {event_type}")

            mojo_knowledge = KnowledgeCollector.get_mojo_knowledge()

            def run_generate_events(events_generator, mojo_knowledge, data):
                try:
                    events_generator.generate_events(mojo_knowledge, data)
                except Exception as err:
                    print("🔴" + str(err))

            executor.submit(run_generate_events, events_generator, mojo_knowledge, data)
            return {"success": "Process started"}, 200
        except Exception as e:
            return {"error": f"Error generating events : {e}"}, 404
