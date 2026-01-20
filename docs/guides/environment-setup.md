# Environment Setup

!!! abstract "Complete Configuration Reference"
    All environment variables for **Tender-RAG-Lab**, organized by service category.
    
    From minimal setup to production-ready configuration.

---

## :material-flash: Quick Reference

!!! tip "What You Need"

=== "🚀 Basic RAG (Minimal)"

    **Required:**
    ```bash
    MILVUS_URI=http://localhost:19530
    OLLAMA_URL=http://localhost:11434
    OLLAMA_EMBED_MODEL=nomic-embed-text
    ```

=== "💼 Tender Management (Full)"

    **Additional:**
    ```bash
    DATABASE_URL=postgresql://user:pass@localhost:5432/tender_db
    SUPABASE_URL=https://xxx.supabase.co
    SUPABASE_KEY=your_key
    ```

=== "🌐 Production (All Services)"

    **Complete:**
    - Milvus (vector DB)
    - Database (PostgreSQL)
    - Storage (Supabase/S3)
    - Neo4j (knowledge graph)
    - LLM provider (Ollama/OpenAI)

---

## :material-file-cog: Environment File

!!! info "Create Configuration"

```bash title="Setup .env file"
# Copy from template
cp .env.example .env

# Edit with your values
nano .env  # or use your favorite editor
```

---

## :material-database-search: Milvus Configuration

!!! abstract "Vector Database Settings"
    Core configuration for semantic search with Milvus.

### Core Settings

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `MILVUS_URI` | ✅ | `http://localhost:19530` | Milvus server URL |
| `MILVUS_USER` | ⚪ | `root` | Authentication username |
| `MILVUS_PASSWORD` | ⚪ | `Milvus` | Authentication password |
| `MILVUS_DB` | ⚪ | `default` | Database name |
| `MILVUS_COLLECTION` | ⚪ | `tender_chunks` | Collection for vectors |

### Index Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MILVUS_INDEX_TYPE` | `HNSW` | Index algorithm (HNSW, IVF_FLAT, DISK_ANN) |
| `MILVUS_METRIC_TYPE` | `IP` | Similarity metric (IP, L2, COSINE) |
| `MILVUS_INDEX_PARAMS_M` | `24` | HNSW M (connections per node) |
| `MILVUS_INDEX_PARAMS_EF` | `200` | HNSW efConstruction (build quality) |

=== "📝 Example"

    ```bash title=".env - Milvus section"
    MILVUS_URI=http://localhost:19530
    MILVUS_USER=root
    MILVUS_PASSWORD=Milvus
    MILVUS_DB=default
    MILVUS_COLLECTION=tender_chunks
    
    # Advanced settings
    MILVUS_INDEX_TYPE=HNSW
    MILVUS_METRIC_TYPE=IP
    ```

=== "⚙️ Tuning Tips"

    !!! tip "Performance Optimization"
        - **HNSW** - Best for most use cases (fast + accurate)
        - **IVF_FLAT** - Exact search (slower, perfect recall)
        - **DISK_ANN** - Large datasets (>10M vectors)
    
    !!! info "Metric Types"
        - **IP** (Inner Product) - For normalized vectors
        - **L2** - Euclidean distance
        - **COSINE** - Cosine similarity

---

## :material-robot: Ollama Configuration

!!! abstract "Local LLM Provider"
    Run embeddings and language models locally with Ollama.

