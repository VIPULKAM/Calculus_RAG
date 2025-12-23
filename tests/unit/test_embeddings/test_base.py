"""
Tests for the base embedder interface.

TDD: These tests define the expected interface before implementation.
"""

from abc import ABC
from typing import Protocol

import pytest


class TestBaseEmbedderInterface:
    """Test the abstract base embedder interface."""

    def test_base_embedder_is_abstract(self) -> None:
        """BaseEmbedder should be an abstract class."""
        from calculus_rag.embeddings.base import BaseEmbedder

        assert issubclass(BaseEmbedder, ABC)

    def test_base_embedder_cannot_be_instantiated(self) -> None:
        """BaseEmbedder should not be directly instantiable."""
        from calculus_rag.embeddings.base import BaseEmbedder

        with pytest.raises(TypeError):
            BaseEmbedder()  # type: ignore

    def test_base_embedder_has_embed_method(self) -> None:
        """BaseEmbedder should define an embed method."""
        from calculus_rag.embeddings.base import BaseEmbedder

        assert hasattr(BaseEmbedder, "embed")
        assert callable(getattr(BaseEmbedder, "embed", None))

    def test_base_embedder_has_embed_batch_method(self) -> None:
        """BaseEmbedder should define an embed_batch method."""
        from calculus_rag.embeddings.base import BaseEmbedder

        assert hasattr(BaseEmbedder, "embed_batch")
        assert callable(getattr(BaseEmbedder, "embed_batch", None))

    def test_base_embedder_has_dimension_property(self) -> None:
        """BaseEmbedder should define a dimension property."""
        from calculus_rag.embeddings.base import BaseEmbedder

        assert hasattr(BaseEmbedder, "dimension")


class TestConcreteEmbedderImplementation:
    """Test that concrete implementations work correctly."""

    def test_concrete_embedder_can_be_created(self) -> None:
        """A concrete embedder implementation should be instantiable."""
        from calculus_rag.embeddings.base import BaseEmbedder

        class MockEmbedder(BaseEmbedder):
            @property
            def dimension(self) -> int:
                return 768

            def embed(self, text: str) -> list[float]:
                return [0.0] * 768

            def embed_batch(self, texts: list[str]) -> list[list[float]]:
                return [[0.0] * 768 for _ in texts]

        embedder = MockEmbedder()
        assert embedder.dimension == 768

    def test_embed_returns_list_of_floats(self) -> None:
        """embed() should return a list of floats."""
        from calculus_rag.embeddings.base import BaseEmbedder

        class MockEmbedder(BaseEmbedder):
            @property
            def dimension(self) -> int:
                return 768

            def embed(self, text: str) -> list[float]:
                return [0.1] * 768

            def embed_batch(self, texts: list[str]) -> list[list[float]]:
                return [[0.1] * 768 for _ in texts]

        embedder = MockEmbedder()
        result = embedder.embed("test text")

        assert isinstance(result, list)
        assert len(result) == 768
        assert all(isinstance(x, float) for x in result)

    def test_embed_batch_returns_list_of_embeddings(self) -> None:
        """embed_batch() should return a list of embedding vectors."""
        from calculus_rag.embeddings.base import BaseEmbedder

        class MockEmbedder(BaseEmbedder):
            @property
            def dimension(self) -> int:
                return 768

            def embed(self, text: str) -> list[float]:
                return [0.1] * 768

            def embed_batch(self, texts: list[str]) -> list[list[float]]:
                return [[0.1] * 768 for _ in texts]

        embedder = MockEmbedder()
        texts = ["text 1", "text 2", "text 3"]
        result = embedder.embed_batch(texts)

        assert isinstance(result, list)
        assert len(result) == 3
        assert all(len(emb) == 768 for emb in result)
