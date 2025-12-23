"""
Hybrid retrieval combining semantic and keyword (BM25) search.

Uses Reciprocal Rank Fusion (RRF) to combine results from both methods,
providing better retrieval for both conceptual queries and exact term matching.
"""

from dataclasses import dataclass
from typing import Any

from calculus_rag.embeddings.base import BaseEmbedder
from calculus_rag.retrieval.retriever import RetrievalResult
from calculus_rag.vectorstore.pgvector_store import PgVectorStore


@dataclass
class HybridRetrievalResult:
    """
    Result from hybrid retrieval.

    Attributes:
        results: Combined retrieval results.
        semantic_count: Number of results from semantic search.
        keyword_count: Number of results from keyword search.
        overlap_count: Number of results found by both methods.
    """

    results: list[RetrievalResult]
    semantic_count: int
    keyword_count: int
    overlap_count: int


class HybridRetriever:
    """
    Hybrid retriever combining semantic search with keyword (BM25) search.

    This retriever provides better results for:
    - Exact term matching: "L'Hôpital's rule", "chain rule"
    - Conceptual queries: "rate of change" → finds "derivative"
    - Math notation: "∫ sin(x) dx", "f'(x)"

    Uses Reciprocal Rank Fusion (RRF) to combine results from both methods.

    Example:
        >>> retriever = HybridRetriever(embedder, vector_store)
        >>> results = await retriever.retrieve("L'Hôpital's rule for limits")
        >>> # Combines semantic matches + exact "L'Hôpital" keyword matches
    """

    def __init__(
        self,
        embedder: BaseEmbedder,
        vector_store: PgVectorStore,
        semantic_weight: float = 0.7,
    ) -> None:
        """
        Initialize the hybrid retriever.

        Args:
            embedder: The embedding model for semantic search.
            vector_store: The pgvector store (must support hybrid_search).
            semantic_weight: Weight for semantic search (0-1).
                           Higher = more semantic, Lower = more keyword.
                           Default 0.7 = 70% semantic, 30% keyword.
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.semantic_weight = semantic_weight

    async def retrieve(
        self,
        query: str,
        n_results: int = 5,
        filters: dict[str, Any] | None = None,
        semantic_weight: float | None = None,
    ) -> HybridRetrievalResult:
        """
        Retrieve documents using hybrid search.

        Args:
            query: The user's search query.
            n_results: Maximum number of results to return.
            filters: Optional metadata filters.
            semantic_weight: Override default semantic weight for this query.

        Returns:
            HybridRetrievalResult: Combined results with statistics.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        weight = semantic_weight if semantic_weight is not None else self.semantic_weight

        # Get query embedding for semantic search
        query_embedding = self.embedder.embed(query)

        # Get results from both methods for statistics
        # First, get separate results to count overlap
        semantic_results = await self.vector_store.query(
            query_embedding=query_embedding,
            n_results=n_results * 2,
            where=filters,
        )
        keyword_results = await self.vector_store.fulltext_search(
            query_text=query,
            n_results=n_results * 2,
            where=filters,
        )

        # Count overlap
        semantic_ids = {r.id for r in semantic_results}
        keyword_ids = {r.id for r in keyword_results}
        overlap_count = len(semantic_ids & keyword_ids)

        # Now get hybrid results
        hybrid_results = await self.vector_store.hybrid_search(
            query_text=query,
            query_embedding=query_embedding,
            n_results=n_results,
            semantic_weight=weight,
            where=filters,
        )

        # Convert to RetrievalResult
        retrieval_results = [
            RetrievalResult(
                content=r.content,
                score=r.score,
                metadata=r.metadata,
                chunk_id=r.id,
            )
            for r in hybrid_results
        ]

        return HybridRetrievalResult(
            results=retrieval_results,
            semantic_count=len(semantic_results),
            keyword_count=len(keyword_results),
            overlap_count=overlap_count,
        )

    async def retrieve_with_method_comparison(
        self,
        query: str,
        n_results: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, list[RetrievalResult]]:
        """
        Retrieve using all methods separately for comparison.

        Useful for debugging and understanding retrieval behavior.

        Args:
            query: The search query.
            n_results: Results per method.
            filters: Optional metadata filters.

        Returns:
            Dict with keys: 'semantic', 'keyword', 'hybrid'
        """
        query_embedding = self.embedder.embed(query)

        # Get results from each method
        semantic_results = await self.vector_store.query(
            query_embedding=query_embedding,
            n_results=n_results,
            where=filters,
        )

        keyword_results = await self.vector_store.fulltext_search(
            query_text=query,
            n_results=n_results,
            where=filters,
        )

        hybrid_results = await self.vector_store.hybrid_search(
            query_text=query,
            query_embedding=query_embedding,
            n_results=n_results,
            semantic_weight=self.semantic_weight,
            where=filters,
        )

        def to_retrieval_results(results):
            return [
                RetrievalResult(
                    content=r.content,
                    score=r.score,
                    metadata=r.metadata,
                    chunk_id=r.id,
                )
                for r in results
            ]

        return {
            "semantic": to_retrieval_results(semantic_results),
            "keyword": to_retrieval_results(keyword_results),
            "hybrid": to_retrieval_results(hybrid_results),
        }

    def __repr__(self) -> str:
        return f"HybridRetriever(semantic_weight={self.semantic_weight})"