### Settings

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `OLLAMA_URL` | ✅* | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_EMBED_MODEL` | ✅* | `nomic-embed-text` | Embedding model |
| `OLLAMA_LLM_MODEL` | ✅* | `llama3.2` | Language model |

<small>*Required if using Ollama (not OpenAI)</small>

### Recommended Models

=== "🎯 Embedding Models"

    | Model | Size | Dim | Best For |
    |-------|------|-----|----------|
    | `nomic-embed-text` | 274MB | 768 | **General use** ⭐ |
    | `mxbai-embed-large` | 670MB | 1024 | High quality |
    | `all-minilm` | 45MB | 384 | Fast, testing |

=== "🤖 LLM Models"

    | Model | Params | Size | Best For |
    |-------|--------|------|----------|
    | `llama3.2` | 3B | 2GB | **Fast inference** ⭐ |
    | `llama3.1` | 8B | 4.7GB | Better quality |
    | `qwen2.5` | 7B | 4.4GB | Multi-lingual |
    | `mistral` | 7B | 4.1GB | Reasoning tasks |

=== "📝 Example"

    ```bash title=".env - Ollama section"
    OLLAMA_URL=http://localhost:11434
    OLLAMA_EMBED_MODEL=nomic-embed-text
    OLLAMA_LLM_MODEL=llama3.2
    ```
    
    ```bash title="Pull models"
    ollama pull nomic-embed-text
    ollama pull llama3.2
    ```

!!! tip "Model Selection"
    [:material-book: Ollama Library](https://ollama.ai/library) - Browse all available models

---

## :material-key: OpenAI Configuration

!!! abstract "Cloud AI Provider"
    Use OpenAI's managed models for production workloads.

### Settings

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `OPENAI_API_KEY` | ✅* | - | Your OpenAI API key |
| `OPENAI_EMBED_MODEL` | ⚪ | `text-embedding-3-small` | Embedding model |
| `OPENAI_LLM_MODEL` | ⚪ | `gpt-4o-mini` | Language model |

<small>*Required if using OpenAI (not Ollama)</small>

### Recommended Models

=== "🎯 Embedding Models"

    | Model | Dims | Best For |
    |-------|------|----------|
    | `text-embedding-3-small` | 1536 | **Cost-effective** ⭐ |
    | `text-embedding-3-large` | 3072 | High quality |
    | `text-embedding-ada-002` | 1536 | Legacy (stable) |

=== "🤖 LLM Models"

    | Model | Context | Best For |
    |-------|---------|----------|
    | `gpt-4o-mini` | 128K | **Fast + cheap** ⭐ |
    | `gpt-4o` | 128K | Highest quality |
    | `gpt-4-turbo` | 128K | Good balance |
    | `gpt-3.5-turbo` | 16K | Budget option |

=== "📝 Example"

    ```bash title=".env - OpenAI section"
    OPENAI_API_KEY=sk-proj-abc...xyz
    OPENAI_EMBED_MODEL=text-embedding-3-small
    OPENAI_LLM_MODEL=gpt-4o-mini
    ```

!!! warning "API Key Security"
    Never commit `.env` to version control! Add to `.gitignore`.

---

## :material-database: Database Configuration

!!! abstract "PostgreSQL Setup"
    Required for tender management features (CRUD operations, metadata storage).

### Settings

| Variable | Required | Description |
|----------|:--------:|-------------|
| `DATABASE_URL` | ✅* | Async PostgreSQL connection string |

<small>*Required for tender management features</small>

### Connection String Format

```bash title="Format"
postgresql+asyncpg://user:password@host:port/database
```

!!! warning "Driver Requirement"
    Must use `asyncpg` driver for async SQLAlchemy operations.

=== "🖥️ Local PostgreSQL"

    ```bash title=".env - Local database"
    DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/tender_db
    ```

=== "☁️ Supabase"

    ```bash title=".env - Supabase database"
    DATABASE_URL=postgresql+asyncpg://postgres.xxx:SecurePass@aws-0-region.pooler.supabase.com:5432/postgres
    ```
    
    !!! tip "Find Connection String"
        Supabase Dashboard → Project Settings → Database → Connection string (Async)

=== "🐳 Docker Compose"

    ```bash title=".env - Docker database"
    DATABASE_URL=postgresql+asyncpg://tender_user:tender_pass@postgres:5432/tender_db
    ```

---

## :material-cloud-upload: Supabase Storage

!!! abstract "File Storage (Optional)"
    Store uploaded tender documents in Supabase cloud storage.

### Settings

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `SUPABASE_URL` | ⚪ | - | Project URL |
| `SUPABASE_KEY` | ⚪ | - | Anon/service key |
| `SUPABASE_BUCKET` | ⚪ | `documents` | Storage bucket |

=== "📝 Example"

    ```bash title=".env - Supabase storage"
    SUPABASE_URL=https://xxx.supabase.co
    SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    SUPABASE_BUCKET=tender-documents
    ```

=== "⚙️ Setup Steps"

    1. **Create Bucket**:
       - Supabase Dashboard → Storage → New bucket
       - Name: `tender-documents`
       - Public/Private: Choose based on needs
    
    2. **Get Credentials**:
       - Project Settings → API → URL + anon key
    
    3. **Configure Policies** (if private):
       ```sql
       CREATE POLICY "Allow uploads" 
       ON storage.objects FOR INSERT 
       WITH CHECK (bucket_id = 'tender-documents');
       ```

!!! tip "Alternative Storage"
    Can also use local filesystem or S3-compatible storage.

---

## :material-math-log: Logging Configuration

!!! abstract "Application Logging"
    Control log output format and verbosity.

### Settings

| Variable | Default | Options | Description |
|----------|---------|---------|-------------|
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | Verbosity level |
| `LOG_FORMAT` | `json` | `json`, `text` | Output format |

=== "🔧 Development"

    ```bash title=".env - Dev logging"
    LOG_LEVEL=DEBUG
    LOG_FORMAT=text
    ```
    
    !!! tip "Readable Output"
        Use `text` format for local development (easier to read).

=== "🚀 Production"

    ```bash title=".env - Prod logging"
    LOG_LEVEL=INFO
    LOG_FORMAT=json
    ```
    
    !!! info "Structured Logs"
        Use `json` format for log aggregation (Datadog, CloudWatch, etc).

!!! note "Log Configuration"
    See `configs/logger.py` for full logging setup.

---

## :material-cog: Application Settings

!!! abstract "General App Configuration"
    Environment-specific settings for the FastAPI application.

### Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Deployment environment |
| `DEBUG` | `True` | Enable debug mode |
| `API_PREFIX` | `/api` | API route prefix |
| `CORS_ORIGINS` | `*` | Allowed origins (comma-separated) |

=== "🖥️ Development"

    ```bash title=".env - Development"
    ENVIRONMENT=development
    DEBUG=True
    API_PREFIX=/api
    CORS_ORIGINS=*
    ```

=== "🚀 Production"

    ```bash title=".env - Production"
    ENVIRONMENT=production
    DEBUG=False
    API_PREFIX=/api
    CORS_ORIGINS=https://app.example.com,https://admin.example.com
    ```
    
    !!! danger "Security"
        - Set `DEBUG=False` in production
        - Restrict `CORS_ORIGINS` to specific domains
        - Use HTTPS endpoints only

---

## :material-file-check: Complete Examples

!!! example "Ready-to-Use Configurations"

=== "🖥️ Local Development"

    ```bash title=".env - Full local setup"
    # ============================================
    # TENDER-RAG-LAB - DEVELOPMENT CONFIG
    # ============================================
    
    # Vector Database
    MILVUS_URI=http://localhost:19530
    MILVUS_USER=root
    MILVUS_PASSWORD=Milvus
    MILVUS_DB=default
    MILVUS_COLLECTION=tender_chunks
    
    # LLM Provider (local)
    OLLAMA_URL=http://localhost:11434
    OLLAMA_EMBED_MODEL=nomic-embed-text
    OLLAMA_LLM_MODEL=llama3.2
    
    # Database (optional)
    DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/tender_db
    
    # Logging
    LOG_LEVEL=DEBUG
    LOG_FORMAT=text
    
    # Application
    ENVIRONMENT=development
    DEBUG=True
    API_PREFIX=/api
    CORS_ORIGINS=*
    ```

=== "☁️ Cloud Production"

    ```bash title=".env - Full production setup"
    # ============================================
    # TENDER-RAG-LAB - PRODUCTION CONFIG
    # ============================================
    
    # Vector Database (managed Milvus)
    MILVUS_URI=https://milvus.example.com:19530
    MILVUS_USER=admin
    MILVUS_PASSWORD=SecurePassword123
    MILVUS_DB=production
    MILVUS_COLLECTION=tender_chunks
    MILVUS_INDEX_TYPE=HNSW
    MILVUS_METRIC_TYPE=IP
    
    # LLM Provider (OpenAI)
    OPENAI_API_KEY=sk-proj-abc...xyz
    OPENAI_EMBED_MODEL=text-embedding-3-small
    OPENAI_LLM_MODEL=gpt-4o-mini
    
    # Database (Supabase PostgreSQL)
    DATABASE_URL=postgresql+asyncpg://postgres.xxx:SecurePass@aws-0-us-west.pooler.supabase.com:5432/postgres
    
    # File Storage (Supabase)
    SUPABASE_URL=https://xxx.supabase.co
    SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    SUPABASE_BUCKET=tender-documents
    
    # Logging
    LOG_LEVEL=INFO
    LOG_FORMAT=json
    
    # Application
    ENVIRONMENT=production
    DEBUG=False
    API_PREFIX=/api
    CORS_ORIGINS=https://app.example.com,https://admin.example.com
    ```

=== "🐳 Docker Compose"

    ```bash title=".env - Docker setup"
    # ============================================
    # TENDER-RAG-LAB - DOCKER COMPOSE
    # ============================================
    
    # Vector Database (Docker service)
    MILVUS_URI=http://milvus:19530
    MILVUS_USER=root
    MILVUS_PASSWORD=Milvus
    MILVUS_DB=default
    MILVUS_COLLECTION=tender_chunks
    
    # LLM Provider (host Ollama)
    OLLAMA_URL=http://host.docker.internal:11434
    OLLAMA_EMBED_MODEL=nomic-embed-text
    OLLAMA_LLM_MODEL=llama3.2
    
    # Database (Docker service)
    DATABASE_URL=postgresql+asyncpg://tender_user:tender_pass@postgres:5432/tender_db
    
    # Logging
    LOG_LEVEL=INFO
    LOG_FORMAT=json
    
    # Application
    ENVIRONMENT=development
    DEBUG=True
    ```

---

## :material-help-circle: Troubleshooting

??? failure "Connection Refused Errors"

    **Problem**: `Connection refused` to Milvus/Ollama/Database
    
    **Solutions**:
    
    1. **Check service is running**:
       ```bash
       # Milvus
       docker ps | grep milvus
       
       # Ollama
       ollama list
       
       # PostgreSQL
       psql -h localhost -U postgres -l
       ```
    
    2. **Verify ports**:
       ```bash
       # Check if ports are open
       nc -zv localhost 19530  # Milvus
       nc -zv localhost 11434  # Ollama
       nc -zv localhost 5432   # PostgreSQL
       ```
    
    3. **Check firewall**: Allow ports in firewall settings

??? failure "Authentication Failed"

    **Problem**: `Authentication failed` errors
    
    **Solutions**:
    
    1. **Verify credentials** in `.env`
    2. **Reset Milvus password**:
       ```bash
       docker exec -it milvus bash
       # Update user credentials
       ```
    3. **Regenerate API keys** (OpenAI, Supabase)

??? failure "Model Not Found"

    **Problem**: `Model 'xxx' not found` in Ollama
    
    **Solution**:
    ```bash
    # Pull missing models
    ollama pull nomic-embed-text
    ollama pull llama3.2
    
    # List available models
    ollama list
    ```

??? warning "Environment Variables Not Loaded"

    **Problem**: Variables not being read
    
    **Solutions**:
    
    1. **Verify `.env` location** (project root)
    2. **Check syntax** (no spaces around `=`)
    3. **Restart application** after changes
    4. **Load manually**:
       ```bash
       export $(cat .env | xargs)
       ```

---

## :material-arrow-right-circle: Next Steps

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg } **[Quickstart Guide](quickstart.md)**

    ---
    
    Get your first RAG pipeline running in 5 minutes

-   :material-file-document-multiple:{ .lg } **[Index Documents](indexing-documents.md)**

    ---
    
    Learn document processing and indexing

-   :material-magnify:{ .lg } **[Search & Retrieval](search-retrieval.md)**

    ---
    
    Master vector, keyword, and hybrid search

</div>

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
- [Indexing Documents](indexing-documents.md) - Document processing
