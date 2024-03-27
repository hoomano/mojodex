
from mojodex_core.logging_handler import MojodexCoreLogger

import os
from mojodex_core.llm_engine.llm import LLM
from mojodex_core.llm_engine.mpt import MPT

from mojodex_core.logging_handler import MojodexCoreLogger

from ollama import Client


class OllamaLLM(LLM):

    def __init__(self, ollama_conf):

        try:

            self.model = ollama_conf.get(
                "model") if ollama_conf.get("model") else None
            self.endpoint = ollama_conf.get("endpoint") if ollama_conf.get(
                "endpoint") else None
            self.logger = MojodexCoreLogger(
                f"OllamaLLM - {self.model}")
            
            if self.endpoint is None or self.model is None:
                raise Exception(f"🔴 model and endpoint not set in models conf: {ollama_conf}")

            # if dataset_dir does not exist, create it
            if not os.path.exists(self.dataset_dir):
                os.mkdir(self.dataset_dir)
            if not os.path.exists(os.path.join(self.dataset_dir, "chat")):
                os.mkdir(os.path.join(self.dataset_dir, "chat"))

            self.client = Client(host=ollama_conf["endpoint"])

        except Exception as e:
            raise Exception(
                f"🔴 Error initializing OllamaLLM __init__  : {e}")

    # TODO: implement this method with appropriate encoding for Ollama
    def num_tokens_from_string(self, string):
        """Returns the number of tokens in a text string."""
        return None

    # TODO: implement this method with appropriate encoding for Ollama
    def num_tokens_from_messages(self, messages):
        """Returns the number of tokens used by a list of messages."""
        num_tokens = 0
        for message in messages:
            num_tokens += self.num_tokens_from_string(message.content)
        return None

    def chatCompletion(self, messages, temperature, max_tokens, n_responses=1,
                       frequency_penalty=0, presence_penalty=0, stream=False, stream_callback=None, json_format=False):
        try:
            # ensure if stream is true, n_responses = 1
            if stream and n_responses != 1:
                n_responses = 1
                self.logger.warning("n_responses must be 1 if stream is True")

            if stream:

                stream_response = self.client.chat(
                    model=self.model,
                    messages=messages,
                    stream=True,
                )

                complete_text = ""
                for chunk in stream_response:
                    partial_token = chunk['message']['content']
                    complete_text += partial_token if partial_token else ""
                    if stream_callback is not None:
                        try:
                            stream_callback(complete_text)
                        except Exception as e:
                            self.logger.error(
                                f"🔴 Error in streamCallback : {e}")
            else:
                response = self.client.chat(
                    model=self.model, messages=messages)

                complete_text = response['message']['content']
            # [content.text for content in stream_response.choices]
            return [complete_text]

        except Exception as e:
            self.logger.error(f"Error in Mojodex Ollama chat: {e}")

    def invoke(self, messages, user_id, temperature, max_tokens, label, n_responses=1,
               frequency_penalty=0, presence_penalty=0, stream=False, stream_callback=None, json_format=False,
               user_task_execution_pk=None, task_name_for_system=None):
        try:
            try:
                if not os.path.exists(os.path.join(self.dataset_dir, "chat", label)):
                    os.mkdir(os.path.join(self.dataset_dir, "chat", label))
            except Exception as e:
                self.logger.error(
                    f"🔴: ERROR creating chat/{label} >> {e}")

            responses = self.chatCompletion(messages, temperature, max_tokens, n_responses=n_responses,
                                            frequency_penalty=frequency_penalty, presence_penalty=presence_penalty, stream=stream, stream_callback=stream_callback, json_format=json_format)
            try:
                self._write_in_dataset({"temperature": temperature, "max_tokens": max_tokens, "n_responses": n_responses,
                                        "frequency_penalty": frequency_penalty, "presence_penalty": presence_penalty,
                                        "messages": [{'role': message.get('role') if message.get('role') else 'unknown', 'content': message.get('content') if message.get('content') else "no_content"} for message in messages], "responses": responses, "model_config": self.model}, task_name_for_system, "chat", label=label)
            except Exception as e:
                self.logger.error(
                    f"Error while writing in dataset for user_id: {user_id} - user_task_execution_pk: {user_task_execution_pk} - task_name_for_system: {task_name_for_system}: {e}", notify_admin=False)
                self.logger.error(messages, notify_admin=False)
            return responses
        except Exception as e:
            self.logger.error(
                f"Error in Mojodex Ollama AI chat for user_id: {user_id} - user_task_execution_pk: {user_task_execution_pk} - task_name_for_system: {task_name_for_system}: {e}", notify_admin=False)
            raise Exception(
                f"🔴 Error in Mojodex Ollama AI chat: {e} - model: {self.model}")

    def invoke_from_mpt(self, mpt: MPT, user_id, temperature, max_tokens, n_responses=1,
                        frequency_penalty=0, presence_penalty=0, stream=False, stream_callback=None, json_format=False,
                        user_task_execution_pk=None, task_name_for_system=None):
        try:
            # put a reference to the execution with the filepath of the MPT instruction
            # label is the filename without the file extension
            label = mpt.filepath.split('/')[-1].split('.')[0]
            if self.model not in mpt.models:
                self.logger.warning(
                    f"{mpt} does not contain model: {self.model} in its dashbangs")
                
            messages = [{"role": "user", "content": mpt.prompt}]
            responses = self.invoke(messages, user_id, temperature, max_tokens, n_responses=n_responses, label=label,
                                    frequency_penalty=frequency_penalty, presence_penalty=presence_penalty, stream=stream, stream_callback=stream_callback, json_format=json_format, user_task_execution_pk=user_task_execution_pk, task_name_for_system=task_name_for_system)
            return responses
        except Exception as e:
            self.logger.error(
                f"Error in Mojodex Ollama AI chat for user_id: {user_id} - label: {label} - user_task_execution_pk: {user_task_execution_pk} - task_name_for_system: {task_name_for_system}: {e}", notify_admin=False)
            raise Exception(
                f"🔴 Error in Mojodex Ollama AI chat: >  label: {label} - {e} - model: {self.model}")
