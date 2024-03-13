from mistralai.models.chat_completion import ChatMessage
from mistralai.client import MistralClient
from mojodex_core.llm_engine.providers.openai_embedding import OpenAIEmbeddingProvider
from mojodex_core.logging_handler import log_error
import json
import logging
import os
from mojodex_core.llm_engine.llm import LLM

logging.basicConfig(level=logging.ERROR)


class MistralAILLM(LLM):
    def __init__(self, api_key, endpoint, model, api_type='azure', max_retries=3, mistral_conf=None, llm_backup_conf=None, label='unknown'):
        """
        :param api_key: API key
        :param endpoint: Endpoint to call Mistral model API
        :param model: Model to use (deployment_id for azure)
        :param api_type: 'azure' or 'la_plateforme'
        :param max_retries: max_retries calls on rateLimit errors, unavailable... (default 3)
        """
        try:
            self.model = model
            self.max_retries = max_retries
            self.client = MistralClient(
                api_key=api_key,
                endpoint=endpoint if api_type == 'azure' else "https://api.mistral.ai",
            )
            LLM.__init__(
            self, mistral_conf, llm_backup_conf=llm_backup_conf, label=label, max_retries=max_retries)
        except Exception as e:
            raise Exception(
                f"🔴 Error initializing MistralAILLM __init__  : {e}")

    # TODO: implement this method with appropriate encoding for Mistral
    def num_tokens_from_string(self, string):
        """Returns the number of tokens in a text string."""
        return None

    # TODO: implement this method with appropriate encoding for Mistral
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
             
    
    def invoke(self, *args, **kwargs):
        # Method implemented in subclass
        pass