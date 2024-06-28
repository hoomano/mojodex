import glob
import os
from flask import request
from flask_restful import Resource
from app import db, authenticate
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *

from sqlalchemy import or_
from mojodex_core.entities.message import Message as MessageEntity
from datetime import datetime
class Message(Resource):

    def __init__(self):
        Message.method_decorators = [authenticate()]

    @staticmethod
    def has_audio_file(message_pk, sender, user_id, session_id):
        from mojodex_core.user_storage_manager.user_audio_file_manager import UserAudioFileManager
        user_audio_file_manager = UserAudioFileManager()
        if sender == MessageEntity.user_message_key:
            audio_storage = user_audio_file_manager.get_user_messages_audio_storage(user_id, session_id)
        else:
            audio_storage = user_audio_file_manager.get_mojo_messages_audio_storage(user_id, session_id)
        files = [os.path.join(audio_storage, f'{message_pk}.{ext}') for ext in ('wav', 'mp3', 'm4a')]
        return any(glob.glob(file) for file in files)


    def get(self, user_id):

        try:
            timestamp = request.args["datetime"]
            session_id = request.args["session_id"]
            offset_direction = request.args["offset_direction"] if "offset_direction" in request.args else "older"
            user_task_execution_pk = request.args["user_task_execution_pk"] if "user_task_execution_pk" in request.args else None
        except KeyError as e:
            log_error(f"Error getting messages : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        try:
            # check session_id belongs to user_id
            session = db.session.query(MdSession).filter(MdSession.session_id == session_id).filter(MdSession.user_id == user_id).first()
            if session is None:
                return {"error": f"Session {session_id} not found for this user"}, 404

            n_messages = min(50,int(request.args[
                                                 "n_messages"])) if "n_messages" in request.args else 50
            offset = int(request.args["offset"]) if "offset" in request.args else 0

            messages = db.session.query(MdMessage).filter(MdMessage.session_id == session_id) \
                .filter(or_(MdMessage.message.op('->>')('text').isnot(None),
                            MdMessage.sender == "user"))
            
            if user_task_execution_pk is not None:
                messages = messages.filter(MdMessage.message.op('->>')('user_task_execution_pk') == user_task_execution_pk)

            if offset_direction == "older":
                messages = messages.order_by(MdMessage.message_date.desc())
            elif offset_direction == "newer":
                messages = messages.order_by(MdMessage.message_date.asc())

            messages = messages.limit(n_messages) \
                .offset(offset) \
                .all()

            if offset_direction == "newer":
                messages = reversed(messages)



            return_messages = []
            for message in messages:
                return_messages.append({
                    "message_pk": message.message_pk,
                    "sender": message.sender,
                    "message": message.message,
                    "audio": Message.has_audio_file(message.message_pk, message.sender, user_id, session_id),
                    "in_error_state": message.in_error_state is not None
                })
                if message.read_by_user is None:
                    message.read_by_user = datetime.now()
                    db.session.flush()
                if "produced_text_version_pk" in message.message:
                    produced_text_version_pk = message.message["produced_text_version_pk"]
                    produced_text_version = db.session.query(MdProducedTextVersion).filter(MdProducedTextVersion.produced_text_version_pk == produced_text_version_pk).first()
                    if produced_text_version is not None and produced_text_version.read_by_user is None:
                        produced_text_version.read_by_user = datetime.now()
                        db.session.flush()

            db.session.commit()

            return {"messages": return_messages}, 200
        except Exception as e:
            log_error(f"Error getting messages : {e}")
            return {"error": f"Error getting messages : {e}"}, 500
