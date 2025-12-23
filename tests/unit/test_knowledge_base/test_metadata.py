"""
Tests for metadata extraction from markdown files.

TDD: These tests define the expected behavior before implementation.
"""

import pytest


class TestMetadataExtractor:
    """Test the metadata extraction from markdown with YAML frontmatter."""

    def test_extract_frontmatter_from_markdown(self) -> None:
        """Should extract YAML frontmatter from markdown."""
        from calculus_rag.knowledge_base.metadata import extract_metadata

        content = """---
topic: limits.introduction
difficulty: 3
prerequisites:
  - algebra.factoring
  - functions.notation
---

# Introduction to Limits

Content here...
"""
        metadata, body = extract_metadata(content)

        assert metadata["topic"] == "limits.introduction"
        assert metadata["difficulty"] == 3
        assert metadata["prerequisites"] == ["algebra.factoring", "functions.notation"]
        assert body.strip().startswith("# Introduction to Limits")

    def test_extract_metadata_without_frontmatter(self) -> None:
        """Should handle markdown without frontmatter."""
        from calculus_rag.knowledge_base.metadata import extract_metadata

        content = """# Introduction to Limits

This document has no frontmatter.
"""
        metadata, body = extract_metadata(content)

        assert metadata == {}
        assert body == content

    def test_extract_metadata_with_tags(self) -> None:
        """Should extract optional tags from frontmatter."""
        from calculus_rag.knowledge_base.metadata import extract_metadata

        content = """---
topic: derivatives.power_rule
difficulty: 2
prerequisites: []
tags:
  - foundational
  - important
---

# Power Rule
"""
        metadata, body = extract_metadata(content)

        assert metadata["tags"] == ["foundational", "important"]

    def test_extract_metadata_with_source_file(self) -> None:
        """Should handle source_file in metadata."""
        from calculus_rag.knowledge_base.metadata import extract_metadata

        content = """---
topic: test
difficulty: 1
prerequisites: []
source_file: calculus/limits/intro.md
---

# Test
"""
        metadata, body = extract_metadata(content)

        assert metadata["source_file"] == "calculus/limits/intro.md"

    def test_extract_metadata_handles_invalid_yaml(self) -> None:
        """Should handle invalid YAML gracefully."""
        from calculus_rag.knowledge_base.metadata import extract_metadata

        content = """---
topic: test
difficulty: invalid_number
---

# Content
"""
        # Should not crash, either return empty dict or raise specific error
        try:
            metadata, body = extract_metadata(content)
            # If it succeeds, it should return something sensible
            assert isinstance(metadata, dict)
        except ValueError:
            # Or it can raise a ValueError
            pass

    def test_extract_metadata_preserves_body(self) -> None:
        """Should preserve all content after frontmatter."""
        from calculus_rag.knowledge_base.metadata import extract_metadata

        content = """---
topic: test
difficulty: 1
prerequisites: []
---

# Title

Paragraph 1

## Section

Paragraph 2
"""
        metadata, body = extract_metadata(content)

        assert "# Title" in body
        assert "Paragraph 1" in body
        assert "## Section" in body
        assert "Paragraph 2" in body

    def test_extract_metadata_handles_empty_prerequisites(self) -> None:
        """Should handle empty prerequisites list."""
        from calculus_rag.knowledge_base.metadata import extract_metadata

        content = """---
topic: test
difficulty: 1
prerequisites: []
---

# Test
"""
        metadata, body = extract_metadata(content)

        assert metadata["prerequisites"] == []


class TestInferMetadataFromPath:
    """Test inferring metadata from file paths."""

    def test_infer_topic_from_path(self) -> None:
        """Should infer topic from file path."""
        from calculus_rag.knowledge_base.metadata import infer_topic_from_path

        path = "knowledge_content/calculus/limits/introduction.md"
        topic = infer_topic_from_path(path)

        assert topic == "limits.introduction"

    def test_infer_topic_from_nested_path(self) -> None:
        """Should handle deeply nested paths."""
        from calculus_rag.knowledge_base.metadata import infer_topic_from_path

        path = "knowledge_content/pre_calculus/trigonometry/unit_circle/basics.md"
        topic = infer_topic_from_path(path)

        # Should be "trigonometry.unit_circle.basics"
        assert "trigonometry" in topic
        assert "unit_circle" in topic
        assert "basics" in topic

    def test_infer_topic_removes_file_extension(self) -> None:
        """Should remove .md extension from topic."""
        from calculus_rag.knowledge_base.metadata import infer_topic_from_path

        path = "knowledge_content/calculus/derivatives/power_rule.md"
        topic = infer_topic_from_path(path)

        assert not topic.endswith(".md")
        assert topic == "derivatives.power_rule"

    def test_infer_topic_handles_windows_paths(self) -> None:
        """Should handle Windows-style paths."""
        from calculus_rag.knowledge_base.metadata import infer_topic_from_path

        path = "knowledge_content\\calculus\\limits\\intro.md"
        topic = infer_topic_from_path(path)

        assert topic == "limits.intro"


class TestCreateDocumentMetadata:
    """Test creating DocumentMetadata from extracted data."""

    def test_create_metadata_from_frontmatter(self) -> None:
        """Should create DocumentMetadata from frontmatter dict."""
        from calculus_rag.knowledge_base.metadata import create_document_metadata

        frontmatter = {
            "topic": "limits.introduction",
            "difficulty": 3,
            "prerequisites": ["algebra.factoring"],
        }

        metadata = create_document_metadata(frontmatter)

        assert metadata.topic == "limits.introduction"
        assert metadata.difficulty == 3
        assert metadata.prerequisites == ["algebra.factoring"]

    def test_create_metadata_with_defaults(self) -> None:
        """Should use defaults for missing fields."""
        from calculus_rag.knowledge_base.metadata import create_document_metadata

        frontmatter = {
            "topic": "test.topic",
        }

        metadata = create_document_metadata(frontmatter, default_difficulty=2)

        assert metadata.topic == "test.topic"
        assert metadata.difficulty == 2
        assert metadata.prerequisites == []

    def test_create_metadata_validates_difficulty(self) -> None:
        """Should validate difficulty is in range."""
        from calculus_rag.knowledge_base.metadata import create_document_metadata

        frontmatter = {
            "topic": "test",
            "difficulty": 10,  # Invalid
        }

        with pytest.raises(ValueError):
            create_document_metadata(frontmatter)

    def test_create_metadata_requires_topic(self) -> None:
        """Should require topic field."""
        from calculus_rag.knowledge_base.metadata import create_document_metadata

        frontmatter = {
            "difficulty": 1,
        }

        with pytest.raises(ValueError):
            create_document_metadata(frontmatter)
