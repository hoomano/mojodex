from openai import OpenAI, AzureOpenAI, RateLimitError
from mojodex_core.llm_engine.llm import LLM
from mojodex_core.llm_engine.providers.openai_llm import OpenAILLM
from mojodex_core.logging_handler import MojodexCoreLogger, log_error
import tiktoken

from typing import List

from mojodex_core.costs_manager.tokens_costs_manager import TokensCostsManager

import os

from mojodex_core.llm_engine.mpt import MPT

mojo_openai_logger = MojodexCoreLogger("mojo_openai_logger")


class OpenAIVisionLLM(OpenAILLM):

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    def __init__(self, llm_conf, llm_backup_conf=None, max_retries=3):
        super().__init__(llm_conf, llm_backup_conf, max_retries)
        
    def num_tokens_from_messages(self, messages):
        raise NotImplementedError("num_tokens_from_messages() not implemented in OpenVisionAILLM")
    
    @staticmethod
    def get_image_message_url_prefix(image_name):
        try:
            extension = image_name.split(".")[-1]
            # check if extension is allowed
            if extension not in OpenAIVisionLLM.ALLOWED_EXTENSIONS:
                raise Exception(f"Image extension not allowed: {extension}")
            return 'data:image/' + extension
        except Exception as e:
            raise Exception(f"_get_image_message_url_prefix :: {e}")


    
    def recursive_invoke(self, messages, user_id, temperature, max_tokens, label, frequency_penalty, presence_penalty,
                       stream=False, stream_callback=None, user_task_execution_pk=None, task_name_for_system=None,
                         n_additional_calls_if_finish_reason_is_length=0, **kwargs):
        try:

            try:
                if not os.path.exists(os.path.join(self.dataset_dir, "chat", label)):
                    os.mkdir(os.path.join(self.dataset_dir, "chat", label))
            except Exception as e:
                log_error(f"Error creating directory for dataset chat/{label}", notify_admin=False)

            # check complete number of tokens in prompt
            #n_tokens_prompt = self.num_tokens_from_messages(messages[:1])
            #n_tokens_conversation = self.num_tokens_from_messages(messages[1:])

            responses = self._call_completion_with_rate_limit_management(messages, user_id, temperature, max_tokens,
                                                                         frequency_penalty, presence_penalty,
                                                                        stream, stream_callback,
                                                                        n_additional_calls_if_finish_reason_is_length,
                                                                        **kwargs)

            if responses is None:
                return None

            #n_tokens_response = self.num_tokens_from_messages(
            #    [{'role': 'assistant', 'content': responses[0]}])

            #self.tokens_costs_manager.on_tokens_counted(user_id, n_tokens_prompt, n_tokens_conversation, n_tokens_response,
            #                                            self.name, label, user_task_execution_pk, task_name_for_system)
            self._write_in_dataset({"temperature": temperature, "max_tokens": max_tokens, "n_responses": 1,
                                    "frequency_penalty": frequency_penalty, "presence_penalty": presence_penalty,
                                    "messages": messages, "responses": responses}, task_name_for_system, "chat", label=label)
            return responses
        except Exception as e:
            log_error(
                f"Error in Mojodex OpenAI chat for user_id: {user_id} - label: {label} user_task_execution_pk: {user_task_execution_pk} - task_name_for_system: {task_name_for_system}: {e}", notify_admin=True)
            raise Exception(
                f"🔴 Error in Mojodex OpenAI recursive_invoke() > label: {label} {e} - model: {self.name}")
