# Installation Guide

!!! abstract "Overview"
    Complete installation and setup process for **Tender-RAG-Lab**.
    
    Follow these steps to get your RAG system up and running in ~15 minutes.

---

## :material-check-circle: Prerequisites

!!! info "Before You Begin"
    Ensure you have the following installed on your system:

<div class="grid cards" markdown>

-   :material-language-python:{ .lg } **Python 3.12+**

    ---

    Python 3.14+ not supported due to spaCy compatibility
    
    ```bash
    python --version  # Should be 3.12.x or 3.13.x
    ```

-   :material-package:{ .lg } **uv Package Manager**

    ---

    Modern, fast Python package manager
    
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

-   :material-docker:{ .lg } **Docker & Compose**

    ---

    For Milvus, Neo4j, PostgreSQL services
    
    ```bash
    docker --version
    docker-compose --version
    ```

-   :material-git:{ .lg } **Git**

    ---

    Version control system
    
    ```bash
    git --version
    ```

</div>

---

## :material-rocket-launch: Quick Installation

### :material-download: 1. Clone Repository

```bash title="Clone and enter directory"
git clone https://github.com/gmottola00/Tender-RAG-Lab.git
cd Tender-RAG-Lab
```

!!! success "Repository Cloned"
    You should now be in the `Tender-RAG-Lab` directory.

---

### :material-package-down: 2. Install Dependencies

=== "uv (Recommended)"

    ```bash title="Install with uv"
    # Create venv and install all dependencies
    uv sync
    
    # Verify installation
    uv pip list | grep rag-toolkit
    ```
    
    !!! tip "Why uv?"
        - ⚡ **10-100x faster** than pip
        - 🔒 **Deterministic** installs
        - 📦 **Automatic venv** management

=== "pip (Alternative)"

    ```bash title="Install with pip"
    # Create virtual environment
    python -m venv .venv
    source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
    
    # Install dependencies
    pip install -e .
    ```

---

### :material-brain: 3. Install spaCy Models

!!! warning "Python Version Requirement"
    **spaCy requires Python 3.12 or lower.** Python 3.14+ is not yet supported due to Pydantic v1 compatibility.

