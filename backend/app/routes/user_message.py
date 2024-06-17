import os
from datetime import datetime
from flask import request
from flask_restful import Resource
from app import db, authenticate, server_socket, time_manager, main_logger

from mojodex_core.entities.message import Message
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *
from models.assistant.session_controller import SessionController
from models.user_storage_manager.user_audio_file_manager import UserAudioFileManager
from packaging import version


class UserMessage(Resource):
    general_backend_error_message = "Oops, something weird has happened. We'll help you by email!"

    def __init__(self):
        try:
            if 'WHISPER_AZURE_OPENAI_API_BASE' in os.environ:
                self.user_audio_file_manager = UserAudioFileManager()
            else:
                self.user_audio_file_manager = None
        except Exception as e:
            self.user_audio_file_manager = None
            main_logger.error(f"Can't initialize user_audio_file_manager: {e}")
        UserMessage.method_decorators = [authenticate()]

    def _acknowledge_message_reception(self, session_id):
        try:
            server_socket.emit("user_message_reception",
                               {"success": "User message has been received", "session_id": session_id}, to=session_id)
        except Exception as e:
            log_error(f"Error acknowledging message : {e}")

    def _retrieve_or_create_db_message(self, session_id, message_id, message_date, user, db_message):
        try:
            # This will receive a form with a m4a file and fields datetime and session_id
            session = db.session.query(MdSession).filter(MdSession.session_id == session_id).filter(
                MdSession.user_id == user.user_id).first()
            if session is None:
                log_error(
                    f"Error getting voice : Session with session_id {session_id} does not exist for user {user.user_id}")
                return {"error": f"Invalid session_id for user: {session_id}"}, 400
            if db_message is None:
                # save in db as user_message
                db_message = MdMessage(session_id=session_id, sender=Message.user_message_key,
                                       event_name='user_message',
                                       message={'message_id': message_id},
                                       # temporary message to be replaced by the transcription
                                       creation_date=datetime.now(), message_date=message_date)
                db.session.add(db_message)
                # Need to commit and not just flush here because if Whisper takes so much time that the same message arrives again,
                # we need to have the message_id in the db to assess it already exists
            else:  # only way to arrive here with not none message is in_error_state is not None
                db_message.in_error_state = None

            db.session.commit()
            db.session.refresh(db_message)
            return db_message
        except Exception as e:
            raise Exception(f"_retrieve_or_create_db_message:: {e}")

    def _get_associated_user_task_execution(self, origin, session_id, user):
        try:
            # Current task of md_session if any
            db_user_task_execution, db_task, db_home_chat = None, None, None
            if origin == "task":
                # if user_task_execution_pk provided, use it to get the task
                if "user_task_execution_pk" in request.form:
                    user_task_execution_pk = request.form["user_task_execution_pk"]
                    db_user_task_execution, db_task = db.session.query(MdUserTaskExecution, MdTask) \
                        .filter(MdUserTaskExecution.session_id == session_id) \
                        .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                        .join(MdTask, MdUserTask.task_fk == MdTask.task_pk) \
                        .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk) \
                        .first()
                #### Can be removed when app version >= 0.4.11, condition 1 will always be true
                else:
                    db_user_task_execution, db_task = db.session.query(MdUserTaskExecution, MdTask) \
                        .filter(MdUserTaskExecution.session_id == session_id) \
                        .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                        .join(MdTask, MdUserTask.task_fk == MdTask.task_pk) \
                        .order_by(MdUserTaskExecution.user_task_execution_pk.desc()) \
                        .first()
                ####

            elif origin == "home_chat":
                # if previous db_message.message of session contained user_task_execution_pk, use it to get the task
                previous_agent_message = db.session.query(MdMessage) \
                    .filter(MdMessage.session_id == session_id) \
                    .filter(MdMessage.sender == Message.agent_message_key) \
                    .order_by(MdMessage.creation_date.desc()) \
                    .first()
                if previous_agent_message and previous_agent_message.message and "user_task_execution_pk" in previous_agent_message.message:
                    user_task_execution_pk = previous_agent_message.message["user_task_execution_pk"]
                    db_user_task_execution, db_task = db.session.query(MdUserTaskExecution, MdTask) \
                        .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk) \
                        .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                        .join(MdTask, MdUserTask.task_fk == MdTask.task_pk) \
                        .first()
                else:
                    # home chat related if any
                    db_home_chat = db.session.query(MdHomeChat) \
                        .filter(MdHomeChat.session_id == session_id) \
                        .first()

            if db_user_task_execution:
                self._trigger_user_task_execution_start(db_user_task_execution,
                                                        session_id,
                                                        user.timezone_offset)
            return db_user_task_execution, db_task, db_home_chat
        except Exception as e:
            raise Exception(f"_get_associated_user_task_execution:: {e}")

    def _trigger_user_task_execution_start(self, db_user_task_execution, session_id, timezone_offset):
        try:
            if db_user_task_execution.start_date is None:
                db_user_task_execution.start_date = datetime.now()
                db.session.commit()
                try:
                    iso_start_date = time_manager.backend_date_to_user_date(db_user_task_execution.start_date,
                                                                            timezone_offset if timezone_offset else 0).isoformat()
                    server_socket.emit("user_task_execution_start", {"start_date": iso_start_date,
                                                                     "user_task_execution_pk": db_user_task_execution.user_task_execution_pk,
                                                                     "session_id": session_id},
                                       to=session_id)
                except Exception as e:
                    log_error(f"Error acknowledging message : {e}")
        except Exception as e:
            raise Exception(f"_trigger_user_task_execution_start:: {e}")

    def put(self, user_id):
        try:
            session_id = request.form['session_id']
            # This message_id is sent by the client to identify the message, no usage in backend but to avoid saving the same message twice
            message_id = request.form['message_id']
            message_pk = request.form['message_pk'] if 'message_pk' in request.form else None
            message_date = request.form['message_date']
            app_version = version.parse(request.form['version'])
            platform = request.form['platform'] if 'platform' in request.form else "webapp"
            use_message_placeholder = request.form[
                                          'use_message_placeholder'] == "true" if 'use_message_placeholder' in request.form else False
            use_draft_placeholder = request.form[
                                        'use_draft_placeholder'] == "true" if 'use_draft_placeholder' in request.form else False
            origin = request.form['origin'] if 'origin' in request.form else "task"
            # check origin is "home_chat" or "task"
            if origin not in ["home_chat", "task"]:
                return {"error": f"Invalid origin: {origin}"}, 400

        except KeyError as e:
            return {"error": f"Missing input in form: {e}"}, 400

        try:
            user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()
            message_date = time_manager.device_date_to_backend_date(message_date,
                                                                    user.timezone_offset if user.timezone_offset else 0)

            db_session = db.session.query(MdSession).filter(MdSession.session_id == session_id).first()
            if db_session is None:
                return {"error": f"Invalid session_id: {session_id}"}, 400

            if message_pk:  # if there is a message_pk, message is supposed to exist already
                db_message = db.session.query(MdMessage).filter(MdMessage.message_pk == message_pk).first()
            else:
                # check if message_id already exists among messages with session_id=session_id and message field is not {}. message_id is stored in message.message json field
                db_message = db.session.query(MdMessage) \
                    .filter(MdMessage.session_id == session_id) \
                    .filter(MdMessage.message.op('->>')('message_id') == message_id) \
                    .first()
            if db_message is not None:
                if db_message.in_error_state is None:
                    if len(db_message.message) == 1:  # only message_id in message
                        return {"status": "processing"}, 200
                    else:
                        return db_message.message, 200
                # else, retry transcription
            db_message = self._retrieve_or_create_db_message(session_id, message_id, message_date, user, db_message)

        except Exception as e:
            db.session.rollback()
            log_error(f"Error with user_message : {e}")
            return {"error": f"{e}"}, 400

        try:
            self._acknowledge_message_reception(session_id)

            db_user_task_execution, db_task, db_home_chat = self._get_associated_user_task_execution(origin,
                                                                                                     session_id,
                                                                                                     user)
            user_task_execution_pk = db_user_task_execution.user_task_execution_pk if db_user_task_execution else None
            task_name_for_system = db_task.name_for_system if db_task else None

            # If message is a written text
            if "text" in request.form:
                db_message.message = {"text": request.form["text"], "message_pk": db_message.message_pk,
                                      'message_id': message_id}
            # Else, message is an audio file
            else:
                file = request.files['file'] if 'file' in request.files else None
                filename = file.filename
                extension = filename.split(".")[-1] if 'file' in request.files else None

                # Prepare transcript
                decoded_text, file_duration = self.user_audio_file_manager.extract_text_and_duration(file,
                                                                                                     extension,
                                                                                                     user_id,
                                                                                                     session_id,
                                                                                                     "user_message",
                                                                                                     db_message.message_pk,
                                                                                                     user_task_execution_pk=user_task_execution_pk,
                                                                                                     task_name_for_system=task_name_for_system)

                # Update db_message.message with the transcript
                db_message.message = {"text": decoded_text, "message_pk": db_message.message_pk,
                                      "audio_duration": file_duration, 'message_id': message_id}

            # Update db_message with user_task_execution_pk if any
            if user_task_execution_pk:
                db_message.message["user_task_execution_pk"] = user_task_execution_pk

            db.session.flush()

            session = SessionController(session_id)

            session_message = {"text": db_message.message["text"],
                               "message_pk": db_message.message_pk,
                               "audio": not "text" in request.form,
                               "user_task_execution_pk": user_task_execution_pk,
                               "origin": origin,
                               "home_chat_pk": db_home_chat.home_chat_pk if db_home_chat else None,
                               "message_date": message_date.isoformat(),
                               "platform": platform,
                               "use_message_placeholder": use_message_placeholder,
                               "use_draft_placeholder": use_draft_placeholder}

            server_socket.start_background_task(session.process_chat_message, session_message)

            db.session.commit()
            return db_message.message, 200
        except Exception as e:
            # If we arrive at this point, message has correctly been stored in db but not transcripted nor transmitted to session for answer generation
            # Mark message as in_error_state so that next retry will go through transcription again
            db_message.in_error_state = datetime.now()
            db.session.commit()
            log_error(f"Error with user_message : {e}")
            return {"error": f"{e}"}, 400

