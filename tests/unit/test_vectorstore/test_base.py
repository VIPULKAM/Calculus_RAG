"""
Tests for the base vector store interface.

TDD: These tests define the expected interface before implementation.
"""

from abc import ABC

import pytest


class TestBaseVectorStoreInterface:
    """Test the abstract base vector store interface."""

    def test_base_vectorstore_is_abstract(self) -> None:
        """BaseVectorStore should be an abstract class."""
        from calculus_rag.vectorstore.base import BaseVectorStore

        assert issubclass(BaseVectorStore, ABC)

    def test_base_vectorstore_cannot_be_instantiated(self) -> None:
        """BaseVectorStore should not be directly instantiable."""
        from calculus_rag.vectorstore.base import BaseVectorStore

        with pytest.raises(TypeError):
            BaseVectorStore()  # type: ignore

    def test_base_vectorstore_has_add_method(self) -> None:
        """BaseVectorStore should define an add method."""
        from calculus_rag.vectorstore.base import BaseVectorStore

        assert hasattr(BaseVectorStore, "add")
        assert callable(getattr(BaseVectorStore, "add", None))

    def test_base_vectorstore_has_query_method(self) -> None:
        """BaseVectorStore should define a query method."""
        from calculus_rag.vectorstore.base import BaseVectorStore

        assert hasattr(BaseVectorStore, "query")
        assert callable(getattr(BaseVectorStore, "query", None))

    def test_base_vectorstore_has_delete_method(self) -> None:
        """BaseVectorStore should define a delete method."""
        from calculus_rag.vectorstore.base import BaseVectorStore

        assert hasattr(BaseVectorStore, "delete")
        assert callable(getattr(BaseVectorStore, "delete", None))

    def test_base_vectorstore_has_count_property(self) -> None:
        """BaseVectorStore should define a count property."""
        from calculus_rag.vectorstore.base import BaseVectorStore

        assert hasattr(BaseVectorStore, "count")


class TestQueryResult:
    """Test the QueryResult data model."""

    def test_query_result_has_required_fields(self) -> None:
        """QueryResult should have id, content, metadata, and score."""
        from calculus_rag.vectorstore.base import QueryResult

        result = QueryResult(
            id="test_id",
            content="test content",
            metadata={"topic": "limits"},
            score=0.95,
        )

        assert result.id == "test_id"
        assert result.content == "test content"
        assert result.metadata == {"topic": "limits"}
        assert result.score == 0.95

    def test_query_result_score_between_0_and_1(self) -> None:
        """QueryResult score should typically be between 0 and 1."""
        from calculus_rag.vectorstore.base import QueryResult

        # Valid scores
        result = QueryResult(id="1", content="test", metadata={}, score=0.5)
        assert 0 <= result.score <= 1


class TestConcreteVectorStoreImplementation:
    """Test that concrete implementations work correctly."""

    def test_concrete_vectorstore_can_be_created(self) -> None:
        """A concrete vectorstore implementation should be instantiable."""
        from calculus_rag.vectorstore.base import BaseVectorStore, QueryResult

        class MockVectorStore(BaseVectorStore):
            def __init__(self) -> None:
                self._data: dict[str, dict] = {}

            @property
            def count(self) -> int:
                return len(self._data)

            def add(
                self,
                ids: list[str],
                embeddings: list[list[float]],
                documents: list[str],
                metadatas: list[dict] | None = None,
            ) -> list[str]:
                for i, id_ in enumerate(ids):
                    self._data[id_] = {
                        "embedding": embeddings[i],
                        "document": documents[i],
                        "metadata": metadatas[i] if metadatas else {},
                    }
                return ids

            def query(
                self,
                query_embedding: list[float],
                n_results: int = 10,
                where: dict | None = None,
            ) -> list[QueryResult]:
                return []

            def delete(self, ids: list[str]) -> None:
                for id_ in ids:
                    self._data.pop(id_, None)

        store = MockVectorStore()
        assert store.count == 0

    def test_add_returns_ids(self) -> None:
        """add() should return the list of added IDs."""
        from calculus_rag.vectorstore.base import BaseVectorStore, QueryResult

        class MockVectorStore(BaseVectorStore):
            def __init__(self) -> None:
                self._data: dict[str, dict] = {}

            @property
            def count(self) -> int:
                return len(self._data)

            def add(
                self,
                ids: list[str],
                embeddings: list[list[float]],
                documents: list[str],
                metadatas: list[dict] | None = None,
            ) -> list[str]:
                for i, id_ in enumerate(ids):
                    self._data[id_] = {"document": documents[i]}
                return ids

            def query(
                self,
                query_embedding: list[float],
                n_results: int = 10,
                where: dict | None = None,
            ) -> list[QueryResult]:
                return []

            def delete(self, ids: list[str]) -> None:
                pass

        store = MockVectorStore()
        result = store.add(
            ids=["id1", "id2"],
            embeddings=[[0.1] * 768, [0.2] * 768],
            documents=["doc1", "doc2"],
        )

        assert result == ["id1", "id2"]
        assert store.count == 2