=== "🌐 Option A: Download Manually"

    **Use this if you have SSL/proxy issues (e.g., TIM network)**
    
    1. **Download from browser:**
       
       [:material-download: it_core_news_lg-3.8.0 (550MB)](https://github.com/explosion/spacy-models/releases/download/it_core_news_lg-3.8.0/it_core_news_lg-3.8.0-py3-none-any.whl)
    
    2. **Install locally:**
       
       ```bash
       uv run pip install ~/Downloads/it_core_news_lg-3.8.0-py3-none-any.whl
       ```
    
    !!! success "Manual Installation"
        This bypasses SSL certificate issues common on corporate networks.

=== "💻 Option B: Command Line"

    ```bash title="Automatic download"
    # Install spaCy
    uv pip install spacy
    
    # Download Italian model (large - best accuracy)
    uv run python -m spacy download it_core_news_lg
    
    # Or smaller model for testing (faster)
    uv run python -m spacy download it_core_news_sm
    ```
    
    !!! tip "Model Sizes"
        - `it_core_news_sm` (13MB) - Fast, good for testing
        - `it_core_news_lg` (550MB) - Best accuracy, production use

=== "🔧 Troubleshooting"

    **Common Issues:**
    
    ```bash
    # SSL Certificate Error
    # → Use Option A (manual download)
    
    # Python version too new
    python --version  # Check version
    pyenv install 3.12.7  # Install 3.12
    pyenv local 3.12.7  # Switch version
    ```
    
    📖 **Full troubleshooting guide:** [INSTALL_SPACY.md](../INSTALL_SPACY.md)

---

### :material-cog: 4. Configure Environment

---

### :material-cog: 4. Configure Environment

!!! tip "Environment Variables"
    Create `.env` file from template:

```bash title="Copy template"
cp .env.example .env
```

**Edit `.env` with your configuration:**

=== "🗄️ Database"

    ```bash title=".env - Database section"
    # PostgreSQL
    DATABASE_URL=postgresql://user:pass@localhost:5432/tender_rag
    
    # Supabase (optional - for storage)
    SUPABASE_URL=https://xxx.supabase.co
    SUPABASE_KEY=your_supabase_anon_key
    ```

=== "🔍 Milvus (Vector DB)"

    ```bash title=".env - Milvus section"
    MILVUS_HOST=localhost
    MILVUS_PORT=19530
    MILVUS_COLLECTION=tender_chunks
    MILVUS_USER=root
    MILVUS_PASSWORD=Milvus
    ```

=== "🕸️ Neo4j (Knowledge Graph)"

    ```bash title=".env - Neo4j section"
    NEO4J_URI=bolt://localhost:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=your_secure_password
    NEO4J_DATABASE=neo4j
    ```

=== "🤖 Ollama (LLM & Embeddings)"

    ```bash title=".env - Ollama section"
    OLLAMA_HOST=http://localhost:11434
    OLLAMA_EMBEDDING_MODEL=nomic-embed-text
    OLLAMA_LLM_MODEL=llama3
    ```

---

### :material-docker: 5. Start Infrastructure Services

!!! info "Docker Services"
    Start Milvus, Neo4j, and PostgreSQL with Docker Compose:

```bash title="Start all services"
# Start in detached mode
docker-compose up -d

# Check status
docker-compose ps
```

**Expected output:**

```text
NAME                SERVICE    STATUS         PORTS
milvus-etcd         etcd       Up            2379/tcp
milvus-minio        minio      Up            9000-9001/tcp
milvus-standalone   milvus     Up            0.0.0.0:19530->19530/tcp
neo4j               neo4j      Up            7474/tcp, 7687/tcp
postgres            postgres   Up            5432/tcp
```

!!! success "Services Running"
    All infrastructure services are now running and ready.

---

### :material-play: 6. Run the Application

=== "🌐 FastAPI Server"

    ```bash title="Start API server"
    uv run python main.py
    
    # Or use make command
    make api
    ```
    
    **Access the API:**
    
    - 🌐 **Swagger UI:** http://localhost:8000/docs
    - 📖 **ReDoc:** http://localhost:8000/redoc
    - 🏠 **Homepage:** http://localhost:8000/

=== "📊 Milvus Explorer"

    ```bash title="Access Milvus Admin UI"
    # Navigate to Milvus Explorer
    open http://localhost:8000/milvus
    ```
    
    **Features:**
    - View collections
    - Search vectors
    - Inspect chunks

=== "🕸️ Neo4j Browser"

    ```bash title="Access Neo4j Browser"
    open http://localhost:7474
    ```
    
    **Credentials:**
    - Username: `neo4j`
    - Password: (from your `.env` file)

---

## :material-checkbox-marked-circle: Verify Installation

!!! example "Run Health Checks"
    Verify all components are working:

```python title="Python health check"
from src.infra.factory import create_tender_stack
from quaerum.infra.embedding import OllamaEmbeddingClient

# Test embedding client
embed_client = OllamaEmbeddingClient()
vector = embed_client.embed("test")
print(f"✅ Embedding dimension: {len(vector)}")

# Test Milvus connection
indexer, searcher = create_tender_stack(embed_client, len(vector))
print("✅ Milvus connection successful")
```

---

## :material-wrench: Common Issues

!!! failure "Issue: Milvus Connection Failed"
    
    **Error:** `Cannot connect to Milvus at localhost:19530`
    
    **Solution:**
    ```bash
    # Check if Milvus is running
    docker-compose ps milvus-standalone
    
    # Restart if needed
    docker-compose restart milvus-standalone
    
    # Check logs
    docker-compose logs milvus-standalone
    ```

!!! failure "Issue: spaCy Model Not Found"
    
    **Error:** `OSError: [E050] Can't find model 'it_core_news_lg'`
    
    **Solution:**
    ```bash
    # Re-download model
    uv run python -m spacy download it_core_news_lg
    
    # Verify installation
    uv run python -m spacy validate
    ```

!!! failure "Issue: Port Already in Use"
    
    **Error:** `Bind for 0.0.0.0:8000 failed: port is already allocated`
    
    **Solution:**
    ```bash
    # Find process using port
    lsof -i :8000
    
    # Kill process
    kill -9 <PID>
    
    # Or use different port
    uvicorn main:app --port 8001
    ```

---

## :material-update: Update Installation

!!! tip "Keep Dependencies Updated"
    
    ```bash
    # Update dependencies
    uv sync --upgrade
    
    # Update spaCy models
    uv run python -m spacy download it_core_news_lg --upgrade
    
    # Pull latest Docker images
    docker-compose pull
    docker-compose up -d
    ```

---

## :material-trash-can: Uninstall

!!! danger "Complete Uninstallation"
    
    ```bash
    # Stop and remove containers
    docker-compose down -v
    
    # Remove virtual environment
    rm -rf .venv
    
    # Remove installed packages (optional)
    uv cache clean
    ```

---

## :material-arrow-right: Next Steps

<div class="grid cards" markdown>

-   :material-rocket:{ .lg } **Quick Start**

    ---

    Follow the quickstart guide to index your first document
    
    [:octicons-arrow-right-24: Quickstart Guide](quickstart.md)

-   :material-cog:{ .lg } **Environment Setup**

    ---

    Detailed configuration options and best practices
    
    [:octicons-arrow-right-24: Environment Setup](environment-setup.md)

-   :material-file-document:{ .lg } **Indexing Documents**

    ---

    Learn how to upload and process tender documents
    
    [:octicons-arrow-right-24: Indexing Guide](indexing-documents.md)

-   :material-lifebuoy:{ .lg } **Troubleshooting**

    ---

    Common issues and solutions
    
    [:octicons-arrow-right-24: spaCy Installation](../INSTALL_SPACY.md)

</div>

---

<div align="center">

**[← Back to Home](../index.md)** | **[Quickstart Guide →](quickstart.md)**

*Last updated: 2026-01-05*

</div>

# Verify services are running
docker-compose ps
```

### 6. Run Application

```bash
# Start FastAPI server
make api

# Or manually
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Visit: [http://localhost:8000/docs](http://localhost:8000/docs)

## Verify Installation

Test that everything works:

```bash
# Run tests
pytest tests/

# Test NER
uv run python tests/test_ner.py

# Test ingestion pipeline
uv run python -m src.domain.tender.services.documents
```

## Development Setup

### Install Dev Dependencies

```bash
uv sync --group dev
```

This installs:
- pytest (testing)
- pytest-asyncio (async tests)
- pytest-cov (coverage)
- sphinx (documentation)
- mypy (type checking)

### IDE Setup

#### VS Code

Install recommended extensions:
- Python
- Pylance
- Docker
- REST Client

`.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true
}
```

#### PyCharm

1. File → Settings → Project → Python Interpreter
2. Select `.venv/bin/python`
3. Enable pytest as test runner

## Troubleshooting

### spaCy Model Download Fails

See [INSTALL_SPACY.md](../INSTALL_SPACY.md) for SSL/proxy workarounds.

### Docker Services Won't Start

```bash
# Check logs
docker-compose logs

# Restart services
docker-compose down
docker-compose up -d
```

### Database Connection Errors

Verify PostgreSQL is running:
```bash
docker-compose ps postgres
docker-compose logs postgres
```

### Milvus Connection Timeout

Check Milvus health:
```bash
curl http://localhost:9091/healthz
```

## Next Steps

- [Quick Start Guide](quickstart.md) - Your first RAG query
- [Environment Setup](environment-setup.md) - Advanced configuration
- [Document Ingestion](indexing-documents.md) - Index tender documents
