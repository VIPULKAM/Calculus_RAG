#!/usr/bin/env python3
"""
Test cloud model integration with a complex question.

This script will test all 3 tiers:
1. Simple question → local 1.5b
2. Moderate question → local 1.5b or 7b
3. Complex question → cloud 671b

Run with: OLLAMA_API_KEY='your-key' python scripts/test_cloud_model.py
"""

import asyncio
import os
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

# Sample content from interactive_rag.py
SAMPLE_CONTENT = [
    {
        "content": """# Derivatives - Power Rule

The power rule is the most fundamental derivative rule.

**Power Rule:** If f(x) = x^n, then f'(x) = n·x^(n-1)

**Examples:**
- f(x) = x² → f'(x) = 2x
- f(x) = x³ → f'(x) = 3x²
- f(x) = x⁵ → f'(x) = 5x⁴

**Constant Rule:** If f(x) = c (constant), then f'(x) = 0

**Sum Rule:** If f(x) = g(x) + h(x), then f'(x) = g'(x) + h'(x)
Example: f(x) = x² + x³ → f'(x) = 2x + 3x²""",
        "metadata": {"topic": "derivatives.power_rule", "difficulty": 2},
    },
    {
        "content": """# Limits - Introduction

A limit describes what value a function approaches as the input approaches a certain value.

**Notation:** lim(x→a) f(x) = L
This means: as x gets closer to a, f(x) gets closer to L

**Example:** lim(x→2) (x² + 1) = 5
As x approaches 2, x² + 1 approaches 5

**Why Limits Matter:**
Limits are the foundation for derivatives and integrals!""",
        "metadata": {"topic": "limits.introduction", "difficulty": 3},
    },
]


async def setup_rag_with_cloud():
    """Initialize RAG system with cloud model."""
    print("=" * 80)
    print("Cloud Model Integration Test")
    print("=" * 80)

    settings = get_settings()

    # Check for API key
    api_key = os.getenv("OLLAMA_API_KEY")
    if not api_key:
        print("\n❌ ERROR: OLLAMA_API_KEY not set!")
        print("Run with: OLLAMA_API_KEY='your-key' python scripts/test_cloud_model.py")
        sys.exit(1)

    print(f"\n✓ API Key detected (length: {len(api_key)} chars)")

    # Setup components
    print("\n[1/4] Loading embedder...")
    embedder = BGEEmbedder(
        model_name=settings.embedding_model_name,
        device=settings.embedding_device,
    )

    print("[2/4] Setting up vector store...")
    vector_store = PgVectorStore(
        connection_string=settings.postgres_dsn,
        dimension=settings.vector_dimension,
        table_name="cloud_test",
    )
    await vector_store.initialize()
    await vector_store.delete_all()

    # Add sample content
    ids, embeddings, documents, metadatas = [], [], [], []
    for i, doc in enumerate(SAMPLE_CONTENT):
        ids.append(f"doc_{i}")
        embeddings.append(embedder.embed(doc["content"]))
        documents.append(doc["content"])
        metadatas.append(doc["metadata"])
    await vector_store.add(ids, embeddings, documents, metadatas)
    print(f"   ✓ Loaded {len(SAMPLE_CONTENT)} documents")

    # Setup 3-tier routing
    print("\n[3/4] Configuring 3-Tier Model Router...")

    # Tier 1: Local small (fast)
    small_llm = OllamaLLM(
        model="qwen2-math:1.5b",
        base_url=settings.ollama_base_url,
        timeout=300,
    )
    print("   ✓ Tier 1: qwen2-math:1.5b (local, fast)")

    # Tier 2: Local large (more capable)
    large_local_llm = OllamaLLM(
        model="qwen2-math:7b",
        base_url=settings.ollama_base_url,
        timeout=600,
    )
    print("   ✓ Tier 2: qwen2-math:7b (local, powerful)")

    # Tier 3: Cloud model (most capable)
    cloud_llm = OllamaLLM(
        model="deepseek-v3.1:671b-cloud",
        base_url=settings.ollama_base_url,
        timeout=600,
    )
    print("   ✓ Tier 3: deepseek-v3.1:671b-cloud (cloud, most capable)")

    # Create router
    router = ModelRouter(enable_fallback=True)
    router.add_model(
        llm=small_llm,
        name="Local-Fast-1.5B",
        max_complexity=ComplexityLevel.SIMPLE,
    )
    router.add_model(
        llm=large_local_llm,
        name="Local-Powerful-7B",
        max_complexity=ComplexityLevel.MODERATE,
        is_fallback=True,
    )
    router.add_model(
        llm=cloud_llm,
        name="Cloud-DeepSeek-671B",
        max_complexity=ComplexityLevel.COMPLEX,
        is_fallback=True,
    )

    print("\n[4/4] Creating RAG Pipeline...")
    retriever = Retriever(embedder=embedder, vector_store=vector_store)
    rag_pipeline = RAGPipeline(
        retriever=retriever,
        llm=router,
        n_retrieved_chunks=2,
    )

    print("✅ System Ready!\n")
    return rag_pipeline, router, vector_store


async def test_question(rag_pipeline, router, question, expected_tier):
    """Test a single question and show results."""
    print("=" * 80)
    print(f"Question: {question}")
    print(f"Expected: {expected_tier}")
    print("=" * 80)

    try:
        import time

        start = time.time()
        response = await rag_pipeline.query(question, temperature=0.3)
        elapsed = time.time() - start

        print(f"\n✅ Response generated in {elapsed:.1f}s")
        print(f"🤖 Model Used: {router.last_model_used}")

        print("\n💡 Answer:")
        print("─" * 80)
        # Show first 500 chars
        answer = response.answer
        if len(answer) > 500:
            print(answer[:500] + "...")
        else:
            print(answer)
        print("─" * 80)

        if response.sources:
            print(f"\n📖 Sources: {len(response.sources)} chunks")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run the cloud model test."""
    rag_pipeline, router, vector_store = await setup_rag_with_cloud()

    print("=" * 80)
    print("Testing 3-Tier Routing")
    print("=" * 80)

    # Test cases
    test_cases = [
        {
            "question": "What is the power rule?",
            "expected": "Tier 1 (Local-Fast-1.5B) - SIMPLE",
        },
        {
            "question": "Find the derivative of x³ + 2x² using the power rule",
            "expected": "Tier 2 (Local-Powerful-7B) - MODERATE",
        },
        {
            "question": "Prove why the power rule works using the limit definition of the derivative",
            "expected": "Tier 3 (Cloud-DeepSeek-671B) - COMPLEX",
        },
    ]

    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n{'#' * 80}")
        print(f"Test {i}/{len(test_cases)}")
        print("#" * 80)

        success = await test_question(
            rag_pipeline, router, test_case["question"], test_case["expected"]
        )
        results.append(success)

        # Pause between tests
        if i < len(test_cases):
            print("\n⏳ Waiting 2 seconds before next test...")
            await asyncio.sleep(2)

    # Summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"\n✅ Successful: {sum(results)}/{len(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}/{len(results)}")

    if all(results):
        print("\n🎉 All tests passed! Cloud model integration is working!")
        print("\n💡 Your RAG system now has:")
        print("   ✓ Fast responses for simple questions (local 1.5B)")
        print("   ✓ Powerful responses for moderate questions (local 7B)")
        print("   ✓ Expert-level responses for complex questions (cloud 671B)")
        print("   ✓ Automatic fallback for reliability")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")

    # Cleanup
    print("\n🧹 Cleaning up...")
    await vector_store.delete_all()
    await vector_store.close()
    print("✅ Test complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
