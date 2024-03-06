from abc import ABC, abstractmethod


class BackgroundLLM(ABC):
    """
    Abstract base class for LLM (Language Model) implementations.
    """

    @abstractmethod
    def __init__(self, llm_conf, label='unknown', max_retries=0):
        """
        Initializes the BackgroundLLM object.

        Args:
            llm_conf (dict): The configuration for the LLM.
            label (str): The label of the task.
            max_retries (int, optional): The maximum number of retries. Defaults to 0.
        """
        pass

    @abstractmethod
    def chat(self, messages, user_id, temperature, max_tokens, user_task_execution_pk, task_name_for_system):
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
