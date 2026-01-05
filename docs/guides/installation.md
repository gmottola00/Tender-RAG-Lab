# Installation Guide

This guide covers the complete installation and setup process for Tender-RAG-Lab.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12+** (Python 3.14 not supported due to spaCy compatibility)
- **uv** (modern Python package manager)
- **Docker & Docker Compose** (for Milvus, Neo4j, PostgreSQL)
- **Git**

## Quick Installation

### 1. Clone Repository

```bash
git clone https://github.com/gmottola00/Tender-RAG-Lab.git
cd Tender-RAG-Lab
```

### 2. Install Dependencies

```bash
# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### 3. Install spaCy Models

!!! warning "Python 3.12 Required"
    spaCy requires Python 3.12 or lower. Python 3.14+ is not yet supported.

=== "Option A: Download Manually"

    If you have SSL/proxy issues, download the model manually:
    
    1. Download from browser: [it_core_news_lg-3.8.0](https://github.com/explosion/spacy-models/releases/download/it_core_news_lg-3.8.0/it_core_news_lg-3.8.0-py3-none-any.whl)
    2. Install locally:
    ```bash
    uv run pip install ~/Downloads/it_core_news_lg-3.8.0-py3-none-any.whl
    ```

=== "Option B: Command Line"

    ```bash
    # Install spaCy
    uv pip install spacy
    
    # Download Italian model (large - best accuracy)
    uv run python -m spacy download it_core_news_lg
    
    # Or smaller model for testing
    uv run python -m spacy download it_core_news_sm
    ```

See [INSTALL_SPACY.md](../INSTALL_SPACY.md) for troubleshooting.

### 4. Configure Environment

Create `.env` file from template:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/tender_rag
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_supabase_key

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=tender_chunks

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_LLM_MODEL=llama3
```

### 5. Start Infrastructure Services

```bash
# Start Milvus, Neo4j, PostgreSQL
docker-compose up -d

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
