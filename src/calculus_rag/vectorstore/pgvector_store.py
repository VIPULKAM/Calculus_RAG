"""
PostgreSQL + pgvector vector store implementation.

This module provides async vector storage using PostgreSQL with the pgvector extension.
"""

import json
from typing import Any

import asyncpg

from calculus_rag.vectorstore.base import BaseVectorStore, QueryResult


def _list_to_vector(embedding: list[float]) -> str:
    """Convert a Python list to pgvector format string."""
    return "[" + ",".join(str(x) for x in embedding) + "]"


class PgVectorStore(BaseVectorStore):
    """
    Vector store using PostgreSQL + pgvector.

    Stores document chunks with their embeddings and supports similarity search
    with metadata filtering.

    Requires:
        - PostgreSQL with pgvector extension installed
        - Database must have pgvector extension enabled
    """

    def __init__(
        self,
        connection_string: str,
        dimension: int = 768,
        table_name: str = "chunks",
    ) -> None:
        """
        Initialize the PgVector store.

        Args:
            connection_string: PostgreSQL connection string.
            dimension: Vector embedding dimension.
            table_name: Name of the table to store chunks.
        """
        self.connection_string = connection_string
        self.dimension = dimension
        self.table_name = table_name
        self._pool: asyncpg.Pool | None = None

    async def initialize(self) -> None:
        """
        Initialize the database connection and schema.

        Creates the pgvector extension and chunks table if they don't exist.
        """
        # Create connection pool
        self._pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=2,
            max_size=10,
        )

        # Create extension and table
        async with self._pool.acquire() as conn:
            # Enable pgvector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # Create chunks table
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    document_id TEXT,
                    chunk_index INTEGER,
                    metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                    embedding vector({self.dimension}),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Create indexes
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx
                ON {self.table_name}
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)

            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_metadata_idx
                ON {self.table_name}
                USING gin (metadata)
            """)

    @property
    async def count(self) -> int:
        """Return the number of chunks in the store."""
        if not self._pool:
            return 0

        async with self._pool.acquire() as conn:
            result = await conn.fetchval(f"SELECT COUNT(*) FROM {self.table_name}")
            return result or 0

    async def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict] | None = None,
    ) -> list[str]:
        """
        Add chunks with embeddings to the store.

        Args:
            ids: Unique identifiers for each chunk.
            embeddings: Embedding vectors for each chunk.
            documents: Text content of each chunk.
            metadatas: Optional metadata for each chunk.

        Returns:
            list[str]: List of IDs that were successfully added.
        """
        if not self._pool:
            raise RuntimeError("Store not initialized. Call initialize() first.")

        if metadatas is None:
            metadatas = [{} for _ in ids]

        async with self._pool.acquire() as conn:
            # Use COPY or INSERT for batch insert
            for id_, embedding, document, metadata in zip(ids, embeddings, documents, metadatas):
                # Extract additional fields from metadata if present
                document_id = metadata.get("document_id", "")
                chunk_index = metadata.get("chunk_index", 0)

                await conn.execute(
                    f"""
                    INSERT INTO {self.table_name}
                        (id, content, document_id, chunk_index, metadata, embedding)
                    VALUES ($1, $2, $3, $4, $5, $6::vector)
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding
                    """,
                    id_,
                    document,
                    document_id,
                    chunk_index,
                    json.dumps(metadata),
                    _list_to_vector(embedding),
                )

        return ids

    async def query(
        self,
        query_embedding: list[float],
        n_results: int = 10,
        where: dict | None = None,
    ) -> list[QueryResult]:
        """
        Query for similar chunks.

        Args:
            query_embedding: The query vector to search with.
            n_results: Maximum number of results to return.
            where: Optional metadata filter conditions.

        Returns:
            list[QueryResult]: List of matching chunks with similarity scores.
        """
        if not self._pool:
            raise RuntimeError("Store not initialized. Call initialize() first.")

        async with self._pool.acquire() as conn:
            # Build WHERE clause for metadata filtering
            where_clause = ""
            params: list[Any] = [query_embedding, n_results]

            if where:
                # Simple equality filter on metadata JSONB
                conditions = []
                for key, value in where.items():
                    param_index = len(params) + 1
                    # Use ->> to extract as text and compare
                    conditions.append(f"metadata->>'{key}' = ${param_index}")
                    params.append(value)

                where_clause = "WHERE " + " AND ".join(conditions)

            # Use cosine distance (1 - cosine similarity)
            # Lower distance = more similar
            # Convert query_embedding to vector format
            query_vec = _list_to_vector(query_embedding)

            query = f"""
                SELECT
                    id,
                    content,
                    metadata,
                    1 - (embedding <=> $1::vector) as similarity
                FROM {self.table_name}
                {where_clause}
                ORDER BY embedding <=> $1::vector
                LIMIT $2
            """

            # Update params to use converted vector string
            params[0] = query_vec
            rows = await conn.fetch(query, *params)

            results = []
            for row in rows:
                result = QueryResult(
                    id=row["id"],
                    content=row["content"],
                    metadata=json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"],
                    score=float(row["similarity"]),
                )
                results.append(result)

            return results

    async def fulltext_search(
        self,
        query_text: str,
        n_results: int = 10,
        where: dict | None = None,
    ) -> list[QueryResult]:
        """
        Perform full-text search using PostgreSQL's tsvector.

        Args:
            query_text: The text query to search for.
            n_results: Maximum number of results to return.
            where: Optional metadata filter conditions.

        Returns:
            list[QueryResult]: List of matching chunks with BM25-like scores.
        """
        if not self._pool:
            raise RuntimeError("Store not initialized. Call initialize() first.")

        async with self._pool.acquire() as conn:
            # Convert query to tsquery format
            # First, sanitize: remove special characters that break tsquery
            import re
            sanitized = re.sub(r'[^\w\s\'-]', ' ', query_text)  # Keep alphanumeric, spaces, hyphens, apostrophes

            # Split into words
            words = sanitized.lower().split()
            # Filter out very short words and common stop words
            words = [w for w in words if len(w) > 2 and w not in {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'was', 'her', 'have'}]

            if not words:
                return []

            ts_query = ' | '.join(words)  # OR for broader matching

            # Build WHERE clause
            where_clause = "WHERE content_tsv @@ to_tsquery('english', $1)"
            params: list[Any] = [ts_query, n_results]

            if where:
                conditions = []
                for key, value in where.items():
                    param_index = len(params) + 1
                    conditions.append(f"metadata->>'{key}' = ${param_index}")
                    params.append(value)
                where_clause += " AND " + " AND ".join(conditions)

            query = f"""
                SELECT
                    id,
                    content,
                    metadata,
                    ts_rank(content_tsv, to_tsquery('english', $1)) as rank
                FROM {self.table_name}
                {where_clause}
                ORDER BY rank DESC
                LIMIT $2
            """

            rows = await conn.fetch(query, *params)

            results = []
            for row in rows:
                result = QueryResult(
                    id=row["id"],
                    content=row["content"],
                    metadata=json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"],
                    score=float(row["rank"]),
                )
                results.append(result)

            return results

    async def hybrid_search(
        self,
        query_text: str,
        query_embedding: list[float],
        n_results: int = 10,
        semantic_weight: float = 0.7,
        where: dict | None = None,
    ) -> list[QueryResult]:
        """
        Perform hybrid search combining semantic and full-text search.

        Uses Reciprocal Rank Fusion (RRF) to combine results from both methods.

        Args:
            query_text: The text query for full-text search.
            query_embedding: The embedding vector for semantic search.
            n_results: Maximum number of results to return.
            semantic_weight: Weight for semantic search (0-1). Full-text gets 1-weight.
            where: Optional metadata filter conditions.

        Returns:
            list[QueryResult]: Combined results with fused scores.
        """
        if not self._pool:
            raise RuntimeError("Store not initialized. Call initialize() first.")

        # Get more results from each method for better fusion
        k = n_results * 3

        # Run both searches
        semantic_results = await self.query(query_embedding, n_results=k, where=where)
        fulltext_results = await self.fulltext_search(query_text, n_results=k, where=where)

        # Reciprocal Rank Fusion (RRF)
        # Score = sum of 1/(k + rank) for each result across methods
        rrf_k = 60  # Constant to prevent high ranks from dominating

        scores: dict[str, float] = {}
        contents: dict[str, str] = {}
        metadatas: dict[str, dict] = {}

        # Add semantic results with weight
        for rank, result in enumerate(semantic_results):
            rrf_score = semantic_weight * (1.0 / (rrf_k + rank + 1))
            scores[result.id] = scores.get(result.id, 0) + rrf_score
            contents[result.id] = result.content
            metadatas[result.id] = result.metadata

        # Add full-text results with weight
        fulltext_weight = 1.0 - semantic_weight
        for rank, result in enumerate(fulltext_results):
            rrf_score = fulltext_weight * (1.0 / (rrf_k + rank + 1))
            scores[result.id] = scores.get(result.id, 0) + rrf_score
            contents[result.id] = result.content
            metadatas[result.id] = result.metadata

        # Sort by combined score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        # Build results
        results = []
        for id_ in sorted_ids[:n_results]:
            result = QueryResult(
                id=id_,
                content=contents[id_],
                metadata=metadatas[id_],
                score=scores[id_],
            )
            results.append(result)

        return results

    async def delete(self, ids: list[str]) -> None:
        """
        Delete chunks by their IDs.

        Args:
            ids: List of chunk IDs to delete.
        """
        if not self._pool:
            raise RuntimeError("Store not initialized. Call initialize() first.")

        async with self._pool.acquire() as conn:
            await conn.execute(
                f"DELETE FROM {self.table_name} WHERE id = ANY($1)",
                ids,
            )

    async def delete_all(self) -> None:
        """Delete all chunks from the store."""
        if not self._pool:
            return

        async with self._pool.acquire() as conn:
            await conn.execute(f"TRUNCATE TABLE {self.table_name}")

    async def close(self) -> None:
        """Close the database connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    def __repr__(self) -> str:
        return f"PgVectorStore(dimension={self.dimension}, table={self.table_name})"
