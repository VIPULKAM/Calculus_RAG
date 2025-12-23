"""
Data models for knowledge base documents and chunks.

These models use Pydantic for validation and serialization.
"""

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


class DocumentMetadata(BaseModel):
    """
    Metadata for a knowledge base document.

    Attributes:
        topic: Dot-separated topic identifier (e.g., "limits.introduction").
        difficulty: Difficulty level from 1 (easiest) to 5 (hardest).
        prerequisites: List of prerequisite topics.
        source_file: Optional path to source file.
        tags: Optional list of tags for categorization.
    """

    topic: str = Field(..., description="Topic identifier in dot notation")
    difficulty: int = Field(..., ge=1, le=5, description="Difficulty level (1-5)")
    prerequisites: list[str] = Field(
        default_factory=list,
        description="List of prerequisite topic identifiers",
    )
    source_file: str | None = Field(default=None, description="Path to source file")
    tags: list[str] = Field(default_factory=list, description="Optional tags")


class Document(BaseModel):
    """
    Represents a knowledge base document.

    Attributes:
        id: Unique identifier for the document.
        content: The full text content of the document.
        metadata: Associated metadata.
        created_at: Timestamp when the document was created.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID")
    content: str = Field(..., min_length=1, description="Document content")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp",
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """Ensure content is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v


class Chunk(BaseModel):
    """
    Represents a chunk of a document for embedding and retrieval.

    Attributes:
        id: Unique identifier for the chunk.
        content: The text content of the chunk.
        document_id: ID of the parent document.
        chunk_index: Position of this chunk in the document (0-indexed).
        metadata: Associated metadata (inherited from document).
        embedding: Optional embedding vector for this chunk.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID")
    content: str = Field(..., min_length=1, description="Chunk content")
    document_id: str = Field(..., description="Parent document ID")
    chunk_index: int = Field(..., ge=0, description="Index of chunk in document")
    metadata: DocumentMetadata = Field(..., description="Chunk metadata")
    embedding: list[float] | None = Field(
        default=None,
        description="Optional embedding vector",
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """Ensure content is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v
