from abc import ABC, abstractmethod
from app import db, log_error
from mojodex_backend_logger import MojodexBackendLogger
from db_models import *
from datetime import datetime
import os
from models.tasks.task_executor import TaskExecutor
from models.tasks.task_inputs_manager import TaskInputsManager
from models.tasks.task_tool_manager import TaskToolManager

class AssistantMessageGenerator(ABC):

    def __init__(self, user, session_id, platform, voice_generator, mojo_messages_audio_storage, logger_prefix, mojo_token_callback):
        self.user_id = user.user_id
        self.username = user.name
        self.session_id = session_id
        self.platform = platform
        self.voice_generator = voice_generator
        self.mojo_messages_audio_storage = mojo_messages_audio_storage
        self.mojo_token_callback = mojo_token_callback
        self.language = None
        self.running_task = None
        self.running_user_task = None
        self.running_user_task_execution = None
        self.running_task_displayed_data = None
        self.task_input_manager = TaskInputsManager(session_id, self.remove_tags_from_text)
        self.task_tool_manager = TaskToolManager(session_id, self.remove_tags_from_text)
        self.task_executor = TaskExecutor(session_id, self.user_id, self._mojo_message_to_db, self._message_will_have_audio, self._generate_voice)
        self.logger = MojodexBackendLogger(f"{logger_prefix} -- session {session_id}")

    

    @staticmethod
    def remove_tags_from_text(text, start_tag, end_tag):
        try:
            return text.split(start_tag)[1].split(end_tag)[0].strip() if start_tag in text else ""
        except Exception as e:
            raise Exception(f"remove_tags_from_text :: text: {text} - start_tag: {start_tag} - end_tag: {end_tag} - {e}")

    # abstract private method answer user
    @abstractmethod
    def _answer_user(self, *args):
        raise NotImplementedError
    
    def _get_all_session_messages(self, session_id):
        try:
            messages = db.session.query(MdMessage).filter(MdMessage.session_id == session_id).order_by(
                MdMessage.message_date).all()
            return messages
        except Exception as e:
            raise Exception("_get_all_session_messages: " + str(e))
        
    def _get_conversation_as_list(self, without_last_message=False, agent_key="assistant", user_key="user"):
        try:
            messages = self._get_all_session_messages(self.session_id)
            if without_last_message:
                messages = messages[:-1]
            conversation = []
            for message in messages:
                if message.sender == "user":  # Session.user_message_key:
                    if "text" in message.message:
                        conversation.append({"role": user_key, "content": message.message['text']})
                elif message.sender == "mojo":  # Session.agent_message_key:
                    if "text" in message.message:
                        if "text_with_tags" in message.message:
                            conversation.append({"role": agent_key, "content": message.message['text_with_tags']})
                        else:
                            conversation.append({"role": agent_key, "content": message.message['text']})
                else:
                    raise Exception("Unknown message sender")
            return conversation
        except Exception as e:
            raise Exception("Error during _get_conversation: " + str(e))

    def _get_conversation_as_string(self, session_id, agent_key="Agent", user_key="User", with_tags=True):
        try:
            messages = self._get_all_session_messages(session_id)
            conversation = ""
            for message in messages:
                if message.sender == "user":  # Session.user_message_key:
                    if "text" in message.message:
                        conversation += f"{user_key}: {message.message['text']}\n"
                elif message.sender == "mojo":  # Session.agent_message_key:
                    if "text" in message.message:
                        if "text_with_tags" in message.message and with_tags:
                            conversation += f"{agent_key}: {message.message['text_with_tags']}\n"
                        else:
                            conversation += f"{agent_key}: {message.message['text']}\n"
                else:
                    raise Exception("Unknown message sender")
            return conversation
        except Exception as e:
            raise Exception("_get_conversation_as_string: " + str(e))
        
    def _mojo_message_to_db(self, mojo_message, event_name):
        try:
            user_task_execution_pk = self.running_user_task_execution.user_task_execution_pk if self.running_user_task_execution else None
            if user_task_execution_pk:
                mojo_message["user_task_execution_pk"] = user_task_execution_pk
            db_message = MdMessage(session_id=self.session_id, sender='mojo', event_name=event_name,
                                message=mojo_message,
                                creation_date=datetime.now(), message_date=datetime.now())
            db.session.add(db_message)
            db.session.commit()
            db.session.refresh(db_message)
            return db_message
        except Exception as e:
            raise Exception(f"__mojo_message_to_db :: {e}")
        
    def _message_will_have_audio(self, mojo_message):
        return "text" in mojo_message and self.platform == "mobile" and self.voice_generator is not None
    
    def _generate_voice(self, db_message):
        output_filename = os.path.join(self.mojo_messages_audio_storage, f"{db_message.message_pk}.mp3")
        try:
            self.voice_generator.text_to_speech(db_message.message["text"], self.language, self.user_id,
                                                output_filename,
                                                user_task_execution_pk=self.running_user_task_execution.user_task_execution_pk if self.running_user_task_execution else None,
                                                task_name_for_system=self.running_task.name_for_system if self.running_task else None,)

        except Exception as e:
            db_message.in_error_state = datetime.now()
            log_error(str(e), session_id=self.session_id, notify_admin=True)