"""
Document loader for markdown files with YAML frontmatter.

This module handles loading markdown files from the filesystem and
converting them into Document objects.
"""

from pathlib import Path

from calculus_rag.knowledge_base.metadata import (
    create_document_metadata,
    extract_metadata,
    infer_topic_from_path,
)
from calculus_rag.knowledge_base.models import Document


class DocumentLoader:
    """
    Loads markdown documents from the filesystem.

    Handles YAML frontmatter extraction, metadata inference from paths,
    and recursive directory loading.
    """

    def __init__(self, default_difficulty: int = 3) -> None:
        """
        Initialize the document loader.

        Args:
            default_difficulty: Default difficulty level for documents without
                explicit difficulty in frontmatter (1-5).
        """
        self.default_difficulty = default_difficulty

    def load_file(self, file_path: str) -> Document:
        """
        Load a single markdown file as a Document.

        Args:
            file_path: Path to the markdown file.

        Returns:
            Document: The loaded document.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read file content
        content = path.read_text(encoding="utf-8")

        # Extract frontmatter and body
        frontmatter, body = extract_metadata(content)

        # Infer topic from path if not in frontmatter
        inferred_topic = infer_topic_from_path(file_path)

        # Add source file to frontmatter if not present
        if "source_file" not in frontmatter:
            frontmatter["source_file"] = str(path)

        # Create metadata
        metadata = create_document_metadata(
            frontmatter,
            default_difficulty=self.default_difficulty,
            inferred_topic=inferred_topic,
        )

        # Create document (keeping full content including frontmatter for now)
        # This preserves the original format
        document = Document(
            content=content,
            metadata=metadata,
        )

        return document

    def load_directory(self, directory_path: str, recursive: bool = True) -> list[Document]:
        """
        Load all markdown files from a directory.

        Args:
            directory_path: Path to the directory containing markdown files.
            recursive: Whether to search subdirectories recursively.

        Returns:
            list[Document]: List of loaded documents.
        """
        path = Path(directory_path)

        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory_path}")

        # Find all markdown files
        if recursive:
            md_files = path.rglob("*.md")
        else:
            md_files = path.glob("*.md")

        # Load each file
        documents = []
        for md_file in sorted(md_files):
            try:
                doc = self.load_file(str(md_file))
                documents.append(doc)
            except Exception as e:
                # Log error but continue loading other files
                print(f"Warning: Failed to load {md_file}: {e}")
                continue

        return documents
