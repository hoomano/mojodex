import configparser

from mojodex_core.llm_engine.providers.openai_embedding import OpenAIEmbedding
from mojodex_core.llm_engine.providers.openai_llm import OpenAILLM
from mojodex_core.llm_engine.providers.mistralai_llm import MistralAILLM

import logging
import os

logging.basicConfig(level=logging.INFO)

class ModelLoader:
    llm_conf_filename = "models.conf"


    @staticmethod
    def get_main_llm_provider():
        
        """
        Returns the first ModelLoader provider in the models.conf file

        """
        try:
            providers = ModelLoader._get_llm_providers()

            # keep only the providers with name different from OpenAIEmbedding.default_embedding_model
            providers = [provider for provider in providers if provider.split('/')[1] != OpenAIEmbedding.default_embedding_model]

            provider = providers[0]
            _, _, llm, conf = ModelLoader._build_provider(provider)
            provider_conf = conf
            if len(providers) > 1:
                provider = providers[1]
                _, _, llm, conf = ModelLoader._build_provider(provider)
                llm_backup_conf = conf
            else:
                llm_backup_conf = None

            return type(llm), provider_conf, llm_backup_conf

        except Exception as e:
            logging.error(f"🔴: ERROR: ModelLoader.get_main_llm_provider() >> {e}")
            return None, None, None


    @staticmethod
    def get_embedding_provider():
        """
        Get the Embedding Provider.

        Returns:
            The Embedding Provider based on the configuration file `LLM.llm_conf_filename`.
        """
        _, embedding_providers = ModelLoader.get_providers()

        # find the embedding provider in the list of providers with model_name = 'embedding'
        if len(embedding_providers) == 0:
            raise Exception("No embedding provider found in the providers list")
        return type(embedding_providers[0]['provider']), embedding_providers[0]['config']        
        
    
    @staticmethod
    def get_providers():
        """
        Returns the list of available LLM & Embedding providers in the models.conf file

        """
        try:
            llm_providers_list = []
            embedding_providers_list = []
            providers = ModelLoader._get_llm_providers()

            for provider in providers:
                provider_name, model_name, llm, conf = ModelLoader._build_provider(provider)
                provider_conf = {
                    "model_name": model_name,
                    "provider_name": provider_name,
                    "provider": llm,
                    "config": conf
                }
                if model_name != OpenAIEmbedding.default_embedding_model:
                    llm_providers_list.append(provider_conf)
                else:
                    embedding_providers_list.append(provider_conf)

            return llm_providers_list, embedding_providers_list

        except Exception as e:
            logging.error(f"🔴: ERROR: {ModelLoader.__subclasses__()[0].__name__} >> {e}")
            return []

    def _build_provider(provider_section):
        """
        Build a provider object from the provider name and model name.
        """
        try:
            # TODO: add smart rules to manage backup engines depending on the configs for each provider
            provider_conf = ModelLoader._get_llm_provider(provider_section)
            provider_name = provider_section.split('/')[0]
            model_name = provider_section.split('/')[1]
            if model_name is None or provider_name is None:
                logging.error(f"🔴: ERROR: ModelLoader _build_provider() >> in config file {ModelLoader.llm_conf_filename} section __{provider_section}__ provider_name or model_name is missing")
                return None, None, None
            
            provider:ModelLoader = None
            conf = None

            if provider_name == "openai":
                conf = {
                    "api_key": provider_conf["openai_api_key"],
                    "api_type": provider_name,
                    "model": model_name
                }
                if model_name == OpenAIEmbedding.default_embedding_model:                    
                    provider = OpenAIEmbedding(conf)
                else:
                    provider = OpenAILLM(conf)
            
            elif provider_name == "azure":
                if model_name == "gpt4-turbo":
                    conf = {
                        "api_key": provider_conf["gpt4_turbo_azure_openai_key"],
                        "api_base": provider_conf["gpt4_turbo_azure_openai_api_base"],
                        "api_type": provider_name,
                        "api_version": provider_conf["gpt4_turbo_azure_openai_api_version"],
                        "deployment_id": provider_conf["gpt4_turbo_azure_openai_deployment_id"]
                    }
                    provider = OpenAILLM(conf)
                elif model_name == "gpt4-32k":
                    conf = {
                        "api_key": provider_conf["gpt4_azure_openai_key"],
                        "api_base": provider_conf["gpt4_azure_openai_api_base"],
                        "api_type": provider_name,
                        "api_version": provider_conf["gpt4_azure_openai_api_version"],
                        "deployment_id": provider_conf["gpt4_azure_openai_deployment_id"]
                    }
                    provider = OpenAILLM(conf)
                elif model_name == "mistral-large":
                    conf = {
                        "api_key": provider_conf["mistral_azure_api_key"],
                        "endpoint": provider_conf["mistral_azure_api_base"],
                        "api_model": model_name,
                        "api_type": provider_name
                    }
                    provider = MistralAILLM(conf)
                
                # TODO: migrate to new embedding v3 
                elif model_name == "embedding":
                    conf = {
                        "api_key": provider_conf["ada_embedding_azure_openai_key"],
                        "api_base": provider_conf["ada_embedding_azure_openai_api_base"],
                        "api_type": provider_name,
                        "api_version": provider_conf["ada_embedding_azure_openai_api_version"],
                        "deployment_id": provider_conf["ada_embedding_azure_openai_deployment_id"] if not provider_conf["ada_embedding_azure_openai_deployment_id"] is None else OpenAIEmbedding.default_embedding_model,
                    }
                    provider = OpenAIEmbedding(conf)

            elif provider_name == "mistral":
                conf = {
                    "api_key": provider_conf["mistral_api_key"],
                    "api_model": model_name
                }
                provider = MistralAILLM(conf)
            
            if provider is None:
                logging.error(f"🔴: ERROR: ModelLoader _build_provider() >> in config file {ModelLoader.llm_conf_filename} section __{provider_section}__ provider has not been implemented")
                
            return provider_name, model_name, provider, conf
        except Exception as e:
            logging.error(f"🔴: ERROR: ModelLoader _build_provider() >> {e}")
            return None, None, None, None
    
    def _get_llm_provider(provider):
        conf_file = os.path.join(os.path.dirname(__file__), ModelLoader.llm_conf_filename)
        config = configparser.ConfigParser()
        config.read(conf_file)
        return dict(config[provider])

    def _get_llm_providers():
        try:
            conf_file = os.path.join(os.path.dirname(__file__), ModelLoader.llm_conf_filename)
            logging.info(f">>>>> confile: {conf_file}")
            config = configparser.ConfigParser()
            config.read(conf_file)
            logging.info(f">>>>> Sections in conf: {config.sections()}")
            return config.sections()
        except Exception as e:
            logging.error(f"🔴: ERROR: ModelLoader _get_llm_providers() >> {e}")
            return []
    
    def _get_providers_by_model(model):
        """
        Return a list of providers that support the given model.
        The providers are encoded in the sections of the config file as the following format <provider>/<model>
        """
        conf_file = os.path.join(os.path.dirname(__file__), ModelLoader.llm_conf_filename)
        config = configparser.ConfigParser()
        config.read(conf_file)
        providers = []
        for section in config.sections():
            provider, model_name = section.split('/')
            if model_name == model:
                providers.append(provider)
        return providers


    def _get_all_models():
        """
        Return a list of all models in the config file.
        """
        conf_file = os.path.join(os.path.dirname(__file__), ModelLoader.llm_conf_filename)
        config = configparser.ConfigParser()
        config.read(conf_file)
        models = []
        for section in config.sections():
            provider, model_name = section.split('/')
            models.append(model_name)
        return set(models)
