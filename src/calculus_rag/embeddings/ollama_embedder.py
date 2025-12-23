"""
Ollama-based embedder using mxbai-embed-large.

Uses Ollama's embedding API for consistent architecture with LLM.
"""

from typing import Any

import ollama

from calculus_rag.embeddings.base import BaseEmbedder


class OllamaEmbedder(BaseEmbedder):
    """Embedder using Ollama's embedding models (mxbai-embed-large)."""

    def __init__(
        self,
        model: str = "mxbai-embed-large",
        base_url: str = "http://localhost:11434",
        dimension: int = 1024,
        max_tokens: int = 256,
    ):
        """
        Initialize Ollama embedder.

        Args:
            model: Ollama embedding model name (default: mxbai-embed-large)
            base_url: Ollama server URL
            dimension: Embedding dimension (1024 for mxbai-embed-large)
            max_tokens: Maximum tokens per text (default: 512 for mxbai)
        """
        self._model = model
        self._dimension = dimension
        self._max_tokens = max_tokens
        self._client = ollama.Client(host=base_url)

    def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

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

        try:
            response = self._client.embeddings(
                model=self._model,
                prompt=text,
            )
            return response["embedding"]
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
