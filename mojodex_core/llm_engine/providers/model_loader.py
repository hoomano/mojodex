import configparser

from mojodex_core.llm_engine.llm import LLM
from mojodex_core.llm_engine.providers.openai_llm import OpenAILLM
from mojodex_core.llm_engine.providers.mistralai_llm import MistralAILLM
from mojodex_core.llm_engine.providers.ollama_llm import OllamaLLM

import logging
import os

from mojodex_core.llm_engine.providers.openai_vision_llm import OpenAIVisionLLM

logging.basicConfig(level=logging.INFO)


class ModelLoader:
    llm_conf_filename = "models.conf"
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ModelLoader, cls).__new__(
                cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self.__class__._initialized:
            self.providers = self._get_providers()
            self.main_llm: LLM = self.get_main_llm_provider()
            self.main_vision_llm: LLM = self.get_main_vision_llm_provider()
            self.__class__._initialized = True

    def get_main_llm_provider(self):
        """
        Returns the first ModelLoader provider in the models.conf file

        """
        try:
            providers = self._get_llm_providers()

            provider = providers[0]
            _, _, llm, conf = self._build_provider(provider)
            provider_conf = conf
            if len(providers) > 1:
                provider = providers[1]
                _, _, _, conf = self._build_provider(provider)
                llm_backup_conf = conf
            else:
                llm_backup_conf = None

            return type(llm)(provider_conf, llm_backup_conf)

        except Exception as e:
            logging.error(
                f"🔴: ERROR: ModelLoader.get_main_llm_provider() >> {e}")
            return None, None, None

    def get_main_vision_llm_provider(self):
        try:
            provider = None
            model_index = 0
            while provider is None and model_index < len(OpenAIVisionLLM.available_vision_models):
                model=OpenAIVisionLLM.available_vision_models[model_index]
                providers = self._get_providers_by_model(model)
                if len(providers) > 0:
                    provider = providers[0]
                else:
                    model_index += 1
            if provider is None:
                logging.error(
                    f"🔴: ERROR: ModelLoader.get_main_vision_llm_provider() >> No vision provider found")
                return None
            
            _, _, llm, conf = self._build_provider(provider + f'/{model}')
            return type(llm)(conf, None)
        except Exception as e:
            logging.error(
                f"🔴: ERROR: ModelLoader.get_main_vision_llm_provider() >> {e}")
            return None


    def _get_providers(self):
        """
        Returns the list of available LLM providers in the models.conf file

        """
        try:
            llm_providers_list = []
            providers = self._get_llm_providers()

            for provider in providers:
                provider_name, model_name, llm, conf = self._build_provider(
                    provider)
                provider_conf = {
                    "model_name": model_name,
                    "provider_name": provider_name,
                    "provider": llm,
                    "config": conf
                }
                llm_providers_list.append(provider_conf)
              

            return llm_providers_list

        except Exception as e:
            logging.error(
                f"🔴: ERROR: {ModelLoader.__subclasses__()[0].__name__} >> {e}")
            return []

    def _build_provider(self, provider_section):
        """
        Build a provider object from the provider name and model name.
        """
        try:
            # TODO: add smart rules to manage backup engines depending on the configs for each provider
            provider_conf = self._get_llm_provider(provider_section)
            provider_name = provider_section.split('/')[0]
            model_name = provider_section.split('/')[1]
            if model_name is None or provider_name is None:
                logging.error(
                    f"🔴: ERROR: ModelLoader _build_provider() >> in config file {ModelLoader.llm_conf_filename} section __{provider_section}__ provider_name or model_name is missing")
                return None, None, None

            provider = None
            conf = None

            if provider_name == "openai":
                conf = {
                    "api_key": provider_conf["openai_api_key"],
                    "api_type": provider_name,
                    "model_name": model_name
                }
                if model_name in OpenAIVisionLLM.available_vision_models:
                    provider = OpenAIVisionLLM(conf)
                else:
                    provider = OpenAILLM(conf)

            elif provider_name == "azure":
                if model_name == "gpt-4o":
                    conf = {
                        "api_key": provider_conf["gpt4o_azure_openai_key"],
                        "api_base": provider_conf["gpt4o_azure_openai_api_base"],
                        "api_type": provider_name,
                        "api_version": provider_conf["gpt4o_azure_openai_api_version"],
                        "deployment_id": provider_conf["gpt4o_azure_openai_deployment_id"],
                        "model_name": model_name
                    }
                    provider = OpenAILLM(conf)
                elif model_name == "gpt-4o-vision":
                    conf = {
                        "api_key": provider_conf["gpt4o_azure_openai_key"],
                        "api_base": provider_conf["gpt4o_azure_openai_api_base"],
                        "api_type": provider_name,
                        "api_version": provider_conf["gpt4o_azure_openai_api_version"],
                        "deployment_id": provider_conf["gpt4o_azure_openai_deployment_id"],
                        "model_name": model_name
                    }
                    provider = OpenAIVisionLLM(conf)
                
                if model_name == "gpt4-turbo":
                    conf = {
                        "api_key": provider_conf["gpt4_turbo_azure_openai_key"],
                        "api_base": provider_conf["gpt4_turbo_azure_openai_api_base"],
                        "api_type": provider_name,
                        "api_version": provider_conf["gpt4_turbo_azure_openai_api_version"],
                        "deployment_id": provider_conf["gpt4_turbo_azure_openai_deployment_id"],
                        "model_name": model_name
                    }
                    provider = OpenAILLM(conf)
                elif model_name == "gpt4-32k":
                    conf = {
                        "api_key": provider_conf["gpt4_azure_openai_key"],
                        "api_base": provider_conf["gpt4_azure_openai_api_base"],
                        "api_type": provider_name,
                        "api_version": provider_conf["gpt4_azure_openai_api_version"],
                        "deployment_id": provider_conf["gpt4_azure_openai_deployment_id"],
                        "model_name": model_name
                    }
                    provider = OpenAILLM(conf)
                elif model_name == "gpt-4-vision-preview":
                    conf = {
                        "api_key": provider_conf["gpt4_vision_azure_openai_key"],
                        "api_base": provider_conf["gpt4_vision_azure_openai_api_base"],
                        "api_type": provider_name,
                        "api_version": provider_conf["gpt4_vision_azure_openai_api_version"],
                        "deployment_id": provider_conf["gpt4_vision_azure_openai_deployment_id"],
                        "model_name": model_name
                    }
                    provider = OpenAIVisionLLM(conf)
                elif model_name == "mistral-large-latest":
                    conf = {
                        "api_key": provider_conf["mistral_azure_api_key"],
                        "endpoint": provider_conf["mistral_azure_api_base"],
                        "api_model": model_name,
                        "api_type": provider_name,
                        "model_name": model_name
                    }
                    provider = MistralAILLM(conf)

            elif provider_name == "mistral":
                conf = {
                    "api_key": provider_conf["mistral_api_key"],
                    "api_model": model_name,
                    "model_name": model_name
                }
                provider = MistralAILLM(conf)

            elif provider_name == "ollama":
                conf = {
                    "endpoint": provider_conf["ollama_endpoint"],
                    "model": model_name,
                    "model_name": model_name
                }
                provider = OllamaLLM(conf)

            if provider is None:
                logging.error(
                    f"🔴: ERROR: ModelLoader _build_provider() >> in config file {ModelLoader.llm_conf_filename} section __{provider_section}__ provider has not been implemented")

            return provider_name, model_name, provider, conf
        except Exception as e:
            logging.error(f"🔴: ERROR: ModelLoader _build_provider() >> {e}")
            return None, None, None, None

    def _get_llm_provider(self, provider):
        conf_file = os.path.join(os.path.dirname(
            __file__), ModelLoader.llm_conf_filename)
        config = configparser.ConfigParser()
        config.read(conf_file)
        return dict(config[provider])

    def _get_llm_providers(self):
        try:
            conf_file = os.path.join(os.path.dirname(
                __file__), ModelLoader.llm_conf_filename)
            config = configparser.ConfigParser()
            config.read(conf_file)
            return config.sections()
        except Exception as e:
            logging.error(f"🔴: ERROR: ModelLoader get_llm_providersr() >> me")
            return []

    def _get_providers_by_model(self, model):
        """
        Return a list of providers that support the given model.
        The providers are encoded in the sections of the config file as the following format <provider>/<model>
        """
        conf_file = os.path.join(os.path.dirname(
            __file__), ModelLoader.llm_conf_filename)
        config = configparser.ConfigParser()
        config.read(conf_file)
        providers = []
        for section in config.sections():
            provider, model_name = section.split('/')
            if model_name == model:
                providers.append(provider)
        return providers

    def _get_all_models(self):
        """
        Return a list of all models in the config file.
        """
        conf_file = os.path.join(os.path.dirname(
            __file__), ModelLoader.llm_conf_filename)
        config = configparser.ConfigParser()
        config.read(conf_file)
        models = []
        for section in config.sections():
            provider, model_name = section.split('/')
            models.append(model_name)
        return set(models)