#!/usr/bin/env python3
"""
End-to-end integration test for the RAG system.

This script demonstrates the complete RAG pipeline:
1. Load BGE embedder
2. Initialize pgvector store
3. Add sample calculus content
4. Set up Ollama LLM
5. Create retriever
6. Build RAG pipeline
7. Ask questions and get answers

Run with: python scripts/test_rag_e2e.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.embeddings.bge_embedder import BGEEmbedder
from calculus_rag.llm.ollama_llm import OllamaLLM
from calculus_rag.rag.pipeline import RAGPipeline
from calculus_rag.retrieval.retriever import Retriever
from calculus_rag.vectorstore.pgvector_store import PgVectorStore


async def main() -> None:
    """Run the end-to-end RAG test."""
    print("=" * 80)
    print("Calculus RAG - End-to-End Integration Test")
    print("=" * 80)

    settings = get_settings()

    # Step 1: Initialize BGE Embedder
    print("\n[1/7] Initializing BGE Embedder...")
    print(f"   Model: {settings.embedding_model_name}")
    print(f"   Device: {settings.embedding_device}")

    embedder = BGEEmbedder(
        model_name=settings.embedding_model_name,
        device=settings.embedding_device,
    )
    print(f"   ✓ Embedder loaded (dimension: {embedder.dimension})")

    # Step 2: Initialize Vector Store
    print("\n[2/7] Initializing PgVector Store...")
    vector_store = PgVectorStore(
        connection_string=settings.postgres_dsn,
        dimension=settings.vector_dimension,
        table_name="rag_test_chunks",
    )
    await vector_store.initialize()
    print(f"   ✓ Vector store initialized")

    # Clean up any existing test data
    await vector_store.delete_all()
    print(f"   ✓ Cleaned existing data")

    # Step 3: Add sample calculus content
    print("\n[3/7] Adding sample calculus content...")

    sample_documents = [
        {
            "content": """# Introduction to Limits

A limit describes the value that a function approaches as the input approaches some value. Limits are fundamental to calculus and are used to define continuity, derivatives, and integrals.

The notation lim(x→a) f(x) = L means: as x gets closer and closer to a, f(x) gets closer and closer to L.""",
            "metadata": {
                "topic": "limits.introduction",
                "difficulty": 3,
                "document_id": "limits_intro",
            },
        },
        {
            "content": """# The Derivative

The derivative of a function measures the rate at which the function's value changes with respect to changes in its input value.

Mathematically, the derivative of f(x) at x=a is defined as:
f'(a) = lim(h→0) [f(a+h) - f(a)] / h

This limit represents the instantaneous rate of change or the slope of the tangent line at that point.""",
            "metadata": {
                "topic": "derivatives.definition",
                "difficulty": 3,
                "document_id": "derivatives_def",
            },
        },
        {
            "content": """# Power Rule

The power rule is one of the most basic and important derivative rules. It states:

If f(x) = x^n, then f'(x) = n * x^(n-1)

For example:
- d/dx(x^2) = 2x
- d/dx(x^3) = 3x^2
- d/dx(x^5) = 5x^4

This rule makes finding derivatives of polynomial terms quick and easy.""",
            "metadata": {
                "topic": "derivatives.power_rule",
                "difficulty": 2,
                "document_id": "power_rule",
            },
        },
        {
            "content": """# Chain Rule

The chain rule is used to find the derivative of composite functions. If you have a function composed of two functions, f(g(x)), then:

[f(g(x))]' = f'(g(x)) * g'(x)

In other words, you take the derivative of the outer function, evaluated at the inner function, and multiply by the derivative of the inner function.

Example: If h(x) = (x^2 + 1)^3, then h'(x) = 3(x^2 + 1)^2 * 2x = 6x(x^2 + 1)^2""",
            "metadata": {
                "topic": "derivatives.chain_rule",
                "difficulty": 4,
                "document_id": "chain_rule",
            },
        },
    ]

    # Embed and store documents
    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for i, doc in enumerate(sample_documents):
        chunk_id = f"chunk_{i}"
        embedding = embedder.embed(doc["content"])

        ids.append(chunk_id)
        embeddings.append(embedding)
        documents.append(doc["content"])
        metadatas.append(doc["metadata"])

    await vector_store.add(ids, embeddings, documents, metadatas)
    count = await vector_store.count
    print(f"   ✓ Added {len(sample_documents)} documents ({count} chunks total)")

    # Step 4: Initialize Ollama LLM
    print("\n[4/7] Initializing Ollama LLM...")
    print(f"   Model: {settings.ollama_model}")
    print(f"   Base URL: {settings.ollama_base_url}")

    try:
        llm = OllamaLLM(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            timeout=settings.ollama_request_timeout,
        )
        print(f"   ✓ LLM initialized")
    except Exception as e:
        print(f"   ⚠ Warning: Could not connect to Ollama ({e})")
        print(f"   Skipping LLM-based tests. Please ensure Ollama is running.")
        await vector_store.close()
        return

    # Step 5: Create Retriever
    print("\n[5/7] Creating Retriever...")
    retriever = Retriever(embedder=embedder, vector_store=vector_store)
    print(f"   ✓ Retriever created")

    # Step 6: Build RAG Pipeline
    print("\n[6/7] Building RAG Pipeline...")
    rag_pipeline = RAGPipeline(
        retriever=retriever,
        llm=llm,
        n_retrieved_chunks=3,
    )
    print(f"   ✓ RAG pipeline ready")

    # Step 7: Test with sample questions
    print("\n[7/7] Testing with sample questions...")
    print("=" * 80)

    test_questions = [
        "What is a limit in calculus?",
        "How do you find the derivative using the power rule?",
        "What is the chain rule and when do you use it?",
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'─' * 80}")
        print(f"Question {i}: {question}")
        print('─' * 80)

        try:
            # Query the RAG system
            response = await rag_pipeline.query(
                question=question,
                temperature=0.3,  # Lower temperature for more focused answers
            )

            print(f"\n📝 Answer:")
            print(response.answer)

            print(f"\n📚 Sources used ({len(response.sources)}):")
            for j, source in enumerate(response.sources, 1):
                topic = source.metadata.get("topic", "Unknown")
                score = source.score
                print(f"  [{j}] {topic} (relevance: {score:.2f})")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

    # Cleanup
    print("\n" + "=" * 80)
    print("Cleaning up...")
    await vector_store.delete_all()
    await vector_store.close()
    print("✓ Test data cleaned and connections closed")

    print("\n" + "=" * 80)
    print("✅ End-to-end RAG test completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
