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

    def __init__(self, embedding_conf, label='openai_embedding'):
        try:
            api_key = embedding_conf["api_key"]
            api_base = embedding_conf["api_base"]
            api_version = embedding_conf["api_version"]
            api_type = embedding_conf["api_type"]
            model = embedding_conf["deployment_id"]
            self.label = label
            # if dataset_dir does not exist, create it
            if not os.path.exists(self.dataset_dir):
                os.mkdir(self.dataset_dir)
            if not os.path.exists(os.path.join(self.dataset_dir, "chat")):
                os.mkdir(os.path.join(self.dataset_dir, "chat"))
            if not os.path.exists(os.path.join(self.dataset_dir, "chat", self.label)):
                os.mkdir(os.path.join(self.dataset_dir, "chat", self.label))

            self.model = model
            self.client = AzureOpenAI(
                api_version=api_version,
                azure_endpoint=api_base,
                azure_deployment=self.model,
                api_key=api_key,
            ) if api_type == 'azure' else OpenAI(api_key=api_key)

            self.label = label
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
        encoding = tiktoken.get_encoding("p50k_base")
        num_tokens = len(encoding.encode(string))
        return num_tokens

    def embed(self, text, user_id, user_task_execution_pk, task_name_for_system, retries=12, wating_time=5):
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
                                                        self.model, self.label, user_task_execution_pk, task_name_for_system)
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
    
    