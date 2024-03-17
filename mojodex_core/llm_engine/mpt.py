import jinja2
import re
import logging

from mojodex_core.llm_engine.llm import LLM

class MPT:
    """
    The MPT class represents a Mojodex Prompt Template.
    See the Mojodex Prompt Template (MPT) documentation for more details.
    https://hoomano.github.io/mojodex/technical-architecture/llm-features/mpt/

    Attributes:
        filepath (str): The filepath of the MPT file.
        dashbangs (list): A list of dashbangs found in the MPT file.
        template (jinja2.Template): The Jinja2 template object representing the MPT file.
        models (list): Returns a list of model names extracted from the dashbangs.
        tags (list): Returns a list of tags extracted from the template.
        template_values (list): Returns a list of jinja2 values extracted from the template.
        prompt (str): Returns the rendered prompt using the provided keyword arguments.

    Methods:
        _parse_file(): Parses the MPT file and extracts dashbangs and template.
        _perform_templating(**kwargs): Performs templating using the provided keyword arguments.
    """

    def __init__(self, filepath, **kwargs):
        self.filepath = filepath
        # store the other arguments for later use
        self.kwargs = kwargs
        self.dashbangs = []
        self.template = None
        self.raw_template = None
        self._parse_file()

        self.available_models = LLM.get_providers()

    @property
    def models(self):
        return [d['model_name'] for d in self.dashbangs]
    
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
        # check if all the required values are provided
        if not all(k in self.kwargs for k in self.template_values):
            # find the missing values
            missing_values = [v for v in self.template_values if v not in self.kwargs]
            logging.warning(f"{self}\nError generating prompt, expecting values: {self.template_values}\nMissing: {missing_values}")
        return self._perform_templating(**self.kwargs)


    def _parse_file(self):
        """
        Parses the MPT file and extracts dashbangs and template.
        """
        try:
            with open(self.filepath, 'r') as file:
                lines = file.readlines()
                i = 0
                # find all the dashbangs and get their values
                while lines[i].startswith("#!"):
                    dashbang = lines[i].strip()
                    match = re.search(r'#!\s*([^/]*)/?([^/]*)?', dashbang)
                    if match is not None:
                        model_name, version = match.groups()
                        self.dashbangs.append({
                            'model_name': model_name,
                            'version': version if version else 'latest'
                        })
                    else:
                        raise ValueError(f"Invalid dashbang: {dashbang}\nFormat: #! model_name(/version)")
                    i += 1
                # find the first non empty line after dashbangs
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

        selected_model : LLM = None
        for model in self.models:
            # TODO: how to use version in provider selection / configuration?
            #version = dashbang['version']
            for provider in self.available_models:
                if provider['model_name'] == model:
                    selected_model = provider['provider']
                    break

            if selected_model is None:
                raise Exception(f"No provider found for model: {model}")
        
        return selected_model.invoke_from_mpt(self, **kwargs)
