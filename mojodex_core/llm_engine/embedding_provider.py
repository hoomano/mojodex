from abc import ABC, abstractmethod

class EmbeddingProvider(ABC):
    """
    Abstract base class for Embedding implementations.
    """

    @abstractmethod
    def get_embedding(self, text):
        """
        Abstract method that should be implemented to return the embedding of a given text.
        """
        pass