# 🧩 Infrastructure: Embedding Implementations

> **Concrete implementations of the EmbeddingClient Protocol**

This module contains vendor-specific implementations for text embedding clients.

---

## 📍 Location

**Directory:** `src/infra/embedding/`

**Files:**
- `ollama.py` - Ollama implementation
- `openai.py` - OpenAI implementation

---

## 🔌 Available Implementations

### Ollama Embedding Client

**Location:** `src/infra/embedding/ollama.py`

Local embeddings via Ollama API.

```python
from src.infra.embedding import OllamaEmbeddingClient

# Initialize
client = OllamaEmbeddingClient(
    model="nomic-embed-text",
    base_url="http://localhost:11434",
    timeout=120
)

# Single embedding
vector = client.embed("Hello world")
# Returns: List[float] with 768 dimensions

# Batch embeddings
vectors = client.embed_batch([
    "First document",
    "Second document",
    "Third document"
])
# Returns: List[List[float]]
```

**Configuration:**
- `model`: Ollama embedding model (default: `nomic-embed-text`)
- `base_url`: Ollama server URL (default: `http://localhost:11434`)
- `timeout`: Request timeout in seconds (default: 120)

**Supported Models:**
- `nomic-embed-text` (768D, best for general text)
- `mxbai-embed-large` (1024D, high quality)
- Any Ollama model with embedding support

---

### OpenAI Embedding Client

**Location:** `src/infra/embedding/openai.py`

OpenAI Embeddings API.

```python
from src.infra.embedding import OpenAIEmbeddingClient

# Initialize
client = OpenAIEmbeddingClient(
    model="text-embedding-3-small",
    api_key="sk-...",
    base_url=None  # Optional: custom endpoint
)

# Single embedding
vector = client.embed("Document text")
# Returns: List[float] with 1536 dimensions

# Batch (automatically handled by OpenAI API)
vectors = client.embed_batch([
    "Doc 1", "Doc 2", "Doc 3"
])
```

**Configuration:**
- `model`: OpenAI embedding model (default: `text-embedding-3-small`)
- `api_key`: OpenAI API key (required, from `OPENAI_API_KEY` env)
- `base_url`: Custom endpoint (optional)

**Available Models:**
- `text-embedding-3-small` (1536D, $0.02/1M tokens)
- `text-embedding-3-large` (3072D, $0.13/1M tokens)
- `text-embedding-ada-002` (1536D, legacy)

---

## 🎯 Protocol Compliance

Both implementations satisfy the `EmbeddingClient` Protocol from `src.core.embedding.base`:

```python
from typing import Protocol, List, Sequence

class EmbeddingClient(Protocol):
    def embed(self, text: str) -> List[float]: ...
    def embed_batch(self, texts: Sequence[str]) -> List[List[float]]: ...
    
    @property
    def model_name(self) -> str: ...
    
    @property
    def dimension(self) -> int | None: ...
```

---

## 🔄 Dependency Injection

Use with factory pattern for swappable implementations:

```python
from src.core.embedding import EmbeddingClient
from src.infra.embedding import OllamaEmbeddingClient, OpenAIEmbeddingClient

def create_embedding_client(provider: str) -> EmbeddingClient:
    """Factory for embedding clients."""
    if provider == "ollama":
        return OllamaEmbeddingClient()
    elif provider == "openai":
        return OpenAIEmbeddingClient()
    else:
        raise ValueError(f"Unknown provider: {provider}")

# Usage
embedder = create_embedding_client("ollama")  # Type: EmbeddingClient
vector = embedder.embed("Some text")
```

**Benefits:**
- ✅ No coupling to specific vendor
- ✅ Easy to swap providers
- ✅ Testable with mocks
- ✅ Configuration at runtime

---

## 📊 Performance Comparison

| Provider | Model | Dimensions | Speed | Cost |
|----------|-------|------------|-------|------|
| Ollama | nomic-embed-text | 768 | ~50ms | Free (local) |
| Ollama | mxbai-embed-large | 1024 | ~80ms | Free (local) |
| OpenAI | text-embedding-3-small | 1536 | ~30ms | $0.02/1M tokens |
| OpenAI | text-embedding-3-large | 3072 | ~50ms | $0.13/1M tokens |

---

## 🛠️ Adding New Providers

To add a new embedding provider (e.g., Cohere, HuggingFace):

1. Create `src/infra/embedding/newprovider.py`
2. Implement the `EmbeddingClient` Protocol methods
3. Add to `src/infra/embedding/__init__.py`
4. No changes needed to core layer!

See [Adding Integrations](adding-integrations.md) for details.

---

## 📚 See Also

- [Core Embedding Documentation](../core/embedding.md) - Protocol definition
- [Vector Search](../core/indexing.md) - Using embeddings for search
- [Milvus Setup](milvus.md) - Vector database configuration
