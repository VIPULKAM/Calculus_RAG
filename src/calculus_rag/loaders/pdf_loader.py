"""
PDF document loader with text extraction and metadata.

Supports loading PDF files and extracting text content with proper chunking.
"""

import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader


class PDFLoader:
    """Load and extract text from PDF files."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Initialize PDF loader.

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load(self, file_path: Path | str) -> list[dict[str, Any]]:
        """
        Load a PDF file and extract text with chunks.

        Args:
            file_path: Path to the PDF file

        Returns:
            List of document chunks with metadata
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        # Extract text from PDF
        reader = PdfReader(str(file_path))
        full_text = ""
        total_pages = len(reader.pages)

        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                full_text += f"\n\n--- Page {page_num + 1} ---\n\n{page_text}"

        # Clean up text
        full_text = self._clean_text(full_text)

        # Create chunks
        chunks = self._create_chunks(full_text)

        # Add metadata to each chunk
        documents = []
        for i, chunk_text in enumerate(chunks):
            documents.append(
                {
                    "content": chunk_text,
                    "metadata": {
                        "source": str(file_path.name),
                        "source_type": "pdf",
                        "total_pages": total_pages,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    },
                }
            )

        return documents

    def _clean_text(self, text: str) -> str:
        """Clean extracted text (remove extra whitespace, fix line breaks)."""
        # Remove excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)

        # Remove page numbers alone on a line (common artifact)
        text = re.sub(r"\n\s*\d+\s*\n", "\n", text)

        return text.strip()

    def _create_chunks(self, text: str) -> list[str]:
        """
        Split text into chunks with overlap.

        Tries to break on sentence boundaries when possible.
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            # Get chunk with overlap
            end = start + self.chunk_size

            if end >= len(text):
                # Last chunk
                chunks.append(text[start:])
                break

            # Try to break at sentence boundary
            chunk = text[start:end]

            # Look for sentence endings: . ! ? followed by space or newline
            sentence_endings = [
                m.end() + start
                for m in re.finditer(r"[.!?][\s\n]", text[start : end + 50])
            ]

            if sentence_endings:
                # Use the last sentence ending in the chunk
                for ending_pos in reversed(sentence_endings):
                    if start < ending_pos <= end:
                        end = ending_pos
                        break

            chunks.append(text[start:end].strip())

            # Move start forward (with overlap)
            start = end - self.chunk_overlap

        return chunks
