#!/usr/bin/env python3
"""
Test RAG system with the full knowledge base.

Quick test to verify everything works end-to-end.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.embeddings.bge_embedder import BGEEmbedder
from calculus_rag.llm.model_router import ComplexityLevel, ModelRouter
from calculus_rag.llm.ollama_llm import OllamaLLM
from calculus_rag.rag.pipeline import RAGPipeline
from calculus_rag.retrieval.retriever import Retriever
from calculus_rag.vectorstore.pgvector_store import PgVectorStore


async def main():
    """Quick RAG test with knowledge base."""
    print("=" * 80)
    print("Testing RAG with Full Knowledge Base")
    print("=" * 80)

    settings = get_settings()

    # Load components
    print("\n[1/4] Loading embedder...")
    embedder = BGEEmbedder(
        model_name=settings.embedding_model_name,
        device=settings.embedding_device,
    )

    print("[2/4] Connecting to vector store...")
    vector_store = PgVectorStore(
        connection_string=settings.postgres_dsn,
        dimension=settings.vector_dimension,
        table_name="calculus_knowledge",
    )
    await vector_store.initialize()

    print("[3/4] Setting up model router...")
    small_llm = OllamaLLM(model="qwen2-math:1.5b", timeout=300)
    large_llm = OllamaLLM(model="qwen2-math:7b", timeout=600)

    router = ModelRouter(enable_fallback=True)
    router.add_model(small_llm, "Fast-1.5B", ComplexityLevel.MODERATE)
    router.add_model(large_llm, "Powerful-7B", ComplexityLevel.COMPLEX, is_fallback=True)

    print("[4/4] Creating RAG pipeline...")
    retriever = Retriever(embedder=embedder, vector_store=vector_store)
    rag_pipeline = RAGPipeline(retriever=retriever, llm=router, n_retrieved_chunks=3)

    print("\n✅ System ready!\n")

    # Test questions
    test_questions = [
        "What is the power rule for derivatives?",
        "How do I solve quadratic equations?",
        "Explain the limit definition of a derivative",
    ]

    for i, question in enumerate(test_questions, 1):
        print("=" * 80)
        print(f"Question {i}/{len(test_questions)}: {question}")
        print("=" * 80)

        response = await rag_pipeline.query(question, temperature=0.3)

        print(f"\n🤖 Model: {router.last_model_used}")
        print(f"\n💡 Answer:")
        print("-" * 80)
        # Show first 500 chars
        answer = response.answer
        if len(answer) > 500:
            print(answer[:500] + "...")
        else:
            print(answer)
        print("-" * 80)

        if response.sources:
            print(f"\n📖 Sources ({len(response.sources)} chunks):")
            for j, source in enumerate(response.sources, 1):
                src_file = source.metadata.get("source", "Unknown")
                score = source.score
                print(f"   [{j}] {src_file} (relevance: {score:.3f})")

        print("\n")

    await vector_store.close()
    print("=" * 80)
    print("✅ Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
