from abc import ABC, abstractmethod

class EmbeddingProvider(ABC):
    """
    Abstract base class for Embedding implementations.
    """

    @abstractmethod
    def embed(self, text, user_id, label, user_task_execution_pk, task_name_for_system, retries=5):
        """
        Abstract method that should be implemented to return the embedding of a given text and store the costs of the operation.
        """
        pass