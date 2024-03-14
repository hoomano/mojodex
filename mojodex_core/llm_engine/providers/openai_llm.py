from openai import OpenAI, AzureOpenAI, RateLimitError
from mojodex_core.llm_engine.llm import LLM
from mojodex_core.logging_handler import MojodexCoreLogger, log_error
import tiktoken

from mojodex_core.costs_manager.tokens_costs_manager import TokensCostsManager

import os

mojo_openai_logger = MojodexCoreLogger("mojo_openai_logger")


class OpenAILLM(LLM):

    def __init__(self, llm_conf, label='undefined', llm_backup_conf=None, max_retries=3):
        """
        :param api_key: API key to call openAI
        :param api_base: Endpoint to call openAI
        :param api_version: Version of the API to user
        :param model: Model to use (deployment_id for azure)
        :param api_type: 'azure' or 'openai'
        :param max_retries: max_retries for openAI calls on rateLimit errors, unavailable... (default 3)
        """
        try:
            api_key = llm_conf["api_key"]
            api_base = llm_conf["api_base"]
            api_version = llm_conf["api_version"]
            api_type = llm_conf["api_type"]
            model = llm_conf["deployment_id"]
            self.label = label
            # if dataset_dir does not exist, create it
            if not os.path.exists(self.dataset_dir):
                os.mkdir(self.dataset_dir)
            if not os.path.exists(os.path.join(self.dataset_dir, "chat")):
                os.mkdir(os.path.join(self.dataset_dir, "chat"))
            if not os.path.exists(os.path.join(self.dataset_dir, "chat", self.label)):
                os.mkdir(os.path.join(self.dataset_dir, "chat", self.label))

            self.model = model
            self.max_retries = max_retries
            self.client = AzureOpenAI(
                api_version=api_version,
                azure_endpoint=api_base,
                azure_deployment=self.model,
                api_key=api_key,
                max_retries=self.max_retries
            ) if api_type == 'azure' else OpenAI(api_key=api_key)

            if llm_backup_conf:
                self.client_backup = AzureOpenAI(
                    api_version=llm_backup_conf["api_version"],
                    azure_endpoint=llm_backup_conf["api_base"],
                    azure_deployment=llm_backup_conf["deployment_id"],
                    api_key=llm_backup_conf["api_key"],
                    max_retries=self.max_retries
                ) if api_type == 'azure' else OpenAI(api_key=llm_backup_conf["api_key"])

            self.tokens_costs_manager = TokensCostsManager()
            LLM.__init__(self, llm_conf, llm_backup_conf=llm_backup_conf,
                         label=label, max_retries=self.max_retries)
        except Exception as e:
            raise Exception(f"🔴 Error initializing OpenAILLM __init__  : {e}")


    def num_tokens_from_messages(self, messages):
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
                    num_tokens += len(encoding.encode(value))
                    if key == "name":  # if there's a name, the role is omitted
                        num_tokens += -1  # role is always required and always 1 token
            num_tokens += 2  # every reply is primed with <im_start>assistant
            return num_tokens
        except Exception as e:
            raise Exception(f"🔴 Error in num_tokens_from_messages : {e}")

    def chatCompletion(self, messages, user_uuid, temperature, max_tokens, frequency_penalty=0,
                       presence_penalty=0, stream=False, stream_callback=None, json_format=False,
                       n_additional_calls_if_finish_reason_is_length=0, assistant_response="", n_calls=0, use_backup_client=False):
        """
        OpenAI chat completion
        :param messages: List of messages composing the conversation, each message is a dict with keys "role" and "content"
        :param user_uuid: Compulsory for openAI to track harmful content. If a user tries to pass the openAI moderation, we will receive an email with this id and we can go back to him to remove his access.
        :param temperature: The higher the temperature, the crazier the text
        :param max_tokens: The maximum number of tokens to generate
        :param frequency_penalty: The higher this is, the less likely the model is to repeat the same line verbatim (default 0)
        :param presence_penalty: The higher this is, the more likely the model is to talk about something that was mentioned in the prompt (default 0)
        :param stream: If True, will stream the completion
        :param stream_callback: If stream is True, will call this function with the completion as parameter
        :param json_format: If True, will return a json object
        :param n_additional_calls_if_finish_reason_is_length: If the finish reason is "length", will relaunch the function, instructing the assistant to continue its response
        :param assistant_response: Assistant response to add to the completion
        :param n_calls: Number of calls to the function
        :return: List of n generated messages
        """
        openai_client = self.client_backup if use_backup_client else self.client

        completion = openai_client.chat.completions.create(
            messages=messages,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            user=user_uuid,
            stream=stream,
            response_format={"type": "json_object"} if json_format else None
        )
        if stream:
            complete_text = ""
            finish_reason = None
            for stream_chunk in completion:
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
                                return None
                        except Exception as e:
                            mojo_openai_logger.error(
                                f"🔴 Error in streamCallback: {e}")

            response = complete_text
        else:
            response = completion.choices[0].message.content
            finish_reason = completion.choices[0].finish_reason

        if finish_reason == "length" and n_calls < n_additional_calls_if_finish_reason_is_length:
            # recall the function with assistant_message + user_message
            messages = messages + [{'role': 'assistant', 'content': response},
                                   {'role': 'user', 'content': 'Continue'}]
            return self.chatCompletion(messages, user_uuid, temperature, max_tokens,
                                       frequency_penalty=frequency_penalty, presence_penalty=presence_penalty,
                                       stream=stream, stream_callback=stream_callback, json_format=json_format,
                                       assistant_response=assistant_response + " " + response,
                                       n_additional_calls_if_finish_reason_is_length=n_additional_calls_if_finish_reason_is_length,
                                       n_calls=n_calls + 1)
        # [] is a legacy from the previous version that could return several completions. Need complete refacto to remove.
        return [assistant_response + " " + response]

    def invoke(self, messages, user_id, temperature, max_tokens,
               frequency_penalty=0, presence_penalty=0, stream=False, stream_callback=None, json_format=False,
               user_task_execution_pk=None, task_name_for_system=None):
        return self.recursive_invoke(messages, user_id, temperature, max_tokens,
                                   frequency_penalty=frequency_penalty, presence_penalty=presence_penalty,
                                   stream=stream, stream_callback=stream_callback, json_format=json_format,
                                   user_task_execution_pk=user_task_execution_pk,
                                   task_name_for_system=task_name_for_system,
                                   n_additional_calls_if_finish_reason_is_length=0)

    def recursive_invoke(self, messages, user_id, temperature, max_tokens,
                       frequency_penalty=0, presence_penalty=0, stream=False, stream_callback=None, json_format=False,
                       user_task_execution_pk=None, task_name_for_system=None, n_additional_calls_if_finish_reason_is_length=0):
        try:

            # check complete number of tokens in prompt
            n_tokens_prompt = self.num_tokens_from_messages(messages[:1])
            n_tokens_conversation = self.num_tokens_from_messages(messages[1:])

            try:
                responses = self.chatCompletion(messages, user_id, temperature, max_tokens,
                                                frequency_penalty=frequency_penalty, presence_penalty=presence_penalty,
                                                json_format=json_format, stream=stream,
                                                stream_callback=stream_callback, n_additional_calls_if_finish_reason_is_length=n_additional_calls_if_finish_reason_is_length)
            except RateLimitError:
                # try to use backup engine
                if self.client_backup:
                    responses = self.chatCompletion(messages, user_id, temperature, max_tokens,
                                                    frequency_penalty=frequency_penalty, presence_penalty=presence_penalty,
                                                    stream=stream,
                                                    stream_callback=stream_callback,
                                                    use_backup_client=True)
                else:
                    raise Exception(
                        "Rate limit exceeded and no backup engine available")
            if responses is None:
                return None
            n_tokens_response = 0
            for response in responses:
                n_tokens_response += self.num_tokens_from_messages(
                    [{'role': 'assistant', 'content': response}])

            self.tokens_costs_manager.on_tokens_counted(user_id, n_tokens_prompt, n_tokens_conversation, n_tokens_response,
                                                        self.model, self.label, user_task_execution_pk, task_name_for_system)
            self._write_in_dataset({"temperature": temperature, "max_tokens": max_tokens, "n_responses": 1,
                                    "frequency_penalty": frequency_penalty, "presence_penalty": presence_penalty,
                                    "messages": messages, "responses": responses}, task_name_for_system, "chat")
            return responses
        except Exception as e:
            log_error(
                f"Error in Mojodex OpenAI chat for user_id: {user_id} - user_task_execution_pk: {user_task_execution_pk} - task_name_for_system: {task_name_for_system}: {e}", notify_admin=True)
            raise Exception(
                f"🔴 Error in Mojodex OpenAI chat: {e} - model: {self.model}")
