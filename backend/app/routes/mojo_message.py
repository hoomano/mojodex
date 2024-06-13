from datetime import datetime
import os

from flask import request
from flask_restful import Resource
from models.assistant.session import Session as SessionModel
from app import db, main_logger
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *

from models.voice_generator import VoiceGenerator


class MojoMessage(Resource):
    logger_prefix = "MojoMessage"

    def __init__(self):
        if 'SPEECH_KEY' in os.environ and 'SPEECH_REGION' in os.environ:
            try:
                self.voice_generator = VoiceGenerator()
            except Exception as e:
                self.voice_generator = None
                main_logger.error(f"{MojoMessage.logger_prefix}:: Can't initialize voice generator")
        else:
            self.voice_generator = None

    # adding new mojo message
    def put(self):
        if not request.is_json:
            return {"error": "Invalid request"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                log_error(f"Error adding new mojo message : Authentication error : Wrong secret")
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"Error adding new mojo message : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        try:
            timestamp = request.json["datetime"]
            message = request.json["message"]
            session_id = request.json["session_id"]
        except KeyError as e:
            log_error(f"Error adding new mojo message : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        try:
            # Find session
            session = db.session.query(MdSession).filter(MdSession.session_id == session_id).first()
            if session is None:
                log_error(f"Error adding new mojo message : Session {session_id} not found")
                return {"error": f"Session {session_id} not found"}, 404

            # Create message
            message_db = MdMessage(session_id=session_id, sender='mojo', event_name='mojo_message',
                                message=message,
                                creation_date=datetime.now(), message_date=datetime.now())
            db.session.add(message_db)
            db.session.flush()
            message_db.message["message_pk"] = message_db.message_pk

            try:
                from models.user_storage_manager.user_audio_file_manager import UserAudioFileManager
                user_audio_file_manager = UserAudioFileManager()
                mojo_messages_audio_storage = user_audio_file_manager.get_mojo_messages_audio_storage(self.user_id, self.id)
                output_filename = os.path.join(mojo_messages_audio_storage, f"{message_db.message_pk}.mp3")


                # get last user_task_execution of the session
                user_task_execution, task = db.session.query(MdUserTaskExecution, MdTask)\
                    .filter(MdUserTaskExecution.session_id == session_id)\
                    .join(MdUserTask, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk)\
                    .join(MdTask, MdTask.task_pk == MdUserTask.task_fk)\
                    .order_by(MdUserTaskExecution.user_task_execution_pk.desc()).first()
                if self.voice_generator:
                    self.voice_generator.text_to_speech(message['text'], session.language, session.user_id, output_filename,
                                                        user_task_execution_pk=user_task_execution.user_task_execution_pk,
                                                        task_name_for_system=task.name_for_system)
                    message_db.message['audio'] = True
                else:
                    message_db.message['audio'] = False
            except Exception as e:
                message_db.in_error_state = datetime.now()
                log_error(str(e), session_id=session_id, notify_admin=True)
            db.session.commit()
            return {"message_pk": message_db.message_pk}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error adding new mojo message : {e}", notify_admin=True)
            return {"error": str(e)}, 500

