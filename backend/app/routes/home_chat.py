import os
from flask import request
from flask_restful import Resource
from models.assistant.session import Session as SessionModel
from app import authenticate, db, server_socket

from models.knowledge.knowledge_manager import KnowledgeManager

from mojodex_core.entities_controllers.user import User
from mojodex_core.entities_controllers.session import Session

from models.assistant.chat_assistant import ChatAssistant
from mojodex_core.llm_engine.mpt import MPT
from mojodex_core.logging_handler import log_error
from datetime import datetime, timedelta
from mojodex_core.entities import *
from packaging import version

from models.session_creator import SessionCreator

from sqlalchemy import extract, text, func, and_


class HomeChat(Resource):
    welcome_message_mpt_filename = "instructions/welcome_message.mpt"
    message_header_start_tag, message_header_end_tag = "<message_header>", "</message_header>"
    message_body_start_tag, message_body_end_tag = "<message_body>", "</message_body>"

    def __init__(self):
        HomeChat.method_decorators = [authenticate(methods=["GET", "POST"])]
        self.session_creator = SessionCreator()

    def __get_this_week_home_conversations(self, user_id):
        try:
            # 1. get list of this week's home_chat sessions
            week_start_date = datetime.now().date() - timedelta(days=datetime.now().date().weekday())
            sessions = db.session.query(MdSession)\
            .join(MdHomeChat, MdSession.session_id == MdHomeChat.session_id)\
            .filter(and_(MdHomeChat.start_date.isnot(None), MdHomeChat.start_date >= week_start_date))\
            .filter(MdSession.user_id == user_id)\
                .all()
            if not sessions:
                return []

            return [{
                "date": session.creation_date,
                "conversation": Session(session.session_id, db.session).get_conversation_as_string(agent_key="YOU", user_key="USER",
                                                                  with_tags=False)
            } for session in sessions]

        except Exception as e:
            raise Exception(f"__get_this_week_home_conversations :: {e}")

    def __get_this_week_task_executions(self, user_id):
        try:
            week_start_date = datetime.now().date() - timedelta(days=datetime.now().date().weekday())
            # last 20 tasks executions of the user this week order by start_date
            user_task_executions = db.session.query(MdUserTaskExecution.title, MdUserTaskExecution.summary, MdTask.name_for_system) \
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

    def _generate_welcome_message(self, user_id):
        try:
            user = User(user_id, db.session)
            previous_conversations = self.__get_this_week_home_conversations(user_id)
            welcome_message_mpt = MPT(self.welcome_message_mpt_filename,
                                  mojo_knowledge=KnowledgeManager.get_mojo_knowledge(),
                                  global_context=KnowledgeManager.get_global_context_knowledge(),
                                  username=user.username,
                                  tasks=user.available_instruct_tasks,
                                  first_time_this_week=len(previous_conversations) == 0,
                                  user_task_executions=self.__get_this_week_task_executions(user_id),
                                  previous_conversations=previous_conversations,
                                  language=user.language_code)

            responses = welcome_message_mpt.run(user_id=user_id, temperature=0, max_tokens=1000,
                                                  user_task_execution_pk=None,
                                                  task_name_for_system=None)
            message = responses[0].strip()
            header = ChatAssistant.remove_tags_from_text(message,
                                                                   self.message_header_start_tag,
                                                                   self.message_header_end_tag)
            body = ChatAssistant.remove_tags_from_text(message,
                                                                 self.message_body_start_tag,
                                                                 self.message_body_end_tag)
            return {"header": header,
                    "body": body,
                    "text": f"{header}\n{body}"}
        except Exception as e:
            raise Exception(f"_generate_welcome_message : {e}")

    def __create_home_chat(self, app_version, platform, user_id, week, close_db=True, use_message_placeholder=False):
        try:
            session_creation = self.session_creator.create_session(user_id, platform, "chat")
            if "error" in session_creation[0]:
                raise Exception(session_creation[0]["error"])
            session_id = session_creation[0]["session_id"]
            home_chat = MdHomeChat(session_id=session_id, user_id=user_id, week=week)
            db.session.add(home_chat)
            db.session.commit()
            message = self._generate_welcome_message(user_id)
            db_message = MdMessage(session_id=session_id, message=message, sender=SessionModel.agent_message_key,
                                   event_name='home_chat_message', creation_date=datetime.now(),
                                   message_date=datetime.now())
            db.session.add(db_message)
            db.session.commit()

            if close_db:
                db.session.close()
        except Exception as e:
            raise Exception(f"__create_home_chat : {e}")

    def __create_home_chat_by_batches(self, user_ids, week):
        for user_id in user_ids:
            self.__create_home_chat("0.0.0", "mobile", user_id, week=week, close_db=True)
        db.session.close()

    def __get_this_week_last_pre_prepared_home_chat(self, user_id, use_message_placeholder):
        try:
            week_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
                days=datetime.now().weekday())
            result = db.session.query(MdHomeChat, MdMessage) \
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

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_SCHEDULER_SECRET"]:
                log_error(f"{error_message} : Authentication error : Wrong secret", notify_admin=True)
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"{error_message} : Missing Authorization secret in headers", notify_admin=True)
            return {"error": f"Missing Authorization secret in headers"}, 403

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
                db.session.query(MdUser)
                .filter(MdUser.timezone_offset.isnot(None))
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
                .order_by(MdUser.user_id)
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
                db.session.query(MdUser, MdHomeChat)
                .select_from(users)
                .join(MdUser, MdUser.user_id == users.c.user_id)
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

            return {"user_ids": [user.user_id for user, _ in user_and_ready_home_chat]}, 200

        except Exception as e:
            log_error(f"{error_message} : {e}", notify_admin=True)
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
            return {}, 200
        except Exception as e:
            log_error(f"Error creating home chat : {e}", notify_admin=True)
            return {"error": f"Error creating home chat : {e}"}, 500
