# Calculus RAG

An AI-powered tutor that helps high school students learn calculus. Ask questions in plain English and get step-by-step explanations with beautiful mathematical notation.

## What Does This Do?

This is a **Retrieval-Augmented Generation (RAG)** system - it combines a knowledge base of calculus materials with AI to give accurate, helpful answers. Think of it as a smart tutor that:

- Answers your calculus questions with clear explanations
- Shows math formulas as proper notation (not ugly code)
- Detects when you're missing prerequisite knowledge and helps fill gaps
- Routes simple questions to fast AI, complex questions to powerful AI

## Example Questions You Can Ask

- "What is a derivative?"
- "Explain the chain rule step by step"
- "How do I solve x² + 5x + 6 = 0?"
- "What is the limit definition of a derivative?"
- "Prove that the derivative of sin(x) is cos(x)"

---

## Requirements

Before starting, you need to install these tools on your computer:

| Tool | What It Does | Install Link |
|------|--------------|--------------|
| **Python 3.10+** | Runs the application | [python.org](https://www.python.org/downloads/) |
| **Docker** | Runs the database | [docker.com](https://docs.docker.com/get-docker/) |
| **Ollama** | Runs AI models locally | [ollama.com](https://ollama.com/download) |

### How to Check If You Have Them

Open a terminal and run:

```bash
python3 --version    # Should show Python 3.10 or higher
docker --version     # Should show Docker version
ollama --version     # Should show Ollama version
```

---

## Installation (Step by Step)

### Step 1: Clone This Repository

```bash
git clone https://github.com/VIPULKAM/Calculus_RAG.git
cd Calculus_RAG
```

### Step 2: Download the AI Models

Ollama needs to download the AI models (this may take a few minutes):

```bash
# The math-specialized AI (small and fast)
ollama pull qwen2-math:1.5b

# The math-specialized AI (larger and smarter)
ollama pull qwen2-math:7b

# The embedding model (converts text to numbers for search)
ollama pull mxbai-embed-large
```

**Note:** These downloads are large (several GB total). Make sure you have enough disk space and a stable internet connection.

### Step 3: Create a Virtual Environment

A virtual environment keeps this project's packages separate from your system:

```bash
# Create the virtual environment
python3 -m venv .venv

# Activate it (you'll need to do this every time you open a new terminal)
source .venv/bin/activate
```

**How do you know it worked?** Your terminal prompt should now start with `(.venv)`.

### Step 4: Install Python Packages

```bash
# Option A: Using pip (standard)
pip install -e ".[dev]"

# Option B: Using uv (faster, if you have it)
~/.local/bin/uv pip install -e ".[dev]"
```

This installs all the required Python libraries. It may take a few minutes.

### Step 5: Start the Database

The app uses PostgreSQL with pgvector to store and search the knowledge base:

```bash
# Start the database in the background
docker-compose up -d postgres
```

**How do you know it worked?** Run `docker ps` and you should see a container named `calculus_rag_postgres`.

### Step 6: Configure the Environment

```bash
# Copy the example configuration file
cp .env.example .env
```

The default settings work out of the box. You only need to edit `.env` if you want to use cloud AI models (see [SETUP_CLOUD.md](SETUP_CLOUD.md)).

### Step 7: Load the Knowledge Base

This processes the PDF textbooks and stores them in the database:

```bash
python scripts/ingest_pdfs.py
```

**What to expect:** This takes 5-15 minutes depending on your computer. You'll see progress messages as each PDF is processed.

### Step 8: Run the App!

```bash
# Start the web interface
./run_app.sh
```

Or if that doesn't work:

```bash
streamlit run app.py
```

**Open your browser** and go to: **http://localhost:8501**

---

## Using the App

1. **Type your question** in the chat box at the bottom
2. **View the answer** - math formulas render as beautiful notation
3. **Check sources** - click "View Sources" to see which textbooks were used
4. **Adjust settings** - use the sidebar to change AI creativity level

---

## Troubleshooting

### "Ollama not running" or connection errors

Make sure Ollama is running:

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it
ollama serve
```

### "Database connection failed"

Make sure PostgreSQL is running:

```bash
# Check if the container is running
docker ps

# If not, start it
docker-compose up -d postgres
```

### "Model not found"

Make sure you downloaded the models:

```bash
ollama list   # Should show qwen2-math:1.5b, qwen2-math:7b, mxbai-embed-large
```

### App is slow on first question

This is normal! The first question takes longer because the AI models need to load into memory. Subsequent questions will be faster.

### Math formulas look like code

Try refreshing the browser page. If that doesn't work, clear your browser cache.

---

## Running Tests (For Developers)

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src/calculus_rag

# Check code quality
ruff check src tests
mypy src
```

---

## Project Structure

```
Calculus_RAG/
├── app.py                 # Streamlit web interface
├── scripts/               # Utility scripts
│   ├── ingest_pdfs.py     # Load PDFs into database
│   └── interactive_rag.py # Terminal chat interface
├── src/calculus_rag/      # Main source code
│   ├── config.py          # Settings and configuration
│   ├── embeddings/        # Text-to-vector conversion
│   ├── vectorstore/       # Database operations
│   ├── llm/               # AI model integration
│   ├── rag/               # Main question-answering logic
│   └── prerequisites/     # Topic dependency tracking
├── knowledge_content/     # PDF textbooks and materials
└── tests/                 # Test suite
```

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| AI Models | Qwen2-Math 1.5B/7B | Answer math questions |
| Embeddings | mxbai-embed-large | Search the knowledge base |
| Database | PostgreSQL + pgvector | Store and search documents |
| PDF Processing | pymupdf4llm | Extract text from textbooks |
| Web Interface | Streamlit | User-friendly chat UI |
| API | FastAPI | Backend endpoints |

---

## Optional: Cloud AI Models

For complex questions (like proofs), you can use powerful cloud AI instead of running the large 7B model locally. This is useful if your computer is slow or has limited RAM.

See [SETUP_CLOUD.md](SETUP_CLOUD.md) for setup instructions.

---

## License

MIT - Feel free to use, modify, and distribute.

---

## Need Help?

- Check the [Troubleshooting](#troubleshooting) section above
- Open an issue on GitHub
- Make sure all prerequisites are installed and running
