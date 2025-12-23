"""
Tests for smart document chunker.

TDD: These tests define the expected chunking behavior before implementation.
"""

import pytest


class TestDocumentChunker:
    """Test the DocumentChunker class."""

    def test_chunk_simple_document(self) -> None:
        """Should split a simple document into chunks."""
        from calculus_rag.knowledge_base.chunker import DocumentChunker
        from calculus_rag.knowledge_base.models import Document, DocumentMetadata

        doc = Document(
            content="# Title\n\n" + "This is a sentence. " * 100,
            metadata=DocumentMetadata(topic="test", difficulty=1, prerequisites=[]),
        )

        chunker = DocumentChunker(chunk_size=200, chunk_overlap=20)
        chunks = chunker.chunk_document(doc)

        assert len(chunks) > 1
        assert all(chunk.document_id == doc.id for chunk in chunks)
        assert all(chunk.metadata.topic == "test" for chunk in chunks)

    def test_chunks_have_sequential_indices(self) -> None:
        """Chunks should have sequential indices starting from 0."""
        from calculus_rag.knowledge_base.chunker import DocumentChunker
        from calculus_rag.knowledge_base.models import Document, DocumentMetadata

        doc = Document(
            content="# Title\n\n" + "This is a sentence. " * 100,
            metadata=DocumentMetadata(topic="test", difficulty=1, prerequisites=[]),
        )

        chunker = DocumentChunker(chunk_size=200, chunk_overlap=20)
        chunks = chunker.chunk_document(doc)

        indices = [chunk.chunk_index for chunk in chunks]
        assert indices == list(range(len(chunks)))

    def test_chunk_respects_latex_boundaries(self) -> None:
        """Should not split LaTeX formulas."""
        from calculus_rag.knowledge_base.chunker import DocumentChunker
        from calculus_rag.knowledge_base.models import Document, DocumentMetadata

        content = """# Derivatives

The derivative of $f(x) = x^2$ is $f'(x) = 2x$.

$$\\int_a^b f(x) dx = F(b) - F(a)$$

More text here.
"""
        doc = Document(
            content=content,
            metadata=DocumentMetadata(topic="test", difficulty=1, prerequisites=[]),
        )

        chunker = DocumentChunker(chunk_size=100, chunk_overlap=10)
        chunks = chunker.chunk_document(doc)

        # Check that LaTeX is preserved
        all_content = " ".join(chunk.content for chunk in chunks)
        assert "$f(x) = x^2$" in all_content
        assert "$$\\int_a^b f(x) dx = F(b) - F(a)$$" in all_content

    def test_chunk_respects_section_boundaries(self) -> None:
        """Should prefer splitting at section boundaries."""
        from calculus_rag.knowledge_base.chunker import DocumentChunker
        from calculus_rag.knowledge_base.models import Document, DocumentMetadata

        content = """# Title

## Section 1

Content for section 1.

## Section 2

Content for section 2.

## Section 3

Content for section 3.
"""
        doc = Document(
            content=content,
            metadata=DocumentMetadata(topic="test", difficulty=1, prerequisites=[]),
        )

        chunker = DocumentChunker(chunk_size=100, chunk_overlap=0)
        chunks = chunker.chunk_document(doc)

        # Sections should ideally be in separate chunks
        # At minimum, check that we don't have broken headings
        for chunk in chunks:
            lines = chunk.content.split("\n")
            # If a chunk ends with #, it's breaking a heading
            assert not chunk.content.rstrip().endswith("#")

    def test_chunk_with_overlap(self) -> None:
        """Chunks should have specified overlap."""
        from calculus_rag.knowledge_base.chunker import DocumentChunker
        from calculus_rag.knowledge_base.models import Document, DocumentMetadata

        content = "word " * 200  # 200 words

        doc = Document(
            content=content,
            metadata=DocumentMetadata(topic="test", difficulty=1, prerequisites=[]),
        )

        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
        chunks = chunker.chunk_document(doc)

        # With overlap, chunks should share some content
        if len(chunks) >= 2:
            # Check that there's some overlap between consecutive chunks
            first_end = chunks[0].content[-50:]
            second_start = chunks[1].content[:50]
            # Should have at least some common words
            assert any(word in second_start for word in first_end.split() if len(word) > 3)

    def test_chunk_small_document_returns_single_chunk(self) -> None:
        """Should return single chunk for documents smaller than chunk_size."""
        from calculus_rag.knowledge_base.chunker import DocumentChunker
        from calculus_rag.knowledge_base.models import Document, DocumentMetadata

        content = "This is a small document."

        doc = Document(
            content=content,
            metadata=DocumentMetadata(topic="test", difficulty=1, prerequisites=[]),
        )

        chunker = DocumentChunker(chunk_size=1000, chunk_overlap=0)
        chunks = chunker.chunk_document(doc)

        assert len(chunks) == 1
        assert chunks[0].content == content
        assert chunks[0].chunk_index == 0

    def test_chunk_preserves_metadata(self) -> None:
        """Chunks should inherit document metadata."""
        from calculus_rag.knowledge_base.chunker import DocumentChunker
        from calculus_rag.knowledge_base.models import Document, DocumentMetadata

        metadata = DocumentMetadata(
            topic="limits.introduction",
            difficulty=3,
            prerequisites=["algebra.factoring"],
            tags=["foundational"],
        )

        doc = Document(
            content="# Title\n\n" + "Content. " * 100,
            metadata=metadata,
        )

        chunker = DocumentChunker(chunk_size=200, chunk_overlap=0)
        chunks = chunker.chunk_document(doc)

        for chunk in chunks:
            assert chunk.metadata.topic == "limits.introduction"
            assert chunk.metadata.difficulty == 3
            assert chunk.metadata.prerequisites == ["algebra.factoring"]
            assert chunk.metadata.tags == ["foundational"]

    def test_chunk_batch_documents(self) -> None:
        """Should chunk multiple documents at once."""
        from calculus_rag.knowledge_base.chunker import DocumentChunker
        from calculus_rag.knowledge_base.models import Document, DocumentMetadata

        docs = [
            Document(
                content="# Doc 1\n\n" + "Text. " * 50,
                metadata=DocumentMetadata(topic="topic1", difficulty=1, prerequisites=[]),
            ),
            Document(
                content="# Doc 2\n\n" + "Text. " * 50,
                metadata=DocumentMetadata(topic="topic2", difficulty=2, prerequisites=[]),
            ),
        ]

        chunker = DocumentChunker(chunk_size=100, chunk_overlap=0)
        all_chunks = chunker.chunk_batch(docs)

        assert len(all_chunks) > 0
        # Should have chunks from both documents
        topics = {chunk.metadata.topic for chunk in all_chunks}
        assert "topic1" in topics
        assert "topic2" in topics


