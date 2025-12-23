"""
Tests for PostgreSQL + pgvector vector store implementation.

TDD: These tests define the expected behavior before implementation.
"""

import pytest
import pytest_asyncio


@pytest.mark.asyncio
class TestPgVectorStoreInitialization:
    """Test PgVectorStore initialization and connection."""

    async def test_create_pgvector_store(self, test_env_vars: dict[str, str]) -> None:
        """Should create a PgVectorStore instance."""
        from calculus_rag.vectorstore.pgvector_store import PgVectorStore

        store = PgVectorStore(
            connection_string=f"postgresql://postgres:postgres@localhost:5432/test_db",
            dimension=768,
        )

        assert store is not None
        assert store.dimension == 768

    async def test_pgvector_store_has_count_property(self) -> None:
        """Should have a count property."""
        from calculus_rag.vectorstore.pgvector_store import PgVectorStore

        store = PgVectorStore(
            connection_string="postgresql://postgres:postgres@localhost:5432/test_db",
            dimension=768,
        )

        # Count should be accessible (even if connection fails, property should exist)
        assert hasattr(store, "count")


@pytest.mark.asyncio
@pytest.mark.slow
class TestPgVectorStoreOperations:
    """Test PgVectorStore CRUD operations."""

    @pytest_asyncio.fixture
    async def pg_store(self, test_env_vars: dict[str, str]):
        """Create a test PgVectorStore with real connection."""
        from calculus_rag.vectorstore.pgvector_store import PgVectorStore

        # Use test database
        store = PgVectorStore(
            connection_string="postgresql://postgres:postgres@localhost:5432/test_calculus_rag",
            dimension=768,
        )

        # Initialize schema
        await store.initialize()

        yield store

        # Cleanup
        await store.delete_all()
        await store.close()

    async def test_add_chunks_to_store(self, pg_store) -> None:
        """Should add chunks with embeddings to the store."""
        ids = ["chunk_1", "chunk_2"]
        embeddings = [[0.1] * 768, [0.2] * 768]
        documents = ["First chunk content", "Second chunk content"]
        metadatas = [
            {"topic": "limits", "difficulty": 1},
            {"topic": "derivatives", "difficulty": 2},
        ]

        result_ids = await pg_store.add(ids, embeddings, documents, metadatas)

        assert result_ids == ids
        assert await pg_store.count == 2

    async def test_query_by_similarity(self, pg_store) -> None:
        """Should query for similar chunks."""
        # Add some chunks
        ids = ["chunk_1", "chunk_2", "chunk_3"]
        embeddings = [[0.1] * 768, [0.9] * 768, [0.15] * 768]
        documents = ["Content 1", "Content 2", "Content 3"]
        metadatas = [
            {"topic": "limits"},
            {"topic": "derivatives"},
            {"topic": "limits"},
        ]

        await pg_store.add(ids, embeddings, documents, metadatas)

        # Query with embedding similar to chunk_1
        query_embedding = [0.12] * 768
        results = await pg_store.query(query_embedding, n_results=2)

        assert len(results) == 2
        # chunk_1 and chunk_3 should be most similar
        assert results[0].id in ["chunk_1", "chunk_3"]

    async def test_query_with_metadata_filter(self, pg_store) -> None:
        """Should filter results by metadata."""
        ids = ["chunk_1", "chunk_2", "chunk_3"]
        embeddings = [[0.1] * 768, [0.1] * 768, [0.1] * 768]
        documents = ["Content 1", "Content 2", "Content 3"]
        metadatas = [
            {"topic": "limits", "difficulty": 1},
            {"topic": "derivatives", "difficulty": 2},
            {"topic": "limits", "difficulty": 3},
        ]

        await pg_store.add(ids, embeddings, documents, metadatas)

        # Query with filter for topic="limits"
        query_embedding = [0.1] * 768
        results = await pg_store.query(
            query_embedding,
            n_results=10,
            where={"topic": "limits"},
        )

        assert len(results) == 2
        assert all(r.metadata["topic"] == "limits" for r in results)

    async def test_delete_chunks(self, pg_store) -> None:
        """Should delete chunks by ID."""
        ids = ["chunk_1", "chunk_2", "chunk_3"]
        embeddings = [[0.1] * 768, [0.2] * 768, [0.3] * 768]
        documents = ["Content 1", "Content 2", "Content 3"]
        metadatas = [{"topic": "test"}] * 3

        await pg_store.add(ids, embeddings, documents, metadatas)
        assert await pg_store.count == 3

        # Delete chunk_2
        await pg_store.delete(["chunk_2"])

        assert await pg_store.count == 2

        # Query should not return deleted chunk
        results = await pg_store.query([0.2] * 768, n_results=10)
        assert all(r.id != "chunk_2" for r in results)

    async def test_query_returns_scores(self, pg_store) -> None:
        """Query results should include similarity scores."""
        ids = ["chunk_1"]
        embeddings = [[0.5] * 768]
        documents = ["Test content"]
        metadatas = [{"topic": "test"}]

        await pg_store.add(ids, embeddings, documents, metadatas)

        query_embedding = [0.5] * 768
        results = await pg_store.query(query_embedding, n_results=1)

        assert len(results) == 1
        assert results[0].score is not None
        assert 0 <= results[0].score <= 1  # Similarity score range


@pytest.mark.asyncio
@pytest.mark.slow
class TestPgVectorStorePersistence:
    """Test that data persists across connections."""

    async def test_data_persists_after_reconnect(self) -> None:
        """Data should persist after closing and reopening connection."""
        from calculus_rag.vectorstore.pgvector_store import PgVectorStore

        conn_str = "postgresql://postgres:postgres@localhost:5432/test_calculus_rag"

        # First connection - add data
        store1 = PgVectorStore(connection_string=conn_str, dimension=768)
        await store1.initialize()

        ids = ["persistent_chunk"]
        embeddings = [[0.5] * 768]
        documents = ["Persistent content"]
        metadatas = [{"topic": "test"}]

        await store1.add(ids, embeddings, documents, metadatas)
        await store1.close()

        # Second connection - verify data exists
        store2 = PgVectorStore(connection_string=conn_str, dimension=768)
        await store2.initialize()

        count = await store2.count
        assert count >= 1

        # Cleanup
        await store2.delete_all()
        await store2.close()


class TestPgVectorStoreSync:
    """Test synchronous wrapper methods."""

    def test_sync_initialization(self) -> None:
        """Should initialize synchronously for convenience."""
        from calculus_rag.vectorstore.pgvector_store import PgVectorStore

        store = PgVectorStore(
            connection_string="postgresql://postgres:postgres@localhost:5432/test_db",
            dimension=768,
        )

        # Should be creatable without async context
        assert store is not None
