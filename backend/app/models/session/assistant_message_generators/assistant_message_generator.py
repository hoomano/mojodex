from abc import ABC, abstractmethod
from jinja2 import Template

class AssistantMessageGenerator(ABC):
    """
    Abstract class for generating messages from the assistant
    """
    logger_prefix = "AssistantMessageGenerator :: "

    def __init__(self, prompt_template_path, tag_proper_nouns, assistant_message_context):
        """
        Constructor for AssistantMessageGenerator
        :param prompt_template_path: path to the prompt template
        :param message_generator: message generator
        :param tag_proper_nouns: whether to tag proper nouns
        :param assistant_message_context: context for the assistant message"""
        try:
            self.prompt_template_path = prompt_template_path
            self.tag_proper_nouns = tag_proper_nouns
            self.context = assistant_message_context
        except Exception as e:
            raise Exception(f"{AssistantMessageGenerator.logger_prefix} __init__ :: {e}")

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
            raise Exception(f"{AssistantMessageGenerator.logger_prefix} remove_tags_from_text :: text: {text} - start_tag: {start_tag} - end_tag: {end_tag} - {e}")

    # getter pour template
    @property
    def prompt_template(self):
        """
        Get the jinja prompt template
        :return: jinja prompt template"""
        try:
            if not hasattr(self, '_prompt_template'):
                with open(self.prompt_template_path, 'r') as f:
                    self._prompt_template = Template(f.read())
            return self._prompt_template
        except Exception as e:
            raise Exception(f"{AssistantMessageGenerator.logger_prefix} prompt_template :: {e}")
    

    @abstractmethod
    def _handle_placeholder(self):
        """
        Handle the placeholder
        :return: placeholder if required, None otherwise"""
        raise NotImplementedError

    @abstractmethod
    def _render_prompt_from_template(self):
        """
        Render the prompt from the template
        :return: rendered prompt from the template"""
        raise NotImplementedError

    @abstractmethod
    def _generate_message_from_prompt(self, prompt):
        """
        Generate a message from the prompt
        :param prompt: prompt
        :return: message from the prompt"""
        raise NotImplementedError

    @abstractmethod
    def _handle_llm_output(self, llm_output):
        """
        Handle the llm output
        :param llm_output: llm output
        :return: handled llm output"""
        raise NotImplementedError

    def generate_message(self):
        """
        Generate a message from the assistant
        :return: message from the assistant"""
        try:
            placeholder = self._handle_placeholder()
            if placeholder:
                return placeholder
            prompt = self._render_prompt_from_template()
            llm_output = self._generate_message_from_prompt(prompt)
            if llm_output:
                return self._handle_llm_output(llm_output)
            return None
        except Exception as e:
            raise Exception(f"{AssistantMessageGenerator.logger_prefix} generate_message :: {e}")

    