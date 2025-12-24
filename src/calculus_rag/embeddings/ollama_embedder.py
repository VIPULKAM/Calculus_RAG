"""
Ollama-based embedder using mxbai-embed-large.

Uses Ollama's embedding API for consistent architecture with LLM.
Includes LRU caching to avoid redundant API calls for repeated queries.
"""

from collections import OrderedDict
from typing import Any

import ollama

from calculus_rag.embeddings.base import BaseEmbedder


class LRUCache:
    """Simple LRU cache implementation."""

    def __init__(self, maxsize: int = 1000):
        self._cache: OrderedDict[str, list[float]] = OrderedDict()
        self._maxsize = maxsize
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> list[float] | None:
        """Get item from cache, moving it to end (most recent)."""
        if key in self._cache:
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
        self._misses += 1
        return None

    def put(self, key: str, value: list[float]) -> None:
        """Add item to cache, evicting oldest if full."""
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self._maxsize:
                self._cache.popitem(last=False)  # Remove oldest
            self._cache[key] = value

    @property
    def stats(self) -> dict:
        """Return cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "size": len(self._cache),
            "maxsize": self._maxsize,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
        }


class OllamaEmbedder(BaseEmbedder):
    """Embedder using Ollama's embedding models (mxbai-embed-large)."""

    def __init__(
        self,
        model: str = "mxbai-embed-large",
        base_url: str = "http://localhost:11434",
        dimension: int = 1024,
        max_tokens: int = 256,
        cache_size: int = 1000,
    ):
        """
        Initialize Ollama embedder.

        Args:
            model: Ollama embedding model name (default: mxbai-embed-large)
            base_url: Ollama server URL
            dimension: Embedding dimension (1024 for mxbai-embed-large)
            max_tokens: Maximum tokens per text (default: 512 for mxbai)
            cache_size: Maximum number of embeddings to cache (default: 1000)
        """
        self._model = model
        self._dimension = dimension
        self._max_tokens = max_tokens
        self._client = ollama.Client(host=base_url)
        self._cache = LRUCache(maxsize=cache_size)

    def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Uses LRU cache to avoid redundant API calls for repeated queries.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self._dimension

        # Truncate text to max_tokens (rough approximation: 1 token ~= 4 chars)
        max_chars = self._max_tokens * 4
        if len(text) > max_chars:
            text = text[:max_chars]

        # Check cache first
        cached = self._cache.get(text)
        if cached is not None:
            return cached

        # Generate embedding via API
        try:
            response = self._client.embeddings(
                model=self._model,
                prompt=text,
            )
            embedding = response["embedding"]

            # Store in cache for future use
            self._cache.put(text, embedding)

            return embedding
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding: {e}")

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embeddings.append(self.embed(text))
        return embeddings

    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        return self._dimension

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model

    @property
    def cache_stats(self) -> dict:
        """Get cache statistics for monitoring."""
        return self._cache.stats
