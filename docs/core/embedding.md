# 🧩 Core Layer: Embedding

> **Transform text into dense vectors for semantic search**

The embedding module provides abstractions for converting text into vector representations.

---

## 📍 Location

**Directory:** `src/core/embedding/`

**Files:**
- `base.py` - `EmbeddingClient` Protocol
- (Implementations in `src/infra/`)

---

## 🎯 Purpose

**What embeddings do:**
- Convert text → fixed-length dense vectors
- Similar text → similar vectors (cosine/dot product)
- Enable semantic search (not just keyword matching)

**Core abstraction:** Transform strings into vectors, vendor-agnostic.

---

## 🏗️ Architecture

### Protocol Definition

```python
class EmbeddingClient(Protocol):
    """Abstract embedding interface"""
    
    def embed_text(self, text: str) -> list[float]:
        """Single text → vector"""
        ...
    
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch processing for efficiency"""
        ...
    
    @property
    def dimension(self) -> int:
        """Vector dimensionality (e.g., 384, 1536)"""
        ...
    
    @property
    def model_name(self) -> str:
        """Model identifier"""
        ...
```

**Layer:** Core (pure abstraction, no imports from infra)

**Implementations:**
- `OllamaEmbedding` (in `src/infra/embedding/`)
- `OpenAIEmbedding` (in `src/infra/embedding/`)

**See:** [Infra: Embedding](../infra/embeddings.md) for implementations.

---

## 📐 Vector Dimensions

Different models → different dimensions:

| Model | Provider | Dims | Use Case |
|-------|----------|------|----------|
| `nomic-embed-text` | Ollama | 768 | Local, fast, good quality |
| `mxbai-embed-large` | Ollama | 1024 | Local, higher quality |
| `text-embedding-3-small` | OpenAI | 1536 | Cloud, cost-effective |
| `text-embedding-3-large` | OpenAI | 3072 | Cloud, best quality |

**Important:** Must match Milvus collection schema!

---

## 🔧 Usage Patterns

### Basic Usage

```python
from src.infra.factories import get_embedding_client

# Get configured client (from .env)
embed_client = get_embedding_client()

# Single text
vector = embed_client.embed_text("Requisiti tecnici del bando")
print(f"Dimension: {len(vector)}")  # e.g., 768

# Batch (more efficient)
texts = ["Lotto 1", "Lotto 2", "Lotto 3"]
vectors = embed_client.embed_batch(texts)
```

### Dependency Injection

**In domain/services:**

```python
# src/domain/services/ingestion.py
class IngestionService:
    def __init__(self, embedding_client: EmbeddingClient):
        self._embed = embedding_client
    
    async def process_document(self, doc: Document):
        chunks = self._chunker.chunk(doc.text)
        
        # Embed all chunks
        texts = [c.text for c in chunks]
        vectors = self._embed.embed_batch(texts)
```

**Factory provides implementation:**

```python
# src/infra/factories/ingestion_factory.py
def get_ingestion_service() -> IngestionService:
    embed_client = get_embedding_client()  # Ollama or OpenAI
    return IngestionService(embedding_client=embed_client)
```

**See:** [Factories](../infra/factories.md) for DI patterns.

---

## 🚀 Performance Best Practices

### 1. Always Use Batch Processing

**❌ Bad (slow):**
```python
vectors = [embed_client.embed_text(text) for text in texts]
```

**✅ Good (fast):**
```python
vectors = embed_client.embed_batch(texts)
```

**Why?** Batching:
- Reduces API calls (OpenAI)
- Better GPU utilization (Ollama)
- ~10-50x faster for large batches

### 2. Batch Size Limits

**Recommended limits:**
- Ollama: 32-64 texts/batch
- OpenAI: 100 texts/batch (API limit)

**For large datasets:**
```python
BATCH_SIZE = 32
for i in range(0, len(texts), BATCH_SIZE):
    batch = texts[i:i+BATCH_SIZE]
    vectors.extend(embed_client.embed_batch(batch))
```

### 3. Caching

**Avoid re-embedding same text:**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_embed(text: str) -> tuple[float, ...]:
    vec = embed_client.embed_text(text)
    return tuple(vec)  # Lists aren't hashable
```

**Use case:** Repetitive queries, common phrases.

---

## 🔬 Embedding Quality

### Factors Affecting Quality

1. **Model Choice**
   - Larger models → better semantic understanding
   - Domain-specific models → better for specialized text

2. **Text Preprocessing**
   - Clean text (remove noise, OCR errors)
   - Preserve structure (headings, lists)
   - Language consistency (don't mix IT + EN in single text)

3. **Chunk Size**
   - Too short → lacks context
   - Too long → diluted semantics
   - Optimal: 200-800 tokens

### Testing Embedding Quality

```python
# Compare similar vs dissimilar texts
text1 = "Requisiti tecnici del bando"
text2 = "Technical tender requirements"  # Similar
text3 = "Prezzo unitario"                # Dissimilar

