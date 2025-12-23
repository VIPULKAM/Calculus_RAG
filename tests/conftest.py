"""
Pytest configuration and shared fixtures for Calculus RAG tests.
"""

import os
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest


# =============================================================================
# Path Fixtures
# =============================================================================


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_docs_dir(temp_dir: Path) -> Path:
    """Create a sample documents directory with test content."""
    docs_dir = temp_dir / "knowledge_content"

    # Create pre-calculus content
    precalc_dir = docs_dir / "pre_calculus" / "algebra"
    precalc_dir.mkdir(parents=True)

    (precalc_dir / "factoring.md").write_text("""---
topic: algebra.factoring
difficulty: 2
prerequisites: []
---

# Factoring Polynomials

Factoring is the process of breaking down a polynomial into simpler terms.

## Common Factoring Patterns

### Difference of Squares
$$a^2 - b^2 = (a + b)(a - b)$$

### Perfect Square Trinomial
$$a^2 + 2ab + b^2 = (a + b)^2$$
""")

    # Create calculus content
    calc_dir = docs_dir / "calculus" / "limits"
    calc_dir.mkdir(parents=True)

    (calc_dir / "introduction.md").write_text("""---
topic: limits.introduction
difficulty: 3
prerequisites:
  - algebra.factoring
  - functions.notation
---

# Introduction to Limits

A limit describes the value a function approaches as the input approaches a value.

## Definition
$$\\lim_{x \\to a} f(x) = L$$

This means as $x$ gets closer to $a$, $f(x)$ gets closer to $L$.
""")

    return docs_dir


# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def test_env_vars(temp_dir: Path) -> Generator[dict[str, str], None, None]:
    """Set up test environment variables."""
    env_vars = {
        "ENVIRONMENT": "testing",
        "EMBEDDING_MODEL_NAME": "BAAI/bge-base-en-v1.5",
        "EMBEDDING_DEVICE": "cpu",
        "CHROMA_PERSIST_DIR": str(temp_dir / "chroma"),
        "CHROMA_COLLECTION_NAME": "test_collection",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "OLLAMA_MODEL": "qwen2.5-math:7b",
        "KNOWLEDGE_BASE_PATH": str(temp_dir / "knowledge_content"),
        "STUDENT_DB_PATH": str(temp_dir / "student.db"),
        "LOG_LEVEL": "DEBUG",
    }

    # Store original values
    original_env = {k: os.environ.get(k) for k in env_vars}

    # Set test values
    for key, value in env_vars.items():
        os.environ[key] = value

    yield env_vars

    # Restore original values
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


# =============================================================================
# Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_embedder() -> MagicMock:
    """Create a mock embedder for testing."""
    mock = MagicMock()
    mock.embed.return_value = [[0.1] * 768]  # BGE-base dimension
    mock.embed_batch.return_value = [[[0.1] * 768], [[0.2] * 768]]
    mock.dimension = 768
    return mock


@pytest.fixture
def mock_vectorstore() -> MagicMock:
    """Create a mock vector store for testing."""
    mock = MagicMock()
    mock.add.return_value = ["id1", "id2"]
    mock.query.return_value = {
        "ids": [["id1"]],
        "documents": [["Test document"]],
        "metadatas": [[{"topic": "limits"}]],
        "distances": [[0.1]],
    }
    return mock


@pytest.fixture
def mock_llm() -> MagicMock:
    """Create a mock LLM for testing."""
    mock = MagicMock()
    mock.generate.return_value = "This is a test response about calculus."
    mock.generate_stream.return_value = iter(["This ", "is ", "a ", "test."])
    return mock


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_document() -> dict:
    """Return a sample document dictionary."""
    return {
        "id": "test_doc_1",
        "content": "The derivative of $x^2$ is $2x$.",
        "metadata": {
            "topic": "derivatives.power_rule",
            "difficulty": 2,
            "prerequisites": ["limits.introduction"],
            "source_file": "derivatives/power_rule.md",
        },
    }


@pytest.fixture
def sample_chunks() -> list[dict]:
    """Return sample document chunks."""
    return [
        {
            "id": "chunk_1",
            "content": "# Power Rule\n\nThe power rule states that...",
            "metadata": {"topic": "derivatives.power_rule", "chunk_index": 0},
        },
        {
            "id": "chunk_2",
            "content": "## Examples\n\nExample 1: Find d/dx of x^3...",
            "metadata": {"topic": "derivatives.power_rule", "chunk_index": 1},
        },
    ]


@pytest.fixture
def sample_student() -> dict:
    """Return a sample student dictionary."""
    return {
        "id": "student_001",
        "name": "Test Student",
        "mastery_levels": {
            "algebra.factoring": 0.8,
            "limits.introduction": 0.6,
            "derivatives.power_rule": 0.3,
        },
        "learning_history": [],
        "preferences": {
            "explanation_style": "step_by_step",
            "difficulty_preference": "adaptive",
        },
    }


# =============================================================================
# Markers
# =============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
