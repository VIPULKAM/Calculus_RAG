"""
BGE (BAAI General Embedding) embedder implementation.

Uses the sentence-transformers library to generate embeddings with BGE models.
"""

from sentence_transformers import SentenceTransformer

from calculus_rag.embeddings.base import BaseEmbedder


class BGEEmbedder(BaseEmbedder):
    """
    Embedder using BAAI BGE models via sentence-transformers.

    BGE models are state-of-the-art open-source embedding models that work
    well for general text and technical content.

    Supported models:
        - BAAI/bge-small-en-v1.5: 384 dimensions, fastest
        - BAAI/bge-base-en-v1.5: 768 dimensions, balanced
        - BAAI/bge-large-en-v1.5: 1024 dimensions, most accurate
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-base-en-v1.5",
        device: str = "cpu",
    ) -> None:
        """
        Initialize the BGE embedder.

        Args:
            model_name: HuggingFace model name (default: bge-base-en-v1.5).
            device: Device to run model on ("cpu", "cuda", or "mps").
        """
        self.model_name = model_name
        self.device = device

        # Load the model
        self._model = SentenceTransformer(model_name, device=device)

        # Get dimension from model
        self._dimension = self._model.get_sentence_embedding_dimension()

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._dimension

    def embed(self, text: str) -> list[float]:
        """
        Generate an embedding for a single text.

        Args:
            text: The input text to embed.

        Returns:
            list[float]: The embedding vector (normalized to unit length).

        Raises:
            ValueError: If text is empty or invalid.
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty or whitespace-only text")

        # Encode returns numpy array, convert to list
        embedding = self._model.encode(
            text,
            normalize_embeddings=True,  # Normalize to unit vectors
            show_progress_bar=False,
        )

        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Batch encoding is more efficient than encoding texts one by one.

        Args:
            texts: List of input texts to embed.

        Returns:
            list[list[float]]: List of embedding vectors.

        Raises:
            ValueError: If any text is empty or invalid.
        """
        if not texts:
            return []

        # Check for empty texts
        if any(not text or not text.strip() for text in texts):
            raise ValueError("Cannot embed empty or whitespace-only text")

        # Batch encode
        embeddings = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=32,  # Reasonable batch size
        )

        # Convert from numpy array to list of lists
        return [emb.tolist() for emb in embeddings]

    def __repr__(self) -> str:
        return f"BGEEmbedder(model={self.model_name}, device={self.device}, dimension={self.dimension})"
