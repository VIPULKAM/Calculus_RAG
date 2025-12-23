"""
Metadata extraction from markdown files with YAML frontmatter.

This module handles parsing YAML frontmatter and inferring metadata from file paths.
"""

import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from calculus_rag.knowledge_base.models import DocumentMetadata


def extract_metadata(content: str) -> tuple[dict[str, Any], str]:
    """
    Extract YAML frontmatter and body from markdown content.

    Args:
        content: The full markdown content.

    Returns:
        tuple: (metadata_dict, body_content)
            - metadata_dict: Parsed YAML frontmatter as dict (empty if no frontmatter)
            - body_content: The markdown content after frontmatter

    Raises:
        ValueError: If YAML frontmatter is malformed.
    """
    # Pattern to match YAML frontmatter: --- at start, then ---, then content
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        # No frontmatter found
        return {}, content

    frontmatter_str = match.group(1)
    body = match.group(2)

    try:
        metadata = yaml.safe_load(frontmatter_str)
        if metadata is None:
            metadata = {}
        return metadata, body
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter: {e}") from e


def infer_topic_from_path(file_path: str) -> str:
    """
    Infer topic identifier from file path.

    Converts a file path like "knowledge_content/calculus/limits/intro.md"
    to a topic identifier like "limits.intro".

    Args:
        file_path: Path to the markdown file.

    Returns:
        str: Topic identifier in dot notation.

    Examples:
        >>> infer_topic_from_path("knowledge_content/calculus/limits/intro.md")
        'limits.intro'
        >>> infer_topic_from_path("pre_calculus/algebra/factoring.md")
        'algebra.factoring'
    """
    # Normalize path separators (handle Windows paths)
    normalized = file_path.replace("\\", "/")
    path = Path(normalized)

    # Get parts, removing extension
    parts = list(path.with_suffix("").parts)

    # Remove common prefixes
    prefixes_to_remove = ["knowledge_content", "calculus", "pre_calculus"]
    while parts and parts[0] in prefixes_to_remove:
        parts.pop(0)

    # Join with dots
    if not parts:
        return "unknown"

    return ".".join(parts)


def create_document_metadata(
    frontmatter: dict[str, Any],
    default_difficulty: int = 3,
    inferred_topic: str | None = None,
) -> DocumentMetadata:
    """
    Create a DocumentMetadata instance from frontmatter dict.

    Args:
        frontmatter: Dictionary from parsed YAML frontmatter.
        default_difficulty: Default difficulty if not specified.
        inferred_topic: Topic inferred from file path (used as fallback).

    Returns:
        DocumentMetadata: Validated metadata instance.

    Raises:
        ValueError: If required fields are missing or invalid.
    """
    # Get topic (required)
    topic = frontmatter.get("topic") or inferred_topic
    if not topic:
        raise ValueError("Topic is required (either in frontmatter or inferred from path)")

    # Get difficulty with default
    difficulty = frontmatter.get("difficulty", default_difficulty)

    # Validate difficulty is an integer
    if not isinstance(difficulty, int):
        raise ValueError(f"Difficulty must be an integer, got {type(difficulty)}")

    # Get prerequisites (default to empty list)
    prerequisites = frontmatter.get("prerequisites", [])
    if prerequisites is None:
        prerequisites = []

    # Get optional fields
    source_file = frontmatter.get("source_file")
    tags = frontmatter.get("tags", [])
    if tags is None:
        tags = []

    try:
        return DocumentMetadata(
            topic=topic,
            difficulty=difficulty,
            prerequisites=prerequisites,
            source_file=source_file,
            tags=tags,
        )
    except ValidationError as e:
        raise ValueError(f"Invalid metadata: {e}") from e
