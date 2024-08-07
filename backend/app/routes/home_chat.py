import os
from mojodex_core.db import with_db_session
from mojodex_core.tag_manager import TagManager
from flask import request
from flask_restful import Resource
from app import db, server_socket
from mojodex_core.authentication import authenticate, authenticate_with_scheduler_secret
from mojodex_core.knowledge_manager import KnowledgeManager

from mojodex_core.entities.message import Message
from mojodex_core.llm_engine.mpt import MPT
from mojodex_core.logging_handler import log_error

from mojodex_core.entities.db_base_entities import MdHomeChat, MdMessage, MdUserTaskExecution, MdUserTask, MdTask
from packaging import version

from models.session_creator import SessionCreator

from sqlalchemy import extract, text, func, and_

from mojodex_core.entities.session import Session
from mojodex_core.entities.user import User
from datetime import datetime, timedelta

class HomeChat(Resource):
    welcome_message_mpt_filename = "instructions/welcome_message.mpt"
    message_header_start_tag, message_header_end_tag = "<message_header>", "</message_header>"
    message_body_start_tag, message_body_end_tag = "<message_body>", "</message_body>"

    def __init__(self):
        HomeChat.method_decorators = [authenticate(methods=["GET", "POST"]), authenticate_with_scheduler_secret(methods=["PUT"])]
        self.session_creator = SessionCreator()

    @with_db_session
    def __get_this_week_home_conversations(self, user_id, db_session):
        try:
            # 1. get list of this week's home_chat sessions
            week_start_date = datetime.now().date() - timedelta(days=datetime.now().date().weekday())
            sessions: list[Session] = db_session.query(Session)\
            .join(MdHomeChat, Session.session_id == MdHomeChat.session_id)\
            .filter(and_(MdHomeChat.start_date.isnot(None), MdHomeChat.start_date >= week_start_date))\
            .filter(Session.user_id == user_id)\
                .all()
            if not sessions:
                return []

            return [{
                "date": session.creation_date,
                "conversation": session.get_conversation_as_string(agent_key="YOU", user_key="USER",
                                                                  with_tags=False)
            } for session in sessions]

        except Exception as e:
            raise Exception(f"__get_this_week_home_conversations :: {e}")

    @with_db_session
    def __get_this_week_task_executions(self, user_id, db_session):
        try:
            week_start_date = datetime.now().date() - timedelta(days=datetime.now().date().weekday())
            # last 20 tasks executions of the user this week order by start_date
            user_task_executions = db_session.query(MdUserTaskExecution.title, MdUserTaskExecution.summary, MdTask.name_for_system) \
                .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                .join(MdTask, MdUserTask.task_fk == MdTask.task_pk) \
                .filter(MdUserTask.user_id == user_id) \
                .filter(and_(MdUserTaskExecution.start_date.isnot(None), MdUserTaskExecution.start_date >= week_start_date)) \
                .order_by(MdUserTaskExecution.start_date.desc()) \
                .limit(20) \
                .all()
            return [{
                "title": execution.title,
                "summary": execution.summary,
                "task": execution.name_for_system
            } for execution in user_task_executions]
        except Exception as e:
            raise Exception(f"__get_this_week_task_executions :: {e}")


    def _generate_welcome_message(self, user_id, user_name, user_available_instruct_tasks, user_language_code, user_datetime_context):
        try:
            previous_conversations = self.__get_this_week_home_conversations(user_id)
            welcome_message_mpt = MPT(self.welcome_message_mpt_filename,
                                  mojo_knowledge=KnowledgeManager().mojodex_knowledge,
                                  user_datetime_context=user_datetime_context,
                                  username=user_name,
                                  tasks=user_available_instruct_tasks,
                                  first_time_this_week=len(previous_conversations) == 0,
                                  user_task_executions=self.__get_this_week_task_executions(user_id),
                                  previous_conversations=previous_conversations,
                                  language=user_language_code)

            response = welcome_message_mpt.run(user_id=user_id, temperature=0, max_tokens=1000,
                                                  user_task_execution_pk=None,
                                                  task_name_for_system=None)
            message = response.strip()
            header_tag_mananger = TagManager('message_header')
            body_tag_manager = TagManager('message_body')
            header = header_tag_mananger.extract_text(message)
            body = body_tag_manager.extract_text(message)
            return {"header": header,
                    "body": body,
                    "text": f"{header}\n{body}"}
        except Exception as e:
            raise Exception(f"_generate_welcome_message : {e}")

    @with_db_session
    def __create_home_chat(self, app_version, platform, user_id, week, db_session, use_message_placeholder=False):
        try:
            session_creation = self.session_creator.create_session(user_id, platform, "chat")
            if "error" in session_creation[0]:
                raise Exception(session_creation[0]["error"])
            session_id = session_creation[0]["session_id"]
            home_chat = MdHomeChat(session_id=session_id, user_id=user_id, week=week)
            db_session.add(home_chat)
            db_session.commit()
            user: User = db_session.query(User).filter(User.user_id == user_id).first()
            message = self._generate_welcome_message(user_id, user.name,
                                                     user.available_instruct_tasks, user.language_code, user.datetime_context)
            db_message = MdMessage(session_id=session_id, message=message, sender=Message.agent_message_key,
                                   event_name='home_chat_message', creation_date=datetime.now(),
                                   message_date=datetime.now())
            db_session.add(db_message)
            db_session.commit()
        except Exception as e:
            raise Exception(f"__create_home_chat : {e}")


    def __create_home_chat_by_batches(self, user_ids, week):
        for user_id in user_ids:
            self.__create_home_chat("0.0.0", "mobile", user_id, week=week)

    @with_db_session
    def __get_this_week_last_pre_prepared_home_chat(self, user_id, use_message_placeholder, db_session):
        try:
            week_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
                days=datetime.now().weekday())
            result = db_session.query(MdHomeChat, MdMessage) \
                .filter(user_id == MdHomeChat.user_id) \
                .filter(MdHomeChat.start_date.is_(None)) \
                .filter(MdHomeChat.week >= week_start) \
                .join(MdMessage, MdMessage.session_id == MdHomeChat.session_id) \
                .order_by(MdHomeChat.creation_date.desc()).first()
            if result is None:
                return None
            home_chat, first_message = result
            return home_chat, first_message
        except Exception as e:
            raise Exception(f"__get_last_pre_prepared_home_chat : {e}")

    # get initial chat message
    def get(self, user_id):
        error_message = "Error getting home chat"

        try:
            timestamp = request.args["datetime"]
            app_version = version.parse(request.args["version"]) if "version" in request.args else version.parse(
                "0.0.0")
            platform = request.args["platform"]
            use_message_placeholder = request.args[
                                          "use_message_placeholder"] == "true" if "use_message_placeholder" in request.args else False
        except KeyError as e:
            return {"error": f"Missing field: {e}"}, 400

        try:
            this_week = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
                days=datetime.now().weekday())
            if use_message_placeholder:
                self.__create_home_chat(app_version, platform, user_id, week=this_week, close_db=False,
                                        use_message_placeholder=True)
            # Then get last prepared home chat
            result = self.__get_this_week_last_pre_prepared_home_chat(user_id, use_message_placeholder)
            if result is None:
                self.__create_home_chat(app_version, platform, user_id, week=this_week, close_db=False)
                result = self.__get_this_week_last_pre_prepared_home_chat(user_id, use_message_placeholder)
            home_chat, first_message = result

            home_chat.start_date = datetime.now()
            db.session.commit()

            return {
                "home_chat_pk": home_chat.home_chat_pk,
                "session_id": first_message.session_id,
                "message_pk": first_message.message_pk,
                "message": first_message.message
            }, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"{error_message}: {e}", notify_admin=True)
            return {"error": f"error_message: {e}"}, 500

    # route to pre-shot first of week homechat
    def put(self):
        error_message = "Error preparing next week first home chat"

        if not request.is_json:
            log_error(f"{error_message} : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        try:
            timestamp = request.json['datetime']
            n_users = request.json['n_users']
            offset = request.json['offset']
        except KeyError as e:
            return {"error": f"Missing field: {e}"}, 400

        try:
            # users that:
            # - datetime in timezone is sunday 10pm

            users = (
                db.session.query(User)
                .filter(User.timezone_offset.isnot(None))
                .filter(
                    extract(
                        "hour",
                        text("NOW() - md_user.timezone_offset * interval '1 minute'")
                    )
                    >= int(22)
                )
                .filter(
                    extract(
                        "hour",
                        text("NOW() - md_user.timezone_offset * interval '1 minute'")
                    )
                    < int(22) + 1
                )
                .filter(
                    extract(
                        "day",
                        text("NOW() - md_user.timezone_offset * interval '1 minute'")
                    )
                    == int(7)
                )
                .order_by(User.user_id)
                .offset(offset)
                .limit(n_users)
                .subquery()
            )

            subquery = (
                db.session.query(
                    MdHomeChat.user_id,
                    func.date_trunc("week", MdHomeChat.creation_date).label("creation_week"),
                    func.count(MdHomeChat.home_chat_pk).label("count"),
                )
                .filter(MdHomeChat.start_date.is_(None))
                .group_by(MdHomeChat.user_id, func.date_trunc("week", MdHomeChat.creation_date))
                .having(func.count(MdHomeChat.home_chat_pk) == 1)
                .subquery()
            )

            user_and_ready_home_chat = (
                db.session.query(User, MdHomeChat)
                .select_from(users)
                .join(User, User.user_id == users.c.user_id)
                .outerjoin(
                    MdHomeChat,
                    and_(
                        MdHomeChat.user_id == users.c.user_id,
                        MdHomeChat.start_date.is_(None),
                    ),
                )
                .outerjoin(
                    subquery,
                    and_(
                        MdHomeChat.user_id == subquery.c.user_id,
                        func.date_trunc("week", MdHomeChat.creation_date) == subquery.c.creation_week,
                    ),
                )
                .order_by(
                    users.c.user_id,
                    MdHomeChat.creation_date.desc(),
                )
                .all()
            )
            to_be_prepared = []
            week = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=7) - timedelta(
                days=datetime.now().weekday())
            for user, home_chat in user_and_ready_home_chat:
                if home_chat is None:
                    to_be_prepared.append(user.user_id)
                else:
                    home_chat.week = week
                    db.session.commit()

            server_socket.start_background_task(self.__create_home_chat_by_batches, to_be_prepared, week)
            user_ids = [user.user_id for user, _ in user_and_ready_home_chat]
            # Normally, flask_socketio will close db.session automatically after the request is done
            # (https://flask.palletsprojects.com/en/2.3.x/patterns/sqlalchemy/) "Flask will automatically remove database sessions at the end of the request or when the application shuts down."
            # But if may not the case because of the background task launched in this route, errors like `QueuePool limit of size 5 overflow 10 reached` may happen in the backend logs and cause issues.
            # That's why here we explicitely call `db.session.close()` to close the session manually.
            db.session.close()

            return {"user_ids": user_ids}, 200

        except Exception as e:
            log_error(f"{error_message} : {e}", notify_admin=True)
            db.session.rollback()
            db.session.close()
            return {"error": f"{error_message} : {e}"}, 500

    # User just killed app, ready for generating next home_chat
    def post(self, user_id):
        if not request.is_json:
            return {"error": "Request must be JSON"}, 400

        try:
            timestamp = request.json['datetime']
        except KeyError as e:
            return {"error": f"Missing field: {e}"}, 400

        try:
            this_week = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
                days=datetime.now().weekday())
            server_socket.start_background_task(self.__create_home_chat, "0.0.0", "mobile", user_id, week=this_week,
                                                close_db=True)
            # Normally, flask_socketio will close db.session automatically after the request is done
            # (https://flask.palletsprojects.com/en/2.3.x/patterns/sqlalchemy/) "Flask will automatically remove database sessions at the end of the request or when the application shuts down."
            # But if may not the case because of the background task launched in this route, errors like `QueuePool limit of size 5 overflow 10 reached` may happen in the backend logs and cause issues.
            # That's why here we explicitely call `db.session.close()` to close the session manually.
            db.session.close()
            return {}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error creating home chat : {e}", notify_admin=True)
            db.session.close()
            return {"error": f"Error creating home chat : {e}"}, 500
