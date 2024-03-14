from abc import ABC, abstractmethod
import json
import logging
import os



class LLM(ABC):
    """
    Abstract base class for LLM (Language Model) implementations.
    """

    dataset_dir = "/data/prompts_dataset"

    @staticmethod
    def get_llm_provider():
        
        llm, llm_conf, llm_backup_conf = None, None, None

        # Read the .env file to check which LLM engine to use
        llm_engine = os.environ.get("LLM_ENGINE", "openai")

        if llm_engine == "openai":
            from mojodex_core.llm_engine.providers.openai_llm import OpenAILLM
            from mojodex_core.openai_conf import OpenAIConf
            # check the .env file to see which LLM_API_PROVIDER is set
            llm_conf = OpenAIConf.gpt4_turbo_conf
            llm_backup_conf = OpenAIConf.gpt4_32_conf

            llm = OpenAILLM
        elif llm_engine == "mistral":
            from mojodex_core.llm_engine.providers.mistralai_llm import MistralAILLM
            from mojodex_core.mistralai_conf import MistralAIConf
            # check the .env file to see which LLM_API_PROVIDER is set
            if os.environ.get("LLM_API_PROVIDER") == "azure":
                llm_conf = MistralAIConf.azure_mistral_large_conf
                llm_backup_conf = MistralAIConf.mistral_large_conf
            else:
                llm_conf = MistralAIConf.mistral_large_conf
                llm_backup_conf = MistralAIConf.azure_mistral_large_conf
            llm = MistralAILLM
        else:
            raise Exception(f"Unknown LLM engine: {llm_engine}")

        return llm, llm_conf, llm_backup_conf


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
            if not os.path.exists(directory):
                os.mkdir(directory)
            filename = len(os.listdir(directory)) + 1
            with open(os.path.join(directory, f"{filename}.json"), "w") as f:
                json.dump(json_data, f)
        except Exception as e:
            logging.error(f"🔴: ERROR: {LLM.__subclasses__()[0].__name__} >> {e}")
    