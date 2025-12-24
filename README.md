# Calculus RAG

An AI-powered tutor that helps high school students learn calculus. Ask questions in plain English and get step-by-step explanations with beautiful mathematical notation.

---

## What Is This?

Imagine having a personal math tutor available 24/7. That's what this app does!

**RAG** stands for "Retrieval-Augmented Generation" - a fancy way of saying the AI looks up information from textbooks before answering your question. This makes answers more accurate and reliable.

**What makes it special:**
- Answers calculus questions with clear, step-by-step explanations
- Shows math formulas beautifully (like in a textbook, not ugly code)
- Detects when you're missing foundational knowledge and helps fill gaps
- Uses smart routing: simple questions → fast AI, complex proofs → powerful AI

---

## Try These Example Questions

Once set up, you can ask things like:

| Simple Questions | Complex Questions |
|------------------|-------------------|
| "What is a derivative?" | "Prove the chain rule" |
| "Explain the power rule" | "Derive the derivative of sin(x) from first principles" |
| "How do I factor x² + 5x + 6?" | "When should I use integration by parts vs substitution?" |

---

## How the AI Routing Works

The app automatically picks the best AI model for your question:

| Your Question Type | AI Model Used | Speed |
|--------------------|---------------|-------|
| Simple definitions | Qwen2-Math 1.5B (runs on your computer) | ⚡ Very fast |
| Standard problems | Qwen2-Math 7B (runs on your computer) | 🔄 Medium |
| Complex proofs | DeepSeek R1 671B (runs in the cloud) | 🧠 Most powerful |

**Don't have a powerful computer?** No problem! You can skip the 7B model and use cloud AI for complex questions instead.

---

## What You'll Need

Before starting, install these free tools:

### For All Users

