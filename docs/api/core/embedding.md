# Embedding API

Documentation for embedding components.

## Overview

The embedding system provides text vectorization using Protocol-based interfaces from quaerum.

## EmbeddingClient Protocol

The `EmbeddingClient` protocol defines the interface for embedding models:

```python
from typing import Protocol, List

class EmbeddingClient(Protocol):
    """Protocol for embedding clients."""
    
    def embed(self, text: str) -> List[float]:
        """Embed text into vector representation."""
        ...

## Usage Examples

### Basic Usage

```python
from quaerum.infra.embedding import OllamaEmbeddingClient

# Initialize client
embed_client = OllamaEmbeddingClient(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

# Embed single text
vector = embed_client.embed("Hello world")
print(f"Dimension: {len(vector)}")  # 768

# Embed batch
texts = ["text 1", "text 2", "text 3"]
vectors = [embed_client.embed(t) for t in texts]
```

### With Domain Factory

```python
from src.infra.factory import create_tender_stack
from quaerum.infra.embedding import OllamaEmbeddingClient

embed_client = OllamaEmbeddingClient()
embedding_dim = len(embed_client.embed("test"))

indexer, searcher = create_tender_stack(
    embed_client=embed_client,
    embedding_dim=embedding_dim
)
```

## Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | str | "nomic-embed-text" | Ollama model name |
| `base_url` | str | "http://localhost:11434" | Ollama server URL |
| `timeout` | int | 30 | Request timeout in seconds |

## Supported Models

- **nomic-embed-text** (768-dim, recommended)
- **all-minilm** (384-dim, fast)
- **bge-large** (1024-dim, accurate)

## See Also

- [LLM API](llm.md) - Language model client
- [Factory](../infra/factory.md) - Domain-specific factories