v1 = embed_client.embed_text(text1)
v2 = embed_client.embed_text(text2)
v3 = embed_client.embed_text(text3)

# Cosine similarity
from numpy import dot
from numpy.linalg import norm

def cosine_sim(a, b):
    return dot(a, b) / (norm(a) * norm(b))

print(f"Similar:    {cosine_sim(v1, v2):.3f}")  # Should be high (~0.7-0.9)
print(f"Dissimilar: {cosine_sim(v1, v3):.3f}")  # Should be low (~0.3-0.5)
```

---

## 🛠️ Implementation Details

### Model Loading (Ollama)

**On first use:**
- Ollama pulls model if not cached
- Takes 1-5 minutes (depending on model size)
- Stored in `~/.ollama/models/`

**Verify model:**
```bash
ollama list
ollama pull nomic-embed-text
```

### Model Versioning

**OpenAI:** Models have versions (e.g., `text-embedding-3-small-v1`)
- Check `.model_name` property
- Document version in metadata

**Ollama:** Models are tagged (e.g., `nomic-embed-text:latest`)
- Pin versions: `nomic-embed-text@sha256:abc123`

### Error Handling

**Common errors:**

1. **Model not found:**
   - Ollama: `ollama pull <model>`
   - OpenAI: Check model name

2. **API rate limits (OpenAI):**
   - Retry with exponential backoff
   - Reduce batch size

3. **Dimension mismatch:**
   - Milvus collection expects 768 dims
   - Model returns 1536 dims
   - → Must recreate collection with correct schema

---

## 🌍 Multi-Language Support

### Language Detection

Embeddings are language-agnostic (mostly):
- `nomic-embed-text`: Trained on 100+ languages
- `text-embedding-3-*`: Multilingual

**Best practice:**
```python
# Document metadata includes language
doc_metadata = {
    "language": "it",  # Detected by LanguageDetector
    "doc_id": "tender-123"
}

# Can use for filtering:
# "Find Italian documents similar to query"
```

### Mixed-Language Documents

**Problem:** Single doc with IT + EN sections

**Solutions:**
1. **Chunk by language:**
   - Detect language per paragraph
   - Create separate chunks with lang metadata

2. **Use multilingual model:**
   - `text-embedding-3-*` handles mixed languages
   - Less optimal than single-language

---

## 🚀 Adding a New Embedding Provider

**Example:** Add Cohere embeddings.

### 1. Create Implementation (Infra Layer)

```python
# src/infra/embedding/cohere_embedding.py
import cohere

class CohereEmbedding:
    """Cohere embedding implementation"""
    
    def __init__(self, api_key: str, model: str = "embed-multilingual-v3.0"):
        self._client = cohere.Client(api_key)
        self._model = model
    
    def embed_text(self, text: str) -> list[float]:
        response = self._client.embed(texts=[text], model=self._model)
        return response.embeddings[0]
    
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embed(texts=texts, model=self._model)
        return response.embeddings
    
    @property
    def dimension(self) -> int:
        return 1024  # Cohere v3.0
    
    @property
    def model_name(self) -> str:
        return f"cohere/{self._model}"
```

### 2. Add to Factory

```python
# src/infra/factories/embedding_factory.py
from src.infra.embedding.cohere_embedding import CohereEmbedding

def get_embedding_client() -> EmbeddingClient:
    provider = os.getenv("EMBEDDING_PROVIDER", "ollama")
    
    if provider == "cohere":
        return CohereEmbedding(
            api_key=os.getenv("COHERE_API_KEY"),
            model=os.getenv("COHERE_MODEL", "embed-multilingual-v3.0")
        )
    # ... existing providers
```

### 3. Environment Config

```bash
# .env
EMBEDDING_PROVIDER=cohere
COHERE_API_KEY=your-key-here
COHERE_MODEL=embed-multilingual-v3.0
```

**See:** [Adding Integrations](../infra/adding-integrations.md) for complete guide.

---

## 📊 Monitoring & Debugging

### Logging Embedding Calls

```python
# configs/logger.py already logs embedding calls

logger.debug(
    "Embedding batch",
    extra={
        "model": embed_client.model_name,
        "batch_size": len(texts),
        "avg_length": sum(len(t) for t in texts) / len(texts)
    }
)
```

### Metrics to Track

- **Latency:** Time per batch
- **Throughput:** Texts/second
- **Cost:** API calls × cost (OpenAI)
- **Errors:** Rate limit hits, timeouts

---

## 📚 Related Documentation

- [Core Layer Overview](README.md)
- [Chunking Module](chunking.md) - Prepare text for embedding
- [Infra: Embeddings](../infra/embeddings.md) - Concrete implementations
- [Adding Integrations](../infra/adding-integrations.md) - Add new providers

---

**[⬅️ Chunking](chunking.md) | [⬆️ Documentation Home](../README.md) | [LLM ➡️](llm.md)**

*Last updated: 2025-12-18*
