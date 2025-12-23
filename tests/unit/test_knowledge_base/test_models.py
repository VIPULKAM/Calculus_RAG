"""
Tests for knowledge base data models.

TDD: These tests define the expected data models before implementation.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError


class TestDocumentMetadata:
    """Test the DocumentMetadata model."""

    def test_metadata_has_required_fields(self) -> None:
        """DocumentMetadata should have topic, difficulty, and prerequisites."""
        from calculus_rag.knowledge_base.models import DocumentMetadata

        metadata = DocumentMetadata(
            topic="limits.introduction",
            difficulty=3,
            prerequisites=["algebra.factoring", "functions.notation"],
        )

        assert metadata.topic == "limits.introduction"
        assert metadata.difficulty == 3
        assert metadata.prerequisites == ["algebra.factoring", "functions.notation"]

    def test_metadata_difficulty_range_validation(self) -> None:
        """Difficulty should be between 1 and 5."""
        from calculus_rag.knowledge_base.models import DocumentMetadata

        # Valid difficulties
        DocumentMetadata(topic="test", difficulty=1, prerequisites=[])
        DocumentMetadata(topic="test", difficulty=5, prerequisites=[])

        # Invalid - too low
        with pytest.raises(ValidationError):
            DocumentMetadata(topic="test", difficulty=0, prerequisites=[])

        # Invalid - too high
        with pytest.raises(ValidationError):
            DocumentMetadata(topic="test", difficulty=6, prerequisites=[])

    def test_metadata_prerequisites_defaults_to_empty_list(self) -> None:
        """Prerequisites should default to an empty list."""
        from calculus_rag.knowledge_base.models import DocumentMetadata

        metadata = DocumentMetadata(topic="test", difficulty=1)

        assert metadata.prerequisites == []

    def test_metadata_has_optional_source_file(self) -> None:
        """DocumentMetadata should support optional source_file field."""
        from calculus_rag.knowledge_base.models import DocumentMetadata

        metadata = DocumentMetadata(
            topic="test",
            difficulty=1,
            prerequisites=[],
            source_file="calculus/limits/intro.md",
        )

        assert metadata.source_file == "calculus/limits/intro.md"

    def test_metadata_has_optional_tags(self) -> None:
        """DocumentMetadata should support optional tags."""
        from calculus_rag.knowledge_base.models import DocumentMetadata

        metadata = DocumentMetadata(
            topic="test",
            difficulty=1,
            prerequisites=[],
            tags=["foundational", "important"],
        )

        assert metadata.tags == ["foundational", "important"]


class TestDocument:
    """Test the Document model."""

    def test_document_has_required_fields(self) -> None:
        """Document should have id, content, and metadata."""
        from calculus_rag.knowledge_base.models import Document, DocumentMetadata

        doc = Document(
            id="doc_001",
            content="# Limits\n\nA limit describes...",
            metadata=DocumentMetadata(
                topic="limits.introduction",
                difficulty=3,
                prerequisites=["algebra.factoring"],
            ),
        )

        assert doc.id == "doc_001"
        assert "A limit describes" in doc.content
        assert doc.metadata.topic == "limits.introduction"

    def test_document_id_is_generated_if_not_provided(self) -> None:
        """Document should auto-generate ID if not provided."""
        from calculus_rag.knowledge_base.models import Document, DocumentMetadata

        doc = Document(
            content="Test content",
            metadata=DocumentMetadata(topic="test", difficulty=1, prerequisites=[]),
        )

        assert doc.id is not None
        assert len(doc.id) > 0

    def test_document_has_created_at_timestamp(self) -> None:
        """Document should have a created_at timestamp."""
        from calculus_rag.knowledge_base.models import Document, DocumentMetadata

        doc = Document(
            content="Test",
            metadata=DocumentMetadata(topic="test", difficulty=1, prerequisites=[]),
        )

        assert doc.created_at is not None
        assert isinstance(doc.created_at, datetime)

    def test_document_content_cannot_be_empty(self) -> None:
        """Document content must not be empty."""
        from calculus_rag.knowledge_base.models import Document, DocumentMetadata

        with pytest.raises(ValidationError):
            Document(
                content="",
                metadata=DocumentMetadata(topic="test", difficulty=1, prerequisites=[]),
            )


class TestChunk:
    """Test the Chunk model."""

    def test_chunk_has_required_fields(self) -> None:
        """Chunk should have id, content, document_id, and metadata."""
        from calculus_rag.knowledge_base.models import Chunk, DocumentMetadata

        chunk = Chunk(
            id="chunk_001",
            content="## Power Rule\n\nThe power rule states...",
            document_id="doc_001",
            chunk_index=0,
            metadata=DocumentMetadata(topic="derivatives.power_rule", difficulty=2, prerequisites=[]),
        )

        assert chunk.id == "chunk_001"
        assert "power rule" in chunk.content.lower()
        assert chunk.document_id == "doc_001"
        assert chunk.chunk_index == 0

    def test_chunk_id_is_generated_if_not_provided(self) -> None:
        """Chunk should auto-generate ID if not provided."""
        from calculus_rag.knowledge_base.models import Chunk, DocumentMetadata

        chunk = Chunk(
            content="Test chunk",
            document_id="doc_001",
            chunk_index=0,
            metadata=DocumentMetadata(topic="test", difficulty=1, prerequisites=[]),
        )

        assert chunk.id is not None
        assert len(chunk.id) > 0

    def test_chunk_has_embedding_field(self) -> None:
        """Chunk should have an optional embedding field."""
        from calculus_rag.knowledge_base.models import Chunk, DocumentMetadata

        chunk = Chunk(
            content="Test",
            document_id="doc_001",
            chunk_index=0,
            metadata=DocumentMetadata(topic="test", difficulty=1, prerequisites=[]),
            embedding=[0.1] * 768,
        )

        assert chunk.embedding is not None
        assert len(chunk.embedding) == 768

    def test_chunk_embedding_defaults_to_none(self) -> None:
        """Chunk embedding should default to None."""
        from calculus_rag.knowledge_base.models import Chunk, DocumentMetadata

        chunk = Chunk(
            content="Test",
            document_id="doc_001",
            chunk_index=0,
            metadata=DocumentMetadata(topic="test", difficulty=1, prerequisites=[]),
        )

        assert chunk.embedding is None

    def test_chunk_index_must_be_non_negative(self) -> None:
        """Chunk index must be >= 0."""
        from calculus_rag.knowledge_base.models import Chunk, DocumentMetadata

        # Valid
        Chunk(
            content="Test",
            document_id="doc_001",
            chunk_index=0,
            metadata=DocumentMetadata(topic="test", difficulty=1, prerequisites=[]),
        )

        # Invalid
        with pytest.raises(ValidationError):
            Chunk(
                content="Test",
                document_id="doc_001",
                chunk_index=-1,
                metadata=DocumentMetadata(topic="test", difficulty=1, prerequisites=[]),
            )

    def test_chunk_to_dict_includes_all_fields(self) -> None:
        """Chunk should serialize to dict with all fields."""
        from calculus_rag.knowledge_base.models import Chunk, DocumentMetadata

        chunk = Chunk(
            id="chunk_001",
            content="Test content",
            document_id="doc_001",
            chunk_index=0,
            metadata=DocumentMetadata(topic="test", difficulty=1, prerequisites=[]),
        )

        data = chunk.model_dump()

        assert data["id"] == "chunk_001"
        assert data["content"] == "Test content"
        assert data["document_id"] == "doc_001"
        assert data["chunk_index"] == 0
        assert data["metadata"]["topic"] == "test"


class TestDocumentFromMarkdown:
    """Test creating documents from markdown files."""

    def test_document_can_be_created_from_file_content(self, tmp_path) -> None:
        """Document should be creatable from markdown file content."""
        from calculus_rag.knowledge_base.models import Document, DocumentMetadata

        content = """---
topic: limits.introduction
difficulty: 3
prerequisites:
  - algebra.factoring
---

# Introduction to Limits

A limit describes the value a function approaches.
"""
        # This test just ensures the model can hold this data
        doc = Document(
            content=content,
            metadata=DocumentMetadata(
                topic="limits.introduction",
                difficulty=3,
                prerequisites=["algebra.factoring"],
            ),
        )

        assert doc.content == content
        assert doc.metadata.topic == "limits.introduction"
