"""
Retrieval functionality for semantic search.

Combines embeddings and vector storage for efficient document retrieval.
"""

from dataclasses import dataclass
from typing import Any

from calculus_rag.embeddings.base import BaseEmbedder
from calculus_rag.vectorstore.base import BaseVectorStore, QueryResult


@dataclass
class RetrievalResult:
    """
    Represents a retrieved document chunk.

    Attributes:
        content: The text content of the chunk.
        score: Similarity score (0-1, higher is better).
        metadata: Associated metadata (topic, difficulty, etc.).
        chunk_id: Unique identifier for the chunk.
    """

    content: str
    score: float
    metadata: dict[str, Any]
    chunk_id: str


class Retriever:
    """
    Semantic retrieval using embeddings and vector store.

    The retriever converts queries to embeddings and searches for similar
    document chunks in the vector store.

    Example:
        >>> retriever = Retriever(embedder, vector_store)
        >>> results = await retriever.retrieve(
        ...     query="What is a derivative?",
        ...     n_results=5
        ... )
        >>> for result in results:
        ...     print(f"{result.score:.2f}: {result.content[:50]}")
    """

    def __init__(
        self,
        embedder: BaseEmbedder,
        vector_store: BaseVectorStore,
    ) -> None:
        """
        Initialize the retriever.

        Args:
            embedder: The embedding model to use for encoding queries.
            vector_store: The vector store containing document chunks.
        """
        self.embedder = embedder
        self.vector_store = vector_store

    async def retrieve(
        self,
        query: str,
        n_results: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant document chunks for a query.

        Args:
            query: The user's question or search query.
            n_results: Maximum number of results to return.
            filters: Optional metadata filters (e.g., {"topic": "limits"}).

        Returns:
            list[RetrievalResult]: Retrieved chunks sorted by relevance.

        Raises:
            ValueError: If query is empty.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Embed the query
        query_embedding = self.embedder.embed(query)

        # Search the vector store
        results = await self.vector_store.query(
            query_embedding=query_embedding,
            n_results=n_results,
            where=filters,
        )

        # Convert to RetrievalResult objects
        retrieval_results = [
            RetrievalResult(
                content=result.content,
                score=result.score,
                metadata=result.metadata,
                chunk_id=result.id,
            )
            for result in results
        ]

        return retrieval_results

    async def retrieve_by_topic(
        self,
        query: str,
        topic: str,
        n_results: int = 5,
    ) -> list[RetrievalResult]:
        """
        Retrieve chunks filtered by topic.

        Args:
            query: The user's question.
            topic: Topic identifier (e.g., "limits.introduction").
            n_results: Maximum number of results to return.

        Returns:
            list[RetrievalResult]: Retrieved chunks from the specified topic.
        """
        return await self.retrieve(
            query=query,
            n_results=n_results,
            filters={"topic": topic},
        )

    async def retrieve_by_difficulty(
        self,
        query: str,
        max_difficulty: int,
        n_results: int = 5,
    ) -> list[RetrievalResult]:
        """
        Retrieve chunks at or below a difficulty level.

        Args:
            query: The user's question.
            max_difficulty: Maximum difficulty level (1-5).
            n_results: Maximum number of results to return.

        Returns:
            list[RetrievalResult]: Retrieved chunks filtered by difficulty.

        Note:
            This currently retrieves all results and filters client-side.
            For better performance, implement server-side filtering in the
            vector store.
        """
        # Get more results to account for filtering
        all_results = await self.retrieve(query=query, n_results=n_results * 2)

        # Filter by difficulty
        filtered = [
            r
            for r in all_results
            if r.metadata.get("difficulty", 5) <= max_difficulty
        ]

        # Return top n_results
        return filtered[:n_results]

    def __repr__(self) -> str:
        return f"Retriever(embedder={self.embedder}, vector_store={self.vector_store})"
