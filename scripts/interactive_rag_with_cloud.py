#!/usr/bin/env python3
"""
Interactive RAG with Cloud Model Support

This version shows how to add a cloud model to the routing system.
Requires: Ollama cloud API key or other cloud provider credentials

Usage: python scripts/interactive_rag_with_cloud.py
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

# Import the sample content from interactive_rag
from interactive_rag import SAMPLE_CONTENT


async def setup_rag_with_cloud() -> tuple:
    """Initialize RAG with cloud model in routing."""
    print("=" * 80)
    print("RAG System with Cloud Model Integration")
    print("=" * 80)

    settings = get_settings()

    # Step 1: Load embedder and vector store
    print("\n[1/4] Loading components...")
    embedder = BGEEmbedder(
        model_name=settings.embedding_model_name,
        device=settings.embedding_device,
    )

    vector_store = PgVectorStore(
        connection_string=settings.postgres_dsn,
        dimension=settings.vector_dimension,
        table_name="cloud_interactive",
    )
    await vector_store.initialize()
    await vector_store.delete_all()

    # Load sample content
    print(f"   Loading {len(SAMPLE_CONTENT)} knowledge documents...")
    ids, embeddings, documents, metadatas = [], [], [], []
    for i, doc in enumerate(SAMPLE_CONTENT):
        ids.append(f"doc_{i}")
        embeddings.append(embedder.embed(doc["content"]))
        documents.append(doc["content"])
        metadatas.append(doc["metadata"])
    await vector_store.add(ids, embeddings, documents, metadatas)
    print("   ✓ Knowledge base loaded")

    # Step 2: Set up 3-tier model routing
    print("\n[2/4] Configuring 3-Tier Model Routing...")
    print("   Tier 1: qwen2-math:1.5b (local, fast)")
    print("   Tier 2: qwen2-math:7b (local, powerful)")
    print("   Tier 3: DeepSeek 671B (cloud, most capable)")

    # Tier 1: Small local model (fast, cheap)
    small_llm = OllamaLLM(
        model="qwen2-math:1.5b",
        base_url=settings.ollama_base_url,
        timeout=300,
    )

    # Tier 2: Large local model (moderate speed, more capable)
    large_local_llm = OllamaLLM(
        model="qwen2-math:7b",
        base_url=settings.ollama_base_url,
        timeout=600,
    )

    # Tier 3: Cloud model (requires auth, most capable)
    # Check if cloud model is available
    cloud_available = False
    cloud_llm = None

    # Check for Ollama API key
    if os.getenv("OLLAMA_API_KEY"):
        print("   ✓ Cloud API key detected")
        cloud_available = True
    else:
        print("   ⚠ No OLLAMA_API_KEY found - cloud model disabled")
        print("     Set it with: export OLLAMA_API_KEY='your-key'")

    if cloud_available:
        try:
            cloud_llm = OllamaLLM(
                model="deepseek-v3.1:671b-cloud",
                base_url=settings.ollama_base_url,
                timeout=600,
            )
        except Exception as e:
            print(f"   ⚠ Could not initialize cloud model: {e}")
            cloud_available = False

    # Create router
    router = ModelRouter(enable_fallback=True)

    # Add models in order of preference (cheapest/fastest first)
    router.add_model(
        llm=small_llm,
        name="Local-Fast-1.5B",
        max_complexity=ComplexityLevel.SIMPLE,
    )

    router.add_model(
        llm=large_local_llm,
        name="Local-Powerful-7B",
        max_complexity=ComplexityLevel.MODERATE,
        is_fallback=True,  # Fallback if small fails
    )

    if cloud_available and cloud_llm:
        router.add_model(
            llm=cloud_llm,
            name="Cloud-DeepSeek-671B",
            max_complexity=ComplexityLevel.COMPLEX,
            is_fallback=True,  # Ultimate fallback
        )
        print("   ✓ 3-tier routing configured (with cloud)")
    else:
        print("   ✓ 2-tier routing configured (local only)")

    # Step 3: Create RAG pipeline
    print("\n[3/4] Building RAG Pipeline...")
    retriever = Retriever(embedder=embedder, vector_store=vector_store)
    rag_pipeline = RAGPipeline(
        retriever=retriever,
        llm=router,
        n_retrieved_chunks=2,
    )

    # Step 4: Show cost estimates
    print("\n[4/4] Cost & Performance Estimates:")
    print("   ┌─────────────────────┬────────────┬──────────┬──────────────┐")
    print("   │ Model               │ Speed      │ Cost     │ Use Case     │")
    print("   ├─────────────────────┼────────────┼──────────┼──────────────┤")
    print("   │ qwen2-math:1.5b     │ ~20-30s    │ Free     │ Simple Qs    │")
    print("   │ qwen2-math:7b       │ ~60-90s    │ Free     │ Moderate Qs  │")
    if cloud_available:
        print("   │ deepseek-v3.1:671b  │ ~5-10s     │ Paid API │ Complex Qs   │")
    print("   └─────────────────────┴────────────┴──────────┴──────────────┘")

    print("\n✅ System Ready!\n")
    return rag_pipeline, router, vector_store, cloud_available


async def interactive_session():
    """Run interactive Q&A with cloud support."""
    rag_pipeline, router, vector_store, cloud_available = await setup_rag_with_cloud()

    print("=" * 80)
    print("Interactive Calculus RAG - Cloud-Enhanced")
    print("=" * 80)

    if cloud_available:
        print("\n🌩️  Cloud Model: ENABLED")
        print("   The system will automatically use the cloud model for:")
        print("   • Very complex proofs")
        print("   • Advanced reasoning")
        print("   • When local models fail")
    else:
        print("\n💻 Local Models Only")
        print("   To enable cloud model:")
        print("   1. Get API key from Ollama")
        print("   2. Set: export OLLAMA_API_KEY='your-key'")
        print("   3. Restart this script")

    print("\n📚 Topics: Algebra, Functions, Trig, Limits, Derivatives")
    print("\n💡 Commands: 'topics', 'quit', or ask any calculus question")
    print("=" * 80)

    question_count = 0

    while True:
        try:
            print("\n" + "─" * 80)
            question = input("\n❓ Your Question: ").strip()

            if not question:
                continue

            if question.lower() in ["quit", "exit", "q"]:
                break

            if question.lower() == "topics":
                print("\n📚 Available Topics:")
                topics_seen = set()
                for doc in SAMPLE_CONTENT:
                    topic = doc["metadata"]["topic"]
                    if topic not in topics_seen:
                        diff = doc["metadata"]["difficulty"]
                        print(f"   • {topic} (difficulty: {diff}/5)")
                        topics_seen.add(topic)
                continue

            question_count += 1
            print(f"\n⏳ Processing... (Question #{question_count})")

            # Query RAG
            response = await rag_pipeline.query(question, temperature=0.3)

            # Show which model was used
            model_used = router.last_model_used
            print(f"\n🤖 Model: {model_used}")

            if "Cloud" in model_used:
                print("   💰 Note: This used the cloud API (may incur costs)")

            # Show answer
            print("\n💡 Answer:")
            print("─" * 80)
            print(response.answer)
            print("─" * 80)

            # Show sources
            if response.sources:
                print(f"\n📖 Sources ({len(response.sources)}):")
                for i, source in enumerate(response.sources, 1):
                    topic = source.metadata.get("topic", "Unknown")
                    score = source.score
                    diff = source.metadata.get("difficulty", "?")
                    print(f"   [{i}] {topic} (relevance: {score:.2f}, difficulty: {diff}/5)")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

    # Cleanup
    print("\n🧹 Cleaning up...")
    await vector_store.delete_all()
    await vector_store.close()
    print("✅ Session ended!")


if __name__ == "__main__":
    asyncio.run(interactive_session())
