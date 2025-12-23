"""
Tests for the Retriever class.

TDD: These tests define the expected behavior for semantic retrieval.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestRetrieverInitialization:
    """Test Retriever initialization."""

    def test_create_retriever(self) -> None:
        """Should create a Retriever instance."""
        from calculus_rag.retrieval.retriever import Retriever

        mock_embedder = MagicMock()
        mock_vector_store = MagicMock()

        retriever = Retriever(embedder=mock_embedder, vector_store=mock_vector_store)

        assert retriever is not None
        assert retriever.embedder == mock_embedder
        assert retriever.vector_store == mock_vector_store


@pytest.mark.asyncio
class TestRetrieverRetrieve:
    """Test basic retrieval functionality."""

    async def test_retrieve_basic(self) -> None:
        """Should retrieve relevant chunks for a query."""
        from calculus_rag.retrieval.retriever import Retriever
        from calculus_rag.vectorstore.base import QueryResult

        # Mock embedder
        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [0.1] * 768

        # Mock vector store
        mock_vector_store = AsyncMock()
        mock_vector_store.query.return_value = [
            QueryResult(
                id="chunk_1",
                content="A limit describes the value a function approaches.",
                metadata={"topic": "limits.introduction", "difficulty": 3},
                score=0.95,
            ),
            QueryResult(
                id="chunk_2",
                content="The derivative measures the rate of change.",
                metadata={"topic": "derivatives.definition", "difficulty": 3},
                score=0.82,
            ),
        ]

        retriever = Retriever(embedder=mock_embedder, vector_store=mock_vector_store)
        results = await retriever.retrieve("What is a limit?", n_results=2)

        assert len(results) == 2
        assert results[0].chunk_id == "chunk_1"
        assert results[0].score == 0.95
        assert results[0].metadata["topic"] == "limits.introduction"
        assert "limit" in results[0].content

    async def test_retrieve_embeds_query(self) -> None:
        """Should embed the query before searching."""
        from calculus_rag.retrieval.retriever import Retriever

        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [0.5] * 768

        mock_vector_store = AsyncMock()
        mock_vector_store.query.return_value = []

        retriever = Retriever(embedder=mock_embedder, vector_store=mock_vector_store)
        await retriever.retrieve("Test query", n_results=5)

        # Verify embedder was called
        mock_embedder.embed.assert_called_once_with("Test query")

    async def test_retrieve_passes_embedding_to_store(self) -> None:
        """Should pass the query embedding to the vector store."""
        from calculus_rag.retrieval.retriever import Retriever

        query_embedding = [0.3] * 768
        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = query_embedding

        mock_vector_store = AsyncMock()
        mock_vector_store.query.return_value = []

        retriever = Retriever(embedder=mock_embedder, vector_store=mock_vector_store)
        await retriever.retrieve("Test", n_results=10)

        # Verify vector store was called with correct embedding
        mock_vector_store.query.assert_called_once()
        call_args = mock_vector_store.query.call_args
        assert call_args.kwargs["query_embedding"] == query_embedding
        assert call_args.kwargs["n_results"] == 10

    async def test_retrieve_empty_query_raises_error(self) -> None:
        """Should raise error for empty query."""
        from calculus_rag.retrieval.retriever import Retriever

        mock_embedder = MagicMock()
        mock_vector_store = AsyncMock()

        retriever = Retriever(embedder=mock_embedder, vector_store=mock_vector_store)

        with pytest.raises(ValueError, match="Query cannot be empty"):
            await retriever.retrieve("", n_results=5)

    async def test_retrieve_with_filters(self) -> None:
        """Should pass filters to vector store."""
        from calculus_rag.retrieval.retriever import Retriever

        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [0.1] * 768

        mock_vector_store = AsyncMock()
        mock_vector_store.query.return_value = []

        retriever = Retriever(embedder=mock_embedder, vector_store=mock_vector_store)
        await retriever.retrieve(
            "Test",
            n_results=5,
            filters={"topic": "limits.introduction"},
        )

        call_args = mock_vector_store.query.call_args
        assert call_args.kwargs["where"] == {"topic": "limits.introduction"}


@pytest.mark.asyncio
class TestRetrieverTopicFiltering:
    """Test topic-based retrieval."""

    async def test_retrieve_by_topic(self) -> None:
        """Should filter results by topic."""
        from calculus_rag.retrieval.retriever import Retriever
        from calculus_rag.vectorstore.base import QueryResult

        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [0.1] * 768

        mock_vector_store = AsyncMock()
        mock_vector_store.query.return_value = [
            QueryResult(
                id="chunk_1",
                content="Limits content",
                metadata={"topic": "limits.introduction"},
                score=0.9,
            ),
        ]

        retriever = Retriever(embedder=mock_embedder, vector_store=mock_vector_store)
        results = await retriever.retrieve_by_topic(
            "Test",
            topic="limits.introduction",
            n_results=5,
        )

        # Verify filter was passed to vector store
        call_args = mock_vector_store.query.call_args
        assert call_args.kwargs["where"] == {"topic": "limits.introduction"}
        assert len(results) == 1


@pytest.mark.asyncio
class TestRetrieverDifficultyFiltering:
    """Test difficulty-based retrieval."""

    async def test_retrieve_by_difficulty(self) -> None:
        """Should filter results by max difficulty."""
        from calculus_rag.retrieval.retriever import Retriever
        from calculus_rag.vectorstore.base import QueryResult

        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [0.1] * 768

        mock_vector_store = AsyncMock()
        mock_vector_store.query.return_value = [
            QueryResult(
                id="chunk_1",
                content="Easy content",
                metadata={"difficulty": 1},
                score=0.9,
            ),
            QueryResult(
                id="chunk_2",
                content="Medium content",
                metadata={"difficulty": 3},
                score=0.85,
            ),
            QueryResult(
                id="chunk_3",
                content="Hard content",
                metadata={"difficulty": 5},
                score=0.8,
            ),
        ]

        retriever = Retriever(embedder=mock_embedder, vector_store=mock_vector_store)
        results = await retriever.retrieve_by_difficulty(
            "Test",
            max_difficulty=3,
            n_results=5,
        )

        # Should only return chunks with difficulty <= 3
        assert len(results) == 2
        assert all(r.metadata.get("difficulty", 5) <= 3 for r in results)

    async def test_retrieve_by_difficulty_respects_n_results(self) -> None:
        """Should return at most n_results after filtering."""
        from calculus_rag.retrieval.retriever import Retriever
        from calculus_rag.vectorstore.base import QueryResult

        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [0.1] * 768

        mock_vector_store = AsyncMock()
        # Return 5 results all with difficulty 2
        mock_vector_store.query.return_value = [
            QueryResult(
                id=f"chunk_{i}",
                content=f"Content {i}",
                metadata={"difficulty": 2},
                score=0.9 - i * 0.1,
            )
            for i in range(5)
        ]

        retriever = Retriever(embedder=mock_embedder, vector_store=mock_vector_store)
        results = await retriever.retrieve_by_difficulty(
            "Test",
            max_difficulty=3,
            n_results=2,
        )

        # Should return only 2 results
        assert len(results) == 2
