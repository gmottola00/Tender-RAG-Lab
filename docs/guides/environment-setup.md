# Environment Setup

> **Complete environment variable reference and configuration guide**

This guide covers all environment variables used by Tender-RAG-Lab, organized by category.

---

## 📋 Quick Reference

**Required for basic RAG:**
- `MILVUS_URI`
- `OLLAMA_URL` + `OLLAMA_EMBED_MODEL` OR `OPENAI_API_KEY` + `OPENAI_EMBED_MODEL`

**Required for Tender management:**
- `DATABASE_URL`
- `SUPABASE_URL` + `SUPABASE_KEY` (for file storage)

---

## 🗂️ Environment File Structure

Create `.env` in project root:

```bash
# Copy from example
cp .env.example .env
```

---

## 🔵 Milvus Configuration

Vector database for RAG retrieval.

### Core Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MILVUS_URI` | ✅ Yes | `http://localhost:19530` | Milvus server URL |
| `MILVUS_USER` | No | `root` | Milvus username |
| `MILVUS_PASSWORD` | No | `Milvus` | Milvus password |
| `MILVUS_DB` | No | `default` | Database name |
| `MILVUS_COLLECTION` | No | `tender_chunks` | Collection name |

### Index Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MILVUS_INDEX_TYPE` | `HNSW` | Index type (HNSW, IVF_FLAT, DISK_ANN) |
| `MILVUS_METRIC_TYPE` | `IP` | Similarity metric (IP, L2, COSINE) |
| `MILVUS_INDEX_PARAMS_M` | `24` | HNSW M parameter (connections per node) |
| `MILVUS_INDEX_PARAMS_EF` | `200` | HNSW efConstruction (build quality) |

**Example:**
```bash
MILVUS_URI=http://localhost:19530
MILVUS_USER=root
MILVUS_PASSWORD=Milvus
MILVUS_DB=default
MILVUS_COLLECTION=tender_chunks
MILVUS_INDEX_TYPE=HNSW
MILVUS_METRIC_TYPE=IP
```

**See:** [Milvus Setup Guide](../infra/milvus.md) for index tuning.

---

## 🤖 Ollama Configuration (Local)

Local LLM and embedding models via Ollama.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OLLAMA_URL` | If using Ollama | `http://localhost:11434` | Ollama API URL |
| `OLLAMA_EMBED_MODEL` | If using Ollama | `nomic-embed-text` | Embedding model name |
| `OLLAMA_LLM_MODEL` | If using Ollama | `llama3.2` | LLM model name |

**Recommended Models:**

Embedding:
- `nomic-embed-text` - Fast, good quality
- `mxbai-embed-large` - Higher quality, slower

LLM:
- `llama3.2` - Fast, 3B params
- `llama3.1` - Higher quality, 8B params
- `qwen2.5` - Excellent for non-English

**Example:**
```bash
OLLAMA_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_LLM_MODEL=llama3.2
```

