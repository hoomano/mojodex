from mojodex_core.llm_engine.embedding_provider import EmbeddingProvider

from mojodex_core.costs_manager.tokens_costs_manager import TokensCostsManager

from mojodex_core.logging_handler import log_error
import time
from openai import RateLimitError, OpenAI, AzureOpenAI
import tiktoken

import os

# TODO: switch to text-embedding-3-small and text-embedding-3-large https://platform.openai.com/docs/guides/embeddings/what-are-embeddings
class OpenAIEmbedding(EmbeddingProvider):
    dataset_dir = "/data/prompts_dataset"
    default_embedding_model = "text-embedding-ada-002"
    
    def __init__(self, embedding_conf):
        try:
            api_key = embedding_conf["api_key"] if "api_key" in embedding_conf else None
            api_base = embedding_conf["api_base"] if "api_base" in embedding_conf else None
            api_version = embedding_conf["api_version"] if "api_version" in embedding_conf else None
            api_type = embedding_conf["api_type"] if "api_type" in embedding_conf else "openai"
            model = embedding_conf["deployment_id"] if "deployment_id" in embedding_conf else embedding_conf["model"]

            self.model = model
            self.client = AzureOpenAI(
                api_version=api_version,
                azure_endpoint=api_base,
                azure_deployment=self.model,
                api_key=api_key,
            ) if api_type == 'azure' else OpenAI(api_key=api_key)

            self.tokens_costs_manager = TokensCostsManager()

        except Exception as e:
            log_error(f"Error in OpenAIEmbedding __init__: {e}", notify_admin=False)

    # calculate the number of tokens in a given string
    def _num_tokens_from_string(self, string):
        # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
        """Returns the number of tokens in a text string."""
        # TODO: find a way to dynamically find the encoding base depending on the embedding model
        encoding = tiktoken.get_encoding("p50k_base")
        num_tokens = len(encoding.encode(string))
        return num_tokens

    def embed(self, text, user_id, user_task_execution_pk, task_name_for_system, label, retries=12, wating_time=5):
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
            time.sleep(wating_time)
            return self.embed(text, user_id, user_task_execution_pk, task_name_for_system, retries=retries-1)
        except Exception as e:
            raise Exception(f"🔴 Error in Mojodex OpenAI embed: {e}")
    
    