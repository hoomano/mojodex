import os
from datetime import datetime
from flask import request
from flask_restful import Resource
from app import db, authenticate, log_error, server_socket, time_manager, main_logger
from mojodex_core.entities import *
from models.session import Session
from models.user_audio_file_manager import UserAudioFileManager
from packaging import version
from sqlalchemy.orm.attributes import flag_modified

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

    def put(self, user_id):

        try:
            session_id = request.form['session_id']
            # This message_id is sent by the client to identify the message, no usage in backend but to avoid saving the same message twice
            message_id = request.form['message_id']
            message_pk = request.form['message_pk'] if 'message_pk' in request.form else None
            message_date = request.form['message_date']
            app_version = version.parse(request.form['version'])
            use_message_placeholder = request.form['use_message_placeholder'] == "true" if 'use_message_placeholder' in request.form else False
            use_draft_placeholder = request.form['use_draft_placeholder'] == "true" if 'use_draft_placeholder' in request.form else False
            origin = request.form['origin'] if 'origin' in request.form else "task"
            # check origin is "home_chat" or "task"
            if origin not in ["home_chat", "task"]:
                return {"error": f"Invalid origin: {origin}"}, 400

        except KeyError as e:
            return {"error": f"Missing input in form: {e}"}, 400

        try:
            user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()
            message_date = time_manager.device_date_to_backend_date(message_date, user.timezone_offset if user.timezone_offset else 0)
        except Exception as e:
            return {"error": f"Invalid message_date or timezone_offset : {e}"}, 400

        # Acknowledge the message reception
        try:
            server_socket.emit("user_message_reception", {"success": "User message has been received", "session_id":session_id}, to=session_id)
        except Exception as e:
            log_error(f"Error acknowledging message : {e}")

        try:
            if message_pk: # if there is a message_pk, message is supposed to exist already
                message = db.session.query(MdMessage).filter(MdMessage.message_pk == message_pk).first()
            else:
                # check if message_id already exists among messages with session_id=session_id and message field is not {}. message_id is stored in message.message json field
                message = db.session.query(MdMessage) \
                    .filter(MdMessage.session_id == session_id) \
                    .filter(MdMessage.message.op('->>')('message_id') == message_id) \
                    .first()
            if message is not None:
                if message.in_error_state is None:
                    if len(message.message) == 1:  # only message_id in message
                        return {"status": "processing"}, 200
                    else:
                        return message.message, 200
                # else, retry transcription

            # This will receive a form with a m4a file and fields datetime and session_id
            session = db.session.query(MdSession).filter(MdSession.session_id == session_id).filter(
                MdSession.user_id == user_id).first()
            if session is None:
                log_error(
                    f"Error getting voice : Session with session_id {session_id} does not exist for user {user_id}")
                return {"error": f"Invalid session_id for user: {session_id}"}, 400
            if message is None:
                # save in db as user_message
                message = MdMessage(session_id=session_id, sender=Session.user_message_key, event_name='user_message',
                                    message={'message_id': message_id},
                                    # temporary message to be replaced by the transcription
                                    creation_date=datetime.now(), message_date=message_date)
                db.session.add(message)
                # Need to commit and not just flush here because if Whisper takes so much time that the same message arrives again,
                # we need to have the message_id in the db to assess it already exists
            else: # only way to arrive here with not none message is in_error_state is not None
                message.in_error_state = None

            db.session.commit()
            db.session.refresh(message)

            try:
                # Current task of md_session if any
                if origin == "task":
                    result = db.session.query(MdUserTaskExecution, MdTask) \
                        .filter(MdUserTaskExecution.session_id == session_id) \
                        .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                        .join(MdTask, MdUserTask.task_fk == MdTask.task_pk) \
                        .order_by(MdUserTaskExecution.user_task_execution_pk.desc()) \
                        .first()
                else:
                    # if previous message.message of session contained user_task_execution_pk, use it to get the task
                    previous_agent_message = db.session.query(MdMessage) \
                        .filter(MdMessage.session_id == session_id) \
                        .filter(MdMessage.sender == Session.agent_message_key) \
                        .order_by(MdMessage.creation_date.desc()) \
                        .first()
                    if previous_agent_message:
                        if previous_agent_message.message and "user_task_execution_pk" in previous_agent_message.message:

                            user_task_execution_pk = previous_agent_message.message["user_task_execution_pk"]
                            result = db.session.query(MdUserTaskExecution, MdTask) \
                                .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk) \
                                .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                                .join(MdTask, MdUserTask.task_fk == MdTask.task_pk) \
                                .first()
                        else:
                            result = None
                    else:
                        result = None


                if result:
                    user_task_execution, task = result
                    user_task_execution_pk, task_name_for_system = user_task_execution.user_task_execution_pk, task.name_for_system
                    home_chat = None

                    user_task_execution = db.session.query(MdUserTaskExecution) \
                        .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                        .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk) \
                        .filter(MdUserTask.user_id == user_id) \
                        .first()
                    if user_task_execution is None:
                        log_error(
                            f"Error with user_message : UserTaskExecution {user_task_execution_pk} not found for user {user_id}")
                        return {"error": f"UserTaskExecution  {user_task_execution_pk} not found for this user"}, 400

                    if user_task_execution.start_date is None:
                        user_task_execution.start_date = datetime.now()
                        db.session.commit()
                        try:
                            iso_start_date = time_manager.backend_date_to_user_date(user_task_execution.start_date,
                                                                                    user.timezone_offset if user.timezone_offset else 0).isoformat()
                            server_socket.emit("user_task_execution_start", {"start_date": iso_start_date,
                                                                            "user_task_execution_pk": user_task_execution_pk,
                                                                            "session_id": session_id},
                                            to=session_id)
                        except Exception as e:
                            log_error(f"Error acknowledging message : {e}")
                else:
                        user_task_execution_pk, task_name_for_system = None, None

                        # home chat related if any
                        home_chat = db.session.query(MdHomeChat) \
                            .filter(MdHomeChat.session_id == session_id) \
                            .first()

                if "text" in request.form:
                    message.message = {"text": request.form["text"], "message_pk": message.message_pk,
                                       'message_id': message_id}

                else:
                    if 'file' in request.files:
                        file = request.files['file']
                        filename = file.filename
                        extension = filename.split(".")[-1]
                    else:
                        file = None
                        extension = None

                    decoded_text, file_duration = self.user_audio_file_manager.extract_text_and_duration(file, extension,
                                                                                                         user_id,
                                                                                                         session_id,
                                                                                                         "user_message",
                                                                                                         message.message_pk,
                                                                                                         user_task_execution_pk=user_task_execution_pk,
                                                                                                         task_name_for_system=task_name_for_system)

                    message.message = {"text": decoded_text, "message_pk": message.message_pk,
                                       "audio_duration": file_duration, 'message_id': message_id}
                
                if user_task_execution_pk:
                        message.message["user_task_execution_pk"] = user_task_execution_pk
                db.session.flush()

                session_db = db.session.query(MdSession).filter(MdSession.session_id == session_id).first()
                if session_db is None:
                    log_error(f"Session {session_id} not found in db", session_id=session_id)
                    return

                from models.session import Session as SessionModel
                session = SessionModel(session_id)

                session_message = {"text": message.message["text"], "message_pk": message.message_pk,
                                   "audio": not "text" in request.form, "user_task_execution_pk":user_task_execution_pk, "origin": origin,
                                   "home_chat_pk": home_chat.home_chat_pk if home_chat else None,
                                     "message_date": message_date.isoformat(),
                                   "use_message_placeholder": use_message_placeholder, "use_draft_placeholder": use_draft_placeholder}

                server_socket.start_background_task(session.process_chat_message, session_message)

            except Exception as e:
                # mark message as in_error_state so that next retry will go through transcription again
                message.in_error_state = datetime.now()
                db.session.commit()
                log_error(f"Error with user_message : {e}")
                return {"error": f"{e}"}, 400

            db.session.commit()
            return message.message, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error with user_message : {e}")
            return {"error": f"{e}"}, 400
