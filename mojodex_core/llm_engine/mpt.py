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
        
        if forced_model is not None:
            for provider in self.available_models:
                if provider['model_name'] == forced_model:
                    self.forced_model : LLM = provider['provider']
                    self.logger.info(f"Forced model: {forced_model}")
                    break

        # store the other arguments for later use
        self.kwargs = kwargs
        self.shebangs = []
        self.template = None
        self.raw_template = None
        self._parse_file()

        self.available_models, _ = LLM.get_providers()
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
        return self._perform_templating(**self.kwargs)


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
                        raise ValueError(f"Invalid shebang: {shebang}\nFormat: #! model_name(/version)")
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

        return self.template.render(**kwargs)


    def __str__(self):
        """
        Returns a string representation of the MPT object.

        Returns:
            str: A string representation of the MPT object.
        """
        return f"MPT: {self.filepath}"
    
    def run(self, **kwargs):
        """
        Run the prompt to the appropriate model.

        Returns:
            str: The result of the LLM call.
        """

        # for each model in the shebangs, in order, check if there is a provider for it
        # if there is, call it with the prompt

        if self.forced_model is not None:
            self.logger.info(f"Running prompt with forced model: {self.forced_model}")
            return self.forced_model.invoke_from_mpt(self, **kwargs)

        selected_model : LLM = None
        for model in self.models:
            # TODO: how to use version in provider selection / configuration?
            #version = shebang['version']
            for provider in self.available_models:
                if provider['model_name'] == model:
                    selected_model = provider['provider']
                    self.logger.debug(f"Selected model: {model}")
                    break
            
            if selected_model is not None:
                break

        if selected_model is None:
            raise Exception(f"No provider found for model: {model}")
        
        # put a reference to the execution with the filepath of the MPT instruction
        # label is the filename without the file extension
        selected_model.label = self.filepath.split('/')[-1].split('.')[0]
        
        return selected_model.invoke_from_mpt(self, **kwargs)
