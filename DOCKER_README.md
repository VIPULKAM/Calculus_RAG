# Docker Deployment Guide

Quick guide to deploy Calculus RAG using Docker Compose with Ollama Cloud models.

## Prerequisites

- Docker 24+ and Docker Compose v2
- 8GB+ RAM
- Ollama Cloud account (free at [ollama.com](https://ollama.com))

## Quick Start (5 Steps)

### Step 1: Clone and Configure

```bash
# Clone repository
git clone https://github.com/VIPULKAM/Calculus_RAG.git
cd Calculus_RAG

# Create production environment file
cp .env.prod.example .env.prod

# Edit .env.prod and set your password
nano .env.prod
```

**.env.prod configuration:**
```bash
POSTGRES_PASSWORD=your_secure_password_here
CLOUD_LLM_ENABLED=true
CLOUD_LLM_PROVIDER=ollama-cloud
CLOUD_LLM_MODEL=deepseek-v3.1:671b-cloud
```

### Step 2: Start Database and Ollama

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d postgres ollama
```

Wait for services to be healthy:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Step 3: Sign in to Ollama Cloud

```bash
# Sign in to Ollama Cloud (opens browser for authentication)
docker exec -it calculus_rag_ollama_prod ollama signin
```

### Step 4: Pull Models

```bash
# Required: Embedding model
docker exec calculus_rag_ollama_prod ollama pull mxbai-embed-large

# Required: Local math model (fast, for simple questions)
docker exec calculus_rag_ollama_prod ollama pull qwen2-math:1.5b

# Cloud models (choose based on your needs)
docker exec calculus_rag_ollama_prod ollama pull deepseek-v3.1:671b-cloud   # Fast, good quality
docker exec calculus_rag_ollama_prod ollama pull deepseek-v3.2:cloud        # Latest DeepSeek
docker exec calculus_rag_ollama_prod ollama pull gpt-oss:120b-cloud         # Best for students
docker exec calculus_rag_ollama_prod ollama pull devstral-2:123b-cloud      # Code questions
docker exec calculus_rag_ollama_prod ollama pull qwen3-vl:235b-cloud        # Vision (images)
```

Verify models:
```bash
docker exec calculus_rag_ollama_prod ollama list
```

### Step 5: Build and Start App

```bash
# Build the app image
docker compose -f docker-compose.prod.yml --env-file .env.prod build app

# Start the app
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d app

# Restore knowledge base (6,835 calculus chunks)
docker cp calculus_rag_app_prod:/app/backups/starter.dump /tmp/starter.dump
docker cp /tmp/starter.dump calculus_rag_postgres_prod:/tmp/starter.dump
docker exec calculus_rag_postgres_prod pg_restore -U calculus -d calculus_rag \
  --clean --if-exists --no-owner -j 4 /tmp/starter.dump
rm /tmp/starter.dump
```

### Access the App

Open http://localhost:8501 in your browser.

---

## Features

### Smart Model Routing

The app automatically routes questions based on complexity:

| Question Type | Model Used | Example |
|--------------|------------|---------|
| Simple | qwen2-math:1.5b (local) | "What is a derivative?" |
| Complex | Cloud model | "Prove the chain rule" |
| Code | devstral-2:123b-cloud | "Write Python for integration" |

### Model Selector (New!)

Users can override auto-routing and select a specific cloud model from the sidebar dropdown:

- **Auto (Smart Routing)** - Default, uses complexity-based routing
- **deepseek-v3.1:671b-cloud** - Fast, good quality (recommended)
- **deepseek-v3.2:cloud** - Latest version, 671B parameters
- **gpt-oss:120b-cloud** - Best explanations for students
- **devstral-2:123b-cloud** - Optimized for code
- **qwen3-vl:235b-cloud** - Can process images

### Cloud Model Comparison

Tested with: *"Explain the chain rule with a simple example for high school students"*

| Model | Response Time | Best For |
|-------|--------------|----------|
| deepseek-v3.1:671b-cloud | 6.4s | Fast + quality balance |
| gpt-oss:120b-cloud | 9.7s | Clearest explanations |
| deepseek-v3.2:cloud | 20.9s | Latest capabilities |
| devstral-2:123b-cloud | 38.3s | Code questions |

---

## Management Commands

### View Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f app
```

### Restart Services

```bash
# Restart app after config changes
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d app

# Restart all
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### Stop Services

```bash
# Stop all (keeps data)
docker compose -f docker-compose.prod.yml down

# Stop and remove volumes (WARNING: deletes data)
docker compose -f docker-compose.prod.yml down -v
```

### Check Health

```bash
docker ps --filter "name=calculus_rag" --format "table {{.Names}}\t{{.Status}}"
```

Expected output:
```
NAMES                        STATUS
calculus_rag_app_prod        Up X minutes (healthy)
calculus_rag_postgres_prod   Up X minutes (healthy)
calculus_rag_ollama_prod     Up X minutes (healthy)
```

---

## Backup & Restore

### Create Backup

```bash
docker exec calculus_rag_postgres_prod pg_dump -U calculus -Fc calculus_rag \
  > backup_$(date +%Y%m%d).dump
```

### Restore Backup

```bash
docker cp your_backup.dump calculus_rag_postgres_prod:/tmp/backup.dump
docker exec calculus_rag_postgres_prod pg_restore -U calculus -d calculus_rag \
  --clean --if-exists --no-owner -j 4 /tmp/backup.dump
```

---

## Troubleshooting

### Ollama Container Unhealthy

If the Ollama container shows "unhealthy":
```bash
# Check logs
docker logs calculus_rag_ollama_prod

# Verify Ollama is responding
docker exec calculus_rag_ollama_prod ollama list
```

### Database Connection Error

If app shows "password authentication failed":
```bash
# Verify environment variables
docker exec calculus_rag_app_prod env | grep POSTGRES

# Ensure .env.prod has correct values and restart
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### Cloud Model Not Working

If cloud models fail:
```bash
# Re-authenticate with Ollama Cloud
docker exec -it calculus_rag_ollama_prod ollama signin

# Re-pull the model
docker exec calculus_rag_ollama_prod ollama pull deepseek-v3.1:671b-cloud
```

### Port Already in Use

```bash
# Check what's using port 8501
sudo lsof -i :8501

# Use a different port in .env.prod
APP_PORT=8502
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                          │
│                     http://localhost:8501                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit App (app)                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Model Selector: Auto / Cloud Model Dropdown        │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  RAG Pipeline: Retrieval → LLM → Response           │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                    │                       │
                    ▼                       ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│   PostgreSQL + pgvector   │   │         Ollama            │
│   (calculus_knowledge)    │   │  ┌─────────────────────┐  │
│                           │   │  │ Local Models:       │  │
│   6,835 chunks            │   │  │ - qwen2-math:1.5b   │  │
│   1024-dim vectors        │   │  │ - mxbai-embed-large │  │
│                           │   │  └─────────────────────┘  │
│                           │   │  ┌─────────────────────┐  │
│                           │   │  │ Cloud Models:       │  │
│                           │   │  │ - deepseek-v3.1     │  │
│                           │   │  │ - gpt-oss:120b      │  │
│                           │   │  │ - etc.              │  │
│                           │   │  └─────────────────────┘  │
└───────────────────────────┘   └───────────────────────────┘
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_PASSWORD` | (required) | Database password |
| `POSTGRES_USER` | calculus | Database user |
| `POSTGRES_DB` | calculus_rag | Database name |
| `APP_PORT` | 8501 | Streamlit port |
| `OLLAMA_MODEL` | qwen2-math:1.5b | Default local model |
| `CLOUD_LLM_ENABLED` | false | Enable cloud models |
| `CLOUD_LLM_PROVIDER` | ollama-cloud | Cloud provider |
| `CLOUD_LLM_MODEL` | deepseek-v3.1:671b-cloud | Default cloud model |

---

## Next Steps

- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment guide with Kubernetes
- [CLAUDE.md](CLAUDE.md) - Developer documentation
- [README.md](README.md) - Project overview