| Tool | What It Does | How to Get It |
|------|--------------|---------------|
| **Python** | Runs the app | [Download Python 3.10+](https://www.python.org/downloads/) - check "Add to PATH" during install |
| **Docker Desktop** | Runs the database | [Download Docker](https://www.docker.com/products/docker-desktop/) - just install and run it |
| **Ollama** | Runs AI models | [Download Ollama](https://ollama.com/download) - install and it runs automatically |

### How to Verify Everything Is Installed

Open a terminal (PowerShell on Windows, Terminal on Mac/Linux) and run these commands:

```bash
python --version
```
✅ You should see: `Python 3.10.x` or higher

```bash
docker --version
```
✅ You should see: `Docker version 24.x.x` or similar

```bash
ollama --version
```
✅ You should see: `ollama version 0.x.x`

**Something not working?** Make sure you restarted your terminal after installing.

---

## Installation Guide

Choose your operating system:

- [Windows Installation](#windows-installation)
- [Mac/Linux Installation](#maclinux-installation)

---

## Windows Installation

### Step 1: Download the Project

Open **PowerShell** (search for it in the Start menu) and run:

```powershell
git clone https://github.com/VIPULKAM/Calculus_RAG.git
cd Calculus_RAG
```

**Don't have git?** [Download Git for Windows](https://git-scm.com/download/win) first.

---

### Step 2: Download AI Models

These are the "brains" of the tutor. Run each command and wait for it to complete:

```powershell
ollama pull mxbai-embed-large
```
⏱️ Wait for download (~670 MB)

```powershell
ollama pull qwen2-math:1.5b
```
⏱️ Wait for download (~1 GB)

```powershell
ollama pull qwen2-math:7b
```
⏱️ Wait for download (~4 GB) - **Skip this if your computer has less than 16GB RAM**

✅ **Verify:** Run `ollama list` - you should see the models listed.

---

### Step 3: Install uv (Fast Package Manager)

This tool installs Python packages much faster than the default method:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Important:** Close PowerShell completely and open a new one.

✅ **Verify:** Run `uv --version` - you should see a version number.

---

### Step 4: Set Up Python Environment

```powershell
uv venv .venv
```

```powershell
.venv\Scripts\activate
```

✅ **Verify:** Your prompt should now start with `(.venv)`

```powershell
uv pip install -e ".[dev]"
```

⏱️ Wait for packages to install (1-2 minutes)

---

### Step 5: Start the Database

Make sure Docker Desktop is running (check your system tray), then:

```powershell
docker-compose up -d postgres
```

✅ **Verify:** Run `docker ps` - you should see `calculus_rag_postgres` running.

---

### Step 6: Configure Settings

```powershell
copy .env.example .env
```

The default settings work out of the box. See [Cloud Setup](#cloud-setup-optional) if you want to enable cloud AI.

---

### Step 7: Load the Knowledge Base

This reads the calculus textbooks and prepares them for searching:

```powershell
python scripts/ingest_pdfs.py
```

⏱️ This takes 5-15 minutes. You'll see progress messages.

✅ **Verify:** You should see "Ingestion complete" with a count of chunks created.

---

### Step 8: Start the App!

```powershell
streamlit run app.py
```

🎉 **Your browser should open automatically to http://localhost:8501**

If not, open your browser and go to that address manually.

---

## Mac/Linux Installation

### Step 1: Download the Project

Open **Terminal** and run:

```bash
git clone https://github.com/VIPULKAM/Calculus_RAG.git
cd Calculus_RAG
```

---

### Step 2: Download AI Models

These are the "brains" of the tutor. Run each command and wait for it to complete:

```bash
ollama pull mxbai-embed-large
```
⏱️ Wait for download (~670 MB)

```bash
ollama pull qwen2-math:1.5b
```
⏱️ Wait for download (~1 GB)

```bash
ollama pull qwen2-math:7b
```
⏱️ Wait for download (~4 GB) - **Skip this if your computer has less than 16GB RAM**

✅ **Verify:** Run `ollama list` - you should see the models listed.

---

### Step 3: Install uv (Fast Package Manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Important:** Close Terminal and open a new one, OR run:
```bash
source $HOME/.local/bin/env
```

✅ **Verify:** Run `uv --version` - you should see a version number.

---

### Step 4: Set Up Python Environment

```bash
uv venv .venv
```

```bash
source .venv/bin/activate
```

✅ **Verify:** Your prompt should now start with `(.venv)`

```bash
uv pip install -e ".[dev]"
```

⏱️ Wait for packages to install (1-2 minutes)

---

### Step 5: Start the Database

Make sure Docker Desktop is running, then:

```bash
docker-compose up -d postgres
```

✅ **Verify:** Run `docker ps` - you should see `calculus_rag_postgres` running.

---

### Step 6: Configure Settings

```bash
cp .env.example .env
```

The default settings work out of the box. See [Cloud Setup](#cloud-setup-optional) if you want to enable cloud AI.

---

### Step 7: Load the Knowledge Base

This reads the calculus textbooks and prepares them for searching:

```bash
python scripts/ingest_pdfs.py
```

⏱️ This takes 5-15 minutes. You'll see progress messages.

✅ **Verify:** You should see "Ingestion complete" with a count of chunks created.

---

### Step 8: Start the App!

```bash
./run_app.sh
```

Or if that doesn't work:
```bash
streamlit run app.py
```

🎉 **Your browser should open automatically to http://localhost:8501**

---

## Cloud Setup (Optional)

**Why use cloud AI?**
- Your computer has less than 16GB RAM
- You want better answers for complex proofs
- You skipped downloading the 7B model

**What is it?**
DeepSeek R1 is a powerful 671 billion parameter AI that runs on Ollama's cloud servers. It's much smarter than the local models for complex math.

### How to Enable Cloud AI

**Step 1:** Create a free Ollama account at [ollama.com](https://ollama.com)

**Step 2:** Log in from your terminal:
```bash
ollama login
```
Follow the prompts to authenticate.

**Step 3:** Edit your `.env` file and change:
```
CLOUD_LLM_ENABLED=true
```

**Step 4:** Restart the app

That's it! Complex questions will now be routed to DeepSeek R1 in the cloud.

---

## Quick Start with Pre-Built Knowledge Base

Don't want to wait for ingestion? A pre-built knowledge base backup is included!

**Instead of Step 7 (Load the Knowledge Base), you can:**

### Windows
```powershell
python scripts/restore_db.py backups/starter.dump
```

### Mac/Linux
```bash
python scripts/restore_db.py backups/starter.dump
```

This restores 6,835 pre-processed chunks from calculus textbooks and Khan Academy in about 30 seconds!

**What's included:**
- 16 calculus PDFs (OpenStax, Paul's Online Notes)
- 44 Khan Academy video summaries
- Pre-computed embeddings for fast search

---

## Backup & Restore

### Create Your Own Backup

After adding new content, back up your knowledge base:

```bash
python scripts/backup_db.py                    # Creates timestamped backup
python scripts/backup_db.py my_backup_name     # Creates named backup
```

Backups are stored in `backups/` as compressed binary files.

### Restore From Backup

```bash
python scripts/restore_db.py backups/starter.dump
```

**Warning:** Restoring replaces all existing data in the knowledge base.

### Adding New PDFs

Add a single PDF without re-ingesting everything:

```bash
python scripts/add_pdf.py path/to/your/file.pdf
```

---

## Using the App

Once the app is running:

1. **Type your question** in the chat box at the bottom
2. **Wait for the answer** - it may take a few seconds, especially for the first question
3. **Read the explanation** - math formulas appear beautifully formatted
4. **Click "View Sources"** to see which textbook sections were used
5. **Ask follow-up questions** - the AI remembers your conversation

**Tip:** The first question is always slower because the AI models need to load into memory.

---

## Troubleshooting

### "Ollama not running"

**Windows:** Look for Ollama in the system tray. If it's not there, search for "Ollama" in the Start menu and run it.

**Mac/Linux:** Run `ollama serve` in a separate terminal.

---

### "Database connection failed"

Make sure Docker Desktop is running, then:
```bash
docker-compose up -d postgres
```

---

### "Model not found"

Check which models you have:
```bash
ollama list
```

You need at least: `mxbai-embed-large` and `qwen2-math:1.5b`

---

### "Out of memory" or computer freezing

Your computer doesn't have enough RAM for the 7B model. Solutions:

1. Close other applications
2. Skip the 7B model and enable cloud AI (see [Cloud Setup](#cloud-setup-optional))
3. Restart your computer and try again

---

### App is slow on first question

This is normal! The AI models need to load into memory. Subsequent questions will be faster.

---

### Math formulas look like code (raw LaTeX)

1. Refresh your browser page
2. If that doesn't work, clear your browser cache
3. Try a different browser (Chrome works best)

---

### "uv: command not found"

Close your terminal completely and open a new one. If still not working:

**Windows:** Run the install command again in a new PowerShell window.

**Mac/Linux:** Run `source $HOME/.local/bin/env`

---

## Running Tests (For Developers)

```bash
# Make sure virtual environment is activated first
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows

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
├── app.py                 # Web interface (Streamlit)
├── scripts/               # Utility scripts
│   ├── ingest_pdfs.py     # Load textbooks into database
│   └── interactive_rag.py # Terminal chat interface
├── src/calculus_rag/      # Main source code
│   ├── config.py          # Settings
│   ├── embeddings/        # Text search
│   ├── vectorstore/       # Database
│   ├── llm/               # AI models & routing
│   ├── rag/               # Question answering
│   └── prerequisites/     # Topic dependencies
├── knowledge_content/     # Calculus textbooks (PDFs)
└── tests/                 # Test suite
```

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Local AI | Qwen2-Math 1.5B/7B | Fast answers for simple questions |
| Cloud AI | DeepSeek R1 671B | Powerful answers for complex proofs |
| Search | mxbai-embed-large | Find relevant textbook sections |
| Database | PostgreSQL + pgvector | Store and search documents |
| PDF Processing | pymupdf4llm | Extract text from textbooks |
| Web Interface | Streamlit | User-friendly chat UI |
| Package Manager | uv | Fast dependency installation |

---

## License

MIT - Feel free to use, modify, and distribute.

---

## Need Help?

1. Check the [Troubleshooting](#troubleshooting) section above
2. Make sure all prerequisites are installed and running
3. Open an issue on [GitHub](https://github.com/VIPULKAM/Calculus_RAG/issues)
