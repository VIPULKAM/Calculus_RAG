#!/usr/bin/env python3
"""
Compare answers from different models side-by-side.

Usage: python scripts/compare_models.py
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


async def setup_rag(model_name: str) -> RAGPipeline:
    """Initialize RAG with specified model."""
    settings = get_settings()

    # Load embedder
    embedder = BGEEmbedder(
        model_name=settings.embedding_model_name,
        device=settings.embedding_device,
    )

    # Initialize vector store
    vector_store = PgVectorStore(
        connection_string=settings.postgres_dsn,
        dimension=settings.vector_dimension,
        table_name="model_comparison",
    )
    await vector_store.initialize()

    # Add sample content (power rule)
    content = """# Power Rule for Derivatives

The power rule is the most basic derivative rule in calculus. It states:

If f(x) = x^n, then f'(x) = n * x^(n-1)

For example:
- The derivative of x^2 is 2x
- The derivative of x^3 is 3x^2
- The derivative of x^5 is 5x^4

This makes finding derivatives of polynomial terms very easy!"""

    count = await vector_store.count
    if count == 0:
        embedding = embedder.embed(content)
        await vector_store.add(
            ids=["doc1"],
            embeddings=[embedding],
            documents=[content],
            metadatas=[{"topic": "derivatives.power_rule", "difficulty": 2}],
        )

    # Initialize LLM with specified model
    llm = OllamaLLM(
        model=model_name,
        base_url=settings.ollama_base_url,
        timeout=settings.ollama_request_timeout,
    )

    # Create RAG pipeline
    retriever = Retriever(embedder=embedder, vector_store=vector_store)
    rag_pipeline = RAGPipeline(
        retriever=retriever,
        llm=llm,
        n_retrieved_chunks=1,
    )

    return rag_pipeline, vector_store


async def test_model(model_name: str, question: str) -> tuple:
    """Test a model and return answer + time."""
    print(f"\n{'=' * 80}")
    print(f"Testing: {model_name}")
    print('=' * 80)

    rag, vector_store = await setup_rag(model_name)

    print(f"⏳ Generating answer with {model_name}...")
    start_time = time.time()

    try:
        response = await rag.query(question, temperature=0.3)
        elapsed = time.time() - start_time

        print(f"✅ Answer generated in {elapsed:.1f} seconds")
        return response.answer, elapsed, None

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Error after {elapsed:.1f} seconds: {e}")
        return None, elapsed, str(e)
    finally:
        await vector_store.close()


async def main():
    """Run model comparison."""
    print("=" * 80)
    print("Model Comparison: Small vs Large")
    print("=" * 80)

    question = "What is the power rule for derivatives? Give a brief explanation with one example."

    print(f"\n📝 Question: {question}\n")

    # Test both models
    models = [
        ("qwen2-math:1.5b", "Small Local Model (1.5B params)"),
        ("deepseek-v3.1:671b-cloud", "Large Cloud Model (671B params)"),
    ]

    results = {}

    for model_name, description in models:
        print(f"\n{'─' * 80}")
        print(f"📊 {description}")
        answer, elapsed, error = await test_model(model_name, question)
        results[model_name] = {
            "description": description,
            "answer": answer,
            "time": elapsed,
            "error": error,
        }

    # Display comparison
    print("\n" + "=" * 80)
    print("COMPARISON RESULTS")
    print("=" * 80)

    for model_name, result in results.items():
        print(f"\n{'─' * 80}")
        print(f"Model: {model_name}")
        print(f"Description: {result['description']}")
        print(f"Time: {result['time']:.1f} seconds")
        print('─' * 80)

        if result['error']:
            print(f"❌ Error: {result['error']}")
        else:
            print(result['answer'])

    print("\n" + "=" * 80)
    print("Analysis:")
    print("=" * 80)

    # Compare times
    small_time = results["qwen2-math:1.5b"]["time"]
    large_time = results["deepseek-v3.1:671b-cloud"]["time"]

    print(f"\n⏱️  Speed Comparison:")
    print(f"   Small model: {small_time:.1f}s")
    print(f"   Large model: {large_time:.1f}s")

    if large_time > small_time:
        print(f"   → Large model is {large_time/small_time:.1f}x slower")
    else:
        print(f"   → Large model is faster!")

    print(f"\n💡 Quality Comparison:")
    print(f"   Compare the answers above to see which one:")
    print(f"   • Provides clearer explanations")
    print(f"   • Uses better examples")
    print(f"   • Is more pedagogically effective")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
