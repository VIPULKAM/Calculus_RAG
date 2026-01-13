"""
Retrieval functionality for semantic search.

Combines embeddings and vector storage for efficient document retrieval.
Supports optional reranking for improved relevance.
"""

from dataclasses import dataclass
from typing import Any

from calculus_rag.embeddings.base import BaseEmbedder
from calculus_rag.retrieval.reranker import Reranker
from calculus_rag.utils.text_cleanup import cleanup_math_text
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
    document chunks in the vector store. Optionally uses reranking for
    improved relevance.

    Example:
        >>> retriever = Retriever(embedder, vector_store, use_reranking=True)
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
        reranker: Reranker | None = None,
        use_reranking: bool = False,
        rerank_candidates: int = 20,
    ) -> None:
        """
        Initialize the retriever.

        Args:
            embedder: The embedding model to use for encoding queries.
            vector_store: The vector store containing document chunks.
            reranker: Optional reranker instance. If None and use_reranking=True,
                      a default BGE reranker will be created.
            use_reranking: Whether to use reranking for improved relevance.
            rerank_candidates: Number of candidates to fetch for reranking.
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.use_reranking = use_reranking
        self.rerank_candidates = rerank_candidates

        if use_reranking and reranker is None:
            from calculus_rag.retrieval.reranker import get_reranker
            self._reranker = None  # Lazy load to avoid slow startup
            self._reranker_getter = get_reranker
        else:
            self._reranker = reranker
            self._reranker_getter = None

    @property
    def reranker(self) -> Reranker | None:
        """Lazy load reranker on first use."""
        if self._reranker is None and self._reranker_getter is not None:
            self._reranker = self._reranker_getter()
        return self._reranker

    async def retrieve(
        self,
        query: str,
        n_results: int = 5,
        filters: dict[str, Any] | None = None,
        min_score: float = 0.45,
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant document chunks for a query.

        Args:
            query: The user's question or search query.
            n_results: Maximum number of results to return.
            filters: Optional metadata filters (e.g., {"topic": "limits"}).
            min_score: Minimum similarity score threshold (0-1). Chunks below
                this score are filtered out to reduce hallucination from
                irrelevant context. Default is 0.45.

        Returns:
            list[RetrievalResult]: Retrieved chunks sorted by relevance.

        Raises:
            ValueError: If query is empty.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Embed the query
        query_embedding = self.embedder.embed(query)

        # Determine how many candidates to fetch
        fetch_count = self.rerank_candidates if self.use_reranking else n_results * 2

        # Search the vector store
        results = await self.vector_store.query(
            query_embedding=query_embedding,
            n_results=fetch_count,
            where=filters,
        )

        # Apply reranking if enabled
        if self.use_reranking and self.reranker and results:
            # Prepare documents for reranking
            docs = [
                {
                    "content": cleanup_math_text(r.content),
                    "score": r.score,
                    "metadata": r.metadata,
                    "id": r.id,
                }
                for r in results
            ]

            # Rerank
            reranked = self.reranker.rerank(query, docs, top_k=n_results)

            # Convert to RetrievalResult
            retrieval_results = [
                RetrievalResult(
                    content=r.content,
                    score=r.score,  # Use reranked score
                    metadata={**r.metadata, "original_score": r.original_score},
                    chunk_id=r.chunk_id,
                )
                for r in reranked
            ]
        else:
            # Standard retrieval without reranking
            retrieval_results = [
                RetrievalResult(
                    content=cleanup_math_text(result.content),
                    score=result.score,
                    metadata=result.metadata,
                    chunk_id=result.id,
                )
                for result in results
                if result.score >= min_score
            ]
            retrieval_results = retrieval_results[:n_results]

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
