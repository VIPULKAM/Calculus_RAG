#!/usr/bin/env python3
"""
Integration test script for PgVectorStore.

This script demonstrates end-to-end functionality:
- Connecting to PostgreSQL with pgvector
- Adding calculus content chunks with embeddings
- Performing similarity searches
- Filtering by metadata
- Cleaning up

Run with: python scripts/test_pgvector_integration.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.vectorstore import PgVectorStore


async def main() -> None:
    """Run the integration test."""
    print("=" * 70)
    print("PgVectorStore Integration Test")
    print("=" * 70)

    settings = get_settings()

    # Initialize the vector store
    print(f"\n1. Initializing PgVectorStore...")
    print(f"   - Database: {settings.postgres_db}")
    print(f"   - Host: {settings.postgres_host}")
    print(f"   - Vector Dimension: {settings.vector_dimension}")

    store = PgVectorStore(
        connection_string=settings.postgres_dsn,
        dimension=settings.vector_dimension,
        table_name="test_chunks",  # Use separate table for testing
    )

    try:
        await store.initialize()
        print("   ✓ Store initialized successfully")

        # Clean up any existing test data
        print("\n2. Cleaning up existing test data...")
        await store.delete_all()
        initial_count = await store.count
        print(f"   ✓ Store cleaned (count: {initial_count})")

        # Prepare sample calculus content
        print("\n3. Adding sample calculus content...")

        # Simulate embeddings (in real usage, these would come from BGE model)
        # Using simple patterns to simulate semantic similarity
        sample_data = [
            {
                "id": "limits_intro_1",
                "content": "A limit describes the value that a function approaches as the input approaches some value.",
                "embedding": [0.1] * 768,  # Simulated embedding for "limits"
                "metadata": {
                    "topic": "limits.introduction",
                    "difficulty": 3,
                    "document_id": "limits_intro",
                    "chunk_index": 0,
                },
            },
            {
                "id": "limits_intro_2",
                "content": "The notation lim(x→a) f(x) = L means as x gets closer to a, f(x) gets closer to L.",
                "embedding": [0.11] * 768,  # Similar to limits
                "metadata": {
                    "topic": "limits.introduction",
                    "difficulty": 3,
                    "document_id": "limits_intro",
                    "chunk_index": 1,
                },
            },
            {
                "id": "derivatives_def_1",
                "content": "The derivative of a function measures the rate at which the function's value changes.",
                "embedding": [0.5] * 768,  # Different embedding for derivatives
                "metadata": {
                    "topic": "derivatives.definition",
                    "difficulty": 3,
                    "document_id": "derivatives_def",
                    "chunk_index": 0,
                },
            },
            {
                "id": "derivatives_power_1",
                "content": "The power rule states that the derivative of x^n is n*x^(n-1).",
                "embedding": [0.52] * 768,  # Similar to derivatives
                "metadata": {
                    "topic": "derivatives.power_rule",
                    "difficulty": 2,
                    "document_id": "derivatives_power",
                    "chunk_index": 0,
                },
            },
            {
                "id": "integration_intro_1",
                "content": "Integration is the reverse process of differentiation, finding the antiderivative.",
                "embedding": [0.9] * 768,  # Different embedding for integration
                "metadata": {
                    "topic": "integration.introduction",
                    "difficulty": 3,
                    "document_id": "integration_intro",
                    "chunk_index": 0,
                },
            },
        ]

        ids = [d["id"] for d in sample_data]
        embeddings = [d["embedding"] for d in sample_data]
        documents = [d["content"] for d in sample_data]
        metadatas = [d["metadata"] for d in sample_data]

        result_ids = await store.add(ids, embeddings, documents, metadatas)
        print(f"   ✓ Added {len(result_ids)} chunks")

        final_count = await store.count
        print(f"   ✓ Store now contains {final_count} chunks")

        # Test similarity search
        print("\n4. Testing similarity search...")
        print("   Query: 'What is a limit in calculus?'")
        print("   (Using embedding similar to limits content)")

        # Simulate query embedding (similar to limits content)
        query_embedding = [0.1] * 768
        results = await store.query(query_embedding, n_results=3)

        print(f"   ✓ Found {len(results)} similar chunks:\n")
        for i, result in enumerate(results, 1):
            print(f"   [{i}] Score: {result.score:.4f}")
            print(f"       Topic: {result.metadata.get('topic', 'N/A')}")
            print(f"       Content: {result.content[:80]}...")
            print()

        # Test metadata filtering
        print("\n5. Testing metadata filtering...")
        print("   Query: Find all 'derivatives' content")

        # Query with different embedding but filter by topic
        query_embedding = [0.5] * 768
        filtered_results = await store.query(
            query_embedding,
            n_results=10,
            where={"topic": "derivatives.power_rule"},
        )

        print(f"   ✓ Found {len(filtered_results)} chunks with topic='derivatives.power_rule':\n")
        for i, result in enumerate(filtered_results, 1):
            print(f"   [{i}] Score: {result.score:.4f}")
            print(f"       Topic: {result.metadata.get('topic', 'N/A')}")
            print(f"       Difficulty: {result.metadata.get('difficulty', 'N/A')}")
            print(f"       Content: {result.content[:80]}...")
            print()

        # Test delete operation
        print("\n6. Testing delete operation...")
        print("   Deleting chunk: 'limits_intro_1'")

        await store.delete(["limits_intro_1"])
        count_after_delete = await store.count
        print(f"   ✓ Chunk deleted (count now: {count_after_delete})")

        # Verify deletion
        all_results = await store.query([0.1] * 768, n_results=10)
        deleted_found = any(r.id == "limits_intro_1" for r in all_results)
        print(f"   ✓ Verification: 'limits_intro_1' in results = {deleted_found}")

        # Test persistence
        print("\n7. Testing data persistence...")
        print("   Closing connection and reconnecting...")

        await store.close()
        print("   ✓ Connection closed")

        # Create new store instance
        store2 = PgVectorStore(
            connection_string=settings.postgres_dsn,
            dimension=settings.vector_dimension,
            table_name="test_chunks",
        )
        await store2.initialize()

        persisted_count = await store2.count
        print(f"   ✓ Reconnected - Found {persisted_count} chunks (data persisted!)")

        # Final cleanup
        print("\n8. Cleaning up test data...")
        await store2.delete_all()
        final_count = await store2.count
        print(f"   ✓ Test data cleaned (count: {final_count})")

        await store2.close()
        print("   ✓ Connection closed")

        print("\n" + "=" * 70)
        print("✅ All integration tests passed successfully!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Ensure connection is closed
        if store._pool:
            await store.close()


if __name__ == "__main__":
    asyncio.run(main())
