#!/usr/bin/env python3
"""
Quick RAG test with a single question.

Run with: python scripts/test_rag_quick.py
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.embeddings.bge_embedder import BGEEmbedder
from calculus_rag.llm.ollama_llm import OllamaLLM
from calculus_rag.rag.pipeline import RAGPipeline
from calculus_rag.retrieval.retriever import Retriever
from calculus_rag.vectorstore.pgvector_store import PgVectorStore


async def main() -> None:
    """Run a quick RAG test."""
    print("=" * 80)
    print("Quick RAG Test - Single Question")
    print("=" * 80)

    settings = get_settings()

    # Initialize components
    print("\n[1/4] Loading BGE Embedder...")
    embedder = BGEEmbedder(
        model_name=settings.embedding_model_name,
        device=settings.embedding_device,
    )
    print(f"   ✓ Loaded (dimension: {embedder.dimension})")

    print("\n[2/4] Connecting to Vector Store...")
    vector_store = PgVectorStore(
        connection_string=settings.postgres_dsn,
        dimension=settings.vector_dimension,
        table_name="rag_quick_test",
    )
    await vector_store.initialize()
    await vector_store.delete_all()
    print(f"   ✓ Connected and cleaned")

    # Add ONE simple document
    print("\n[3/4] Adding sample content...")
    content = """# Power Rule for Derivatives

The power rule is the most basic derivative rule in calculus. It states:

If f(x) = x^n, then f'(x) = n * x^(n-1)

For example:
- The derivative of x^2 is 2x
- The derivative of x^3 is 3x^2
- The derivative of x^5 is 5x^4

This makes finding derivatives of polynomial terms very easy!"""

    embedding = embedder.embed(content)
    await vector_store.add(
        ids=["doc1"],
        embeddings=[embedding],
        documents=[content],
        metadatas=[{"topic": "derivatives.power_rule", "difficulty": 2}],
    )
    print(f"   ✓ Added 1 document")

    print("\n[4/4] Initializing RAG Pipeline...")
    llm = OllamaLLM(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        timeout=settings.ollama_request_timeout,
    )
    retriever = Retriever(embedder=embedder, vector_store=vector_store)
    rag = RAGPipeline(retriever=retriever, llm=llm, n_retrieved_chunks=1)
    print(f"   ✓ Pipeline ready")

    # Ask ONE question
    print("\n" + "=" * 80)
    question = "What is the power rule for derivatives?"
    print(f"Question: {question}")
    print("=" * 80)

    print("\n⏳ Generating answer (this may take 1-3 minutes on CPU)...")
    start_time = time.time()

    try:
        response = await rag.query(question, temperature=0.3)
        elapsed = time.time() - start_time

        print(f"\n✅ Answer generated in {elapsed:.1f} seconds")
        print("\n" + "─" * 80)
        print(response.answer)
        print("─" * 80)

        print(f"\n📚 Source: {response.sources[0].metadata.get('topic', 'Unknown')}")
        print(f"   Relevance: {response.sources[0].score:.2f}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    # Cleanup
    await vector_store.delete_all()
    await vector_store.close()

    print("\n" + "=" * 80)
    print("✅ Quick test complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
