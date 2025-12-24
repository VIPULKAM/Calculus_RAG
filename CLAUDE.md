# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Retrieval-Augmented Generation (RAG) system designed to help high school students learn calculus with intelligent prerequisite support. The system detects knowledge gaps and provides adaptive, step-by-step explanations.

**Tech Stack:**
- LLM: Qwen2-Math 1.5B/7B + DeepSeek 671B Cloud (via Ollama with smart routing)
- Embeddings: mxbai-embed-large (1024 dimensions) via Ollama
- Vector Store: PostgreSQL 16 + pgvector (IVFFlat indexing)
- PDF Processing: pymupdf4llm
- API: FastAPI
- Frontend: Streamlit

## Development Commands

### Setup
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies (using uv is faster)
~/.local/bin/uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

### Database
```bash
# Start PostgreSQL with pgvector (required for development)
docker-compose up -d postgres

# Start test database
docker-compose up -d postgres_test
```

### Knowledge Base Management
```bash
# Full ingestion - PDFs from knowledge_content/ (clears existing data)
python scripts/ingest_pdfs.py

# Add a single PDF without clearing existing data
python scripts/add_pdf.py path/to/file.pdf

# Ingest Khan Academy markdown files
python scripts/ingest_markdown.py --dir knowledge_content/khan_academy

# Check what's been ingested
python scripts/check_ingestion.py

# Interactive RAG testing (terminal)
python scripts/interactive_rag.py

# Interactive with cloud model support
python scripts/interactive_rag_with_cloud.py
```

### Backup & Restore
```bash
# Create backup (compressed binary format)
python scripts/backup_db.py                    # Timestamped backup
python scripts/backup_db.py my_backup          # Named backup

# Restore from backup (parallel restore)
python scripts/restore_db.py backups/starter.dump

# Pre-built starter backup included: backups/starter.dump (6,835 chunks)
```

### Web Interface (Recommended)
```bash
# Launch Streamlit app with beautiful LaTeX rendering
./run_app.sh

# Or manually:
streamlit run app.py

# Access at: http://localhost:8501
```

**Note:** The Streamlit app renders LaTeX as beautiful mathematical notation (fractions, limits, integrals, etc.) instead of raw LaTeX code. Perfect for student-facing use!

### Testing
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src/calculus_rag

# Run specific test markers
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m slow           # Slow tests

# Run specific test file
pytest tests/unit/test_embeddings/test_base.py

# Run single test
pytest tests/unit/test_embeddings/test_base.py::test_function_name
```

### Code Quality
```bash
# Lint code
ruff check src tests

# Type checking
mypy src

# Both together
ruff check src tests && mypy src
```

### Environment Configuration
Copy `.env.example` to `.env` and configure as needed. Default values work with the docker-compose setup.

## Code Architecture

### Core Modules

The codebase follows a layered architecture with clear separation of concerns:

**`src/calculus_rag/config.py`**
- Centralized configuration using pydantic-settings
- All settings loaded from environment variables or `.env` file
- Access settings via `get_settings()` which returns cached singleton

**`src/calculus_rag/embeddings/`**
- `base.py`: Abstract base class for embedders
- `bge_embedder.py`: BGE-base-en-v1.5 via sentence-transformers (768d, legacy)
- `ollama_embedder.py`: **mxbai-embed-large via Ollama (1024d, current)**
- Embedder type configurable via `EMBEDDING_TYPE` env var ("ollama" or "sentence-transformers")

**`src/calculus_rag/vectorstore/`**
- `base.py`: Abstract base class for vector stores
- `pgvector_store.py`: PostgreSQL + pgvector implementation
- Stores document chunks with embeddings for retrieval

**`src/calculus_rag/llm/`**
- `base.py`: Abstract base class for LLM providers
- `ollama_llm.py`: Ollama integration (qwen2.5-math:7b)
- `cloud_llm.py`: Cloud providers (OpenRouter, DeepSeek, Ollama Cloud)
- `model_router.py`: Smart routing based on question complexity:
  - SIMPLE: Basic definitions → qwen2-math:1.5b (fast, local)
  - MODERATE: Standard problems → qwen2-math:7b (local)
  - COMPLEX: Proofs/derivations → DeepSeek 671B (cloud fallback)

**`src/calculus_rag/knowledge_base/`**
- `models.py`: Pydantic models for Document, Chunk, and DocumentMetadata
- `loader.py`: Loads markdown files from `knowledge_content/`
- `chunker.py`: Splits documents into chunks for embedding
- `metadata.py`: Extracts YAML frontmatter from markdown files

**`src/calculus_rag/loaders/`**
- `pdf_loader.py`: Base PDF loading functionality
- `pymupdf_loader.py`: PyMuPDF-based PDF extraction (better for math/structure)

**`src/calculus_rag/prerequisites/`**
- **Core feature:** Manages prerequisite relationships between calculus topics
- `topics.py`: Complete calculus curriculum with topic metadata and prerequisites
- `graph.py`: PrerequisiteGraph for dependency resolution and topological sorting
- `detector.py`: Detects missing prerequisites from student queries
- Topics use dot notation (e.g., "limits.introduction", "derivatives.chain_rule")

**`src/calculus_rag/student/`**
- Student progress tracking and mastery level management
- Tracks which topics students have mastered

**`src/calculus_rag/rag/`**
- `pipeline.py`: Main RAG orchestration logic
- Combines retrieval, LLM generation, and prerequisite detection

**`src/calculus_rag/retrieval/`**
- `retriever.py`: Base semantic search and retrieval logic
- `hybrid_retriever.py`: Combines semantic + keyword search
- `prerequisite_aware_retriever.py`: Retrieves context while considering prerequisite topics

**`src/calculus_rag/api/`**
- FastAPI application for serving the RAG system

### Knowledge Content Structure

The `knowledge_content/` directory contains PDFs and markdown files organized by topic:
```
knowledge_content/
├── calculus/                    # Main calculus PDFs
│   ├── derivatives/             # Derivative cheat sheets
│   ├── integration/             # Integration cheat sheets
│   └── limits/                  # Limits cheat sheets
├── pre_calculus/
│   ├── algebra/                 # Algebra PDFs and review materials
│   └── trigonometry/            # Trig cheat sheets
├── guides/                      # Study guides (How to Study Math, etc.)
├── reference/                   # Reference materials (Laplace tables, etc.)
└── khan_academy/
    └── precalculus/             # 44 Khan Academy video summaries (markdown)
