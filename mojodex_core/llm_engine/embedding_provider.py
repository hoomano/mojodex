from abc import ABC, abstractmethod

from mojodex_core.llm_engine.llm import LLM

class EmbeddingProvider(ABC):
    """
    Abstract base class for Embedding implementations.
    """

    @staticmethod
    def get_embedding_provider():
        """
        Get the Embedding Provider.

        Returns:
            The Embedding Provider based on the configuration file `LLM.llm_conf_filename`.
        """
        embedding_providers = LLM.get_providers()

        # find the embedding provider in the list of providers with model_name = 'embedding'
        embedding_provider = next((provider for provider in embedding_providers if provider['model_name'] == 'embedding'), None)
        if embedding_provider is None:
            raise Exception("No embedding provider found in the providers list")
        return type(embedding_provider['provider']), embedding_provider['config']        
        
    @abstractmethod
    def embed(self, text, user_id, user_task_execution_pk, task_name_for_system, retries=5):
        """
        Abstract method that should be implemented to return the embedding of a given text and store the costs of the operation.
        """
        pass