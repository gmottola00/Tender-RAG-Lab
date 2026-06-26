# Extending quaerum

Guide to extending quaerum with custom components.

## Protocol-Based Extension

quaerum uses **Protocols** for extensibility - implement the protocol, no inheritance needed.

## Custom Embedding Client

```python
from quaerum.core.embedding import EmbeddingClient
from typing import List

class MyCustomEmbedding:
    """Custom embedding implementation."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def embed(self, text: str) -> List[float]:
        """Implement required method."""
        # Your embedding logic
        return vector
    
    def get_dimension(self) -> int:
        """Optional helper method."""
        return 768

# Use it anywhere EmbeddingClient is expected
embed_client: EmbeddingClient = MyCustomEmbedding(api_key="...")
indexer = create_index_service(embed_fn=embed_client.embed, ...)
```

## Custom LLM Client

```python
from quaerum.core.llm import LLMClient
from typing import List, Dict, Any

class MyCustomLLM:
    """Custom LLM implementation."""
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Required method for LLMClient protocol."""
        # Your LLM logic
        return response
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Optional helper."""
        return self.chat([{"role": "user", "content": prompt}])

# Use in RAG pipeline
llm_client: LLMClient = MyCustomLLM()
pipeline = RagPipeline(llm_client=llm_client, ...)
```

## Custom Chunk Type

```python
from quaerum.core.chunking.types import ChunkLike
from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class CustomChunk:
    """Custom chunk with domain fields."""
    
    # Required by ChunkLike protocol
    id: str
    text: str
    title: str
    heading_level: int
    blocks: List[Dict[str, Any]]
    page_numbers: List[int]
    
    # Your custom fields
    custom_field_1: str
    custom_field_2: int
    
    def to_dict(self, *, include_blocks: bool = True) -> Dict[str, Any]:
        """Required method."""
        data = {
            "id": self.id,
            "text": self.text,
            "custom_field_1": self.custom_field_1,
        }
        if include_blocks:
            data["blocks"] = self.blocks
        return data

# Use anywhere ChunkLike is expected
chunks: List[ChunkLike] = [CustomChunk(...), ...]
indexer.index(chunks)
```

## Custom Search Strategy

```python
from quaerum.core.index.search_strategies import SearchStrategy
from quaerum.core.index.service import IndexService
from typing import List

class SemanticBoostSearch(SearchStrategy):
    """Boost results with specific keywords."""
    
    def __init__(self, boost_terms: List[str], top_k: int = 10):
        self.boost_terms = boost_terms
        self.top_k = top_k
    
    def search(
        self,
        query: str,
        index_service: IndexService,
        **kwargs
    ) -> List[Any]:
        # Get base results
        results = index_service.vector_search(query, top_k=self.top_k * 2)
        
        # Boost if contains boost terms
        for result in results:
            if any(term in result.text.lower() for term in self.boost_terms):
                result.score *= 1.5
        
        # Re-sort and return top k
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:self.top_k]

# Use it
strategy = SemanticBoostSearch(boost_terms=["mandatory", "required"])
results = index_service.search(query, strategy=strategy)
```

## Custom Reranker

```python
from quaerum.rag.rerankers import Reranker
from typing import List, Any

class CustomReranker(Reranker):
    """Custom reranking logic."""
    
    def __init__(self, criteria: str):
        self.criteria = criteria
    
    async def rerank(
        self,
        query: str,
        chunks: List[Any],
        top_k: int = 5
    ) -> List[Any]:
        # Your reranking logic
        scored = []
        for chunk in chunks:
            score = self._score_chunk(query, chunk)
            scored.append((score, chunk))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        return [chunk for _, chunk in scored[:top_k]]
    
    def _score_chunk(self, query: str, chunk: Any) -> float:
        # Custom scoring
        return score

# Use in pipeline
reranker = CustomReranker(criteria="technical_relevance")
pipeline = RagPipeline(reranker=reranker, ...)
```

## Custom Vector Store

```python
from quaerum.core.vectorstore import VectorStoreClient
from typing import List, Dict, Any

class MyVectorStore:
    """Custom vector database implementation."""
    
    def __init__(self, connection_string: str):
        self.client = ...  # Your DB client
    
    def insert(
        self,
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]]
    ):
        """Required method."""
        # Insert logic
        pass
    
    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Required method."""
        # Search logic
        return results
    
    def delete(self, ids: List[str]):
        """Required method."""
        # Delete logic
        pass

# Use it
vector_store: VectorStoreClient = MyVectorStore("postgresql://...")
index_service = create_index_service(vector_store=vector_store, ...)
```

## Best Practices

1. **Follow Protocols** - Implement required methods exactly
2. **Type Hints** - Use proper type annotations
3. **Documentation** - Document your extensions
4. **Testing** - Write tests for custom components
5. **Naming** - Use descriptive class names

## Testing Extensions

```python
import pytest
from quaerum.core.embedding import EmbeddingClient

def test_custom_embedding():
    """Test custom embedding client."""
    embed_client = MyCustomEmbedding(api_key="test")
    
    # Test protocol compliance
    assert hasattr(embed_client, "embed")
    
    # Test functionality
    vector = embed_client.embed("test text")
    assert len(vector) == 768
    assert all(isinstance(v, float) for v in vector)
```

## See Also

- [quaerum Integration](../architecture/rag-toolkit.md) - Integration guide
- [Clean Architecture](../architecture/clean-architecture.md) - Design principles
- [API Reference](../api/core/embedding.md) - Protocol documentation
