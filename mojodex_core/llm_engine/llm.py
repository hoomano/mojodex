from abc import ABC, abstractmethod
import json
import logging
import os
from typing import List, Any
from mojodex_core.logging_handler import MojodexCoreLogger, log_error

logging.basicConfig(level=logging.INFO)


class LLM(ABC):
    """
    Abstract base class for LLM (Language Model) implementations.
    """

    dataset_dir = "/data/prompts_dataset"

    def __init__(self, name, model):
        try:
            self.name = name
            self.model = model
            self.logger = MojodexCoreLogger(f"{self.name} - {self.model}")

            # suggestion:
            #self.dataset_dir = self.common_dataset_dir.join(f"{self.name}")
            if not os.path.exists(self.dataset_dir):
                os.mkdir(self.dataset_dir)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} __init__  : {e}")

    @abstractmethod
    def num_tokens_from_text_messages(self, string):
        """
        Abstract method that should be implemented to return the number of tokens from a given string of messages.
        """
        raise NotImplementedError

    @abstractmethod
    def invoke(self, messages: List[Any], user_id: str, temperature: float, max_tokens: int, label: str,
               stream: bool = False, stream_callback=None, user_task_execution_pk: int = None,
               task_name_for_system: str = None, **kwargs):
        """
        Perform LLM call

        Args:
            :param messages: messages an array of messages to chat with, e.g. [{role: 'user', content: 'Hello'}]
            :param user_id: ID of the current user.
            :param temperature: Temperature parameter for generating responses.
            :param max_tokens: Maximum number of tokens in the generated response.
            :param label: Label for the chat completion.
            :param stream: Whether to stream the response.
            :param stream_callback: Callback function for streaming the response.
            :param user_task_execution_pk: Primary key of the user task execution.
            :param task_name_for_system: Name of the task for the system.
            **kwargs: Additional keyword arguments.


        Returns:
            LLM responses list
        """
        raise NotImplementedError

    def invoke_from_mpt(self, mpt, user_id: str, temperature: float, max_tokens: int, stream: bool,stream_callback, user_task_execution_pk: int,
                        task_name_for_system: str, **kwargs):
        """
        Perform LLM call from an MPT object.
        :param mpt: MPT object.
        :param user_id: ID of the current user.
        :param temperature: Temperature parameter for generating responses.
        :param max_tokens: Maximum number of tokens in the generated response.
        :param user_task_execution_pk: Primary key of the user task execution.
        :param task_name_for_system: Name of the task for the system.
        :param stream: Whether to stream the response.
        :param stream_callback: Callback function for streaming the response.
        **kwargs: Additional keyword arguments.

        :return:
        LLM responses list
        """
        label = ""
        try:
            # put a reference to the execution with the filepath of the MPT instruction
            # label is the filename without the file extension
            label = mpt.filepath.split('/')[-1].split('.')[0]
            if self.model not in mpt.models:
                self.logger.warning(f"{mpt} does not contain model: {self.model} in its dashbangs")

            messages = [{"role": "user", "content": mpt.prompt}]
            responses = self.invoke(messages, user_id, temperature, max_tokens, label=label,
                                    stream=stream, stream_callback=stream_callback,
                                    user_task_execution_pk=user_task_execution_pk,
                                    task_name_for_system=task_name_for_system, **kwargs)
            return responses
        except Exception as e:
            raise Exception(f"LLM {self.name} - invoke_from_mpt - label: {label} - model: {self.model}: {e}")

    def _write_in_dataset(self, json_data, task_name_for_system, type, label):
        try:
            # write data in dataset_dir/label/task_name_for_system.json
            directory = f"{self.dataset_dir}/{type}/{label}/{task_name_for_system}"
            if not os.path.exists(os.path.join(self.dataset_dir, type)):
                os.mkdir(os.path.join(self.dataset_dir, type))
            if not os.path.exists(os.path.join(self.dataset_dir, type, label)):
                os.mkdir(os.path.join(self.dataset_dir, type, label))
            if not os.path.exists(directory):
                os.mkdir(directory)
            filename = len(os.listdir(directory)) + 1
            with open(os.path.join(directory, f"{filename}.json"), "w") as f:
                json.dump(json_data, f)
        except Exception as e:
            log_error(f"LLM {self.name} - _write_in_dataset : type: {type} - label {label} - "
                              f"task_name_for_system: {task_name_for_system} : {e}", notify_admin=True)
