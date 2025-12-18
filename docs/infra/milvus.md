# 🔌 Infrastructure: Milvus Vector Database

> **Complete setup, configuration, and optimization guide for Milvus**

Milvus is the vector database powering semantic search in Tender-RAG-Lab.

---

## 📍 What is Milvus?

**Milvus** is an open-source vector database optimized for:
- ✅ Billion-scale vector similarity search
- ✅ Hybrid search (vector + keyword)
- ✅ Metadata filtering
- ✅ Multiple index types (HNSW, IVF_FLAT, DiskANN)
- ✅ Horizontal scaling

**Why Milvus over alternatives?**

| Feature | Milvus | Pinecone | Weaviate | Qdrant |
|---------|--------|----------|----------|--------|
| **Cost** | 🆓 Free | 💰 Paid | 🆓 Free | 🆓 Free |
| **Hybrid Search** | ✅ Built-in | ❌ No | ✅ Yes | ⚠️ Limited |
| **Scale** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Self-Hosted** | ✅ Yes | ❌ Cloud-only | ✅ Yes | ✅ Yes |
| **Italian Support** | ✅ BM25 | ❌ | ✅ | ⚠️ |

**See:** [ADR: Why Milvus](../architecture/decisions.md#adr-004-why-milvus)

---

## 🚀 Setup

### Local Development (Docker)

**1. Start Milvus:**

```bash
# Uses docker-compose.yml in project root
docker-compose up -d
```

**Services started:**
- `milvus-standalone` - Vector database (port 19530)
- `etcd` - Metadata store
- `minio` - Object storage for vectors

**2. Verify:**

```bash
curl http://localhost:19530/healthz
# Expected: OK
```

**3. Check logs:**

```bash
docker-compose logs milvus-standalone
```

---

### Production Deployment

**Option 1: Kubernetes (Recommended)**

```bash
# Install via Helm
helm repo add milvus https://zilliztech.github.io/milvus-helm/
helm install milvus milvus/milvus \
  --set cluster.enabled=true \
  --set persistence.enabled=true
```

**Option 2: Managed Zilliz Cloud**

1. Sign up at https://cloud.zilliz.com
2. Create cluster
3. Get connection URI
4. Update `.env`:
   ```bash
   MILVUS_URI=https://your-cluster.zilliz.com:19530
   MILVUS_USER=your-user
   MILVUS_PASSWORD=your-password
   ```

---

## 🗄️ Collection Schema

### Tender Chunks Collection

**Default collection:** `tender_chunks`

**Schema:**
```python
{
    "id": "auto-generated UUID",
    "text": "chunk content (BM25 searchable)",
    "vector": [768 floats],  # Embedding dimension
    "metadata": {
        "doc_id": "tender-123",
        "page": 5,
        "language": "it",
        "chunk_index": 0,
        "total_chunks": 10,
        "tender_id": "optional-FK",
        "lot_id": "optional-FK"
    }
}
```

### Field Types

| Field | Type | Indexed | Description |
|-------|------|---------|-------------|
| `id` | VARCHAR | PK | Auto-generated UUID |
| `text` | VARCHAR | ✅ BM25 | Full chunk text |
| `vector` | FLOAT_VECTOR | ✅ HNSW | Embedding (768 dims) |
| `metadata` | JSON | ⚠️ Partial | Nested metadata (filterable fields) |

---

## 🔧 Configuration

### Environment Variables

```bash
# .env
MILVUS_URI=http://localhost:19530
MILVUS_USER=root
MILVUS_PASSWORD=Milvus
MILVUS_DB=default
MILVUS_COLLECTION=tender_chunks

# Index configuration
MILVUS_INDEX_TYPE=HNSW
MILVUS_METRIC_TYPE=IP  # Inner Product (cosine similarity)
MILVUS_INDEX_PARAMS_M=24
MILVUS_INDEX_PARAMS_EF=200
```

**See:** [Environment Setup](../guides/environment-setup.md) for all variables.

---

### Index Types

#### HNSW (Recommended)

**Best for:** Most use cases (fast + accurate)

**Parameters:**
- `M` (default: 24) - Connections per node
  - Higher = better quality, slower indexing
  - Range: 8-64
- `efConstruction` (default: 200) - Build quality
  - Higher = better index, slower build
  - Range: 100-500

**Configuration:**
```python
index_params = {
    "index_type": "HNSW",
    "metric_type": "IP",  # Inner Product
    "params": {"M": 24, "efConstruction": 200}
}
```

**Search parameters:**
```python
search_params = {
    "metric_type": "IP",
    "params": {"ef": 100}  # Higher = better recall, slower
}
```

---

#### IVF_FLAT

**Best for:** Smaller datasets (<100K vectors)

**Parameters:**
- `nlist` - Number of clusters
  - Formula: `sqrt(num_vectors)`
  - Example: 10K vectors → nlist=100

**Configuration:**
```python
index_params = {
    "index_type": "IVF_FLAT",
    "metric_type": "IP",
    "params": {"nlist": 100}
}
```

---

#### DiskANN (For Large Scale)

**Best for:** Billion-scale datasets

**Benefits:**
- Low memory footprint
- Handles massive datasets
- SSD-optimized

**Configuration:**
```python
index_params = {
    "index_type": "DISKANN",
    "metric_type": "IP",
    "params": {"search_list": 100}
}
```

---

### Metric Types

| Metric | Description | Use Case | Range |
|--------|-------------|----------|-------|
| `IP` | Inner Product | Normalized embeddings (recommended) | Higher = more similar |
| `COSINE` | Cosine Similarity | Any embeddings | 0-1 (higher = more similar) |
| `L2` | Euclidean Distance | Non-normalized embeddings | Lower = more similar |

**Recommendation:** Use `IP` with normalized embeddings for best performance.

---

## 🔍 Usage Examples

### Create Collection

```python
from src.core.index.vector import get_milvus_service

service = get_milvus_service()

# Create collection with schema
await service.create_collection(
    collection_name="tender_chunks",
    dimension=768,  # Must match embedding model
    index_type="HNSW",
    metric_type="IP"
)
```

---

### Insert Vectors

```python
# Batch insert
await service.insert(
    collection_name="tender_chunks",
    vectors=[[0.1, 0.2, ...], [0.3, 0.4, ...]],  # List of 768-dim vectors
    texts=["chunk 1 text", "chunk 2 text"],
    metadata=[
        {"doc_id": "tender-123", "page": 1},
        {"doc_id": "tender-123", "page": 2}
    ]
)
```

---

### Vector Search

```python
# Semantic search
results = await service.search(
    collection_name="tender_chunks",
    query_vector=[0.5, 0.6, ...],  # 768-dim query vector
    top_k=10,
    filters={"doc_id": "tender-123"}  # Optional metadata filter
)

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Text: {result.text}")
    print(f"Metadata: {result.metadata}")
```

---

### Keyword Search (BM25)

```python
# Full-text search
results = await service.keyword_search(
    collection_name="tender_chunks",
    query_text="CIG 1234567890",
    top_k=10
)
```

---

### Hybrid Search

```python
# Combine vector + keyword (RRF fusion)
results = await service.hybrid_search(
    collection_name="tender_chunks",
    query_vector=[0.5, 0.6, ...],
    query_text="requisiti tecnici CIG 1234567890",
    top_k=10,
    vector_weight=0.6,  # 60% vector, 40% keyword
    keyword_weight=0.4
)
```

---

### Delete by Filter

```python
# Delete all chunks from a tender
deleted_count = await service.delete(
    collection_name="tender_chunks",
    filters={"doc_id": "tender-123"}
)

print(f"Deleted {deleted_count} chunks")
```

---

## 📊 Performance Tuning

### Indexing Performance

**Slow indexing? Adjust parameters:**

```python
# Faster indexing (lower quality)
index_params = {
    "M": 16,              # Fewer connections
    "efConstruction": 100 # Lower build quality
}

# Slower indexing (higher quality)
index_params = {
    "M": 32,              # More connections
    "efConstruction": 300 # Higher build quality
}
```

**Batch size optimization:**
```python
# Index in batches of 1000
BATCH_SIZE = 1000
for i in range(0, len(chunks), BATCH_SIZE):
    batch = chunks[i:i+BATCH_SIZE]
    await service.insert(collection_name, batch)
```

---

### Search Performance

**Slow search? Adjust parameters:**

```python
# Faster search (lower recall)
search_params = {"ef": 50}  # Instead of 100

# Slower search (higher recall)
search_params = {"ef": 200}  # Instead of 100
```

**Use filters to reduce search space:**
```python
# Search only 1 tender (faster)
results = await service.search(
    ...,
    filters={"doc_id": "tender-123"}
)
```

**Reduce top_k:**
```python
# Retrieve fewer results (faster)
results = await service.search(..., top_k=10)  # Instead of 100
```

---

### Memory Usage

**Reduce memory footprint:**

1. **Use DiskANN index** (for large datasets)
2. **Enable memory mapping:**
   ```yaml
   # docker-compose.yml
   milvus-standalone:
     environment:
       - MILVUS_CACHE_ENABLED=true
   ```

3. **Reduce vector precision:**
   ```python
   # Use float16 instead of float32 (saves 50% memory)
   # Note: Requires Milvus 2.3+
   ```

---

## 🐛 Troubleshooting

### Issue: Connection Refused

**Error:** `Failed to connect to Milvus at http://localhost:19530`

**Solutions:**
1. Check Milvus is running:
   ```bash
   docker-compose ps
   # milvus-standalone should be "Up"
   ```

2. Check logs:
   ```bash
   docker-compose logs milvus-standalone
   ```

3. Restart:
   ```bash
   docker-compose restart milvus-standalone
   ```

4. Wait 30 seconds after starting (initialization time)

---

### Issue: Database Not Found

**Error:** `database not found[database=default]`

**Solution:** Create database first:
```python
from pymilvus import connections, db

connections.connect(host="localhost", port="19530")
db.create_database("default")
```

Or via REST API:
```bash
curl -X POST http://localhost:19530/v1/vector/databases \
  -H "Content-Type: application/json" \
  -d '{"database_name": "default"}'
```

---

### Issue: Collection Not Found

**Error:** `collection not found[collection=tender_chunks]`

**Solution:** Create collection:
```python
await service.create_collection(
    collection_name="tender_chunks",
    dimension=768
)
```

---

### Issue: Dimension Mismatch

**Error:** `dimension mismatch: expected 768, got 1536`

**Cause:** Collection created with different embedding dimension.

**Solution:**
1. **Check embedding model dimension:**
   ```python
   embed_client = get_embedding_client()
   print(embed_client.dimension)  # e.g., 768 or 1536
   ```

2. **Recreate collection with correct dimension:**
   ```python
   # Drop old collection
   await service.drop_collection("tender_chunks")
   
   # Create with correct dimension
   await service.create_collection(
       collection_name="tender_chunks",
       dimension=1536  # Match embedding model
   )
   ```

---

### Issue: Slow Search

**Symptom:** Search takes >1 second

**Solutions:**
1. **Lower `ef` parameter:**
   ```python
   search_params = {"ef": 50}  # Default is 100
   ```

2. **Reduce `top_k`:**
   ```python
   results = await service.search(..., top_k=10)  # Instead of 100
   ```

3. **Add filters:**
   ```python
   filters = {"doc_id": "tender-123"}  # Narrow search space
   ```

4. **Check index status:**
   ```python
   index_info = await service.describe_index("tender_chunks")
   print(index_info)  # Should show "INDEXED"
   ```

---

## 🔒 Security

### Authentication

**Enable authentication (production):**

```yaml
# docker-compose.yml
milvus-standalone:
  environment:
    - MILVUS_AUTHORIZATION_ENABLED=true
```

**Create user:**
```python
from pymilvus import connections, utility

connections.connect(
    alias="default",
    host="localhost",
    port="19530",
    user="root",
    password="Milvus"
)

utility.create_user(username="app_user", password="SecurePass123")
```

**Update `.env`:**
```bash
MILVUS_USER=app_user
MILVUS_PASSWORD=SecurePass123
```

---

### TLS/SSL

**Enable TLS (production):**

```yaml
# docker-compose.yml
milvus-standalone:
  environment:
    - MILVUS_TLS_ENABLED=true
    - MILVUS_TLS_CERT=/certs/server.crt
    - MILVUS_TLS_KEY=/certs/server.key
```

**Connect with TLS:**
```bash
MILVUS_URI=https://localhost:19530  # Use https
```

---

## 📚 Related Documentation

- [Infra Layer Overview](README.md)
- [Core: Indexing](../core/indexing.md) - Usage patterns
- [Environment Setup](../guides/environment-setup.md) - Configuration
- [Adding Integrations](adding-integrations.md) - Switch to Pinecone

---

**[⬅️ Infra README](README.md) | [⬆️ Documentation Home](../README.md) | [Factories ➡️](factories.md)**

*Last updated: 2025-12-18*
