# Quick Start Guide

> **Get Tender-RAG-Lab running in 10 minutes**

This guide will get you from zero to a working RAG system as quickly as possible.

---

## Prerequisites

Before starting, ensure you have:

- **Python 3.11+** installed
- **Docker & Docker Compose** installed
- **Git** installed
- **5GB free disk space** (for Docker volumes)

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/gmottola00/Tender-RAG-Lab.git
cd Tender-RAG-Lab
```

---

## Step 2: Install Dependencies

We use `uv` for fast dependency management:

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync
```

This creates `.venv/` and installs all dependencies from `pyproject.toml`.

---

## Step 3: Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

**Minimal configuration** (edit `.env`):

```bash
# Milvus (required)
MILVUS_URI=http://localhost:19530
MILVUS_USER=root
MILVUS_PASSWORD=Milvus
MILVUS_DB=default
MILVUS_COLLECTION=tender_chunks

# Choose ONE embedding provider:

# Option A: Ollama (local, free)
OLLAMA_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_LLM_MODEL=llama3.2

# Option B: OpenAI (cloud, paid)
# OPENAI_API_KEY=your-key-here
# OPENAI_EMBED_MODEL=text-embedding-3-small
# OPENAI_LLM_MODEL=gpt-4

# Database (optional for basic testing)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/tender_db
```

**See [Environment Setup](environment-setup.md) for complete configuration.**

---

## Step 4: Start Services

### Start Milvus (vector database):

```bash
docker-compose up -d
```

This starts:
- Milvus standalone
- etcd (metadata store)
- MinIO (object storage)

**Wait 30 seconds** for services to initialize.

**Verify Milvus is running:**
```bash
curl http://localhost:19530/healthz
# Should return: OK
```

### (Optional) Start Ollama:

If using Ollama for embeddings/LLM:

```bash
# Install Ollama from https://ollama.ai
ollama pull nomic-embed-text
ollama pull llama3.2
ollama serve  # Runs on http://localhost:11434
```

---

## Step 5: Initialize Database (Optional)

If you plan to use the Tender management features:

```bash
# Run migrations
source .venv/bin/activate
alembic upgrade head
```

For basic RAG testing, **you can skip this step**.

---

## Step 6: Start the Application

```bash
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Application starts on:** http://localhost:8000

---

## Step 7: Test the API

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{"status": "healthy"}
```

### Test 2: Parse a Document

```bash
curl -X POST http://localhost:8000/api/ingestion/parse \
  -F "file=@path/to/your-document.pdf"
```

**Expected:** JSON with parsed pages and text.

### Test 3: RAG Query

First, index some documents (via web UI or API), then:

```bash
curl -X POST http://localhost:8000/api/ingestion/rag-query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the tender requirements?",
    "collection_name": "tender_chunks"
  }'
```

**Expected:** JSON with answer and citations.

---

## 🎉 Success!

You now have a working RAG system! Here's what you can do next:

### Web UI

- **Home:** http://localhost:8000/
- **Demo:** http://localhost:8000/demo
- **Milvus Explorer:** http://localhost:8000/api/milvus/

### Next Steps

1. **[Environment Setup](environment-setup.md)** - Complete configuration guide
2. **[Local Development](local-development.md)** - Development workflow
3. **[Architecture Overview](../architecture/overview.md)** - Understand the system
4. **[API Endpoints](../apps/api-endpoints.md)** - Complete API reference

---

## Troubleshooting

### Milvus Connection Error

**Error:** `Failed to connect to Milvus at http://localhost:19530`

**Solutions:**
1. Check Milvus is running: `docker-compose ps`
2. Check logs: `docker-compose logs milvus-standalone`
3. Restart: `docker-compose restart`
4. Wait 30 seconds after starting

### Database Not Found

**Error:** `database not found[database=default]`

**Solution:** Create the database first:
```bash
# Using Milvus admin UI or:
curl -X POST http://localhost:19530/v1/vector/databases \
  -H "Content-Type: application/json" \
  -d '{"database_name": "default"}'
```

### Ollama Not Responding

**Error:** `Connection refused` when calling Ollama

**Solutions:**
1. Ensure Ollama is running: `ollama serve`
2. Check URL in `.env`: `OLLAMA_URL=http://localhost:11434`
3. Pull models: `ollama pull nomic-embed-text`

### Module Import Errors

**Error:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
```bash
# Ensure you're in the virtual environment
source .venv/bin/activate

# Reinstall dependencies
uv sync
```

---

## 📞 Need Help?

- **Documentation:** [Full docs](../README.md)
- **Issues:** [GitHub Issues](https://github.com/gmottola00/Tender-RAG-Lab/issues)
- **Discussions:** [GitHub Discussions](https://github.com/gmottola00/Tender-RAG-Lab/discussions)

---

**[⬆️ Documentation Home](../README.md) | [Environment Setup ➡️](environment-setup.md)**

*Last updated: 2025-12-18*
