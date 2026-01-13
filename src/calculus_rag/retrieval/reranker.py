"""
Reranker module for improving retrieval quality.

Uses cross-encoder models to rerank retrieved documents for better relevance.
Cross-encoders are more accurate than bi-encoders because they see query
and document together rather than comparing separate embeddings.
"""

from dataclasses import dataclass
from functools import lru_cache

from sentence_transformers import CrossEncoder


@dataclass
class RerankResult:
    """Result from reranking."""

    content: str
    score: float
    original_score: float
    metadata: dict
    chunk_id: str


class Reranker:
    """
    Reranks retrieved documents using a cross-encoder model.

    Cross-encoders provide more accurate relevance scores by processing
    the query and document together, rather than comparing embeddings.

    Example:
        >>> reranker = Reranker()
        >>> results = reranker.rerank(
        ...     query="What is the chain rule?",
        ...     documents=[doc1, doc2, doc3],
        ...     top_k=5
        ... )
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-large",
        device: str | None = None,
        batch_size: int = 32,
    ) -> None:
        """
        Initialize the reranker.

        Args:
            model_name: HuggingFace model name for the cross-encoder.
            device: Device to run on ('cuda', 'cpu', or None for auto).
            batch_size: Batch size for reranking.
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self._model = None
        self._device = device

    @property
    def model(self) -> CrossEncoder:
        """Lazy load the model on first use."""
        if self._model is None:
            self._model = CrossEncoder(
                self.model_name,
                max_length=512,
                device=self._device,
            )
        return self._model

    def rerank(
        self,
        query: str,
        documents: list[dict],
        top_k: int = 5,
        score_threshold: float | None = None,
    ) -> list[RerankResult]:
        """
        Rerank documents based on relevance to the query.

        Args:
            query: The search query.
            documents: List of documents with 'content', 'score', 'metadata', 'id' keys.
            top_k: Number of top results to return.
            score_threshold: Optional minimum score threshold.

        Returns:
            List of RerankResult sorted by reranked score (descending).
        """
        if not documents:
            return []

        # Prepare query-document pairs for cross-encoder
        pairs = [(query, doc["content"]) for doc in documents]

        # Get cross-encoder scores
        scores = self.model.predict(pairs, batch_size=self.batch_size)

        # Combine with original results
        results = []
        for doc, rerank_score in zip(documents, scores):
            results.append(
                RerankResult(
                    content=doc["content"],
                    score=float(rerank_score),
                    original_score=doc["score"],
                    metadata=doc["metadata"],
                    chunk_id=doc["id"],
                )
            )

        # Sort by reranked score (descending)
        results.sort(key=lambda x: x.score, reverse=True)

        # Apply threshold if specified
        if score_threshold is not None:
            results = [r for r in results if r.score >= score_threshold]

        return results[:top_k]

    def rerank_with_boost(
        self,
        query: str,
        documents: list[dict],
        top_k: int = 5,
        original_weight: float = 0.3,
    ) -> list[RerankResult]:
        """
        Rerank with a blend of original and reranked scores.

        Useful for maintaining some influence of the original vector search.

        Args:
            query: The search query.
            documents: List of documents.
            top_k: Number of top results to return.
            original_weight: Weight for original score (0-1). Rerank weight = 1 - original_weight.

        Returns:
            List of RerankResult with blended scores.
        """
        if not documents:
            return []

        # Get reranked results
        pairs = [(query, doc["content"]) for doc in documents]
        rerank_scores = self.model.predict(pairs, batch_size=self.batch_size)

        # Normalize rerank scores to 0-1 range (sigmoid-like normalization)
        import math
        normalized_rerank = [1 / (1 + math.exp(-s)) for s in rerank_scores]

        # Blend scores
        results = []
        for doc, rerank_score, norm_rerank in zip(documents, rerank_scores, normalized_rerank):
            blended = (original_weight * doc["score"]) + ((1 - original_weight) * norm_rerank)
            results.append(
                RerankResult(
                    content=doc["content"],
                    score=blended,
                    original_score=doc["score"],
                    metadata=doc["metadata"],
                    chunk_id=doc["id"],
                )
            )

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def __repr__(self) -> str:
        return f"Reranker(model={self.model_name})"


@lru_cache(maxsize=1)
def get_reranker(model_name: str = "BAAI/bge-reranker-large") -> Reranker:
    """
    Get a cached reranker instance.

    Uses LRU cache to avoid reloading the model on every call.
    """
    return Reranker(model_name=model_name)