```

Khan Academy markdown files have YAML frontmatter:
```yaml
---
topic: precalculus.khan_academy
title: "Video Title"
source: Khan Academy
source_url: https://youtube.com/watch?v=...
video_id: abc123
difficulty: 2
content_type: video_summary
---
```

### Topic Identifier Convention

Topics use **dot notation** (e.g., `algebra.basics`, `derivatives.chain_rule`):
- Pre-calculus: `algebra.*`, `functions.*`, `trig.*`, `exp_log.*`
- Calculus: `limits.*`, `derivatives.*`, `integration.*`, `applications.*`

All topics are defined in `src/calculus_rag/prerequisites/topics.py` with their prerequisites, difficulty levels, and metadata.

### Testing Structure

Tests are organized in `tests/` with unit and integration subdirectories:
- `tests/conftest.py`: Shared fixtures for all tests
- `tests/unit/`: Unit tests mirroring the source structure
- `tests/integration/`: Integration tests for full workflows
- Fixtures include mock embedders, vector stores, LLMs, and sample data

**Important testing notes:**
- Coverage requirement: 80% (configured in pyproject.toml)
- Use provided fixtures (`mock_embedder`, `mock_vectorstore`, `mock_llm`) for unit tests
- Test database runs on port 5433 to avoid conflicts with development database
- Use `sample_docs_dir` fixture for testing knowledge base loading

### Configuration Management

All configuration is managed through `src/calculus_rag/config.py`:
- Uses pydantic-settings for validation and environment variable loading
- Settings singleton: `from calculus_rag.config import get_settings`
- Key settings: embedding model, vector dimensions, PostgreSQL connection, Ollama URL
- Connection strings built automatically via `postgres_dsn` and `postgres_async_dsn` properties

### Important Patterns

**Vector Dimensions:**
- **Current:** mxbai-embed-large produces 1024-dimensional embeddings (better retrieval quality)
- Legacy: BGE-base-en-v1.5 produces 768-dimensional embeddings
- Vector dimension is configurable via `VECTOR_DIMENSION` env var (currently 1024)
- Must match between embedding model and vector store

**Knowledge Base:**
- **Total: 6,835 chunks** in calculus_knowledge table
- 17 PDFs ingested from OpenStax + Paul's Online Notes + user content
- 44 Khan Academy video summaries (markdown)
- Chunking: 512 characters with 50-char overlap (optimized for mxbai context window)
- PDF processor: pymupdf4llm (better than pypdf for math/structure preservation)
- Database: calculus_knowledge table with 1024-d vectors
- Categories: Pre-Calculus (Algebra, Trig), Calculus 1 (Limits, Derivatives, Integration), Khan Academy, Guides, Reference
- **Pre-built backup:** `backups/starter.dump` (33.97 MB) - restore in ~30 seconds

**Database Setup:**
- PostgreSQL 16 with pgvector extension is required
- Two databases: development (port 5432) and test (port 5433)
- Use docker-compose for local development

**Prerequisite Graph:**
- Built from `CALCULUS_TOPICS` dictionary in `topics.py`
- Use `build_prerequisite_graph()` to get a graph instance
- Graph provides topological sort and prerequisite checking

**Async Patterns:**
- Vector store operations are async (use `async`/`await`)
- Retrievers expose async methods for queries
- App code manages event loops for Streamlit compatibility

**Key Environment Variables:**
```
ENVIRONMENT=development|testing|production
EMBEDDING_TYPE=ollama|sentence-transformers
EMBEDDING_MODEL_NAME=mxbai-embed-large
VECTOR_DIMENSION=1024
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2-math:7b
CLOUD_LLM_ENABLED=true|false
CLOUD_LLM_MODEL=deepseek-r1:671b
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

**Cloud LLM Setup:**
- Uses Ollama Cloud (via `ollama login`) - no API key management needed
- Cloud model: DeepSeek R1 671B for complex proofs/derivations
- Set `CLOUD_LLM_ENABLED=true` after running `ollama login`
