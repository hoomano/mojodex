from abc import ABC, abstractmethod
from jinja2 import Template


class AssistantMessageContext:

    def __init__(self, user):
        self.user = user
        

    @property
    def user_id(self):
        return self.user.user_id
    
    @property
    def username(self):
        return self.user.name
    
class AssistantMessageGenerator(ABC):

    def __init__(self, prompt_template_path, message_generator, tag_proper_nouns, assistant_message_context):
        try:
            self.prompt_template_path = prompt_template_path
            self.message_generator = message_generator
            self.tag_proper_nouns = tag_proper_nouns
            self.context = assistant_message_context
        except Exception as e:
            raise Exception(f"AssistantMessageGenerator :: __init__ :: {e}")

    def remove_tags_from_text(text, start_tag, end_tag):
        try:
            return text.split(start_tag)[1].split(end_tag)[0].strip() if start_tag in text else ""
        except Exception as e:
            raise Exception(f"remove_tags_from_text :: text: {text} - start_tag: {start_tag} - end_tag: {end_tag} - {e}")

    # getter pour template
    @property
    def prompt_template(self):
        if not hasattr(self, '_prompt_template'):
            with open(self.prompt_template_path, 'r') as f:
                self._prompt_template = Template(f.read())
        return self._prompt_template
    

    @abstractmethod
    def _handle_placeholder(self):
        pass

    @abstractmethod
    def _render_prompt_from_template(self):
        pass

    @abstractmethod
    def _generate_message_from_prompt(self, prompt):
        pass

    @abstractmethod
    def _handle_llm_output(self, llm_output):
        pass

    def generate_message(self):
        placeholder = self._handle_placeholder()
        if placeholder:
            return placeholder
        prompt = self._render_prompt_from_template()
        llm_output = self._generate_message_from_prompt(prompt)
        if llm_output:
            return self._handle_llm_output(llm_output)
        return None

    