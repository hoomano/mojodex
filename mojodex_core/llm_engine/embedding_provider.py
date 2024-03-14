from abc import ABC, abstractmethod
import os

class EmbeddingProvider(ABC):
    """
    Abstract base class for Embedding implementations.
    """

    @staticmethod
    def get_embedding_provider():
        """
        Get the Embedding Provider.

        Returns:
            The Embedding Provider based on the environment variable EMBEDDING_ENGINE.
        """
        embedding_engine = os.environ.get("EMBEDDING_ENGINE", "openai")
        if embedding_engine == "openai":
            from mojodex_core.openai_conf import OpenAIConf
            from mojodex_core.llm_engine.providers.openai_embedding import OpenAIEmbedding
            return OpenAIEmbedding, OpenAIConf.conf_embedding
        else:
            raise Exception(f"Unknown embedding engine: {embedding_engine}")

    @abstractmethod
    def embed(self, text, user_id, user_task_execution_pk, task_name_for_system, retries=5):
        """
        Abstract method that should be implemented to return the embedding of a given text and store the costs of the operation.
        """
        pass