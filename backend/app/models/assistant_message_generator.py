from abc import ABC, abstractmethod

import requests
from app import db, log_error, placeholder_generator, server_socket
from mojodex_backend_logger import MojodexBackendLogger
from db_models import *
from datetime import datetime
import os
from models.tasks.task_executor import TaskExecutor
from models.tasks.task_inputs_manager import TaskInputsManager
from models.tasks.task_tool_manager import TaskToolManager

class AssistantMessageGenerator(ABC):

    user_language_start_tag = "<user_language>"
    user_language_end_tag = "</user_language>"

    def __init__(self, user, session_id, platform, voice_generator, mojo_messages_audio_storage, logger_prefix, mojo_token_callback, app_version):
        self.user_id = user.user_id
        self.username = user.name
        self.session_id = session_id
        self.platform = platform
        self.voice_generator = voice_generator
        self.mojo_messages_audio_storage = mojo_messages_audio_storage
        self.mojo_token_callback = mojo_token_callback
        self.app_version = app_version
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
    
    @abstractmethod
    def _token_callback(self, partial_text):
        raise NotImplementedError
    
    @abstractmethod
    def _get_message_placeholder(self):
        raise NotImplementedError
    
    @abstractmethod
    def _get_execution_placeholder(self):
        raise NotImplementedError
    
    @abstractmethod
    def _generate_assistant_response(self, tag_proper_nouns=False):
        raise NotImplementedError
    
    @abstractmethod
    def _manage_response_tag(self, response, user_message, use_draft_placeholder):
        raise NotImplementedError
    
    def response_to_user_message(self, user_message, tag_proper_nouns=False):
        try:
            if self.running_user_task_execution:
                server_socket.start_background_task(self._give_title_and_summary_task_execution,
                                                self.running_user_task_execution.user_task_execution_pk)
            mojo_message = self._answer_user(user_message, tag_proper_nouns=tag_proper_nouns)
            if mojo_message and self.running_user_task_execution:
                mojo_message['user_task_execution_pk'] = self.running_user_task_execution.user_task_execution_pk
            return 'mojo_message', mojo_message, self.language
        except Exception as e:
            raise Exception(f"response_to_user_message :: {e}")
    
    def _give_title_and_summary_task_execution(self, user_task_execution_pk):
        try:
            # call background backend /end_user_task_execution to update user task execution title and summary
            uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/user_task_execution_title_and_summary"
            pload = {'datetime': datetime.now().isoformat(),
                     'user_task_execution_pk': user_task_execution_pk}
            internal_request = requests.post(uri, json=pload)
            if internal_request.status_code != 200:
                log_error(
                    f"Error while calling background user_task_execution_title_and_summary : {internal_request.json()}")
        except Exception as e:
            print(f"🔴 _give_title_and_summary_task_execution :: {e}")

    def _get_empty_json_input_values(self):
        try:
            empty_json_input_values = []
            for input in self.running_task_displayed_data.json_input:
                input["value"] = None
                empty_json_input_values.append(input)
            return empty_json_input_values
        except Exception as e:
            raise Exception(f"_get_empty_json_input_values :: {e}")

    def _manage_placeholders(self, use_message_placeholder, use_draft_placeholder):
        try:
            if use_message_placeholder:
                response = self._get_message_placeholder()
            elif use_draft_placeholder:
                response = self._get_execution_placeholder()
                placeholder_generator.stream(response, self._token_callback)
            return response
        except Exception as e:
            raise Exception(f"_manage_placeholders :: {e}")
        
    def _extract_placeholders_from_user_message(self, user_message):
        try:
            use_message_placeholder = user_message["use_message_placeholder"] if (
                    "use_message_placeholder" in user_message) else False
            use_draft_placeholder = user_message["use_draft_placeholder"] if (
                    "use_draft_placeholder" in user_message) else False
        except Exception as e:
            use_message_placeholder, use_draft_placeholder = False, False
        return use_message_placeholder, use_draft_placeholder
    
    def _answer_user(self, user_message=None, use_message_placeholder=False, use_draft_placeholder=False, tag_proper_nouns=False):
        self.logger.debug(f"_answer_user")
        
        try:
            if user_message is not None:
                use_message_placeholder, use_draft_placeholder = self._extract_placeholders_from_user_message(user_message)

            if use_message_placeholder or use_draft_placeholder:
                response = self._manage_placeholders(use_message_placeholder, use_draft_placeholder)
            else:
                response = self._generate_assistant_response(tag_proper_nouns=tag_proper_nouns)
                
            
            self._manage_response_language_tag(response)
            response = self._manage_response_tag(response, user_message, use_draft_placeholder)
            return response

        except Exception as e:
            raise Exception(f"_answer_user :: {e}")
    
    def _get_produced_text_done(self):
        try:
            if self.running_user_task_execution is None:
                return False
            return db.session.query(MdProducedText).filter(
                MdProducedText.user_task_execution_fk == self.running_user_task_execution.user_task_execution_pk).count() > 1
        except Exception as e:
            raise Exception(f"_get_produced_text_done :: {e}")

    def _get_task_tools_json(self):
        try:
            if self.running_task is None:
                return None
            task_tool_associations = db.session.query(MdTaskToolAssociation, MdTool)\
                .join(MdTool, MdTool.tool_pk == MdTaskToolAssociation.tool_fk)\
                .filter(MdTaskToolAssociation.task_fk == self.running_task.task_pk).all()
            return [{"task_tool_association_pk": task_tool_association.task_tool_association_pk,
                     "usage_description": task_tool_association.usage_description,
                     "tool_name": tool.name}
                    for task_tool_association, tool in task_tool_associations]
        except Exception as e:
            raise Exception(f"_get_task_tools_json :: {e}")

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

    def _manage_response_language_tag(self, response):
        try:
            if self.language is None and AssistantMessageGenerator.user_language_start_tag in response:
                try:
                    self.language = self.remove_tags_from_text(response, AssistantMessageGenerator.user_language_start_tag,
                                                                      AssistantMessageGenerator.user_language_end_tag).lower()
                    self.logger.info(f"language: {self.language}")
                    # update session
                    db_session = db.session.query(MdSession).filter(MdSession.session_id == self.session_id).first()
                    db_session.language = self.language
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    self.logger.error(f"Error while updating session language: {e}")
        except Exception as e:
            raise Exception(f"_manage_response_language_tag :: {e}")