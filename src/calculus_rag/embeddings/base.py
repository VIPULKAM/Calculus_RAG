"""
Base abstract class for embedding models.

All embedding implementations should inherit from BaseEmbedder.
"""

from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    """
    Abstract base class for text embedding models.

    Provides a consistent interface for different embedding implementations
    (e.g., BGE, OpenAI, local models).
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        """
        Return the dimension of the embedding vectors.

        Returns:
            int: The dimensionality of embeddings produced by this model.
        """
        ...

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """
        Generate an embedding for a single text.

        Args:
            text: The input text to embed.

        Returns:
            list[float]: The embedding vector.
        """
        ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts to embed.

        Returns:
            list[list[float]]: List of embedding vectors.
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(dimension={self.dimension})"
