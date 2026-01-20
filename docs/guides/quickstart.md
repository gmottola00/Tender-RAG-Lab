# Quick Start Guide

!!! tip "⚡ From Zero to RAG in 10 Minutes"
    Get **Tender-RAG-Lab** running in record time with this streamlined guide.
    
    Perfect for: Demos, testing, first-time setup.

---

## :material-checkbox-marked-circle-outline: Prerequisites

!!! info "What You Need"
    Quick checklist before starting:

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| :material-language-python: **Python** | 3.12+ | `python --version` |
| :material-docker: **Docker** | Latest | `docker --version` |
| :material-git: **Git** | Any | `git --version` |
| :material-harddisk: **Disk Space** | ~5GB | `df -h` |

---

## :material-numeric-1-circle: Clone Repository

```bash title="Get the code"
git clone https://github.com/gmottola00/Tender-RAG-Lab.git
cd Tender-RAG-Lab
```

!!! success "✅ Step 1 Complete"
    You're now in the project directory.

---

## :material-numeric-2-circle: Install Dependencies

!!! tip "We use `uv` for blazing-fast installs"

=== "🚀 Install uv First"

    ```bash title="Install uv package manager"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Restart shell or run:
    source ~/.bashrc  # or ~/.zshrc
    ```

=== "📦 Install Project Deps"

    ```bash title="Create venv and install"
    # One command does it all
    uv sync
    
    # Verify installation
    uv pip list | grep fastapi
    ```
    
    !!! success "Done!"
        Creates `.venv/` and installs everything from `pyproject.toml`

---

## :material-numeric-3-circle: Configure Environment

!!! info "Minimal Setup"
    Copy and edit the environment template:

```bash title="Create .env file"
cp .env.example .env
```

**Edit `.env` with these minimal settings:**

=== "🔍 Milvus (Required)"

    ```bash title=".env - Vector Database"
    MILVUS_URI=http://localhost:19530
    MILVUS_USER=root
    MILVUS_PASSWORD=Milvus
    MILVUS_DB=default
    MILVUS_COLLECTION=tender_chunks
    ```

=== "🤖 Choose LLM Provider"

    **Option A: Ollama (Local, Free)** ⭐ Recommended
    
    ```bash title=".env - Ollama"
    OLLAMA_URL=http://localhost:11434
    OLLAMA_EMBED_MODEL=nomic-embed-text
    OLLAMA_LLM_MODEL=llama3.2
    ```
    
    **Option B: OpenAI (Cloud, Paid)**
    
    ```bash title=".env - OpenAI"
    OPENAI_API_KEY=sk-your-key-here
    OPENAI_EMBED_MODEL=text-embedding-3-small
    OPENAI_LLM_MODEL=gpt-4
    ```

=== "🗄️ Database (Optional)"

    ```bash title=".env - PostgreSQL"
    DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/tender_db
    ```
    
    !!! note "Optional for Testing"
        Not required for basic RAG functionality. Only needed for persistent metadata storage.

!!! tip "Full Configuration Guide"
    For production setup, see [:octicons-arrow-right-24: Environment Setup](environment-setup.md)

---

## :material-numeric-4-circle: Start Services

!!! info "Start Infrastructure"
    Launch Milvus and supporting services:

```bash title="Start all Docker services"
docker-compose up -d
```

**This starts:**

| Service | Purpose | Port |
|---------|---------|------|
| 🔍 **Milvus** | Vector database | 19530 |
| 📦 **etcd** | Metadata store | 2379 |
| 💾 **MinIO** | Object storage | 9000 |

!!! warning "Wait for Initialization"
    Services need ~30 seconds to fully start. Grab a coffee! ☕

**Verify Milvus is ready:**

```bash title="Health check"
curl http://localhost:19530/healthz
# Should return: OK
```

=== "🤖 Using Ollama?"

    If you chose Ollama in Step 3, start it now:
    
    ```bash title="Install and start Ollama"
    # Install from https://ollama.ai
    
    # Pull models
    ollama pull nomic-embed-text
    ollama pull llama3.2
    
    # Start server (runs on localhost:11434)
    ollama serve
    ```

---

## :material-numeric-5-circle: Start Application

!!! tip "Launch FastAPI Server"

