from mistralai.models.chat_completion import ChatMessage
from mistralai.client import MistralClient
from mojodex_core.logging_handler import log_error
import logging
import os
from mojodex_core.llm_engine.llm import LLM
from mojodex_core.llm_engine.mpt import MPT

logging.basicConfig(level=logging.ERROR)


class MistralAILLM(LLM):

    def __init__(self, mistral_conf):

        try:
            self._name = mistral_conf["model_name"]
            api_key = mistral_conf["api_key"]
            self.model = mistral_conf["api_model"]

            endpoint = mistral_conf.get("endpoint") if mistral_conf.get(
                "endpoint") else None
            api_type = "azure" if mistral_conf.get(
                "endpoint") else "la_plateforme"


            # if dataset_dir does not exist, create it
            if not os.path.exists(self.dataset_dir):
                os.mkdir(self.dataset_dir)
            if not os.path.exists(os.path.join(self.dataset_dir, "chat")):
                os.mkdir(os.path.join(self.dataset_dir, "chat"))

            self.client = MistralClient(
                api_key=api_key,
                endpoint=endpoint if api_type == 'azure' else "https://api.mistral.ai",
            )
            # TODO: manage llm_backup_conf to manage rate limits > see OpenAILLM implementation

        except Exception as e:
            raise Exception(
                f"🔴 Error initializing MistralAILLM __init__  : {e}")
        
    # TODO: implement this method with appropriate encoding for Mistral
    def num_tokens_from_string(self, string):
        """Returns the number of tokens in a text string."""
        return None

    # TODO: implement this method with appropriate encoding for Mistral
    def num_tokens_from_text_messages(self, messages):
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
                logging.warning("n_responses must be 1 if stream is True")

            # Convert messages into Mistral ChatMessages
            if len(messages) == 1:
                messages = [ChatMessage(
                    role='user', content=messages[0]['content'])]
            else:
                messages = [ChatMessage(
                    role=message['role'], content=message['content']) for message in messages]

            if stream:
                stream_response = self.client.chat_stream(
                    model=self.model, messages=messages, temperature=temperature, max_tokens=max_tokens)

                complete_text = ""
                for chunk in stream_response:
                    partial_token = chunk.choices[0].delta.content
                    complete_text += partial_token if partial_token else ""
                    if stream_callback is not None:
                        try:
                            stream_callback(complete_text)
                        except Exception as e:
                            logging.error(
                                f"🔴 Error in streamCallback : {e}")
            else:
                response = self.client.chat(
                    model=self.model, messages=messages, temperature=temperature, max_tokens=max_tokens)

                complete_text = response.choices[0].message.content
            # [content.text for content in stream_response.choices]
            return [complete_text]

        except Exception as e:
            log_error(f"💨❌: Error in Mojodex Mistral chat: {e}")

    def invoke(self, messages, user_id, temperature, max_tokens, label, n_responses=1,
               frequency_penalty=0, presence_penalty=0, stream=False, stream_callback=None, json_format=False,
               user_task_execution_pk=None, task_name_for_system=None):
        try:
            try:
                if not os.path.exists(os.path.join(self.dataset_dir, "chat", label)):
                    os.mkdir(os.path.join(self.dataset_dir, "chat", label))
            except Exception as e:
                logging.error(
                    f"🔴: ERROR creating chat/{label} >> {e}")


            responses = self.chatCompletion(messages, temperature, max_tokens, n_responses=n_responses,
                                            frequency_penalty=frequency_penalty, presence_penalty=presence_penalty, stream=stream, stream_callback=stream_callback, json_format=json_format)
            try:
                self._write_in_dataset({"temperature": temperature, "max_tokens": max_tokens, "n_responses": n_responses,
                                        "frequency_penalty": frequency_penalty, "presence_penalty": presence_penalty,
                                        "messages": [{'role': message.get('role') if message.get('role') else 'unknown', 'content': message.get('content') if message.get('content') else "no_content"} for message in messages], "responses": responses, "model_config": self.model}, task_name_for_system, "chat", label=label)
            except Exception as e:
                log_error(
                    f"Error while writing in dataset for user_id: {user_id} - user_task_execution_pk: {user_task_execution_pk} - task_name_for_system: {task_name_for_system}: {e}", notify_admin=False)
                log_error(messages, notify_admin=False)
            return responses
        except Exception as e:
            log_error(
                f"Error in Mojodex Mistral AI chat for user_id: {user_id} - user_task_execution_pk: {user_task_execution_pk} - task_name_for_system: {task_name_for_system}: {e}", notify_admin=False)
            raise Exception(
                f"🔴 Error in Mojodex Mistral AI chat: {e} - model: {self.model}")

    def invoke_from_mpt(self, mpt: MPT, user_id, temperature, max_tokens, n_responses=1,
                        frequency_penalty=0, presence_penalty=0, stream=False, stream_callback=None, json_format=False,
                        user_task_execution_pk=None, task_name_for_system=None):
        try:
            # put a reference to the execution with the filepath of the MPT instruction
            # label is the filename without the file extension
            label = mpt.filepath.split('/')[-1].split('.')[0]
            
            if self.model not in mpt.models:
                logging.warning(
                    f"{mpt} does not contain model: {self.model} in its dashbangs")
            messages = [{"role": "user", "content": mpt.prompt}]
            responses = self.invoke(messages, user_id, temperature, max_tokens, label=label, n_responses=n_responses,
                                    frequency_penalty=frequency_penalty, presence_penalty=presence_penalty, stream=stream, stream_callback=stream_callback, json_format=json_format, user_task_execution_pk=user_task_execution_pk, task_name_for_system=task_name_for_system)
            return responses
        except Exception as e:
            log_error(
                f"Error in Mojodex Mistral AI chat for user_id: {user_id} - label: {label} user_task_execution_pk: {user_task_execution_pk} - task_name_for_system: {task_name_for_system}: {e}", notify_admin=False)
            raise Exception(
                f"🔴 Error in Mojodex Mistral AI chat > label: {label} {e} - model: {self.model}")
