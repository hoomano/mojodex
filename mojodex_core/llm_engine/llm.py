from abc import ABC, abstractmethod
import json
import logging
import os

logging.basicConfig(level=logging.INFO)

import configparser

class LLM(ABC):
    """
    Abstract base class for LLM (Language Model) implementations.
    """

    dataset_dir = "/data/prompts_dataset"

    llm_conf_filename = "llm.conf"

    @staticmethod
    def get_main_llm_provider():
        
        
        """
        Returns the first LLM provider in the llm.conf file

        """
        try:
            logging.info(f"🟢: INFO: LLM get_main_llm_provider()")
            providers = LLM._get_llm_providers()
            logging.info(f"🟢: INFO: {providers}")

            provider = providers[0]
            provider_name, model_name, llm, conf = LLM._build_provider(provider)
            provider_conf = conf
            if len(providers) > 1:
                provider = providers[1]
                provider_name, model_name, llm, conf = LLM._build_provider(provider)
                llm_backup_conf = conf
            else:
                llm_backup_conf = None

            return type(llm), provider_conf, llm_backup_conf

        except Exception as e:
            logging.error(f"🔴: ERROR: LLM.get_main_llm_provider() >> {e}")
            return None, None, None

    
    @staticmethod
    def get_providers():
        """
        Returns the list of available LLM providers in the llm.conf file

        """
        try:
            providers_list = []
            providers = LLM._get_llm_providers()

            for provider in providers:
                provider_name, model_name, llm = LLM._build_provider(provider)
                provider_conf = {
                    "model_name": model_name,
                    "provider_name": provider_name,
                    "provider": llm
                }
                logging.info(f"🟢: INFO: LLM get_providers() >> provider_conf: {provider_conf}")
                providers_list.append(provider_conf)

            return providers_list

        except Exception as e:
            logging.error(f"🔴: ERROR: {LLM.__subclasses__()[0].__name__} >> {e}")
            return []

    def _build_provider(provider_section):
        """
        Build a provider object from the provider name and model name.
        """
        try:
            # TODO: add smart rules to manage backup engines depending on the configs for each provider
            provider_conf = LLM._get_llm_provider(provider_section)
            provider_name = provider_section.split('/')[0]
            model_name = provider_section.split('/')[1]
            if model_name is None or provider_name is None:
                logging.error(f"🔴: ERROR: LLM _build_provider() >> in config file {LLM.llm_conf_filename} section __{provider_section}__ provider_name or model_name is missing")
                return None, None, None
            
            provider:LLM = None
            conf = None

            if provider_name == "openai":
                from mojodex_core.llm_engine.providers.openai_llm import OpenAILLM
                conf = {
                    "api_key": provider_conf["openai_api_key"],
                    "api_type": provider_name
                }
                provider = OpenAILLM(conf)
            
            elif provider_name == "azure":
                if model_name == "gpt4-turbo":
                    from mojodex_core.llm_engine.providers.openai_llm import OpenAILLM
                    conf = {
                        "api_key": provider_conf["gpt4_turbo_azure_openai_key"],
                        "api_base": provider_conf["gpt4_turbo_azure_openai_api_base"],
                        "api_type": provider_name,
                        "api_version": provider_conf["gpt4_turbo_azure_openai_api_version"],
                        "deployment_id": provider_conf["gpt4_turbo_azure_openai_deployment_id"]
                    }
                    provider = OpenAILLM(conf)
                elif model_name == "gpt4-32k":
                    from mojodex_core.llm_engine.providers.openai_llm import OpenAILLM
                    conf = {
                        "api_key": provider_conf["gpt4_azure_openai_key"],
                        "api_base": provider_conf["gpt4_azure_openai_api_base"],
                        "api_type": provider_name,
                        "api_version": provider_conf["gpt4_azure_openai_api_version"],
                        "deployment_id": provider_conf["gpt4_azure_openai_deployment_id"]
                    }
                    provider = OpenAILLM(conf)
                elif model_name == "mistral-large":
                    from mojodex_core.llm_engine.providers.mistralai_llm import MistralAILLM
                    conf = {
                        "api_key": provider_conf["mistral_azure_api_key"],
                        "endpoint": provider_conf["mistral_azure_api_base"],
                        "api_model": model_name,
                        "api_type": provider_name
                    }
                    provider = MistralAILLM(conf)

            elif provider_name == "mistral":
                from mojodex_core.llm_engine.providers.mistralai_llm import MistralAILLM
                conf = {
                    "api_key": provider_conf["mistral_api_key"],
                    "api_model": model_name
                }
                provider = MistralAILLM(conf)
            
            if provider is None:
                logging.error(f"🔴: ERROR: LLM _build_provider() >> in config file {LLM.llm_conf_filename} section __{provider_section}__ provider has not been implemented")
                
            return provider_name, model_name, provider, conf
        except Exception as e:
            logging.error(f"🔴: ERROR: LLM _build_provider() >> {e}")
            return None, None, None, None
    
    def _get_llm_provider(provider):
        conf_file = os.path.join(os.path.dirname(__file__), LLM.llm_conf_filename)
        config = configparser.ConfigParser()
        config.read(conf_file)
        return dict(config[provider])

    def _get_llm_providers():
        try:
            conf_file = os.path.join(os.path.dirname(__file__), LLM.llm_conf_filename)
            config = configparser.ConfigParser()
            config.read(conf_file)
            return config.sections()
        except Exception as e:
            logging.error(f"🔴: ERROR: LLM _get_llm_providers() >> {e}")
            return []
    
    def _get_providers_by_model(model):
        """
        Return a list of providers that support the given model.
        The providers are encoded in the sections of the config file as the following format <provider>/<model>
        """
        conf_file = os.path.join(os.path.dirname(__file__), LLM.llm_conf_filename)
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
        conf_file = os.path.join(os.path.dirname(__file__), LLM.llm_conf_filename)
        config = configparser.ConfigParser()
        config.read(conf_file)
        models = []
        for section in config.sections():
            provider, model_name = section.split('/')
            models.append(model_name)
        return set(models)

    @abstractmethod
    def __init__(self, llm_conf, llm_backup_conf=None, label='undefined', max_retries=0):
        """
        Initializes the LLM object.

        Args:
            llm_conf (dict): The configuration for the LLM.
            llm_backup_conf (dict, optional): The configuration for the backup LLM to manage rate limits. Defaults to None.
            label (str): The label of the task.
            max_retries (int, optional): The maximum number of retries. Defaults to 0.
        """
        pass

    def num_tokens_from_messages(self, string):
        """
        Abstract method that should be implemented to return the number of tokens from a given string of messages.
        """
        pass


    @abstractmethod
    def invoke(self, messages, user_id, temperature, max_tokens, user_task_execution_pk, task_name_for_system):
        """
        Perform a LLM chat completion.

        Args:
            messages (list): List of messages.
            user_id (str): ID of the current user.
            temperature (float): Temperature parameter for generating responses.
            max_tokens (int): Maximum number of tokens in the generated response.
            user_task_execution_pk (int): Primary key of the user task execution.
            task_name_for_system (str): Name of the task for the system.

        Returns:
            None
        """
        pass
    
    @abstractmethod
    def invoke_from_mpt(self, mpt, user_id, temperature, max_tokens, user_task_execution_pk, task_name_for_system):
        """
        Perform a LLM chat completion using the provided MPT.

        Args:
            mpt (MPT): The MPT object.
            user_id (str): ID of the current user.
            temperature (float): Temperature parameter for generating responses.
            max_tokens (int): Maximum number of tokens in the generated response.
            user_task_execution_pk (int): Primary key of the user task execution.
            task_name_for_system (str): Name of the task for the system.

        Returns:
            None
        """
        pass

    @abstractmethod
    def chatCompletion(self, *args, **kwargs):
        """
        Abstract method that should be implemented to handle chat completions. The parameters for each subclass that
        implements this method may vary, hence the use of *args and **kwargs to accept any number of arguments.
        """
        pass

    def _write_in_dataset(self, json_data, task_name_for_system, type):
        try:
            # write data in MojodexMistralAI.dataset_dir/label/task_name_for_system.json
            directory = f"{self.dataset_dir}/{type}/{self.label}/{task_name_for_system}"
            if not os.path.exists(os.path.join(self.dataset_dir, "chat", self.label)):
                os.mkdir(os.path.join(self.dataset_dir, "chat", self.label))
            if not os.path.exists(directory):
                os.mkdir(directory)
            filename = len(os.listdir(directory)) + 1
            with open(os.path.join(directory, f"{filename}.json"), "w") as f:
                json.dump(json_data, f)
        except Exception as e:
            logging.error(f"🔴: ERROR: {LLM.__subclasses__()[0].__name__} >> {e}")
    