```bash title="Start the API"
# Activate venv
source .venv/bin/activate  # or `uv shell`

# Run application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Application starts on:** 🌐 http://localhost:8000

---

## :material-test-tube: Test Your Setup

!!! example "Verify Everything Works"

### Test 1: Health Check

```bash title="Ping the API"
curl http://localhost:8000/health
```

??? success "Expected Response"
    ```json
    {
      "status": "healthy",
      "services": {
        "milvus": "connected",
        "database": "connected"
      }
    }
    ```

---

### Test 2: Parse a Document

```bash title="Upload and parse PDF"
curl -X POST http://localhost:8000/api/ingestion/parse \
  -F "file=@path/to/document.pdf"
```

??? success "Expected Response"
    ```json
    {
      "pages": 10,
      "text_length": 15420,
      "chunks": 34,
      "metadata": {...}
    }
    ```

---

### Test 3: RAG Query

```bash title="Semantic search query"
curl -X POST http://localhost:8000/api/ingestion/rag-query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the tender requirements?",
    "collection_name": "tender_chunks"
  }'
```

??? success "Expected Response"
    ```json
    {
      "answer": "The tender requirements include...",
      "sources": [
        {"chunk_id": "chunk_123", "score": 0.89, "text": "..."}
      ],
      "confidence": 0.85
    }
    ```

---

## :material-party-popper: Success!

!!! success "You Did It!"
    Your RAG system is **up and running**! 🎉

### 🌐 Access Points

<div class="grid cards" markdown>

-   :material-home:{ .lg } **Home Page**

    ---

    Main landing page with navigation
    
    [http://localhost:8000/](http://localhost:8000/)

-   :material-api:{ .lg } **Swagger UI**

    ---

    Interactive API documentation
    
    [http://localhost:8000/docs](http://localhost:8000/docs)

-   :material-flask:{ .lg } **Demo Interface**

    ---

    Try the RAG system with a web UI
    
    [http://localhost:8000/demo](http://localhost:8000/demo)

-   :material-database-search:{ .lg } **Milvus Explorer**

    ---

    Browse vector database collections
    
    [http://localhost:8000/api/milvus/](http://localhost:8000/api/milvus/)

</div>

---

## :material-arrow-right-circle: Next Steps

!!! tip "Where to Go From Here"

<div class="grid cards" markdown>

-   :material-file-upload:{ .lg } **Index Documents**

    ---

    Learn how to upload and process tender documents
    
    [:octicons-arrow-right-24: Indexing Guide](indexing-documents.md)

-   :material-magnify:{ .lg } **Search & Retrieval**

    ---

    Master semantic search and hybrid retrieval
    
    [:octicons-arrow-right-24: Search Guide](search-retrieval.md)

-   :material-cog:{ .lg } **Environment Setup**

    ---

    Production configuration and best practices
    
    [:octicons-arrow-right-24: Full Configuration](environment-setup.md)

-   :material-chart-box:{ .lg } **Architecture**

    ---

    Understand the system design and patterns
    
    [:octicons-arrow-right-24: Architecture Overview](../architecture/overview.md)

</div>

---

## :material-help-circle: Troubleshooting

!!! failure "Milvus Connection Error"
    
    **Error:** `Failed to connect to Milvus at http://localhost:19530`
    
    **Solutions:**
    
    ```bash
    # 1. Check if running
    docker-compose ps
    
    # 2. View logs
    docker-compose logs milvus-standalone
    
    # 3. Restart service
    docker-compose restart milvus-standalone
    
    # 4. Wait 30-60 seconds and retry
    ```

!!! failure "Database Not Found"
    
    **Error:** `database not found[database=default]`
    
    **Solution:** Milvus creates database automatically on first use. If error persists:
    
    ```python
    from pymilvus import connections, db
    
    connections.connect(host="localhost", port="19530")
    db.create_database("default")
    ```

!!! failure "Port Already in Use"
    
    **Error:** `Error: address already in use`
    
    **Solution:**
    
    ```bash
    # Find what's using port 8000
    lsof -i :8000
    
    # Kill the process
    kill -9 <PID>
    
    # Or use different port
    uvicorn main:app --port 8001
    ```

!!! failure "Ollama Model Not Found"
    
    **Error:** `Model 'nomic-embed-text' not found`
    
    **Solution:**
    
    ```bash
    # Pull the model
    ollama pull nomic-embed-text
    
    # Verify it's available
    ollama list
    ```

---

<div align="center">

**[← Installation Guide](installation.md)** | **[Index Documents →](indexing-documents.md)**

*Last updated: 2026-01-05*

</div>

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

## Need Help?

- **Documentation:** [Home](../index.md)
- **Issues:** [GitHub Issues](https://github.com/gmottola00/Tender-RAG-Lab/issues)
- **Discussions:** [GitHub Discussions](https://github.com/gmottola00/Tender-RAG-Lab/discussions)
