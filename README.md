# Calculus RAG

A Retrieval-Augmented Generation (RAG) system designed to help high school students learn calculus with intelligent prerequisite support.

## Features

- **Prerequisite Detection**: Automatically identifies gaps in foundational knowledge
- **Adaptive Learning**: Tracks student progress and adjusts difficulty
- **Step-by-Step Explanations**: Breaks down complex calculus concepts
- **Open Source Stack**: Built entirely with open-source tools

## Tech Stack

- **LLM**: Qwen2-Math 1.5B/7B + DeepSeek 671B Cloud (via Ollama with smart routing)
- **Embeddings**: mxbai-embed-large (1024 dimensions) via Ollama
- **Vector Store**: PostgreSQL 16 + pgvector (IVFFlat indexing)
- **PDF Processing**: pymupdf4llm
- **API**: FastAPI
- **Frontend**: Streamlit

## Current Status

✅ **Sprint 5 Complete** - PDF Knowledge Base & Smart Routing
- 16 PDFs ingested (OpenStax + Paul's Online Notes)
- 3-tier model routing (simple → local 1.5B, complex → cloud 671B)
- Migrating to mxbai-embed-large (1024d) for better retrieval quality

See [NEXT_STEPS.md](NEXT_STEPS.md) for detailed status and upcoming work.

## Installation

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with uv (faster)
~/.local/bin/uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

### 2. Start PostgreSQL with pgvector

```bash
# Using Docker Compose (recommended)
docker-compose up -d postgres

# Or install PostgreSQL 16 + pgvector extension manually
# See: https://github.com/pgvector/pgvector#installation
```

### 3. Configure Environment

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your settings (defaults work with docker-compose)
```

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=src/calculus_rag

# Code quality
ruff check src tests
mypy src
```

## Project Status

Currently in active development. See Sprint planning in the project documentation.

## License

MIT
