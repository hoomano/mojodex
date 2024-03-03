import glob
import os
import time

from flask import request
from flask_restful import Resource
from models.session import Session as SessionModel
from app import db, authenticate, log_error
from mojodex_core.entities import *
from flask import send_file
from packaging import version

from models.tasks.task_manager import TaskManager


class Voice(Resource):
    def __init__(self):
        Voice.method_decorators = [authenticate()]

    def get(self, user_id):

        try:
            timestamp = request.args["datetime"]
            message_pk = request.args["message_pk"] if "message_pk" in request.args else None
            filename = request.args["filename"] if "filename" in request.args else None # case welcome_text
            app_version = version.parse(request.args["app_version"] if "app_version" in request.args else "0.0.0")
            if filename is None and message_pk is None:
                log_error(f"Error getting voice : Missing field filename or message_pk")
                return {"error": f"Missing field filename or message_pk"}, 400
        except KeyError as e:
            log_error(f"Error getting voice : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            if message_pk is not None:
                message = db.session.query(MdMessage).join(MdSession, MdMessage.session_id == MdSession.session_id)\
                    .filter(MdSession.user_id == user_id)\
                    .filter(MdMessage.message_pk == message_pk)\
                    .first()

                if message is None:
                    log_error(f"Error getting voice : Message with message_pk {message_pk} does not exist for user {user_id}")
                    return {"error": f"Invalid message message_pk for user: {message_pk}"}, 400
                filename=message_pk
                session_id = message.session_id
            user_storage = os.path.join(SessionModel.sessions_storage, user_id)
            session_storage = os.path.join(user_storage, session_id) if message_pk is not None else None
            if message_pk and message.sender == SessionModel.user_message_key:
                audio_storage = os.path.join(session_storage, "user_messages_audios")
            elif message_pk and message.sender == SessionModel.agent_message_key:
                audio_storage = os.path.join(session_storage, "mojo_messages_audios")
            elif message_pk is None:
                audio_storage = os.path.join(user_storage, "welcome_text_audios")
            file_pattern = os.path.join(audio_storage, f"{filename}.*")
            matching_files = glob.glob(file_pattern)
            if len(matching_files) == 0:
                if message_pk and message.sender == SessionModel.agent_message_key:
                    # audio could be still processing or in error
                    if not message.in_error_state:
                        return {"status": "processing"}, 200
                    # note: else it's too bad not to try again...
                log_error(f"Error getting voice : No matching file for file {file_pattern}")
                return {"error": f"No matching file for file {file_pattern}"}, 400
            audio_file = matching_files[0]
            retries = 3
            while retries > 0:
                if os.path.isfile(audio_file):
                    break
                else:
                    retries -= 1
                    time.sleep(1) # wait for file to be created 1 second
            if not os.path.isfile(audio_file):
                log_error(f"Error getting voice : Audio file {audio_file} does not exist")
                return {"error": f"Audio file {audio_file} does not exist"}, 400

            response = send_file(audio_file, conditional=True)
            response.headers.add('Accept-Ranges', 'bytes')
            return response
        except Exception as e:
            db.session.rollback()
            log_error(f"Error getting voice : {e}")
            return {"error": f"{e}"}, 400

