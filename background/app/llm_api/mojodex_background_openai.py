import json
import os
import time


from llm_api.background_llm import BackgroundLLM
from mojodex_core.llm_engine.providers.openai_llm import OpenAILLM
import openai

from mojodex_core.costs_manager.tokens_costs_manager import TokensCostsManager
from mojodex_core.llm_engine.providers.openai_embedding import OpenAIEmbeddingProvider

from mojodex_core.logging_handler import send_admin_error_email
from mojodex_core.costs_manager.tokens_costs_manager import TokensCostsManager
tokens_costs_manager = TokensCostsManager()


class OpenAIConf:

    gpt4_turbo_conf = {
        "api_key": os.environ.get("GPT4_TURBO_AZURE_OPENAI_KEY",  os.environ.get("OPENAI_API_KEY")),
        "api_base": os.environ.get("GPT4_TURBO_AZURE_OPENAI_API_BASE"),
        "api_type": os.environ.get("LLM_API_PROVIDER"),
        "api_version": os.environ.get("GPT4_TURBO_AZURE_OPENAI_API_VERSION"),
        "deployment_id": os.environ.get("GPT4_TURBO_AZURE_OPENAI_DEPLOYMENT_ID", 'gpt-4-1106-preview')
    }

    embedding_conf = {
        "api_key": os.environ.get("ADA_EMBEDDING_AZURE_OPENAI_KEY", os.environ.get("OPENAI_API_KEY")),
        "api_base": os.environ.get("ADA_EMBEDDING_AZURE_OPENAI_API_BASE"),
        "api_type": os.environ.get("EMBEDDING_API_PROVIDER"),
        "api_version": os.environ.get("ADA_EMBEDDING_AZURE_OPENAI_API_VERSION"),
        "deployment_id": os.environ.get("ADA_EMBEDDING_AZURE_OPENAI_DEPLOYMENT_ID", "text-embedding-ada-002")
    }


class MojodexBackgroundOpenAI(BackgroundLLM, OpenAILLM, OpenAIEmbeddingProvider):
    logger_prefix = "MojodexBackgroundOpenAI"
    dataset_dir = "/data/prompts_dataset"

    def __init__(self, openai_conf, label='unknown', max_retries=0):
        api_key = openai_conf["api_key"]
        api_base = openai_conf["api_base"]
        api_version = openai_conf["api_version"]
        api_type = openai_conf["api_type"]
        self.model = openai_conf["deployment_id"]
        self.label = label
        # if dataset_dir does not exist, create it
        if not os.path.exists(self.dataset_dir):
            os.mkdir(self.dataset_dir)
        if not os.path.exists(os.path.join(self.dataset_dir, "chat")):
            os.mkdir(os.path.join(self.dataset_dir, "chat"))
        if not os.path.exists(os.path.join(self.dataset_dir, "chat", self.label)):
            os.mkdir(os.path.join(self.dataset_dir, "chat", self.label))
        super().__init__(api_key, api_base, api_version, self.model,
                         api_type=api_type, max_retries=max_retries)

    def chat(self, messages, user_id, temperature, max_tokens,
             frequency_penalty=0, presence_penalty=0, stream=False, stream_callback=None, json_format=False,
             user_task_execution_pk=None, task_name_for_system=None, retries=12):
        return self.recursive_chat(messages, user_id, temperature, max_tokens,
                                   frequency_penalty=frequency_penalty, presence_penalty=presence_penalty, stream=stream, stream_callback=stream_callback, json_format=json_format,
                                   user_task_execution_pk=user_task_execution_pk, task_name_for_system=task_name_for_system, n_additional_calls_if_finish_reason_is_length=0, retries=retries)

    def recursive_chat(self, messages, user_id, temperature, max_tokens,
                       frequency_penalty=0, presence_penalty=0, stream=False, stream_callback=None, json_format=False,
                       user_task_execution_pk=None, task_name_for_system=None, n_additional_calls_if_finish_reason_is_length=0, retries=12):
        try:
            # check complete number of tokens in prompt
            try:
                n_tokens_prompt = self.num_tokens_from_messages(messages[:1])
                n_tokens_conversation = self.num_tokens_from_messages(
                    messages[1:])
            except Exception as e:
                send_admin_error_email(
                    f"{MojodexBackgroundOpenAI.logger_prefix}: chat - n_tokens_prompt & n_tokens_conversation: {e}")
                n_tokens_prompt, n_tokens_conversation = 0, 0

            responses = super().chatCompletion(messages, user_id, temperature, max_tokens,
                                               frequency_penalty=frequency_penalty, presence_penalty=presence_penalty,
                                               json_format=json_format, stream=stream,
                                               stream_callback=stream_callback,
                                               n_additional_calls_if_finish_reason_is_length=n_additional_calls_if_finish_reason_is_length)

            n_tokens_response = 0
            try:
                for response in responses:
                    n_tokens_response += self.num_tokens_from_messages(
                        [{'role': 'assistant', 'content': response}])
            except Exception as e:
                send_admin_error_email(
                    f"{MojodexBackgroundOpenAI.logger_prefix}: chat - num_tokens_from_messages: {e}")

            tokens_costs_manager.on_tokens_counted(user_id, n_tokens_prompt, n_tokens_conversation, n_tokens_response,
                                                   self.model, self.label, user_task_execution_pk, task_name_for_system)
            self._write_in_dataset({"temperature": temperature, "max_tokens": max_tokens, "n_responses": 1,
                                    "frequency_penalty": frequency_penalty, "presence_penalty": presence_penalty,
                                    "messages": messages, "responses": responses}, task_name_for_system, "chat")
            return responses
        except (openai.RateLimitError, openai.APITimeoutError) as e:
            # wait 30 seconds and retry because we are in background, we can wait
            if retries == 0:
                raise Exception(
                    f"🔴 Error in Mojodex OpenAI chat: {type(e).__name__} despite all retries {e}")
            time.sleep(30)
            return self.recursive_chat(messages, user_id, temperature, max_tokens,
                                       frequency_penalty=frequency_penalty, presence_penalty=presence_penalty,
                                       json_format=json_format, stream=stream, stream_callback=stream_callback,
                                       user_task_execution_pk=user_task_execution_pk, task_name_for_system=task_name_for_system,
                                       n_additional_calls_if_finish_reason_is_length=n_additional_calls_if_finish_reason_is_length, retries=retries-1)
        except Exception as e:
            raise Exception(
                f"🔴 Error in Mojodex OpenAI chat of type {type(e).__name__}: {e}")

    def embed(self, text, user_id, user_task_execution_pk, task_name_for_system, retries=12):
        try:
            try:
                n_tokens_prompt = self.num_tokens_from_string(text)
            except Exception as e:
                send_admin_error_email(
                    f"{MojodexBackgroundOpenAI.logger_prefix}: embed - num_tokens_from_string: {e}")
                n_tokens_prompt = 0
            responses = super().get_embedding(text)
            tokens_costs_manager.on_tokens_counted(user_id, n_tokens_prompt, 0, 0,
                                                   self.model, self.label, user_task_execution_pk, task_name_for_system)
            return responses
        except openai.RateLimitError as e:
            # wait 5 seconds and retry because we are in background, we can wait
            if retries == 0:
                raise Exception(
                    f"🔴 Error in Mojodex OpenAI embed, rate limit exceeded despite all retries {e}")
            time.sleep(5)
            return self.embed(text, user_id, user_task_execution_pk, task_name_for_system, retries=retries-1)
        except Exception as e:
            raise Exception(f"🔴 Error in Mojodex OpenAI embed: {e}")
