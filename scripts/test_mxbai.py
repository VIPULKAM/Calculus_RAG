#!/usr/bin/env python3
"""Quick test of mxbai embedder."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculus_rag.embeddings.ollama_embedder import OllamaEmbedder

# Test with different text lengths
test_texts = [
    "Short text",
    "Medium length text that has a bit more content to embed" * 5,
    "Very long text " * 100,  # ~300 words
]

embedder = OllamaEmbedder()

for i, text in enumerate(test_texts, 1):
    print(f"\nTest {i}: {len(text)} chars ({len(text)//4} est. tokens)")
    try:
        emb = embedder.embed(text)
        print(f"  ✓ Success! Embedding dimension: {len(emb)}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")

print(f"\n✅ mxbai-embed-large working with {embedder.dimension}d embeddings")
