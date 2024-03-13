from abc import ABC, abstractmethod
import json
import logging
import os

class LLM(ABC):
    """
    Abstract base class for LLM (Language Model) implementations.
    """

    @abstractmethod
    def __init__(self, llm_conf, llm_backup_conf=None, label='undefined', max_retries=0):
        """
        Initializes the BackgroundLLM object.

        Args:
            llm_conf (dict): The configuration for the LLM.
            llm_backup_conf (dict, optional): The configuration for the backup LLM to manage rate limits. Defaults to None.
            label (str): The label of the task.
            max_retries (int, optional): The maximum number of retries. Defaults to 0.
        """
        pass

    @abstractmethod
    def num_tokens_from_string(self, string):
        """
        Abstract method that should be implemented to return the number of tokens from a given string.
        """
        pass

    @abstractmethod
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
    