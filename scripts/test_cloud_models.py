#!/usr/bin/env python3
"""Test all cloud models with a calculus question."""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.embeddings.ollama_embedder import OllamaEmbedder
from calculus_rag.llm.ollama_llm import OllamaLLM
from calculus_rag.rag.pipeline import RAGPipeline
from calculus_rag.retrieval.retriever import Retriever
from calculus_rag.vectorstore.pgvector_store import PgVectorStore

import requests


def get_cloud_models():
    """Get available cloud models from Ollama."""
    settings = get_settings()
    try:
        response = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [m["name"] for m in models if "-cloud" in m["name"] or ":cloud" in m["name"]]
    except Exception as e:
        print(f"Error fetching models: {e}")
    return []


async def test_model(model_name: str, question: str, rag_pipeline: RAGPipeline):
    """Test a specific model with a question."""
    settings = get_settings()

    print(f"\n{'='*60}")
    print(f"Testing: {model_name}")
    print(f"{'='*60}")

    # Create LLM for this model
    llm = OllamaLLM(
        model=model_name,
        base_url=settings.ollama_base_url,
        timeout=180,
    )

    start_time = time.time()
    try:
        response = await rag_pipeline.query(
            question=question,
            temperature=0.3,
            llm_override=llm,
        )
        elapsed = time.time() - start_time

        print(f"✅ Success! ({elapsed:.1f}s)")
        print(f"\nQuestion: {question}")
        print(f"\nAnswer preview (first 500 chars):")
        print("-" * 40)
        print(response.answer[:500] + "..." if len(response.answer) > 500 else response.answer)
        print("-" * 40)

        if response.sources:
            print(f"\nSources used: {len(response.sources)}")
            for i, src in enumerate(response.sources[:3], 1):
                print(f"  {i}. {src.metadata.get('source', 'Unknown')} (score: {src.score:.2f})")

        return True, elapsed

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Failed after {elapsed:.1f}s")
        print(f"Error: {e}")
        return False, elapsed


async def main():
    settings = get_settings()

    print("="*60)
    print("Cloud Model Test Suite")
    print("="*60)

    # Get available cloud models
    cloud_models = get_cloud_models()
    if not cloud_models:
        print("No cloud models found!")
        return

    print(f"\nFound {len(cloud_models)} cloud models:")
    for m in cloud_models:
        print(f"  - {m}")

    # Initialize RAG components
    print("\nInitializing RAG system...")

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

    retriever = Retriever(
        embedder=embedder,
        vector_store=vector_store,
        use_reranking=False,  # Disable reranking for faster tests
    )

    # Create pipeline with dummy LLM (we'll override it for each test)
    dummy_llm = OllamaLLM(
        model="qwen2-math:1.5b",
        base_url=settings.ollama_base_url,
        timeout=60,
    )

    rag_pipeline = RAGPipeline(
        retriever=retriever,
        llm=dummy_llm,
        n_retrieved_chunks=3,
    )

    print("RAG system ready!\n")

    # Test question
    question = "What is the derivative of sin(x) and why?"

    print(f"Test Question: {question}")

    # Test each model
    results = []
    for model in cloud_models:
        success, elapsed = await test_model(model, question, rag_pipeline)
        results.append((model, success, elapsed))

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    for model, success, elapsed in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {model:30} | {elapsed:.1f}s")

    passed = sum(1 for _, s, _ in results if s)
    print(f"\nTotal: {passed}/{len(results)} models passed")

    await vector_store.close()


if __name__ == "__main__":
    asyncio.run(main())
