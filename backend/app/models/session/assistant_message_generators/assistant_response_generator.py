from models.session.assistant_message_generators.assistant_message_generator import AssistantMessageGenerator
from abc import ABC, abstractmethod

class AssistantResponseGenerator(AssistantMessageGenerator, ABC):
    """
    Abstract class for generating responses from the assistant within the context of a conversation
    """

    user_language_start_tag, user_language_end_tag = "<user_language>",  "</user_language>"

    def __init__(self, prompt_template_path, message_generator, chat_context, use_message_placeholder, use_draft_placeholder, tag_proper_nouns, llm_call_temperature):
        """
        Constructor for AssistantResponseGenerator
        :param prompt_template_path: path to the prompt template
        :param message_generator: message generator
        :param chat_context: context for the assistant message
        :param use_message_placeholder: whether to use the message placeholder
        :param use_draft_placeholder: whether to use the draft placeholder
        :param tag_proper_nouns: whether to tag proper nouns
        :param llm_call_temperature: temperature for the LLM call
        """
        try:
            self.use_message_placeholder = use_message_placeholder
            self.use_draft_placeholder = use_draft_placeholder
            self.llm_call_temperature = llm_call_temperature
            super().__init__(prompt_template_path, message_generator, tag_proper_nouns, chat_context)
        except Exception as e:
            raise Exception(f"AssistantResponseGenerator :: __init__ :: {e}")


    def _generate_message_from_prompt(self, prompt):
        """
        Generate a message from a prompt by calling the message generator
        :param prompt: prompt
        :return: generated message
        """
        try:
            conversation_list = self.context.state.get_conversation_as_list(self.context.session_id)
            messages = [{"role": "system", "content": prompt}] + conversation_list

            responses = self.message_generator.chat(messages, self.context.user_id,
                                                        temperature=0,
                                                        max_tokens=4000,
                                                        stream=True, stream_callback=self._token_callback)

            return responses[0].strip() if responses else None
        except Exception as e:
            raise Exception(f"_generate_message_from_prompt:: {e}")


    def _handle_llm_output(self, llm_output):
        """
        Handle the output from the LLM by removing and managing response tags
        :param llm_output: output from the LLM
        :return: response without tags
        """
        try:
            self.__manage_response_language_tags(llm_output)
            response = self._manage_response_tags(llm_output)
            return response
        except Exception as e:
            raise Exception(f"_handle_llm_output:: {e}")

    

    ### SPECIFIC METHODS ###
    @abstractmethod
    def _get_message_placeholder(self):
        """
        Get the message placeholder
        """
        raise NotImplementedError


    def __manage_response_language_tags(self, response):
        """
        Remove language tags from the response and update the language in the context
        :param response: response
        """
        try:
            if AssistantResponseGenerator.user_language_start_tag in response:
                try:
                    self.context.state.current_language = AssistantMessageGenerator.remove_tags_from_text(response, AssistantResponseGenerator.user_language_start_tag,
                                                                        AssistantResponseGenerator.user_language_end_tag).lower()
                except Exception as e:
                    pass
        except Exception as e:
            raise Exception(f"__manage_response_language_tags:: {e}")

    @abstractmethod
    def _manage_response_tags(self, response):
        """
        Remove and managed tags from the response
        """
        raise NotImplementedError

    @abstractmethod
    def _token_callback(self, partial_text):
        """
        Stream callback for the message generator
        :param partial_text: partial text
        """
        raise NotImplementedError