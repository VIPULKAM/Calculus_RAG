#!/usr/bin/env python3
"""
Test script for hybrid search functionality.

Tests:
1. Full-text search (BM25) works
2. Hybrid search (semantic + keyword) works
3. Comparison between semantic-only and hybrid results
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.embeddings.ollama_embedder import OllamaEmbedder
from calculus_rag.vectorstore.pgvector_store import PgVectorStore


async def test_hybrid_search():
    """Test hybrid search functionality."""
    settings = get_settings()

    print("=" * 60)
    print("HYBRID SEARCH TEST")
    print("=" * 60)

    # Initialize components
    print("\n1. Initializing embedder and vector store...")
    embedder = OllamaEmbedder(
        model=settings.embedding_model_name,
        base_url=settings.ollama_base_url,
        dimension=settings.vector_dimension,
    )

    vector_store = PgVectorStore(
        connection_string=settings.postgres_dsn,
        dimension=settings.vector_dimension,
        table_name="calculus_knowledge",
    )
    await vector_store.initialize()

    # Test queries - mix of exact terms and conceptual
    test_queries = [
        "L'Hopital's rule",           # Exact term (should benefit from keyword)
        "chain rule derivative",       # Exact terms
        "rate of change",              # Conceptual (should benefit from semantic)
        "integral of sin(x)",          # Math notation
        "limit as x approaches zero",  # Mathematical concept
    ]

    for query in test_queries:
        print(f"\n{'=' * 60}")
        print(f"Query: '{query}'")
        print("=" * 60)

        # Get embedding for query
        query_embedding = embedder.embed(query)

        # Test 1: Semantic search only
        print("\n📊 SEMANTIC SEARCH (top 3):")
        semantic_results = await vector_store.query(
            query_embedding=query_embedding,
            n_results=3,
        )
        for i, r in enumerate(semantic_results, 1):
            preview = r.content[:80].replace("\n", " ")
            print(f"  {i}. [score: {r.score:.4f}] {preview}...")

        # Test 2: Full-text search only
        print("\n🔤 KEYWORD SEARCH (BM25, top 3):")
        try:
            keyword_results = await vector_store.fulltext_search(
                query_text=query,
                n_results=3,
            )
            if keyword_results:
                for i, r in enumerate(keyword_results, 1):
                    preview = r.content[:80].replace("\n", " ")
                    print(f"  {i}. [score: {r.score:.4f}] {preview}...")
            else:
                print("  (no keyword matches)")
        except Exception as e:
            print(f"  Error: {e}")

        # Test 3: Hybrid search
        print("\n🔀 HYBRID SEARCH (70% semantic + 30% keyword, top 3):")
        try:
            hybrid_results = await vector_store.hybrid_search(
                query_text=query,
                query_embedding=query_embedding,
                n_results=3,
                semantic_weight=0.7,
            )
            for i, r in enumerate(hybrid_results, 1):
                preview = r.content[:80].replace("\n", " ")
                print(f"  {i}. [score: {r.score:.4f}] {preview}...")
        except Exception as e:
            print(f"  Error: {e}")

        # Compare: find unique results in hybrid vs semantic
        semantic_ids = {r.id for r in semantic_results[:3]}
        hybrid_ids = {r.id for r in hybrid_results[:3]} if hybrid_results else set()
        new_in_hybrid = hybrid_ids - semantic_ids

        if new_in_hybrid:
            print(f"\n  ✨ Hybrid found {len(new_in_hybrid)} result(s) not in semantic top-3")
        else:
            print("\n  ℹ️  Hybrid and semantic top-3 are identical")

    await vector_store.close()
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_hybrid_search())
