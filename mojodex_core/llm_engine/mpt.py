from typing import List, Any

import jinja2
import re

from mojodex_core.llm_engine.llm import LLM

from mojodex_core.logging_handler import MojodexCoreLogger


class MPT:
    """
    The MPT class represents a Mojodex Prompt Template.
    See the Mojodex Prompt Template (MPT) documentation for more details.
    https://hoomano.github.io/mojodex/technical-architecture/llm-features/mpt/

    Attributes:
        filepath (str): The filepath of the MPT file.
        shebangs (list): A list of shebangs found in the MPT file.
        template (jinja2.Template): The Jinja2 template object representing the MPT file.
        models (list): Returns a list of model names extracted from the shebangs.
        tags (list): Returns a list of tags extracted from the template.
        template_values (list): Returns a list of jinja2 values extracted from the template.
        prompt (str): Returns the rendered prompt using the provided keyword arguments.

    Methods:
        _parse_file(): Parses the MPT file and extracts shebangs and template.
        _perform_templating(**kwargs): Performs templating using the provided keyword arguments.
    """

    def __init__(self, filepath, forced_model=None, **kwargs):
        self.logger = MojodexCoreLogger(
            f"MPT - {filepath}")
        self.filepath = filepath

        try:
            from mojodex_core.llm_engine.providers.model_loader import ModelLoader
            self.available_models, _ = ModelLoader().providers
        except Exception as e:
            self.logger.debug(
                f"{self.filepath} > available_models loading: {e}")
            self.available_models = None

        if forced_model is not None and self.available_models is not None:
            for provider in self.available_models:
                if provider['model_name'] == forced_model:
                    self.forced_model: LLM = provider['provider']
                    self.logger.info(f"Forced model: {forced_model}")
                    break
            if self.forced_model is None:
                self.logger.info(f"Forced model not found: {forced_model}")
        else:
            self.forced_model = None

        # store the other arguments for later use
        self.kwargs = kwargs
        self.shebangs = []
        self.template = None
        self.raw_template = None
        self._parse_file()

        # TODO: move import to the top
        from mojodex_core.llm_engine.providers.model_loader import ModelLoader
        self.available_models, _ = ModelLoader().providers
        self.models = [d['model_name'] for d in self.shebangs]

    @property
    def tags(self):
        """
        Extracts tags from the template.
        Tags are in the format: <tag_name>

        Returns:
            list: A list of tags extracted from the template.
        """
        return re.findall(r'(<[^>]*>)', self.raw_template)

    @property
    def template_values(self):
        """
        Extracts jinja2 values from the template.
        Jinja2 values are in the format: {{ value }}

        Returns:
            list: A list of jinja2 values extracted from the template.
        """
        return list(set(re.findall(r'{{([^}]*)}}', self.raw_template)))

    @property
    def prompt(self):
        """
        Returns the rendered prompt using the provided keyword arguments.

        Args:
            **kwargs: Keyword arguments to be used for templating.

        Returns:
            str: The rendered prompt.
        """

        if self.forced_model is not None:
            self.logger.info(
                f"Prompt template resolved with forced_model: {self.forced_model.name}")
            return self._perform_templating(**self.kwargs, model=self.forced_model)
        elif self.matching_model is not None:
            return self._perform_templating(**self.kwargs, model=self.matching_model.name)
        else:
            return self._perform_templating(**self.kwargs)

    @property
    def matching_model(self) -> LLM:
        # return the first available model matching with the shebangs
        try:
            selected_model = None
            for model in self.models:
                for provider in self.available_models:
                    if provider['model_name'] == model:
                        selected_model = provider['provider']
                        break

                if selected_model is not None:
                    break

            return selected_model
        except Exception as e:
            self.logger.error(f"Error finding matching model: {e}")
            return None

    def _parse_file(self):
        """
        Parses the MPT file and extracts shebangs and template.
        """
        try:
            with open(self.filepath, 'r') as file:
                lines = file.readlines()
                i = 0
                # find all the shebangs and get their values
                while lines[i].startswith("#!"):
                    shebang = lines[i].strip()
                    match = re.search(r'#!\s*([^/]*)/?([^/]*)?', shebang)
                    if match is not None:
                        model_name, version = match.groups()
                        self.shebangs.append({
                            'model_name': model_name,
                            'version': version if version else 'latest'
                        })
                    else:
                        raise ValueError(
                            f"Invalid shebang: {shebang}\nFormat: #! model_name(/version)")
                    i += 1
                # find the first non empty line after shebangs
                while not lines[i].strip():
                    i += 1
                # remove all the empty lines at the end of the file
                while not lines[-1].strip():
                    lines.pop()

                self.raw_template = ''.join(lines[i:])
                self.template = jinja2.Template(self.raw_template)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {self.filepath}")
        except Exception as e:
            raise Exception(f"Error parsing file: {self.filepath} - {e}")

    def _perform_templating(self, **kwargs):
        """
        Performs templating using the provided keyword arguments.

        Args:
            **kwargs: Keyword arguments to be used for templating.

        Returns:
            str: The rendered template.
        """
        # if one of the args is of type MPT, call its prompt method
        for k, v in kwargs.items():
            if isinstance(v, MPT):
                kwargs[k] = v.prompt
                # also retrieve the models from the MPT and choose the common model with the current MPT
                self.models = list(set(self.models).intersection(v.models))

        try:
            return self.template.render(**kwargs)
        except Exception as e:
            self.logger.error(f"Error performing templating: {e}")
            self.logger.error(
                f"Check that you passed all the template values: {self.template_values}")
            return None

    def __str__(self):
        """
        Returns a string representation of the MPT object.

        Returns:
            str: A string representation of the MPT object.
        """
        return f"MPT: {self.filepath}"

    @property
    def label(self):
        return self.filepath.split('/')[-1].split('.')[0]

    def _run(self, messages: List[Any], user_id: str, temperature: float, max_tokens: int, stream: bool = False,
             stream_callback=None, user_task_execution_pk: int = None, task_name_for_system: str = None, **kwargs):
        """
        Call appropriate LLM model with given list of messages.

        Returns:
            str: The result of the LLM call.
        """
        try:
            # for each model in the shebangs, in order, check if there is a provider for it
            # if there is, call it with the prompt
            if self.forced_model is not None:
                self.logger.info(f"Running prompt with forced model: {self.forced_model.name}")
                model = self.forced_model
            elif self.matching_model is not None:
                model = self.matching_model
            else:
                raise Exception(f"""{self} > No matching provider <> model found:
providers: {self.available_models}
MPT's compatibility list: {self.models}
To fix the problem:
1. Check the providers in the models.conf file.
2. Check the MPT file's shebangs for compatibility with the providers.""")
            if model.name not in self.models:
                self.logger.warning(f"{self} does not contain model: {model.name} in its dashbangs")

            return model.invoke(messages, user_id, temperature,
                                max_tokens, label=self.label,
                                stream=stream, stream_callback=stream_callback,
                                user_task_execution_pk=user_task_execution_pk,
                                task_name_for_system=task_name_for_system, **kwargs)
        except Exception as e:
            raise Exception(f"_run : {e}")

    def run(self, user_id: str, temperature: float, max_tokens: int, stream: bool = False,
            stream_callback=None, user_task_execution_pk: int = None, task_name_for_system: str = None, **kwargs):
        """
        Call appropriate LLM model with prompt as single "user" (role) message to simulate instruct model.

        Returns:
            str: The result of the LLM call.
        """
        try:
            return self._run([{"role": "user", "content": self.prompt}], user_id, temperature, max_tokens, stream,
                             stream_callback, user_task_execution_pk, task_name_for_system, **kwargs)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} - {self} :: run: {e}")

    def chat(self, conversation: List[Any], user_id: str, temperature: float, max_tokens: int, stream: bool = False,
             stream_callback=None, user_task_execution_pk: int = None, task_name_for_system: str = None, **kwargs):
        """
        Call appropriate LLM model with messages made of :
            - prompt as first system message
            - messages from conversation between user and assistant as following messages

        Returns:
            str: The result of the LLM call.
        """
        try:
            first_system_message = {"role": "system", "content": self.prompt}
            # Note: on Mistral, if there is only first_system_message, this role will be changed to "user" by the LLM_engine
            return self._run([first_system_message] + conversation, user_id, temperature, max_tokens, stream,
                             stream_callback, user_task_execution_pk, task_name_for_system, **kwargs)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} - {self} :: chat: {e}")
