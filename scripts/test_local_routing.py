#!/usr/bin/env python3
"""
Test smart routing with LOCAL models only.

Uses:
- qwen2-math:1.5b for simple questions (fast)
- qwen2-math:7b for complex questions (more capable)

Run with: python scripts/test_local_routing.py
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.llm.base import LLMMessage
from calculus_rag.llm.model_router import ComplexityLevel, ModelRouter
from calculus_rag.llm.ollama_llm import OllamaLLM


async def main():
    """Test the routing system."""
    print("=" * 80)
    print("Smart Routing Test - Local Models Only")
    print("=" * 80)

    # Set up router with two local models
    print("\n[1/2] Setting up Model Router...")

    small_llm = OllamaLLM(model="qwen2-math:1.5b", timeout=300)
    print("   ✓ Loaded: qwen2-math:1.5b (small, fast)")

    large_llm = OllamaLLM(model="qwen2-math:7b", timeout=600)
    print("   ✓ Loaded: qwen2-math:7b (large, more capable)")

    router = ModelRouter(enable_fallback=True)
    router.add_model(
        llm=small_llm,
        name="Small-1.5B",
        max_complexity=ComplexityLevel.MODERATE,
    )
    router.add_model(
        llm=large_llm,
        name="Large-7B",
        max_complexity=ComplexityLevel.COMPLEX,
        is_fallback=True,
    )
    print("   ✓ Router configured!\n")

    # Test questions
    print("[2/2] Testing Questions...")
    print("=" * 80)

    test_questions = [
        {
            "text": "What is the power rule?",
            "expected": "Small (SIMPLE question)",
        },
        {
            "text": "Calculate the derivative of x^3",
            "expected": "Small (SIMPLE calculation)",
        },
        {
            "text": "Explain the chain rule with an example",
            "expected": "Small (MODERATE question)",
        },
        {
            "text": "Prove that the derivative of sin(x) is cos(x) using the limit definition",
            "expected": "Large (COMPLEX - needs proof)",
        },
    ]

    for i, q in enumerate(test_questions, 1):
        print(f"\n{'─' * 80}")
        print(f"[Question {i}/{len(test_questions)}]")
        print(f"Q: {q['text']}")
        print(f"Expected routing: {q['expected']}")
        print('─' * 80)

        messages = [LLMMessage(role="user", content=q["text"])]

        start = time.time()
        try:
            response = router.generate(messages, temperature=0.3, max_tokens=200)
            elapsed = time.time() - start

            print(f"\n✅ Success in {elapsed:.1f}s")
            print(f"📊 Model used: {router.last_model_used}")
            print(f"🔍 Detected complexity: {response.metadata.get('router_complexity', 'unknown')}")
            print(f"\n💡 Answer (first 200 chars):")
            print(response.content[:200] + "..." if len(response.content) > 200 else response.content)

        except Exception as e:
            elapsed = time.time() - start
            print(f"\n❌ Error after {elapsed:.1f}s: {e}")

    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)
    print("\n📊 How Routing Works:")
    print("   • Analyzes question complexity using keywords")
    print("   • Simple/Moderate → 1.5B model (faster)")
    print("   • Complex → 7B model (more capable)")
    print("   • Auto fallback if small model fails")
    print("\n💡 This optimizes speed while maintaining quality!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
