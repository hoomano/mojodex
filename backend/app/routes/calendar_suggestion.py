import os
import time
from flask import request
from flask_restful import Resource
from app import authenticate, db, log_error, server_socket

from datetime import datetime, timedelta
from jinja2 import Template
from mojodex_core.entities import *

from mojodex_core.llm_engine.mpt import MPT

from placeholder_generator import PlaceholderGenerator
from mojodex_core.json_loader import json_decode_retry
from app import on_json_error
from packaging import version


class CalendarSuggestion(Resource):

    calendar_suggestion_generator_from_calendar_mpt_filename = "instructions/generate_suggestion_from_calendar.mpt"

    calendar_suggestion_waiting_mpt_filename = "instructions/calendar_waiting_message.mpt"

    def __init__(self):
        CalendarSuggestion.method_decorators = [authenticate()]

    def __get_mojo_knwoledge(self):
        with open("/data/knowledge/mojo_knowledge.txt", 'r') as f:
            return f.read()

    def __get_global_context(self, timezoneOffsetMinutes):
        with open("/data/knowledge/global_context.txt", 'r') as f:
            template = Template(f.read())
            timestamp = datetime.utcnow(
            ) - timedelta(minutes=timezoneOffsetMinutes if timezoneOffsetMinutes else 0)
            return template.render(weekday=timestamp.strftime("%A"),
                                   datetime=timestamp.strftime("%d %B %Y"),
                                   time=timestamp.strftime("%H:%M"))

    def __get_calendar_suggestion(self, user_id, use_placeholders=False):
        try:
            if not use_placeholders:  # if placeholder, create one
                # try to find a calendar suggestion pre-set and not used
                calendar_suggestion = db.session.query(MdCalendarSuggestion) \
                    .filter(MdCalendarSuggestion.user_id == user_id) \
                    .filter(MdCalendarSuggestion.waiting_message_sent.is_(None)) \
                    .filter(MdCalendarSuggestion.waiting_message.isnot(None)) \
                    .first()
                if calendar_suggestion:
                    return calendar_suggestion

            calendar_suggestion = MdCalendarSuggestion(
                user_id=user_id
            )
            db.session.add(calendar_suggestion)
            db.session.flush()
            return calendar_suggestion
        except Exception as e:
            raise Exception(f"get_calendar_suggestion: {e}")

    def __generate_calendar_suggestion(self, user_id, calendar_suggestion_pk, use_placeholder, planning, app_version):
        try:
            user = db.session.query(MdUser).filter(
                MdUser.user_id == user_id).first()

            def get_user_tasks(user_id):
                user_tasks = db.session.query(MdTask) \
                    .join(MdUserTask, MdUserTask.task_fk == MdTask.task_pk) \
                    .filter(MdUserTask.user_id == user_id).all()
                return [{
                    "icon": task.icon,
                    "name_for_system": task.name_for_system,
                    "definition": task.definition_for_system,
                    "task_pk": task.task_pk
                } for task in user_tasks]

            def get_user_tasks_done_today(user_id):
                start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                user_tasks_done_today = db.session.query(MdTask.name_for_system, MdUserTaskExecution.title,
                                                         MdUserTaskExecution.start_date) \
                    .join(MdUserTask, MdUserTask.task_fk == MdTask.task_pk) \
                    .join(MdUserTaskExecution, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                    .filter(MdUserTask.user_id == user_id) \
                    .filter(MdUserTaskExecution.start_date >= start_date) \
                    .all()
                return [{
                    "task": task,
                    "title": title,
                    "date": start_date.strftime("%Y-%m-%d-%Hh:%Mm"),
                } for task, title, start_date in user_tasks_done_today]

            if use_placeholder:
                # await 10 seconds to simulate openai
                time.sleep(10)
                data = {"message_for_user": PlaceholderGenerator.calendar_suggestion_placeholder,
                        "message_title": PlaceholderGenerator.calendar_suggestion_title_placeholder,
                        "message_emoji": PlaceholderGenerator.calendar_suggestion_emoji_placeholder}
            else:
                @json_decode_retry(retries=3, required_keys=[], on_json_error=on_json_error)
                def generate(planning):
                    # Answer using openai
                    generate_suggestion_mpt = MPT(CalendarSuggestion.calendar_suggestion_generator_from_calendar_mpt_filename, mojo_knowledge=self.__get_mojo_knwoledge(),
                                                  global_context=self.__get_global_context(
                        user.timezone_offset),
                        username=user.name,
                        user_company_knowledge=user.company_description,
                        user_business_goal=user.goal,
                        language=user.language_code,
                        user_tasks=get_user_tasks(user_id),
                        user_planning=planning,
                        user_tasks_done_today=get_user_tasks_done_today(
                        user_id)
                    )

                    responses = generate_suggestion_mpt.run(user_id,
                                                            temperature=1,
                                                            max_tokens=1000,
                                                            json_format=True)
                    return responses[0]

                data = generate(planning)

            calendar_suggestion = db.session.query(MdCalendarSuggestion) \
                .filter(MdCalendarSuggestion.calendar_suggestion_pk == calendar_suggestion_pk) \
                .filter(MdCalendarSuggestion.user_id == user_id) \
                .first()

            calendar_suggestion.text_generated_date = datetime.now()
            task_pk_to_display = None
            if data and not ("in_user_today_tasks" in data and data["in_user_today_tasks"]):
                calendar_suggestion.event_id = data["event_id"] if "event_id" in data else None
                calendar_suggestion.suggestion_text = data["message_for_user"].strip(
                ) if "message_for_user" in data else None
                calendar_suggestion.calendar_suggestion_title = data["message_title"].strip(
                ) if "message_title" in data else None
                calendar_suggestion.calendar_suggestion_emoji = data["message_emoji"].strip(
                ) if "message_emoji" in data else None
                calendar_suggestion.proposed_task_fk = data["task_pk"] if "task_pk" in data else None
                if "event_id" in data:
                    # find the end date of the event
                    event = next(
                        filter(lambda x: x["eventId"] == data["event_id"], planning))
                    calendar_suggestion.reminder_date = datetime.strptime(event["eventEndDate"],
                                                                          "%Y-%m-%dT%H:%M:%S.%f%z") if "eventEndDate" in event else None
                    db.session.flush()

                    # if there is an event and event is not started yet, do not propose any task
                    event_start_date = datetime.strptime(
                        event["eventStartDate"], "%Y-%m-%dT%H:%M:%S.%f%z") if "eventStartDate" in event else None
                    if event_start_date and event_start_date > datetime.now(event_start_date.tzinfo):
                        task_pk_to_display = None  # Do not display any task if event is not started yet
                    else:
                        task_pk_to_display = calendar_suggestion.proposed_task_fk

            message = {
                "calendar_suggestion_pk": calendar_suggestion.calendar_suggestion_pk,
                "message_text": calendar_suggestion.suggestion_text,
                "message_title": calendar_suggestion.calendar_suggestion_title,
                "message_emoji": calendar_suggestion.calendar_suggestion_emoji,
                "task_pk": task_pk_to_display
            }
            server_socket.emit('calendar_suggestion', message,
                               to=f"mojo_events_{user_id}")

            db.session.commit()
            db.session.close()
        except Exception as e:
            server_socket.emit('calendar_suggestion', {
                               "error": "error"}, to=f"mojo_events_{user_id}")

            db.session.rollback()
            db.session.close()
            log_error(f"generate_calendar_suggestion: {e}", notify_admin=True)

    def __get_waiting_message(self, user_id, use_placeholders=False):
        try:
            # generate waiting message
            if use_placeholders:
                return {"waiting_message": PlaceholderGenerator.waiting_message_placeholder,
                        "done_message": PlaceholderGenerator.done_message_placeholder}
            else:
                return self.__generate_waiting_message(user_id)
        except Exception as e:
            raise Exception(f"__get_waiting_message: {e}")

    @json_decode_retry(retries=3, required_keys=["waiting_message", "done_message"],
                       on_json_error=on_json_error)
    def __generate_waiting_message(self, user_id):
        try:

            user = db.session.query(MdUser).filter(
                MdUser.user_id == user_id).first()
            
            waiting_message_mpt = MPT(CalendarSuggestion.calendar_suggestion_waiting_mpt_filename,
                                      mojo_knowledge=self.__get_mojo_knwoledge(),
                                      # no global context so that it can be used any day / time
                                      username=user.name,
                                      language=user.language_code
                                      )

            responses = waiting_message_mpt.run(user_id, temperature=1,
                                                max_tokens=1000)
            return responses[0]
        except Exception as e:
            raise Exception(f"get_waiting_message: {e}")

    def __prepare_next_calendar_suggestion(self, user_id):
        try:
            calendar_suggestion = MdCalendarSuggestion(
                user_id=user_id
            )
            db.session.add(calendar_suggestion)
            db.session.flush()
            waiting_json = self.__get_waiting_message(
                user_id, use_placeholders=False)
            calendar_suggestion.waiting_message = waiting_json["waiting_message"].strip(
            ) if "waiting_message" in waiting_json else None
            calendar_suggestion.ready_message = waiting_json["done_message"].strip(
            ) if "done_message" in waiting_json else None
            db.session.commit()
            db.session.close()
            return calendar_suggestion
        except Exception as e:
            db.session.rollback()
            db.session.close()
            log_error(
                f"prepare_next_calendar_suggestion: {e}", notify_admin=True)

    def __has_next_calendar_suggestion(self, user_id):
        try:
            calendar_suggestion = db.session.query(MdCalendarSuggestion) \
                .filter(MdCalendarSuggestion.user_id == user_id) \
                .filter(MdCalendarSuggestion.waiting_message_sent.is_(None)) \
                .filter(MdCalendarSuggestion.waiting_message.isnot(None)) \
                .first()
            return calendar_suggestion is not None
        except Exception as e:
            log_error(f"has_next_calendar_suggestion: {e}", notify_admin=True)
            return False

    # route to put a new calendar suggestion in backend. Returns waiting message.

    def put(self, user_id):
        error_message = "Error getting calendar suggestion"

        try:
            timestamp = request.json["datetime"]
            user_planning = request.json["user_planning"]
            app_version = version.parse(
                request.json["version"]) if "version" in request.json else version.parse("0.0.0")
        except KeyError:
            return {"error": "Missing timezone in args"}, 400

        try:
            # ensure user_planning is a list of dict
            if not isinstance(user_planning, list):
                return {"error": "user_planning must be a list"}, 400
            for event in user_planning:
                if not isinstance(event, dict):
                    return {"error": "user_planning must be a list of dict"}, 400
            use_placeholders = 'use_placeholder' in request.json and request.json[
                'use_placeholder']

            # remove from user_planning events that have been managed in past calendar suggestions
            event_managed_today = db.session.query(MdCalendarSuggestion.event_id) \
                .filter(MdCalendarSuggestion.user_id == user_id) \
                .filter(MdCalendarSuggestion.creation_date >= datetime.now().replace(hour=0, minute=0,
                                                                                     second=0, microsecond=0)) \
                .all()
            event_managed_today = [
                event_id for event_id, in event_managed_today]
            planning = [
                event for event in user_planning if event["eventId"] not in event_managed_today]
            if len(planning) == 0:
                return {}, 200

            # find pre-set calendar suggestion for this user or create new one
            calendar_suggestion = self.__get_calendar_suggestion(
                user_id, use_placeholders=use_placeholders)

            server_socket.start_background_task(self.__generate_calendar_suggestion, user_id,
                                                calendar_suggestion.calendar_suggestion_pk, use_placeholders, planning, app_version)

            try:
                if not calendar_suggestion.waiting_message:
                    waiting_json = self.__get_waiting_message(
                        user_id, use_placeholders=use_placeholders)
                    calendar_suggestion.waiting_message = waiting_json[
                        "waiting_message"].strip() if "waiting_message" in waiting_json else None
                    calendar_suggestion.ready_message = waiting_json[
                        "done_message"].strip() if "done_message" in waiting_json else None

            except Exception as e:
                log_error(f"{error_message} : {e}", notify_admin=True)
                calendar_suggestion.waiting_message = "Searching how I can help you..."
                calendar_suggestion.ready_message = "Look what I've found!"

            calendar_suggestion.waiting_message_sent = datetime.now()
            db.session.flush()
            try:
                # if no preset calendar_suggestion
                if not self.__has_next_calendar_suggestion(user_id):
                    server_socket.start_background_task(
                        self.__prepare_next_calendar_suggestion, user_id)
            except Exception as e:
                log_error(f"{error_message} : {e}", notify_admin=True)

            db.session.commit()

            return {
                "calendar_suggestion_pk": calendar_suggestion.calendar_suggestion_pk,
                "waiting_message": calendar_suggestion.waiting_message,
                "ready_message": calendar_suggestion.ready_message,
            }, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"{error_message} : {e}")
            return {f"{error_message} : {e}"}, 400

    # route to get a calendar suggestion from backend. Returns calendar suggestion.
    def get(self, user_id):
        error_message = "Error getting calendar suggestion text"

        try:
            timestamp = request.args["datetime"]
            calendar_suggestion_pk = request.args["calendar_suggestion_pk"]
            app_version = version.parse(
                request.args["version"]) if "version" in request.args else version.parse("0.0.0")
        except KeyError as e:
            return {"error": f"Missing field: {e}"}, 400

        try:
            # Check calendar suggestion exists
            calendar_suggestion = db.session.query(MdCalendarSuggestion) \
                .filter(MdCalendarSuggestion.calendar_suggestion_pk == calendar_suggestion_pk) \
                .filter(MdCalendarSuggestion.user_id == user_id) \
                .first()
            if calendar_suggestion is None:
                return {"error": f"Calendar suggestion not found for this user"}, 404

            # has calendar suggestion been generated ? If yes, return it, else return "processing"
            if calendar_suggestion.text_generated_date is not None:
                if calendar_suggestion.suggestion_text is None:
                    return {}, 200

                return {
                    "calendar_suggestion_pk": calendar_suggestion.calendar_suggestion_pk,
                    "suggestion_text": calendar_suggestion.suggestion_text,
                    "message_title": calendar_suggestion.calendar_suggestion_title,
                    "message_emoji": calendar_suggestion.calendar_suggestion_emoji,
                    "task_pk": calendar_suggestion.proposed_task_fk
                }, 200

            else:
                return {"status": "processing"}, 200
        except Exception as e:
            log_error(f"{error_message} : {e}")
            return {f"{error_message} : {e}"}, 400

    # route to answer calendar suggestion
    def post(self, user_id):
        error_message = "Error treating answer to calendar suggestion"

        try:
            timestamp = request.json["datetime"]
            calendar_suggestion_pk = request.json["calendar_suggestion_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            # Check calendar suggestion exists
            calendar_suggestion = db.session.query(MdCalendarSuggestion) \
                .filter(MdCalendarSuggestion.calendar_suggestion_pk == calendar_suggestion_pk) \
                .filter(MdCalendarSuggestion.user_id == user_id) \
                .first()
            if calendar_suggestion is None:
                return {"error": f"Calendar suggestion not found for this user"}, 404

            if "user_reacted" in request.json and request.json["user_reacted"]:
                # update calendar_suggestion
                calendar_suggestion.reminder = True
            elif "user_task_execution_pk" in request.json:
                calendar_suggestion.triggered_user_task_execution_pk = request.json[
                    "user_task_execution_pk"]

            calendar_suggestion.user_reaction_date = datetime.now()
            db.session.commit()
            return {"success": "ok"}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"{error_message} : {e}")
            return {f"{error_message} : {e}"}, 500


# This class is to manage old app versions calling /welcome_message
class CalendarSuggestionOldWelcomeMessage(CalendarSuggestion):
    def __init__(self):
        super().__init__()
