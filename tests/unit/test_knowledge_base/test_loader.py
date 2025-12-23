"""
Tests for document loader.

TDD: These tests define the expected behavior before implementation.
"""

from pathlib import Path

import pytest


class TestDocumentLoader:
    """Test the DocumentLoader class."""

    def test_load_single_file(self, tmp_path: Path) -> None:
        """Should load a single markdown file as a Document."""
        from calculus_rag.knowledge_base.loader import DocumentLoader

        # Create a test file
        file_path = tmp_path / "test.md"
        file_path.write_text("""---
topic: test.topic
difficulty: 2
prerequisites: []
---

# Test Document

This is a test.
""")

        loader = DocumentLoader()
        doc = loader.load_file(str(file_path))

        assert doc.content is not None
        assert "Test Document" in doc.content
        assert doc.metadata.topic == "test.topic"
        assert doc.metadata.difficulty == 2

    def test_load_file_without_frontmatter(self, tmp_path: Path) -> None:
        """Should load file without frontmatter, inferring topic from path."""
        from calculus_rag.knowledge_base.loader import DocumentLoader

        file_path = tmp_path / "limits" / "intro.md"
        file_path.parent.mkdir(parents=True)
        file_path.write_text("""# Limits Introduction

This has no frontmatter.
""")

        loader = DocumentLoader()
        doc = loader.load_file(str(file_path))

        assert doc is not None
        assert "Limits Introduction" in doc.content
        # Topic should be inferred from path
        assert "intro" in doc.metadata.topic

    def test_load_directory_recursively(self, tmp_path: Path) -> None:
        """Should load all markdown files from a directory recursively."""
        from calculus_rag.knowledge_base.loader import DocumentLoader

        # Create directory structure
        (tmp_path / "calculus" / "limits").mkdir(parents=True)
        (tmp_path / "calculus" / "derivatives").mkdir(parents=True)

        # Create test files
        (tmp_path / "calculus" / "limits" / "intro.md").write_text("""---
topic: limits.intro
difficulty: 1
prerequisites: []
---
# Limits Intro
""")

        (tmp_path / "calculus" / "derivatives" / "power_rule.md").write_text("""---
topic: derivatives.power_rule
difficulty: 2
prerequisites: [limits.intro]
---
# Power Rule
""")

        loader = DocumentLoader()
        docs = loader.load_directory(str(tmp_path))

        assert len(docs) == 2
        topics = [doc.metadata.topic for doc in docs]
        assert "limits.intro" in topics
        assert "derivatives.power_rule" in topics

    def test_load_directory_filters_non_markdown(self, tmp_path: Path) -> None:
        """Should only load .md files, ignoring other file types."""
        from calculus_rag.knowledge_base.loader import DocumentLoader

        (tmp_path / "test.md").write_text("---\ntopic: test\ndifficulty: 1\nprerequisites: []\n---\n# Test")
        (tmp_path / "readme.txt").write_text("Not markdown")
        (tmp_path / "image.png").write_text("Binary data")

        loader = DocumentLoader()
        docs = loader.load_directory(str(tmp_path))

        assert len(docs) == 1
        assert docs[0].metadata.topic == "test"

    def test_load_file_adds_source_file_to_metadata(self, tmp_path: Path) -> None:
        """Should add source file path to metadata."""
        from calculus_rag.knowledge_base.loader import DocumentLoader

        file_path = tmp_path / "test.md"
        file_path.write_text("""---
topic: test
difficulty: 1
prerequisites: []
---
# Test
""")

        loader = DocumentLoader()
        doc = loader.load_file(str(file_path))

        assert doc.metadata.source_file is not None
        assert "test.md" in doc.metadata.source_file

    def test_load_file_raises_on_missing_file(self) -> None:
        """Should raise FileNotFoundError for non-existent file."""
        from calculus_rag.knowledge_base.loader import DocumentLoader

        loader = DocumentLoader()

        with pytest.raises(FileNotFoundError):
            loader.load_file("/nonexistent/file.md")

    def test_load_directory_returns_empty_for_empty_dir(self, tmp_path: Path) -> None:
        """Should return empty list for directory with no markdown files."""
        from calculus_rag.knowledge_base.loader import DocumentLoader

        loader = DocumentLoader()
        docs = loader.load_directory(str(tmp_path))

        assert docs == []

    def test_loader_with_custom_default_difficulty(self, tmp_path: Path) -> None:
        """Should use custom default difficulty for files without frontmatter."""
        from calculus_rag.knowledge_base.loader import DocumentLoader

        file_path = tmp_path / "test.md"
        file_path.write_text("# Test\n\nNo frontmatter here.")

        loader = DocumentLoader(default_difficulty=4)
        doc = loader.load_file(str(file_path))

        assert doc.metadata.difficulty == 4


class TestDocumentLoaderIntegration:
    """Integration tests with sample documents from fixtures."""

    def test_load_sample_documents(self, sample_docs_dir: Path) -> None:
        """Should load the sample documents from fixtures."""
        from calculus_rag.knowledge_base.loader import DocumentLoader

        loader = DocumentLoader()
        docs = loader.load_directory(str(sample_docs_dir))

        # Should have loaded both sample docs
        assert len(docs) >= 2

        # Check that we got the expected topics
        topics = [doc.metadata.topic for doc in docs]
        assert any("factoring" in topic for topic in topics)
        assert any("limits" in topic for topic in topics)

    def test_loaded_documents_have_valid_structure(self, sample_docs_dir: Path) -> None:
        """Should load documents with all required fields populated."""
        from calculus_rag.knowledge_base.loader import DocumentLoader

        loader = DocumentLoader()
        docs = loader.load_directory(str(sample_docs_dir))

        for doc in docs:
            # All docs should have these fields
            assert doc.id is not None
            assert len(doc.content) > 0
            assert doc.metadata.topic is not None
            assert 1 <= doc.metadata.difficulty <= 5
            assert isinstance(doc.metadata.prerequisites, list)
            assert doc.created_at is not None
