"""
Tests for BGE embedder implementation.

TDD: These tests define the expected behavior before implementation.
"""

import pytest


class TestBGEEmbedder:
    """Test the BGE embedder implementation."""

    @pytest.mark.slow
    def test_bge_embedder_initialization(self) -> None:
        """Should initialize with model name and device."""
        from calculus_rag.embeddings.bge_embedder import BGEEmbedder

        embedder = BGEEmbedder(
            model_name="BAAI/bge-base-en-v1.5",
            device="cpu",
        )

        assert embedder.model_name == "BAAI/bge-base-en-v1.5"
        assert embedder.device == "cpu"

    @pytest.mark.slow
    def test_bge_embedder_has_correct_dimension(self) -> None:
        """Should report correct embedding dimension."""
        from calculus_rag.embeddings.bge_embedder import BGEEmbedder

        # bge-base has 768 dimensions
        embedder = BGEEmbedder(model_name="BAAI/bge-base-en-v1.5", device="cpu")

        assert embedder.dimension == 768

    @pytest.mark.slow
    def test_embed_single_text(self) -> None:
        """Should embed a single text string."""
        from calculus_rag.embeddings.bge_embedder import BGEEmbedder

        embedder = BGEEmbedder(model_name="BAAI/bge-base-en-v1.5", device="cpu")
        text = "The derivative of x^2 is 2x."

        embedding = embedder.embed(text)

        assert isinstance(embedding, list)
        assert len(embedding) == 768
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.slow
    def test_embed_batch_multiple_texts(self) -> None:
        """Should embed multiple texts in a batch."""
        from calculus_rag.embeddings.bge_embedder import BGEEmbedder

        embedder = BGEEmbedder(model_name="BAAI/bge-base-en-v1.5", device="cpu")
        texts = [
            "The derivative of x^2 is 2x.",
            "Integration is the reverse of differentiation.",
            "A limit describes the value a function approaches.",
        ]

        embeddings = embedder.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 768 for emb in embeddings)
        assert all(isinstance(x, float) for emb in embeddings for x in emb)

    @pytest.mark.slow
    def test_embed_returns_normalized_vectors(self) -> None:
        """Embeddings should be normalized (unit vectors)."""
        import math

        from calculus_rag.embeddings.bge_embedder import BGEEmbedder

        embedder = BGEEmbedder(model_name="BAAI/bge-base-en-v1.5", device="cpu")
        embedding = embedder.embed("Test text")

        # Calculate magnitude
        magnitude = math.sqrt(sum(x * x for x in embedding))

        # Should be approximately 1.0 (unit vector)
        assert abs(magnitude - 1.0) < 0.01

    @pytest.mark.slow
    def test_similar_texts_have_similar_embeddings(self) -> None:
        """Similar texts should have high cosine similarity."""
        from calculus_rag.embeddings.bge_embedder import BGEEmbedder

        embedder = BGEEmbedder(model_name="BAAI/bge-base-en-v1.5", device="cpu")

        text1 = "The derivative measures the rate of change."
        text2 = "Derivatives measure how functions change."
        text_different = "The color of the sky is blue."

        emb1 = embedder.embed(text1)
        emb2 = embedder.embed(text2)
        emb_diff = embedder.embed(text_different)

        # Cosine similarity (dot product since vectors are normalized)
        sim_similar = sum(a * b for a, b in zip(emb1, emb2))
        sim_different = sum(a * b for a, b in zip(emb1, emb_diff))

        # Similar texts should have higher similarity
        assert sim_similar > sim_different
        assert sim_similar > 0.5  # Should be reasonably similar

    @pytest.mark.slow
    def test_embed_handles_empty_string(self) -> None:
        """Should handle empty string gracefully."""
        from calculus_rag.embeddings.bge_embedder import BGEEmbedder

        embedder = BGEEmbedder(model_name="BAAI/bge-base-en-v1.5", device="cpu")

        # Should either return a valid embedding or raise a clear error
        try:
            embedding = embedder.embed("")
            assert len(embedding) == 768
        except ValueError as e:
            assert "empty" in str(e).lower() or "blank" in str(e).lower()

    @pytest.mark.slow
    def test_embed_batch_preserves_order(self) -> None:
        """Batch embeddings should maintain input order."""
        from calculus_rag.embeddings.bge_embedder import BGEEmbedder

        embedder = BGEEmbedder(model_name="BAAI/bge-base-en-v1.5", device="cpu")

        texts = ["First text", "Second text", "Third text"]

        batch_embeddings = embedder.embed_batch(texts)
        individual_embeddings = [embedder.embed(text) for text in texts]

        # Batch should match individual (order preserved)
        for batch_emb, ind_emb in zip(batch_embeddings, individual_embeddings):
            # Check they're very similar (allowing for minor floating point differences)
            diff = sum(abs(a - b) for a, b in zip(batch_emb, ind_emb))
            assert diff < 0.01


class TestBGEEmbedderWithMath:
    """Test BGE embedder with mathematical content."""

    @pytest.mark.slow
    def test_embed_latex_content(self) -> None:
        """Should embed text containing LaTeX."""
        from calculus_rag.embeddings.bge_embedder import BGEEmbedder

        embedder = BGEEmbedder(model_name="BAAI/bge-base-en-v1.5", device="cpu")

        text = "The formula $\\frac{d}{dx}(x^n) = nx^{n-1}$ is the power rule."
        embedding = embedder.embed(text)

        assert len(embedding) == 768
        # Should produce valid embedding despite LaTeX
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.slow
    def test_math_similarity(self) -> None:
        """Math-related texts should cluster together."""
        from calculus_rag.embeddings.bge_embedder import BGEEmbedder

        embedder = BGEEmbedder(model_name="BAAI/bge-base-en-v1.5", device="cpu")

        calc_text1 = "Differentiation is the process of finding derivatives."
        calc_text2 = "Integration is the process of finding integrals."
        unrelated = "The weather is sunny today."

        emb1 = embedder.embed(calc_text1)
        emb2 = embedder.embed(calc_text2)
        emb_unrelated = embedder.embed(unrelated)

        sim_calc = sum(a * b for a, b in zip(emb1, emb2))
        sim_unrelated = sum(a * b for a, b in zip(emb1, emb_unrelated))

        # Calculus topics should be more similar to each other
        assert sim_calc > sim_unrelated
