from openai import OpenAI, AzureOpenAI, RateLimitError
from mojodex_core.llm_engine.llm import LLM
from mojodex_core.logging_handler import MojodexCoreLogger, log_error
import tiktoken

from typing import List, Any

from mojodex_core.costs_manager.tokens_costs_manager import TokensCostsManager

import os

from mojodex_core.llm_engine.mpt import MPT

mojo_openai_logger = MojodexCoreLogger("mojo_openai_logger")


class OpenAILLM(LLM):

    def __init__(self, llm_conf, llm_backup_conf=None, max_retries=3):
        """
        api_key: API key to call openAI
        api_base: Endpoint to call openAI
        api_version: Version of the API to user
        Model to use (deployment_id for azure)
        api_type: 'azure' or 'openai'
        max_retries: max_retries for openAI calls on rateLimit errors, unavailable... (default 3)
        """
        try:

            api_key = llm_conf["api_key"]
            api_base = llm_conf["api_base"] if "api_base" in llm_conf else None
            api_version = llm_conf["api_version"] if "api_version" in llm_conf else None
            api_type = llm_conf["api_type"] if "api_type" in llm_conf else "openai"
            self.deployment = llm_conf["deployment_id"] if "deployment_id" in llm_conf else None
            super().__init__(name=llm_conf["model_name"], model=self.deployment)

            self.client = AzureOpenAI(
                api_version=api_version,
                azure_endpoint=api_base,
                azure_deployment=self.deployment,
                api_key=api_key,
                max_retries=0 if llm_backup_conf else max_retries
            ) if api_type == 'azure' else OpenAI(api_key=api_key)

            self.client_backup = None
            if llm_backup_conf:
                self.client_backup = AzureOpenAI(
                    api_version=llm_backup_conf["api_version"] if "api_version" in llm_backup_conf else None,
                    azure_endpoint=llm_backup_conf["api_base"] if "api_base" in llm_backup_conf else None,
                    azure_deployment=llm_backup_conf["deployment_id"] if "deployment_id" in llm_backup_conf else None,
                    api_key=llm_backup_conf["api_key"],
                    max_retries=max_retries
                ) if llm_backup_conf['api_type'] == 'azure' else OpenAI(api_key=llm_backup_conf["api_key"])

            self.tokens_costs_manager = TokensCostsManager()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} __init__  : {e}")

    def num_tokens_from_text_messages(self, messages: List[Any]):
        # Working for models gpt-4, gpt-3.5-turbo, text-embedding-ada-002
        # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
        """Returns the number of tokens used by a list of messages.
        Code inspired from : https://platform.openai.com/docs/guides/chat/introduction - 04-12-2023"""
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            num_tokens = 0
            for message in messages:
                # every message follows <im_start>{role/name}\n{content}<im_end>\n
                num_tokens += 4
                for key, value in message.items():
                    if key == "content":
                        if isinstance(value, list):
                            for item in value:
                                if item.get("type") == "text":
                                    num_tokens += len(encoding.encode(item["text"]))
                        elif isinstance(value, str):
                            num_tokens += len(encoding.encode(value))
                    if key == "name":  # if there's a name, the role is omitted
                        num_tokens += -1  # role is always required and always 1 token
            num_tokens += 2  # every reply is primed with <im_start>assistant
            return num_tokens
        except Exception as e:
            raise Exception(f"num_tokens_from_text_messages : {e}")

    def _handle_chat_completion_response(self, completion, stream, stream_callback):
        try:
            if stream:
                complete_text = ""
                finish_reason = None
                for stream_chunk in completion:
                    if stream_chunk.choices:
                        choice = stream_chunk.choices[0]
                        partial_token = choice.delta
                        finish_reason = choice.finish_reason
                        if partial_token.content:
                            complete_text += partial_token.content
                            if stream_callback is not None:
                                try:
                                    flag_to_stop_streaming = stream_callback(
                                        complete_text)
                                    if flag_to_stop_streaming:
                                        return None, None
                                except Exception as e:
                                    mojo_openai_logger.error(
                                        f"🔴 Error in streamCallback: {e}")

                response = complete_text
            else:
                response = completion.choices[0].message.content
                finish_reason = completion.choices[0].finish_reason

            return response, finish_reason
        except Exception as e:
            raise Exception(f"_handle_chat_completion_stream : {e}")

    def _chat_completion(self, messages: List[Any], user_uuid: str, temperature: float, max_tokens: int,
                         frequency_penalty: int = 0, presence_penalty: int = 0,
                         stream: bool = False, stream_callback=None,
                         n_additional_calls_if_finish_reason_is_length: int = 0, assistant_response: str = "",
                         n_calls: int = 0,
                         use_backup_client: bool = False, **kwargs):
        """
        OpenAI chat completion
        :param messages: List of messages composing the conversation, each message is a dict with keys "role" and "content"
        :param user_uuid: Compulsory for openAI to track harmful content. If a user tries to pass the openAI moderation, we will receive an email with this id and we can go back to him to remove his access.
        :param temperature: The higher the temperature, the crazier the text
        :param max_tokens: The maximum number of tokens to generate
        :param frequency_penalty: The higher the penalty, the less likely the model is to repeat itself
        :param presence_penalty: The higher the penalty, the less likely the model is to generate a response that is similar to the prompt
        :param stream: If True, will stream the completion
        :param stream_callback: If stream is True, will call this function with the completion as parameter
        :param n_additional_calls_if_finish_reason_is_length: If the finish reason is "length", will relaunch the function, instructing the assistant to continue its response
        :param assistant_response: Assistant response to add to the completion
        :param n_calls: Number of calls to the function
        :return: List of n generated messages
        """
        openai_client = self.client_backup if use_backup_client else self.client

        # if "json_format" in kwargs and kwargs["json_format"]:
        # set response_format={"type": "json_object"} in kwargs
        if "json_format" in kwargs and kwargs["json_format"]:
            kwargs.pop("json_format")
            kwargs["response_format"] = {"type": "json_object"}

        completion = openai_client.chat.completions.create(
            messages=messages,
            model=self.name,
            temperature=temperature,
            max_tokens=max_tokens,
            user=user_uuid,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stream=stream,
            **kwargs
        )

        response, finish_reason = self._handle_chat_completion_response(completion, stream, stream_callback)
        if response is None:
            return None

        if finish_reason == "length" and n_calls < n_additional_calls_if_finish_reason_is_length:
            # recall the function with assistant_message + user_message
            messages = messages + [{'role': 'assistant', 'content': response},
                                   {'role': 'user', 'content': 'Continue'}]
            return self._chat_completion(messages, user_uuid, temperature, max_tokens,
                                         frequency_penalty=frequency_penalty, presence_penalty=presence_penalty,
                                         stream=stream, stream_callback=stream_callback,
                                         assistant_response=assistant_response + " " + response,
                                         n_additional_calls_if_finish_reason_is_length=n_additional_calls_if_finish_reason_is_length,
                                         n_calls=n_calls + 1, **kwargs)
        return assistant_response + " " + response

    def invoke(self, messages: List[Any], user_id: str, temperature: float, max_tokens: int, label: str,
               stream: bool = False, stream_callback=None, user_task_execution_pk: int = None,
               task_name_for_system: str = None, frequency_penalty: float = 0, presence_penalty: float = 0, **kwargs):
        try:
            return self.recursive_invoke(messages, user_id, temperature, max_tokens, label,
                                          frequency_penalty=frequency_penalty, presence_penalty=presence_penalty,
                                          stream=stream, stream_callback=stream_callback,
                                          user_task_execution_pk=user_task_execution_pk,
                                          task_name_for_system=task_name_for_system,
                                          n_additional_calls_if_finish_reason_is_length=0, **kwargs)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}- name: {self.name} - model:{self.model} - invoke: {e}")

    def _call_completion_with_rate_limit_management(self, messages, user_id, temperature, max_tokens, frequency_penalty,
                                                    presence_penalty,
                                                    stream, stream_callback,
                                                    n_additional_calls_if_finish_reason_is_length, **kwargs):
        try:
            try:
                return self._chat_completion(messages, user_id, temperature, max_tokens, frequency_penalty,
                                             presence_penalty, stream=stream,
                                             stream_callback=stream_callback,
                                             n_additional_calls_if_finish_reason_is_length=n_additional_calls_if_finish_reason_is_length,
                                             **kwargs)
            except RateLimitError:
                # try to use backup engine
                if self.client_backup:
                    return self._chat_completion(messages, user_id, temperature, max_tokens, frequency_penalty,
                                                 presence_penalty,
                                                 stream=stream,
                                                 stream_callback=stream_callback,
                                                 use_backup_client=True, **kwargs)
                else:
                    raise Exception("Rate limit exceeded and no backup engine available")
        except Exception as e:
            raise Exception(f"_call_completion_with_rate_limit_management : {e}")

    def recursive_invoke(self, messages: List[Any], user_id: str, temperature: float, max_tokens: int, label: str,
                          stream: bool = False, stream_callback=None, user_task_execution_pk: int = None,
                          task_name_for_system: str = None, frequency_penalty: float = 0, presence_penalty: float = 0,
                          n_additional_calls_if_finish_reason_is_length: int = 0, **kwargs):
        try:
            # check complete number of tokens in prompt
            n_tokens_prompt = self.num_tokens_from_text_messages(messages[:1])
            n_tokens_conversation = self.num_tokens_from_text_messages(messages[1:])

            response = self._call_completion_with_rate_limit_management(messages, user_id, temperature, max_tokens,
                                                                         frequency_penalty, presence_penalty,
                                                                         stream, stream_callback,
                                                                         n_additional_calls_if_finish_reason_is_length,
                                                                         **kwargs)

            if response is None:
                return None

            n_tokens_response = self.num_tokens_from_text_messages(
                [{'role': 'assistant', 'content': response[0]}])

            self.tokens_costs_manager.on_tokens_counted(user_id, n_tokens_prompt, n_tokens_conversation,
                                                        n_tokens_response,
                                                        self.name, label, user_task_execution_pk, task_name_for_system)
            self._write_in_dataset({"temperature": temperature, "max_tokens": max_tokens, "n_responses": 1,
                                    "frequency_penalty": frequency_penalty, "presence_penalty": presence_penalty,
                                    "messages": messages, "responses": response}, task_name_for_system, "chat",
                                   label=label)
            return response
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : recursive_invoke: {e}")