**See:** [Ollama Documentation](https://ollama.ai/library) for model list.

---

## 🔑 OpenAI Configuration (Cloud)

Cloud-based OpenAI models.

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | If using OpenAI | Your OpenAI API key |
| `OPENAI_EMBED_MODEL` | If using OpenAI | Embedding model (default: `text-embedding-3-small`) |
| `OPENAI_LLM_MODEL` | If using OpenAI | LLM model (default: `gpt-4o-mini`) |

**Recommended Models:**

Embedding:
- `text-embedding-3-small` - Cost-effective, 1536 dims
- `text-embedding-3-large` - Higher quality, 3072 dims

LLM:
- `gpt-4o-mini` - Fast, cost-effective
- `gpt-4o` - Highest quality
- `gpt-4-turbo` - Good balance

**Example:**
```bash
OPENAI_API_KEY=sk-proj-abc...xyz
OPENAI_EMBED_MODEL=text-embedding-3-small
OPENAI_LLM_MODEL=gpt-4o-mini
```

---

## Database Configuration

PostgreSQL database for tender management.

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | For Tender CRUD | Async PostgreSQL connection string |

**Format:**
```bash
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
```

**Examples:**

Local PostgreSQL:
```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/tender_db
```

Supabase:
```bash
DATABASE_URL=postgresql+asyncpg://postgres.xxx:password@aws-0-region.pooler.supabase.com:5432/postgres
```

**Note:** Must use `asyncpg` driver for async SQLAlchemy.

---

## ☁️ Supabase Configuration (Optional)

File storage for uploaded documents.

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | For file storage | Supabase project URL |
| `SUPABASE_KEY` | For file storage | Supabase anon/service key |
| `SUPABASE_BUCKET` | No | Storage bucket name (default: `documents`) |

**Example:**
```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_BUCKET=documents
```

**Setup:** Create bucket in Supabase Dashboard → Storage.

---

## 📝 Logging Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FORMAT` | `json` | Log format (json, text) |

**Example:**
```bash
LOG_LEVEL=DEBUG
LOG_FORMAT=json
```

**See:** `configs/logger.py` for logging setup.

---

## 🔧 Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Environment (development, staging, production) |
| `DEBUG` | `True` | Debug mode (disable in production) |
| `API_PREFIX` | `/api` | API route prefix |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated) |

**Example (Production):**
```bash
ENVIRONMENT=production
DEBUG=False
API_PREFIX=/api
CORS_ORIGINS=https://app.example.com,https://admin.example.com
```

---

## 📊 Complete Example Configurations

### Development (Local)

```bash
# Milvus
MILVUS_URI=http://localhost:19530
MILVUS_USER=root
MILVUS_PASSWORD=Milvus
MILVUS_DB=default
MILVUS_COLLECTION=tender_chunks

# Ollama (local models)
OLLAMA_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_LLM_MODEL=llama3.2

# Database (optional)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/tender_db

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=text

# App
ENVIRONMENT=development
DEBUG=True
```

### Production (Cloud)

```bash
# Milvus (managed)
MILVUS_URI=https://milvus.example.com:19530
MILVUS_USER=admin
MILVUS_PASSWORD=SecurePassword123
MILVUS_DB=production
MILVUS_COLLECTION=tender_chunks

# OpenAI (cloud models)
OPENAI_API_KEY=sk-proj-...
OPENAI_EMBED_MODEL=text-embedding-3-small
OPENAI_LLM_MODEL=gpt-4o-mini

# Database (Supabase)
DATABASE_URL=postgresql+asyncpg://postgres.xxx:SecurePass@aws-0-us-west.pooler.supabase.com:5432/postgres

# Supabase Storage
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_BUCKET=tender-documents

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# App
ENVIRONMENT=production
DEBUG=False
API_PREFIX=/api
CORS_ORIGINS=https://app.example.com
```

---

## 🔐 Security Best Practices

### Never Commit `.env`

Add to `.gitignore`:
```
.env
.env.local
.env.production
```

### Use Environment-Specific Files

```bash
.env.development
.env.staging
.env.production
```

Load based on `ENVIRONMENT` variable.

### Rotate Secrets Regularly

- Change `MILVUS_PASSWORD` every 90 days
- Rotate `OPENAI_API_KEY` if compromised
- Update `SUPABASE_KEY` periodically

### Use Secret Management (Production)

Instead of `.env` files:
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- Kubernetes Secrets

---

## Related Documentation

- [Quick Start Guide](quickstart.md) - Get started quickly
- [Local Development](local-development.md) - Development workflow
- [Deployment](deployment.md) - Production deployment
- [Milvus Setup](../infra/milvus.md) - Vector database configuration

---

**[⬅️ Quick Start](quickstart.md) | [⬆️ Documentation Home](../README.md) | [Local Dev ➡️](local-development.md)**

*Last updated: 2025-12-18*
