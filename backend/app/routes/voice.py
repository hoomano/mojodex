import glob
import os
import time

from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.authentication import authenticate
from mojodex_core.entities.message import Message
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *
from flask import send_file
from packaging import version
from mojodex_core.user_storage_manager.user_audio_file_manager import UserAudioFileManager

class Voice(Resource):
    def __init__(self):
        Voice.method_decorators = [authenticate()]

    def get(self, user_id):

        try:
            timestamp = request.args["datetime"]
            message_pk = request.args["message_pk"] if "message_pk" in request.args else None
            filename = request.args["filename"] if "filename" in request.args else None # case welcome_text
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
            if message_pk and message.sender == Message.user_message_key:
                audio_storage = UserAudioFileManager().get_user_messages_audio_storage(user_id, session_id)
            elif message_pk and message.sender == Message.agent_message_key:
                audio_storage = UserAudioFileManager().get_mojo_messages_audio_storage(user_id, session_id)
            file_pattern = os.path.join(audio_storage, f"{filename}.*")
            matching_files = glob.glob(file_pattern)
            if len(matching_files) == 0:
                if message_pk and message.sender == Message.agent_message_key:
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

