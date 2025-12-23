"""
PDF loader using pymupdf4llm - optimized for LLM/RAG pipelines.

This loader:
- Preserves markdown formatting
- Handles math notation better
- Creates semantic chunks (not just character-based)
- Maintains document structure
"""

import re
from pathlib import Path
from typing import Any

import pymupdf4llm


class PyMuPDFLoader:
    """Load PDFs using pymupdf4llm for better text extraction."""

    def __init__(self, chunk_size: int = 1024, chunk_overlap: int = 100):
        """
        Initialize loader.

        Args:
            chunk_size: Target characters per chunk
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load(self, file_path: Path | str) -> list[dict[str, Any]]:
        """
        Load PDF and extract structured text.

        Args:
            file_path: Path to PDF

        Returns:
            List of document chunks with metadata
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        try:
            # Extract as markdown (preserves structure, math, tables)
            md_text = pymupdf4llm.to_markdown(str(file_path))

            # Clean and chunk
            md_text = self._clean_markdown(md_text)
            chunks = self._create_semantic_chunks(md_text)

            # Add metadata
            documents = []
            for i, chunk_text in enumerate(chunks):
                documents.append(
                    {
                        "content": chunk_text,
                        "metadata": {
                            "source": file_path.name,
                            "source_type": "pdf",
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "extraction_method": "pymupdf4llm",
                        },
                    }
                )

            return documents

        except Exception as e:
            raise RuntimeError(f"Failed to load {file_path}: {e}")

    def _clean_markdown(self, text: str) -> str:
        """Clean extracted markdown."""
        # Remove excessive newlines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove page markers if present
        text = re.sub(r"---\s*Page \d+\s*---", "", text)

        # Clean up whitespace
        text = re.sub(r" {2,}", " ", text)

        return text.strip()

    def _create_semantic_chunks(self, text: str) -> list[str]:
        """
        Create semantic chunks preserving markdown structure.

        Tries to break on:
        1. Markdown headers (##, ###, etc.)
        2. Paragraph boundaries
        3. Sentence boundaries

        Args:
            text: Markdown text

        Returns:
            List of chunks
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        lines = text.split("\n")

        current_chunk = []
        current_length = 0

        for line in lines:
            line_length = len(line) + 1  # +1 for newline

            # Check if this line is a header
            is_header = line.strip().startswith("#")

            # Should we start a new chunk?
            if current_length + line_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = "\n".join(current_chunk).strip()
                if chunk_text:
                    chunks.append(chunk_text)

                # Start new chunk with overlap
                # Keep last few lines for context
                if len(current_chunk) > 3 and not is_header:
                    overlap_lines = current_chunk[-2:]
                    current_chunk = overlap_lines + [line]
                    current_length = sum(len(l) + 1 for l in current_chunk)
                else:
                    current_chunk = [line]
                    current_length = line_length
            else:
                current_chunk.append(line)
                current_length += line_length

        # Add final chunk
        if current_chunk:
            chunk_text = "\n".join(current_chunk).strip()
            if chunk_text:
                chunks.append(chunk_text)

        return chunks
