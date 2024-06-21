from models.assistant.execution_manager import ExecutionManager
from mojodex_core.llm_engine.mpt import MPT
from mojodex_core.llm_engine.providers.openai_vision_llm import VisionMessagesData
from abc import ABC, abstractmethod
from mojodex_core.llm_engine.providers.model_loader import ModelLoader


class ChatAssistant(ABC):
    language_start_tag, language_end_tag = "<user_language>", "</user_language>"

    @staticmethod
    def remove_tags_from_text(text, start_tag, end_tag):
        """
        Remove tags from text
        :param text: text
        :param start_tag: start tag
        :param end_tag: end tag

        :return: text without tags
        """
        try:
            return text.split(start_tag)[1].split(end_tag)[0].strip() if start_tag in text else ""
        except Exception as e:
            raise Exception(
                f"ChatAssistant: remove_tags_from_text :: text: {text} - start_tag: {start_tag} - end_tag: {end_tag} - {e}")

    def __init__(self, mojo_message_token_stream_callback, draft_token_stream_callback,
                 tag_proper_nouns, user_messages_are_audio, db_session, temperature=0, max_tokens=4000):
        try:

            self.db_session = db_session
            self.execution_manager = ExecutionManager()
            self.tag_proper_nouns = tag_proper_nouns
            self.user_messages_are_audio = user_messages_are_audio
            self.mojo_message_token_stream_callback = mojo_message_token_stream_callback
            self.draft_token_stream_callback = draft_token_stream_callback
            self.default_temperature = temperature
            self.default_max_tokens = max_tokens
            self.language = None

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} __init__ :: {e}")

    @abstractmethod
    def generate_message(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def _mpt(self) -> MPT:
        raise NotImplementedError

    @property
    @abstractmethod
    def requires_vision_llm(self):
        raise NotImplementedError

    @property
    def input_images(self):
        return []

    def _call_llm(self, conversation_list, user_id, session_id, user_task_execution_pk, task_name_for_system,
                  temperature=None, max_tokens=None):
        try:
            temperature = temperature if temperature else self.default_temperature
            max_tokens = max_tokens if max_tokens else self.default_max_tokens
            if self.requires_vision_llm:
                return self.__call_vision_llm(conversation_list, temperature, max_tokens, user_id,
                                              session_id, user_task_execution_pk, task_name_for_system)
            responses = self._mpt.chat(conversation_list, user_id,
                                         temperature=temperature,
                                         max_tokens=max_tokens,
                                         stream=True, stream_callback=self._token_callback,
                                         user_task_execution_pk=user_task_execution_pk,
                                         task_name_for_system=task_name_for_system)

            return responses[0].strip() if responses else None
        except Exception as e:
            raise Exception(f"_call_llm :: {e}")

    def __call_vision_llm(self, conversation_list, temperature, max_tokens, user_id, session_id,
                          user_task_execution_pk, task_name_for_system):
        try:
            from mojodex_core.user_storage_manager.user_images_file_manager import UserImagesFileManager
            user_image_file_manager = UserImagesFileManager()
            initial_system_message_data = [VisionMessagesData(role="system", text=self._mpt.prompt, images_path=[
                user_image_file_manager.get_image_file_path(image, user_id, session_id)
                for image in self.input_images])]
            conversation_messages_data = [
                VisionMessagesData(role=message["role"], text=message["content"], images_path=[]) for message in
                conversation_list]
            messages_data = initial_system_message_data + conversation_messages_data
            responses = ModelLoader().main_vision_llm.invoke(messages_data, user_id,
                                                            temperature=temperature,
                                                            max_tokens=max_tokens,
                                                            label=self._mpt.label,
                                                            stream=True, stream_callback=self._token_callback,
                                                            user_task_execution_pk=user_task_execution_pk,
                                                            task_name_for_system=task_name_for_system)
            return responses[0].strip() if responses else None
        except Exception as e:
            raise Exception(f"__call_vision_llm:: {e}")

    @abstractmethod
    def _token_callback(self, partial_text):
        raise NotImplementedError

    def _handle_llm_output(self, llm_output):
        try:
            self._manage_response_language_tags(llm_output)
            response = self._manage_response_tags(llm_output)
            return response
        except Exception as e:
            raise Exception(f"_handle_llm_output:: {e}")

    def _manage_response_language_tags(self, response):
        """
        Remove language tags from the response and update the language in the context
        :param response: response
        """
        try:
            if self.language_start_tag in response:
                try:
                    self.language = self.remove_tags_from_text(response,
                                                               self.language_start_tag,
                                                               self.language_end_tag).lower()
                except Exception as e:
                    pass
        except Exception as e:
            raise Exception(f"__manage_response_language_tags:: {e}")

    def _manage_execution_tags(self, response):
        try:
            if ExecutionManager.execution_start_tag in response:
                return self.execution_manager.manage_execution_text(response)
        except Exception as e:
            raise Exception(f"_manage_execution_tags :: {e}")

    @abstractmethod
    def _manage_response_tags(self, response):
        raise NotImplementedError
