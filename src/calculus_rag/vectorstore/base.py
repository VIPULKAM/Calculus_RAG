"""
Base abstract class for vector stores.

All vector store implementations should inherit from BaseVectorStore.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class QueryResult:
    """
    Represents a single result from a vector store query.

    Attributes:
        id: Unique identifier of the document.
        content: The text content of the document.
        metadata: Associated metadata dictionary.
        score: Similarity score (typically 0-1, higher is more similar).
    """

    id: str
    content: str
    metadata: dict = field(default_factory=dict)
    score: float = 0.0


class BaseVectorStore(ABC):
    """
    Abstract base class for vector storage backends.

    Provides a consistent interface for different vector store implementations
    (e.g., Chroma, Qdrant, pgvector).
    """

    @property
    @abstractmethod
    def count(self) -> int:
        """
        Return the number of documents in the store.

        Returns:
            int: Total count of stored documents.
        """
        ...

    @abstractmethod
    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict] | None = None,
    ) -> list[str]:
        """
        Add documents with their embeddings to the store.

        Args:
            ids: Unique identifiers for each document.
            embeddings: Embedding vectors for each document.
            documents: Text content of each document.
            metadatas: Optional metadata for each document.

        Returns:
            list[str]: List of IDs that were successfully added.
        """
        ...

    @abstractmethod
    def query(
        self,
        query_embedding: list[float],
        n_results: int = 10,
        where: dict | None = None,
    ) -> list[QueryResult]:
        """
        Query the store for similar documents.

        Args:
            query_embedding: The query vector to search with.
            n_results: Maximum number of results to return.
            where: Optional filter conditions.

        Returns:
            list[QueryResult]: List of matching documents with scores.
        """
        ...

    @abstractmethod
    def delete(self, ids: list[str]) -> None:
        """
        Delete documents by their IDs.

        Args:
            ids: List of document IDs to delete.
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(count={self.count})"
