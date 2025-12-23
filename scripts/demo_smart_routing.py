#!/usr/bin/env python3
"""
Demo: Smart Model Routing

Shows how the system routes simple questions to small models
and complex questions to larger models (with fallback).

Run with: python scripts/demo_smart_routing.py
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.config import get_settings
from calculus_rag.embeddings.bge_embedder import BGEEmbedder
from calculus_rag.llm.model_router import ComplexityLevel, ModelRouter
from calculus_rag.llm.ollama_llm import OllamaLLM
from calculus_rag.rag.pipeline import RAGPipeline
from calculus_rag.retrieval.retriever import Retriever
from calculus_rag.vectorstore.pgvector_store import PgVectorStore


async def setup_rag_with_routing():
    """Initialize RAG system with smart model routing."""
    print("=" * 80)
    print("Smart Model Routing Demo")
    print("=" * 80)

    settings = get_settings()

    # Step 1: Initialize components
    print("\n[1/5] Loading BGE Embedder...")
    embedder = BGEEmbedder(
        model_name=settings.embedding_model_name,
        device=settings.embedding_device,
    )
    print(f"   ✓ Loaded (dimension: {embedder.dimension})")

    print("\n[2/5] Connecting to Vector Store...")
    vector_store = PgVectorStore(
        connection_string=settings.postgres_dsn,
        dimension=settings.vector_dimension,
        table_name="routing_demo",
    )
    await vector_store.initialize()
    await vector_store.delete_all()
    print("   ✓ Connected")

    # Add sample content
    print("\n[3/5] Adding sample content...")
    content = """# Derivatives - Power Rule and Chain Rule

**Power Rule:** If f(x) = x^n, then f'(x) = n·x^(n-1)

Examples:
- f(x) = x² → f'(x) = 2x
- f(x) = x³ → f'(x) = 3x²

**Chain Rule:** For composite functions f(g(x)):
[f(g(x))]' = f'(g(x)) · g'(x)

Example: h(x) = (x² + 1)³
Using chain rule: h'(x) = 3(x² + 1)² · 2x = 6x(x² + 1)²

The chain rule is essential for differentiating complex composite functions."""

    embedding = embedder.embed(content)
    await vector_store.add(
        ids=["doc1"],
        embeddings=[embedding],
        documents=[content],
        metadatas=[{"topic": "derivatives", "difficulty": 3}],
    )
    print("   ✓ Added 1 document")

    # Step 2: Set up model router
    print("\n[4/5] Setting up Smart Model Router...")

    # Small local model - fast, handles simple questions
    small_llm = OllamaLLM(
        model="qwen2-math:1.5b",
        base_url=settings.ollama_base_url,
        timeout=settings.ollama_request_timeout,
    )
    print(f"   ✓ Loaded small model: qwen2-math:1.5b")

    # Large model (cloud) - for complex questions and fallback
    # Note: This will fail without auth, but demonstrates the concept
    large_llm = OllamaLLM(
        model="deepseek-v3.1:671b-cloud",
        base_url=settings.ollama_base_url,
        timeout=settings.ollama_request_timeout,
    )
    print(f"   ✓ Configured large model: deepseek-v3.1:671b-cloud (cloud)")

    # Create router
    router = ModelRouter(enable_fallback=True)
    router.add_model(
        llm=small_llm,
        name="Small-1.5B",
        max_complexity=ComplexityLevel.MODERATE,  # Handles simple & moderate
    )
    router.add_model(
        llm=large_llm,
        name="Large-671B",
        max_complexity=ComplexityLevel.COMPLEX,  # Handles complex
        is_fallback=True,  # Also used as fallback if small fails
    )
    print(f"   ✓ Router configured with 2 models")

    # Step 3: Create RAG pipeline with router
    print("\n[5/5] Creating RAG Pipeline with Router...")
    retriever = Retriever(embedder=embedder, vector_store=vector_store)
    rag_pipeline = RAGPipeline(retriever=retriever, llm=router, n_retrieved_chunks=1)
    print("   ✓ RAG pipeline ready with smart routing!")

    return rag_pipeline, router, vector_store


async def test_question(rag_pipeline, router, question, expected_complexity):
    """Test a question and show which model was used."""
    print("\n" + "=" * 80)
    print(f"Question: {question}")
    print(f"Expected Complexity: {expected_complexity}")
    print("=" * 80)

    start_time = time.time()

    try:
        response = await rag_pipeline.query(question, temperature=0.3)
        elapsed = time.time() - start_time

        # Get routing info
        model_used = response.sources[0].metadata.get("router_model", router.last_model_used)

        print(f"\n✅ Answer generated in {elapsed:.1f} seconds")
        print(f"📊 Model Used: {router.last_model_used}")

        if "router_fallback_from" in response.sources[0].metadata:
            print(f"⚠️  Fallback triggered from: {response.sources[0].metadata['router_fallback_from']}")

        print("\n💡 Answer:")
        print("─" * 80)
        # Show first 500 chars
        answer = response.answer
        if len(answer) > 500:
            print(answer[:500] + "...")
        else:
            print(answer)
        print("─" * 80)

        return True

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ Error after {elapsed:.1f} seconds: {e}")
        return False


async def main():
    """Run the demo."""
    rag_pipeline, router, vector_store = await setup_rag_with_routing()

    print("\n" + "=" * 80)
    print("Testing Different Complexity Levels")
    print("=" * 80)

    # Test questions of varying complexity
    test_cases = [
        {
            "question": "What is the power rule?",
            "complexity": "SIMPLE",
            "reason": "Simple definition question",
        },
        {
            "question": "Find the derivative of x² + 3x",
            "complexity": "SIMPLE",
            "reason": "Basic calculation using power rule",
        },
        {
            "question": "Explain the chain rule and give an example",
            "complexity": "MODERATE",
            "reason": "Requires explanation + example",
        },
        {
            "question": "Prove why the chain rule works using the limit definition",
            "complexity": "COMPLEX",
            "reason": "Requires proof and deep understanding",
        },
    ]

    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n{'#' * 80}")
        print(f"Test Case {i}/{len(test_cases)}")
        print(f"Reason: {test_case['reason']}")
        print('#' * 80)

        success = await test_question(
            rag_pipeline,
            router,
            test_case["question"],
            test_case["complexity"],
        )
        results.append(success)

        # Small pause between questions
        if i < len(test_cases):
            await asyncio.sleep(1)

    # Summary
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n✅ Successful: {sum(results)}/{len(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}/{len(results)}")

    print("\n📊 Routing Strategy:")
    print("   • Simple questions → Small local model (fast, free)")
    print("   • Moderate questions → Small local model (still capable)")
    print("   • Complex questions → Large cloud model (most capable)")
    print("   • Fallback → Large model if small fails")

    print("\n💡 Benefits:")
    print("   ✓ Fast responses for most questions (90% are simple/moderate)")
    print("   ✓ Low cost (cloud model only for ~10% of questions)")
    print("   ✓ Automatic fallback for reliability")
    print("   ✓ Optimal resource usage")

    # Cleanup
    print("\n🧹 Cleaning up...")
    await vector_store.delete_all()
    await vector_store.close()
    print("✅ Demo complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