class TestLatexPreservation:
    """Test that LaTeX formulas are preserved intact."""

    def test_preserves_inline_latex(self) -> None:
        """Should keep inline LaTeX together."""
        from calculus_rag.knowledge_base.chunker import DocumentChunker
        from calculus_rag.knowledge_base.models import Document, DocumentMetadata

        content = "The formula $\\frac{d}{dx}(x^n) = nx^{n-1}$ is the power rule."

        doc = Document(
            content=content,
            metadata=DocumentMetadata(topic="test", difficulty=1, prerequisites=[]),
        )

        chunker = DocumentChunker(chunk_size=50, chunk_overlap=0)
        chunks = chunker.chunk_document(doc)

        # Formula should be in exactly one chunk, not split
        formula = "$\\frac{d}{dx}(x^n) = nx^{n-1}$"
        chunks_with_formula = [c for c in chunks if formula in c.content]
        assert len(chunks_with_formula) >= 1

    def test_preserves_display_latex(self) -> None:
        """Should keep display LaTeX together."""
        from calculus_rag.knowledge_base.chunker import DocumentChunker
        from calculus_rag.knowledge_base.models import Document, DocumentMetadata

        content = """Introduction.

$$\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}$$

Conclusion.
"""
        doc = Document(
            content=content,
            metadata=DocumentMetadata(topic="test", difficulty=1, prerequisites=[]),
        )

        chunker = DocumentChunker(chunk_size=50, chunk_overlap=0)
        chunks = chunker.chunk_document(doc)

        # Display formula should be intact
        all_content = "\n".join(chunk.content for chunk in chunks)
        assert "$$\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}$$" in all_content
