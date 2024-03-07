import json
from models.tasks.task_tool_manager import TaskToolManager
from models.tasks.task_inputs_manager import TaskInputsManager
from models.produced_text_manager import ProducedTextManager
from models.session.assistant_message_generator import AssistantMessageGenerator
from abc import ABC, abstractmethod
from app import db
from db_models import * 
from models.tasks.task_executor import TaskExecutor


class ChatState:

    def __init__(self):
        self.current_language = None

    def _get_all_session_messages(self, session_id):
        try:
            messages = db.session.query(MdMessage).filter(MdMessage.session_id == session_id).order_by(
                MdMessage.message_date).all()
            return messages
        except Exception as e:
            raise Exception("_get_all_session_messages: " + str(e))

    def get_conversation_as_list(self, session_id, without_last_message=False, agent_key="assistant", user_key="user"):
        try:
            messages = self._get_all_session_messages(session_id)
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
            raise Exception("get_conversation_as_list: " + str(e))

class ChatContext:

    def __init__(self, user, session_id, origin, user_messages_are_audio, chat_state):
        self.state = chat_state
        self.origin = origin
        self.user_messages_are_audio = user_messages_are_audio
        self.user = user
        self.session_id = session_id
        

    @property
    def user_id(self):
        return self.user.user_id
    
    @property
    def username(self):
        return self.user.name

class AssistantResponseGenerator(AssistantMessageGenerator, ABC):
    user_language_start_tag, user_language_end_tag = "<user_language>",  "</user_language>"

    def __init__(self, prompt_template_path, message_generator, chat_context, use_message_placeholder, use_draft_placeholder, tag_proper_nouns, llm_call_temperature):
        self.use_message_placeholder = use_message_placeholder
        self.use_draft_placeholder = use_draft_placeholder
        self.llm_call_temperature = llm_call_temperature
        self.chat_context = chat_context
        super().__init__(prompt_template_path, message_generator, tag_proper_nouns)


    def _generate_message_from_prompt(self, prompt):
        try:
            conversation_list = self.chat_context.state.get_conversation_as_list(self.chat_context.session_id)
            messages = [{"role": "system", "content": prompt}] + conversation_list

            # write messages in /data/messages.json
            with open("/data/messages.json", "w") as f:
                f.write(json.dumps(messages))

            responses = self.message_generator.chat(messages, self.chat_context.user_id,
                                                        temperature=0,
                                                            max_tokens=4000,
                                                        stream=True, stream_callback=self._token_callback)
            return responses[0].strip()
        except Exception as e:
            raise Exception(f"_generate_message_from_prompt:: {e}")


    def _handle_llm_output(self, llm_output):
        try:
            print("llm_output: ", llm_output)
            self.__manage_response_language_tags(llm_output)
            response = self._manage_response_tags(llm_output)
            return response
        except Exception as e:
            raise Exception(f"_handle_llm_output:: {e}")

    

    ### SPECIFIC METHODS ###
    @abstractmethod
    def _get_message_placeholder(self):
        pass


    def __manage_response_language_tags(self, response):
        try:
            if AssistantResponseGenerator.user_language_start_tag in response:
                try:
                    self.chat_context.state.current_language = AssistantMessageGenerator.remove_tags_from_text(response, AssistantResponseGenerator.user_language_start_tag,
                                                                        AssistantResponseGenerator.user_language_end_tag).lower()
                except Exception as e:
                    print(f"Error while updating language: {e}")
        except Exception as e:
            raise Exception(f"__manage_response_language_tags:: {e}")

    @abstractmethod
    def _manage_response_tags(self, response):
        pass

    @abstractmethod
    def _token_callback(self, partial_text):
        pass