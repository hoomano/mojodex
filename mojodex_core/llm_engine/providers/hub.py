
from langchain_core.language_models import BaseLanguageModel

# Definition of all the available models: "gpt-4-turbo", "gpt4-32k", "mistral-tiny"
GPT4_TURBO = "gpt-4-turbo"
GPT4_32k = "gpt4-32k"
MISTRAL_TINY = "mistral-tiny"


class LLMProvider:
    def __init__(self, model_name, base_model: BaseLanguageModel) -> None:
        self.model_name = model_name
        self.base_model = base_model
        pass

class LLMProviderHub:
    def __init__(self):
        self.available = []
        self._init_providers()

    def add(self, model: LLMProvider):
        self.available.append(model)

    def first(self, model_name: str):
        # if at least one llmmodel with the name model_name is available, return the first one
        if any([model.model_name == model_name for model in self.available]):
            return next(model for model in self.available if model.model_name == model_name).base_model
        else:
            raise Exception(f"No provider available for model {model_name}")

    def all(self):
        return self.providers
        
    def _init_providers(self):
        # initialize providers from environment variables
        from providers.mojodex_azure_openai import azure_list
        from providers.mojodex_openai import openai_list
        from providers.mojodex_mistral import mistral_list
        self.available.extend(azure_list)
        self.available.extend(openai_list)
        self.available.extend(mistral_list)

    def __str__(self) -> str:
        # print model_name and base_model for each provider
        return "\n".join([f"{model.model_name} - {model.base_model}" for model in self.available])