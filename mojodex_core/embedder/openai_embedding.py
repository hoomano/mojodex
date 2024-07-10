from mojodex_core.embedder.embedding_engine import EmbeddingEngine

from mojodex_core.costs_manager.tokens_costs_manager import TokensCostsManager

from mojodex_core.logging_handler import log_error
import time
from openai import RateLimitError, OpenAI, AzureOpenAI
import tiktoken

import os

# TODO: switch to text-embedding-3-small and text-embedding-3-large https://platform.openai.com/docs/guides/embeddings/what-are-embeddings
class OpenAIEmbedding(EmbeddingEngine):
    dataset_dir = "/data/prompts_dataset"
    
    
    def __init__(self, model, api_key, api_type, deployment=None, api_base=None, api_version=None):
        try:
            self.model = model
            self.client = AzureOpenAI(
                api_version=api_version,
                azure_endpoint=api_base,
                azure_deployment=deployment,
                api_key=api_key,
            ) if api_type == 'azure' else OpenAI(api_key=api_key)

            self.tokens_costs_manager = TokensCostsManager()

        except Exception as e:
            log_error(f"Error in OpenAIEmbedding __init__: {e}", notify_admin=False)

    @property
    def tokenizer(self):
        return tiktoken.get_encoding("cl100k_base") # The encoding scheme to use for tokenization

    # calculate the number of tokens in a given string
    def _num_tokens_from_string(self, string):
        # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
        """Returns the number of tokens in a text string."""
        num_tokens = len(self.tokenizer.encode(string))
        return num_tokens

    def embed(self, text, user_id, label, user_task_execution_pk=None, task_name_for_system=None, retries=12, waiting_time=5):
        try:
            try:
                n_tokens_prompt = self._num_tokens_from_string(text)
            except Exception as e:
                log_error(
                    f"OpenAIEmbedding: embed - num_tokens_from_string: {e}")
                n_tokens_prompt = 0
            embedding = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            responses = embedding.data[0].embedding
            self.tokens_costs_manager.on_tokens_counted(user_id, n_tokens_prompt, 0, 0,
                                                        self.model, label, user_task_execution_pk, task_name_for_system)
            return responses
        except RateLimitError as e:
            # wait 5 seconds and retry because we are in background, we can wait
            if retries == 0:
                raise Exception(
                    f"🔴 Error in Mojodex OpenAI embed, rate limit exceeded despite all retries {e}")
            time.sleep(waiting_time)
            return self.embed(text, user_id, user_task_execution_pk, task_name_for_system, retries=retries-1)
        except Exception as e:
            raise Exception(f"🔴 Error in Mojodex OpenAI embed: {e}")
    
    