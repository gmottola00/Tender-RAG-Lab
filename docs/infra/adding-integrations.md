# 🔌 Infrastructure: Adding New Integrations

> **Step-by-step guide for adding new vendors and implementations**

This guide walks you through adding new implementations of core protocols.

---

## 🎯 Overview

**Common integrations to add:**
- New embedding provider (Cohere, HuggingFace, etc.)
- New vector store (Pinecone, Weaviate, Qdrant)
- New LLM provider (Anthropic, Cohere, local models)
- New document parser (Excel, PowerPoint, etc.)
- New search strategy (graph-based, semantic reranking)

**General pattern:**
1. Implement core Protocol in `src/infra/`
2. Add to factory for dependency injection
3. Configure via environment variables
4. Test implementation
5. Document usage

---

## 📝 Checklist

Before starting, ensure you have:

- [ ] Read [Architecture Overview](../architecture/overview.md)
- [ ] Understand [Protocol-based design](../architecture/decisions.md#adr-001)
- [ ] Identified which Protocol to implement
- [ ] External library installed (`pip install <library>`)
- [ ] API credentials (if cloud service)

---

## 🔌 Adding an Embedding Provider

**Example:** Add Cohere embeddings support.

### Step 1: Install Library

```bash
pip install cohere
# or
uv add cohere
```

### Step 2: Create Implementation

**File:** `src/infra/embedding/cohere_embedding.py`

```python
"""Cohere embedding implementation"""
import cohere
from src.core.embedding import EmbeddingClient


class CohereEmbedding:
    """
    Cohere embedding client.
    
    Implements EmbeddingClient Protocol from src.core.embedding.
    """
    
    def __init__(self, api_key: str, model: str = "embed-multilingual-v3.0"):
        """
        Initialize Cohere client.
        
        Args:
            api_key: Cohere API key
            model: Embedding model name
        """
        self._client = cohere.Client(api_key)
        self._model = model
        self._dimension = 1024  # Cohere v3.0 dimension
    
    def embed_text(self, text: str) -> list[float]:
        """Embed single text."""
        response = self._client.embed(
            texts=[text],
            model=self._model,
            input_type="search_document"  # Cohere-specific
        )
        return response.embeddings[0]
    
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts (efficient)."""
        response = self._client.embed(
            texts=texts,
            model=self._model,
            input_type="search_document"
        )
        return response.embeddings
    
    @property
    def dimension(self) -> int:
        """Vector dimensionality."""
        return self._dimension
    
    @property
    def model_name(self) -> str:
        """Model identifier."""
        return f"cohere/{self._model}"
```

**Key points:**
- ✅ Implements all methods from `EmbeddingClient` Protocol
- ✅ Constructor takes configuration (no hardcoded values)
- ✅ Includes docstrings
- ✅ Type hints for all methods
- ✅ Handles vendor-specific parameters

---

### Step 3: Add to Factory

**File:** `src/infra/factories/embedding_factory.py`

```python
import os
from functools import lru_cache
from src.core.embedding import EmbeddingClient
from src.infra.embedding.ollama import OllamaEmbedding
from src.infra.embedding.openai_embedding import OpenAIEmbedding
from src.infra.embedding.cohere_embedding import CohereEmbedding  # ← Add import


@lru_cache
def get_embedding_client() -> EmbeddingClient:
    """
    Get configured embedding client based on EMBEDDING_PROVIDER env var.
    
    Supported providers: ollama, openai, cohere
    """
    provider = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()
    
    if provider == "ollama":
        return OllamaEmbedding(
            base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        )
    
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")
        return OpenAIEmbedding(
            api_key=api_key,
            model=os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
        )
    
    elif provider == "cohere":  # ← Add provider
        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            raise ValueError("COHERE_API_KEY environment variable required")
        return CohereEmbedding(
            api_key=api_key,
            model=os.getenv("COHERE_EMBED_MODEL", "embed-multilingual-v3.0")
        )
    
    else:
        raise ValueError(
            f"Unknown embedding provider: {provider}. "
            f"Supported: ollama, openai, cohere"
        )
```

---

### Step 4: Environment Configuration

**Add to `.env.example`:**

```bash
# Cohere Embeddings
EMBEDDING_PROVIDER=cohere
COHERE_API_KEY=your-api-key-here
COHERE_EMBED_MODEL=embed-multilingual-v3.0
```

**User configuration (`.env`):**

```bash
EMBEDDING_PROVIDER=cohere
COHERE_API_KEY=xxx-your-actual-key-xxx
```

---

### Step 5: Test Implementation

**Create test:** `tests/unit/infra/embedding/test_cohere.py`

```python
import pytest
from src.infra.embedding.cohere_embedding import CohereEmbedding


@pytest.fixture
def cohere_client():
    """Fixture for Cohere embedding client."""
    return CohereEmbedding(
        api_key="test-key-fake",  # Use test key or mock
        model="embed-multilingual-v3.0"
    )


def test_embed_text(cohere_client):
    """Test single text embedding."""
    vector = cohere_client.embed_text("tender requirements")
    
    assert isinstance(vector, list)
    assert len(vector) == 1024  # Cohere dimension
    assert all(isinstance(x, float) for x in vector)


def test_embed_batch(cohere_client):
    """Test batch embedding."""
    texts = ["text 1", "text 2", "text 3"]
    vectors = cohere_client.embed_batch(texts)
    
    assert len(vectors) == 3
    assert all(len(v) == 1024 for v in vectors)


def test_properties(cohere_client):
    """Test property methods."""
    assert cohere_client.dimension == 1024
    assert "cohere" in cohere_client.model_name
```

**Run tests:**
```bash
pytest tests/unit/infra/embedding/test_cohere.py -v
```

---

### Step 6: Document Usage

**Add to** `docs/infra/embeddings.md` (or create if missing):

```markdown
### Cohere

**Model:** `embed-multilingual-v3.0`
**Dimension:** 1024
**Languages:** 100+
**Cost:** $0.10 per 1M tokens

**Setup:**
\`\`\`bash
# .env
EMBEDDING_PROVIDER=cohere
COHERE_API_KEY=your-key
COHERE_EMBED_MODEL=embed-multilingual-v3.0
\`\`\`

**Usage:**
\`\`\`python
from src.infra.factories import get_embedding_client

embed_client = get_embedding_client()  # Auto-loads Cohere
vector = embed_client.embed_text("text")
\`\`\`
```

---

## 🗄️ Adding a Vector Store

**Example:** Add Pinecone support.

### Step 1: Install Library

```bash
pip install pinecone-client
```

### Step 2: Create Implementation

**File:** `src/infra/vectorstores/pinecone_store.py`

```python
"""Pinecone vector store implementation"""
import pinecone
from src.core.index.vector.database import VectorStore
from src.core.index.search.models import SearchResult


class PineconeVectorStore:
    """
    Pinecone vector store.
    
    Implements VectorStore Protocol from src.core.index.vector.
    """
    
    def __init__(self, api_key: str, environment: str, index_name: str):
        """Initialize Pinecone client."""
        self._client = pinecone.Pinecone(api_key=api_key)
        self._index = self._client.Index(index_name)
        self._index_name = index_name
    
    async def insert(
        self,
        vectors: list[list[float]],
        texts: list[str],
        metadata: list[dict]
    ) -> list[str]:
        """Insert vectors into Pinecone."""
        # Generate IDs
        ids = [f"chunk_{i}" for i in range(len(vectors))]
        
        # Format for Pinecone
        records = [
            {
                "id": id_,
                "values": vector,
                "metadata": {**meta, "text": text}
            }
            for id_, vector, text, meta in zip(ids, vectors, texts, metadata)
        ]
        
        # Upsert (batch)
        self._index.upsert(vectors=records)
        return ids
    
    async def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict | None = None
    ) -> list[SearchResult]:
        """Search for similar vectors."""
        # Convert filters to Pinecone format
        pinecone_filter = self._convert_filters(filters) if filters else None
        
        # Query
        response = self._index.query(
            vector=query_vector,
            top_k=top_k,
            filter=pinecone_filter,
            include_metadata=True
        )
        
        # Convert to SearchResult
        return [
            SearchResult(
                id=match["id"],
                score=match["score"],
                text=match["metadata"]["text"],
                metadata=match["metadata"]
            )
            for match in response["matches"]
        ]
    
    def _convert_filters(self, filters: dict) -> dict:
        """Convert generic filters to Pinecone format."""
        # Implement filter conversion logic
        return filters
    
    # ... implement other Protocol methods
```

---

### Step 3: Add to Factory

**File:** `src/infra/factories/vector_store_factory.py`

```python
import os
from functools import lru_cache
from src.core.index.vector.database import VectorStore
from src.core.index.vector.service import get_milvus_service
from src.infra.vectorstores.pinecone_store import PineconeVectorStore


@lru_cache
def get_vector_store() -> VectorStore:
    """Get configured vector store."""
    provider = os.getenv("VECTOR_STORE", "milvus").lower()
    
    if provider == "milvus":
        return get_milvus_service()
    
    elif provider == "pinecone":
        return PineconeVectorStore(
            api_key=os.getenv("PINECONE_API_KEY"),
            environment=os.getenv("PINECONE_ENV", "us-west1-gcp"),
            index_name=os.getenv("PINECONE_INDEX", "tender-index")
        )
    
    else:
        raise ValueError(f"Unknown vector store: {provider}")
```

---

### Step 4: Configure

```bash
# .env
VECTOR_STORE=pinecone
PINECONE_API_KEY=xxx
PINECONE_ENV=us-west1-gcp
PINECONE_INDEX=tender-index
```

---

## 🤖 Adding an LLM Provider

**Example:** Add Anthropic Claude.

**Follow similar pattern:**

1. **Install:** `pip install anthropic`
2. **Implement Protocol:** `src/infra/llm/anthropic_llm.py`
3. **Add to factory:** `src/infra/factories/llm_factory.py`
4. **Configure:** Add `LLM_PROVIDER=anthropic` to `.env`

**Implementation:**

```python
# src/infra/llm/anthropic_llm.py
import anthropic
from src.core.llm import LLMClient


class AnthropicLLM:
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
    
    async def agenerate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> str:
        """Generate response with Claude."""
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    @property
    def model_name(self) -> str:
        return f"anthropic/{self._model}"
```

---

## 📚 Best Practices

### 1. Error Handling

**Always handle vendor-specific errors:**

```python
class CohereEmbedding:
    def embed_text(self, text: str) -> list[float]:
        try:
            response = self._client.embed(...)
            return response.embeddings[0]
        except cohere.errors.CohereAPIError as e:
            # Convert to generic error or log
            logger.error(f"Cohere API error: {e}")
            raise RuntimeError(f"Embedding failed: {e}") from e
```

---

### 2. Logging

**Add structured logging:**

```python
from configs.logger import get_logger

logger = get_logger(__name__)


class CohereEmbedding:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        logger.info(
            "Embedding batch",
            extra={
                "provider": "cohere",
                "model": self._model,
                "batch_size": len(texts)
            }
        )
        # ... implementation
```

---

### 3. Validation

**Validate inputs:**

```python
def embed_text(self, text: str) -> list[float]:
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    if len(text) > 10000:  # Vendor limit
        raise ValueError("Text too long (max 10000 chars)")
    
    # ... implementation
```

---

### 4. Type Hints

**Always use type hints:**

```python
from typing import Protocol

class CohereEmbedding:
    def __init__(self, api_key: str, model: str = "...") -> None:
        ...
    
    def embed_text(self, text: str) -> list[float]:
        ...
    
    @property
    def dimension(self) -> int:
        ...
```

---

## 🧪 Testing Strategy

### Unit Tests

**Mock external API calls:**

```python
from unittest.mock import Mock, patch
import pytest


@patch("cohere.Client")
def test_cohere_embedding(mock_client):
    """Test Cohere embedding with mocked API."""
    # Setup mock
    mock_response = Mock()
    mock_response.embeddings = [[0.1, 0.2, 0.3]]
    mock_client.return_value.embed.return_value = mock_response
    
    # Test
    client = CohereEmbedding(api_key="test-key")
    vector = client.embed_text("test")
    
    assert vector == [0.1, 0.2, 0.3]
    mock_client.return_value.embed.assert_called_once()
```

---

### Integration Tests

**Test with real API (optional):**

```python
@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("COHERE_API_KEY"), reason="No API key")
def test_cohere_real_api():
    """Test with real Cohere API."""
    client = CohereEmbedding(api_key=os.getenv("COHERE_API_KEY"))
    vector = client.embed_text("tender requirements")
    
    assert len(vector) == 1024
    assert all(-1 <= x <= 1 for x in vector)  # Normalized
```

---

## 📚 Related Documentation

- [Architecture Overview](../architecture/overview.md)
- [Where to Put Code](../architecture/where-to-put-code.md)
- [Core Layer](../core/README.md) - Protocol definitions
- [Factories](factories.md) - Dependency injection

---

**[⬅️ Milvus](milvus.md) | [⬆️ Documentation Home](../README.md) | [Infra README ➡️](README.md)**

*Last updated: 2025-12-18*
