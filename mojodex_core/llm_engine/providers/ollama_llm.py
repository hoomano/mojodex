from typing import List, Any

from mojodex_core.logging_handler import MojodexCoreLogger

import os
from mojodex_core.llm_engine.llm import LLM
from mojodex_core.llm_engine.mpt import MPT

from mojodex_core.logging_handler import MojodexCoreLogger

from ollama import Client


class OllamaLLM(LLM):

    def __init__(self, ollama_conf):
        try:
            self.endpoint = ollama_conf.get("endpoint") if ollama_conf.get(
                "endpoint") else None

            super().__init__(name=ollama_conf["model_name"], model=ollama_conf.get(
                "model") if ollama_conf.get("model") else None)

            if self.endpoint is None or self.model is None:
                raise Exception(f"🔴 model and endpoint not set in models conf: {ollama_conf}")

            self.client = Client(host=ollama_conf["endpoint"])

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} __init__  : {e}")


    # TODO: implement this method with appropriate encoding for Ollama
    def num_tokens_from_text_messages(self, messages: List[Any]):
        """Returns the number of tokens used by a list of messages."""
        pass

    def _chat_completion(self, messages: List[Any], temperature: float, max_tokens: int, stream: bool = False,
                         stream_callback=None):
        try:

            if stream:
                stream_response = self.client.chat(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    options={"temperature": temperature,
                             "num_predict": max_tokens}
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
                    model=self.model, messages=messages,
                    stream=False,
                    options={"temperature": temperature,
                             "num_predict": max_tokens})

                complete_text = response['message']['content']
            # [content.text for content in stream_response.choices]
            return [complete_text]

        except Exception as e:
            raise Exception(f"_chat_completion: {e}")

    def invoke(self, messages: List[Any], user_id: str, temperature: float, max_tokens: int, label: str,
               stream: bool = False, stream_callback=None, user_task_execution_pk: int = None,
               task_name_for_system: str = None, **kwargs):
        try:

            responses = self._chat_completion(messages, temperature, max_tokens, stream=stream,
                                              stream_callback=stream_callback)

            self._write_in_dataset({"temperature": temperature, "max_tokens": max_tokens, "n_responses": 1,
                                    "frequency_penalty": None, "presence_penalty": None,
                                    "messages": [{'role': message.get('role') if message.get('role') else 'unknown',
                                                  'content': message.get('content') if message.get('content') else "no_content"} for
                                                 message in messages], "responses": responses, "model_config": self.model}, task_name_for_system, "chat", label=label)

            return responses
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} - name: {self.name} - model:{self.model} - invoke: {e}")
