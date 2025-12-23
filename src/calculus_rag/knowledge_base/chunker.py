"""
Smart document chunker that respects LaTeX and section boundaries.

This module chunks documents while preserving mathematical formulas and
preferring splits at section boundaries.
"""

import re
from typing import Pattern

from calculus_rag.knowledge_base.models import Chunk, Document


class DocumentChunker:
    """
    Chunks documents intelligently, respecting LaTeX and structure.

    Attempts to split at natural boundaries (sections, paragraphs) while
    keeping LaTeX formulas intact and maintaining roughly equal chunk sizes.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ) -> None:
        """
        Initialize the chunker.

        Args:
            chunk_size: Target size for each chunk in characters.
            chunk_overlap: Number of characters to overlap between chunks.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Separators in order of preference (most preferred first)
        self.separators: list[str | Pattern[str]] = [
            "\n## ",  # Level 2 headings
            "\n### ",  # Level 3 headings
            "\n\n",  # Paragraph breaks
            "\n",  # Line breaks
            ". ",  # Sentences
            " ",  # Words
        ]

    def chunk_document(self, document: Document) -> list[Chunk]:
        """
        Chunk a single document.

        Args:
            document: The document to chunk.

        Returns:
            list[Chunk]: List of chunks created from the document.
        """
        content = document.content

        # If document is smaller than chunk size, return as single chunk
        if len(content) <= self.chunk_size:
            return [
                Chunk(
                    content=content,
                    document_id=document.id,
                    chunk_index=0,
                    metadata=document.metadata,
                )
            ]

        # Split the content
        splits = self._split_text(content)

        # Create chunks with overlap
        chunks = []
        for i, split in enumerate(splits):
            chunk = Chunk(
                content=split,
                document_id=document.id,
                chunk_index=i,
                metadata=document.metadata,
            )
            chunks.append(chunk)

        return chunks

    def chunk_batch(self, documents: list[Document]) -> list[Chunk]:
        """
        Chunk multiple documents.

        Args:
            documents: List of documents to chunk.

        Returns:
            list[Chunk]: Flat list of all chunks from all documents.
        """
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)
        return all_chunks

    def _split_text(self, text: str) -> list[str]:
        """
        Split text into chunks of approximately chunk_size.

        Respects LaTeX boundaries and tries to split at natural points.

        Args:
            text: The text to split.

        Returns:
            list[str]: List of text chunks.
        """
        # Protect LaTeX formulas by replacing them with placeholders
        text, latex_map = self._protect_latex(text)

        # Recursively split the text
        splits = self._recursive_split(text, self.separators)

        # Restore LaTeX formulas
        splits = [self._restore_latex(s, latex_map) for s in splits]

        # Add overlap if configured
        if self.chunk_overlap > 0:
            splits = self._add_overlap(splits)

        return splits

    def _protect_latex(self, text: str) -> tuple[str, dict[str, str]]:
        """
        Replace LaTeX formulas with placeholders to protect them from splitting.

        Args:
            text: The text containing LaTeX.

        Returns:
            tuple: (protected_text, mapping of placeholders to original LaTeX)
        """
        latex_map = {}
        counter = 0

        # Protect display math ($$...$$)
        def replace_display(match: re.Match[str]) -> str:
            nonlocal counter
            placeholder = f"__LATEX_DISPLAY_{counter}__"
            latex_map[placeholder] = match.group(0)
            counter += 1
            return placeholder

        text = re.sub(r"\$\$.*?\$\$", replace_display, text, flags=re.DOTALL)

        # Protect inline math ($...$)
        def replace_inline(match: re.Match[str]) -> str:
            nonlocal counter
            placeholder = f"__LATEX_INLINE_{counter}__"
            latex_map[placeholder] = match.group(0)
            counter += 1
            return placeholder

        text = re.sub(r"\$[^\$]+?\$", replace_inline, text)

        return text, latex_map

    def _restore_latex(self, text: str, latex_map: dict[str, str]) -> str:
        """
        Restore LaTeX formulas from placeholders.

        Args:
            text: Text with placeholders.
            latex_map: Mapping of placeholders to original LaTeX.

        Returns:
            str: Text with LaTeX restored.
        """
        for placeholder, latex in latex_map.items():
            text = text.replace(placeholder, latex)
        return text

    def _recursive_split(self, text: str, separators: list[str | Pattern[str]]) -> list[str]:
        """
        Recursively split text using separators in order of preference.

        Args:
            text: Text to split.
            separators: List of separators to try, in order.

        Returns:
            list[str]: List of text splits.
        """
        if not separators or len(text) <= self.chunk_size:
            return [text] if text else []

        separator = separators[0]
        remaining_separators = separators[1:]

        # Split by current separator
        if isinstance(separator, Pattern):
            parts = separator.split(text)
        else:
            parts = text.split(separator)

        # Recombine parts into chunks
        chunks = []
        current_chunk = []
        current_length = 0

        for i, part in enumerate(parts):
            # Add separator back (except for first part)
            if i > 0:
                part = separator + part if isinstance(separator, str) else part

            part_length = len(part)

            # If adding this part would exceed chunk_size, start a new chunk
            if current_length + part_length > self.chunk_size and current_chunk:
                chunk_text = "".join(current_chunk)
                # If chunk is still too big, split it further
                if len(chunk_text) > self.chunk_size:
                    chunks.extend(self._recursive_split(chunk_text, remaining_separators))
                else:
                    chunks.append(chunk_text)
                current_chunk = []
                current_length = 0

            current_chunk.append(part)
            current_length += part_length

        # Add remaining chunk
        if current_chunk:
            chunk_text = "".join(current_chunk)
            if len(chunk_text) > self.chunk_size and remaining_separators:
                chunks.extend(self._recursive_split(chunk_text, remaining_separators))
            else:
                chunks.append(chunk_text)

        return [c for c in chunks if c.strip()]  # Filter empty chunks

    def _add_overlap(self, splits: list[str]) -> list[str]:
        """
        Add overlap between consecutive chunks.

        Args:
            splits: List of text chunks without overlap.

        Returns:
            list[str]: List of chunks with overlap added.
        """
        if len(splits) <= 1:
            return splits

        overlapped = []

        for i, split in enumerate(splits):
            if i == 0:
                # First chunk: no prefix, add suffix from next
                if len(splits) > 1:
                    suffix = splits[1][:self.chunk_overlap]
                    overlapped.append(split + " " + suffix if suffix else split)
                else:
                    overlapped.append(split)
            elif i == len(splits) - 1:
                # Last chunk: add prefix from previous, no suffix
                prefix = splits[i - 1][-self.chunk_overlap:]
                overlapped.append((prefix + " " if prefix else "") + split)
            else:
                # Middle chunks: add both prefix and suffix
                prefix = splits[i - 1][-self.chunk_overlap:]
                suffix = splits[i + 1][:self.chunk_overlap]
                chunk = (prefix + " " if prefix else "") + split
                chunk = chunk + (" " + suffix if suffix else "")
                overlapped.append(chunk)

        return overlapped
