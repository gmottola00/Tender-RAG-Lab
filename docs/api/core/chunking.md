# Chunking API

Document chunking strategies and token optimization.

## DynamicChunker

Splits documents by structure (headings, sections):

```python
from quaerum.core.chunking import DynamicChunker

class DynamicChunker:
    """Dynamic document chunking by structure."""
    
    def __init__(
        self,
        max_tokens: int = 512,
        overlap_tokens: int = 50,
        respect_boundaries: bool = True
    ):
        ...

## Usage Examples

### Basic Chunking

```python
from quaerum.core.chunking import DynamicChunker

chunker = DynamicChunker(
    max_tokens=512,
    overlap_tokens=50,
)

chunks = chunker.chunk_document(document)

for chunk in chunks:
    print(f"Chunk {chunk.id}: {len(chunk.text)} chars")
```

### Token Optimization

```python
from quaerum.core.chunking import TokenChunker

token_chunker = TokenChunker(
    max_tokens=512,
    overlap=50,
)

token_chunks = token_chunker.create_token_chunks(chunks)

# Token chunks are optimized for embedding
vectors = [embed_client.embed(tc.text) for tc in token_chunks]
```

### Domain Extension

```python
from quaerum.core.chunking.types import ChunkLike
from dataclasses import dataclass

@dataclass
class TenderChunk:
    """Domain-specific chunk implementing ChunkLike protocol."""
    
    # Protocol fields
    id: str
    text: str
    title: str
    heading_level: int
    
    # Tender-specific
    tender_id: str
    lot_id: Optional[str]
    
    def to_dict(self, *, include_blocks: bool = True) -> Dict:
        return {
            "id": self.id,
            "text": self.text,
            "tender_id": self.tender_id,
        }
```

## Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_tokens` | int | 512 | Maximum chunk size |
| `overlap_tokens` | int | 50 | Overlap between chunks |
| `respect_boundaries` | bool | True | Respect sentence boundaries |

## See Also

- [Tender Chunks](../domain/services.md) - Domain-specific implementations
- [Indexing Guide](../../guides/indexing-documents.md) - Document ingestion
