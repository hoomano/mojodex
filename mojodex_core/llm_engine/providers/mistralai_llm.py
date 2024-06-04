from typing import List, Any

from mistralai.models.chat_completion import ChatMessage
from mistralai.client import MistralClient
import logging
import os
from mojodex_core.llm_engine.llm import LLM

logging.basicConfig(level=logging.ERROR)


class MistralAILLM(LLM):

    def __init__(self, mistral_conf):

        try:
            api_key = mistral_conf["api_key"]
            super().__init__(name=mistral_conf["model_name"], model=mistral_conf["api_model"])

            endpoint = mistral_conf.get("endpoint") if mistral_conf.get(
                "endpoint") else None
            api_type = "azure" if mistral_conf.get(
                "endpoint") else "la_plateforme"

            self.client = MistralClient(
                api_key=api_key,
                endpoint=endpoint if api_type == 'azure' else "https://api.mistral.ai",
            )
            # TODO: manage llm_backup_conf to manage rate limits > see OpenAILLM implementation

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} __init__  : {e}")

    # TODO: implement this method with appropriate encoding for Mistral
    def num_tokens_from_text_messages(self, messages: List[Any]):
        """Returns the number of tokens used by a list of messages."""
        pass

    def _chat_completion(self, messages: List[Any], temperature: float, max_tokens: int, stream: bool = False,
                         stream_callback=None):
        try:
            # Convert messages into Mistral ChatMessages
            if len(messages) == 1:
                messages = [ChatMessage(role='user', content=messages[0]['content'])]
            else:
                messages = [ChatMessage(role=message['role'], content=message['content']) for message in messages]

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
                            self.logger.error(
                                f"🔴 Error in streamCallback : {e}")
            else:
                response = self.client.chat(
                    model=self.model, messages=messages, temperature=temperature, max_tokens=max_tokens)

                complete_text = response.choices[0].message.content
            # [content.text for content in stream_response.choices]
            return [complete_text]

        except Exception as e:
            raise Exception(f"_chat_completion: {e}")

    def invoke(self, messages: List[Any], user_id: str, temperature: float, max_tokens: int, label: str,
               stream: bool = False, stream_callback=None, user_task_execution_pk: int = None,
               task_name_for_system: str = None, **kwargs):
        # TODO: it seems mistral does accept response_format https://github.com/mistralai/client-python/blob/main/src/mistralai/client.py#L26
        try:

            responses = self._chat_completion(messages, temperature, max_tokens, stream=stream,
                                              stream_callback=stream_callback)

            self._write_in_dataset(
                {"temperature": temperature, "max_tokens": max_tokens, "n_responses": 1,
                 "frequency_penalty": None, "presence_penalty": None,
                 "messages": [{'role': message.get('role') if message.get('role') else 'unknown',
                               'content': message.get('content') if message.get('content') else "no_content"} for
                              message in messages], "responses": responses, "model_config": self.model},
                task_name_for_system, "chat", label=label)

            return responses

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} - name: {self.name} - model:{self.model} - invoke: {e}")
