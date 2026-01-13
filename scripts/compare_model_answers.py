#!/usr/bin/env python3
"""Compare model answers for high school student readability."""

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


def analyze_answer(answer: str) -> dict:
    """Analyze answer for readability metrics."""
    lines = answer.strip().split('\n')
    words = answer.split()
    sentences = answer.count('.') + answer.count('!') + answer.count('?')

    # Count formatting elements
    headers = sum(1 for line in lines if line.strip().startswith('#'))
    bullet_points = sum(1 for line in lines if line.strip().startswith('-') or line.strip().startswith('*'))
    numbered_steps = sum(1 for line in lines if len(line.strip()) >= 2 and line.strip()[0].isdigit())
    latex_inline = answer.count('$') // 2  # Approximate inline math
    latex_display = answer.count('$$') // 2  # Display math

    # Simple readability indicators
    avg_words_per_sentence = len(words) / max(sentences, 1)

    return {
        'word_count': len(words),
        'sentence_count': sentences,
        'avg_words_per_sentence': round(avg_words_per_sentence, 1),
        'headers': headers,
        'bullet_points': bullet_points,
        'numbered_steps': numbered_steps,
        'math_expressions': latex_inline + latex_display,
        'has_step_by_step': 'step' in answer.lower() or numbered_steps > 2,
        'has_examples': 'example' in answer.lower() or 'for instance' in answer.lower(),
        'uses_simple_language': avg_words_per_sentence < 20,
    }


async def get_model_answer(model_name: str, question: str, rag_pipeline: RAGPipeline) -> tuple:
    """Get answer from a specific model."""
    settings = get_settings()

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
        return model_name, response.answer, elapsed, None
    except Exception as e:
        elapsed = time.time() - start_time
        return model_name, None, elapsed, str(e)


async def main():
    settings = get_settings()

    # High school appropriate calculus question
    question = "Explain the chain rule in calculus with a simple example. I'm a high school student learning this for the first time."

    print("=" * 80)
    print("MODEL COMPARISON FOR HIGH SCHOOL STUDENTS")
    print("=" * 80)
    print(f"\nQuestion: {question}\n")

    # Get available cloud models
    cloud_models = get_cloud_models()
    if not cloud_models:
        print("No cloud models found!")
        return

    print(f"Testing {len(cloud_models)} models...\n")

    # Initialize RAG components
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
        use_reranking=False,
    )

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

    # Get answers from all models
    results = []
    for model in cloud_models:
        print(f"  Querying {model}...", end=" ", flush=True)
        model_name, answer, elapsed, error = await get_model_answer(model, question, rag_pipeline)
        if error:
            print(f"❌ Error: {error}")
        else:
            print(f"✅ ({elapsed:.1f}s)")
        results.append((model_name, answer, elapsed, error))

    # Display full answers
    print("\n" + "=" * 80)
    print("FULL ANSWERS")
    print("=" * 80)

    for model_name, answer, elapsed, error in results:
        print(f"\n{'─' * 80}")
        print(f"MODEL: {model_name} ({elapsed:.1f}s)")
        print(f"{'─' * 80}")

        if error:
            print(f"ERROR: {error}")
            continue

        print(answer)

        # Show analysis
        analysis = analyze_answer(answer)
        print(f"\n📊 READABILITY ANALYSIS:")
        print(f"   Words: {analysis['word_count']} | Sentences: {analysis['sentence_count']} | Avg words/sentence: {analysis['avg_words_per_sentence']}")
        print(f"   Structure: {analysis['headers']} headers, {analysis['bullet_points']} bullets, {analysis['numbered_steps']} numbered steps")
        print(f"   Math expressions: {analysis['math_expressions']}")
        print(f"   ✓ Step-by-step: {'Yes' if analysis['has_step_by_step'] else 'No'}")
        print(f"   ✓ Has examples: {'Yes' if analysis['has_examples'] else 'No'}")
        print(f"   ✓ Simple language: {'Yes' if analysis['uses_simple_language'] else 'No'}")

    # Summary comparison table
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    print(f"\n{'Model':<30} {'Time':>8} {'Words':>8} {'Steps':>8} {'Simple':>8} {'Examples':>10}")
    print("-" * 80)

    for model_name, answer, elapsed, error in results:
        if error:
            print(f"{model_name:<30} {'ERROR':>8}")
            continue
        analysis = analyze_answer(answer)
        simple = "✓" if analysis['uses_simple_language'] else "✗"
        examples = "✓" if analysis['has_examples'] else "✗"
        steps = analysis['numbered_steps'] + analysis['bullet_points']
        print(f"{model_name:<30} {elapsed:>7.1f}s {analysis['word_count']:>8} {steps:>8} {simple:>8} {examples:>10}")

    print("\n" + "=" * 80)
    print("RECOMMENDATION CRITERIA FOR HIGH SCHOOL STUDENTS:")
    print("=" * 80)
    print("""
    Best answers for high school students typically have:
    ✓ Step-by-step structure (numbered steps or clear progression)
    ✓ Simple, concrete examples
    ✓ Shorter sentences (< 20 words average)
    ✓ Visual organization (headers, bullets)
    ✓ Relatable analogies
    ✓ Not too long (300-500 words ideal)
    """)

    await vector_store.close()


if __name__ == "__main__":
    asyncio.run(main())
