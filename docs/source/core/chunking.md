# 🧩 Core Layer: Chunking

> **Protocol-based chunking abstractions for document processing with domain-specific extensions**

The chunking module provides Protocol-based abstractions (PEP 544) for breaking documents into semantically meaningful chunks while allowing domain-specific implementations with custom metadata.

---

## 📍 Location

**Core Protocols:** `src/core/chunking/types.py`
**Core Implementations:** `src/core/chunking/`
**Domain Implementations:** `src/domain/tender/schemas/chunking.py`

**Files:**
- `types.py` - Protocol definitions (`ChunkLike`, `TokenChunkLike`)
- `chunking.py` - Token-based chunking implementation
- `dynamic_chunker.py` - Heading-based chunking implementation

---

## 🎯 Purpose

**Protocol-Based Design:**
- ✅ **Structural subtyping** - No inheritance required
- ✅ **Domain extensions** - Add custom fields without modifying core
- ✅ **Type safety** - Static type checking with Protocol conformance
- ✅ **Flexibility** - Any implementation matching the interface works

**Why chunking matters:**
- Embeddings work best on focused, coherent text units
- Too small = loss of context
- Too large = diluted relevance scores
- Dynamic chunking adapts to document structure

---

## 🏗️ Architecture

### ChunkLike Protocol

**Core interface for document chunks:**

```python
from typing import Protocol, runtime_checkable, List, Dict, Any

@runtime_checkable
class ChunkLike(Protocol):
    """Protocol defining the interface for document chunks.
    
    Attributes:
        id: Unique identifier
        title: Section title or heading
        heading_level: Hierarchical level (h1=1, h2=2)
        text: Actual text content
        blocks: Structured text blocks
        page_numbers: Pages where chunk appears
    """
    id: str
    title: str
    heading_level: int
    text: str
    blocks: List[Dict[str, Any]]
    page_numbers: List[int]

    def to_dict(self, *, include_blocks: bool = True) -> Dict[str, Any]:
        """Convert chunk to dictionary representation."""
        ...
```

### TokenChunkLike Protocol

**Core interface for token-optimized chunks:**

```python
@runtime_checkable
class TokenChunkLike(Protocol):
    """Protocol for token-optimized chunks.
    
    Attributes:
        id: Unique identifier
        text: Token-optimized text content
        section_path: Hierarchical section path
        metadata: Additional metadata
        page_numbers: Pages where chunk appears
        source_chunk_id: Reference to original chunk
    """
    id: str
    text: str
    section_path: str
    metadata: Dict[str, str]
    page_numbers: List[int]
    source_chunk_id: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert token chunk to dictionary."""
        ...
```

---

## 📦 Domain Implementations

### TenderChunk

**Tender-specific implementation with domain metadata:**

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class TenderChunk:
    """Implements ChunkLike with tender-specific fields."""
    
    # Core protocol fields
    id: str
    title: str
    heading_level: int
    text: str
    blocks: List[Dict[str, Any]] = field(default_factory=list)
    page_numbers: List[int] = field(default_factory=list)
    
    # Domain-specific fields
    tender_id: str = ""
    lot_id: Optional[str] = None
    section_type: str = ""

    def to_dict(self, *, include_blocks: bool = True) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "title": self.title,
            "heading_level": self.heading_level,
            "text": self.text,
            "page_numbers": self.page_numbers,
            "tender_id": self.tender_id,
            "lot_id": self.lot_id,
            "section_type": self.section_type,
        }
        if include_blocks:
            data["blocks"] = self.blocks
        return data
```

**Protocol Conformance:**

```python
from src.core.chunking.types import ChunkLike
from src.domain.tender.schemas.chunking import TenderChunk

chunk = TenderChunk(id="1", title="Test", heading_level=1, text="Content", blocks=[], page_numbers=[])
assert isinstance(chunk, ChunkLike)  # ✅ True
```

### TenderTokenChunk

**Token-optimized chunk with tender metadata:**

```python
@dataclass
class TenderTokenChunk:
    """Implements TokenChunkLike with tender-specific fields."""
    
    # Core protocol fields
    id: str
    text: str
    section_path: str
    metadata: Dict[str, str] = field(default_factory=dict)
    page_numbers: List[int] = field(default_factory=list)
    source_chunk_id: str = ""
    
    # Domain-specific fields
    tender_id: str = ""
    lot_id: Optional[str] = None
    section_type: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "section_path": self.section_path,
            "metadata": self.metadata,
            "page_numbers": self.page_numbers,
            "source_chunk_id": self.source_chunk_id,
            "tender_id": self.tender_id,
            "lot_id": self.lot_id,
            "section_type": self.section_type,
        }
```

---

## 🔧 Chunking Strategies

### DynamicChunker

**Strategy:** Heading-based chunking using document structure.

1. **Split into sentences** (using `nltk`)
**Creates chunks using heading hierarchy:**

```python
from src.core.chunking.dynamic_chunker import DynamicChunker

chunker = DynamicChunker(
    include_tables=True,
    max_heading_level=6,
    allow_preamble=False
)

chunks = chunker.chunk_document(blocks)
# Returns List[ChunkLike] - any implementation conforming to protocol
```

**When to Use:**

✅ **Good for:**
- Structured documents (PDFs with sections)
- Documents with clear heading hierarchy
- Preserving semantic context (doesn't split mid-topic)
- High-quality retrieval (semantic coherence)

❌ **Avoid for:**
- Simple plain text without structure
- High-volume batch processing (slower)
- Documents without clear headings

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_tables` | bool | `True` | Include table blocks in chunks |
| `max_heading_level` | int | `6` | Maximum heading level to process |
| `allow_preamble` | bool | `False` | Allow text before first heading |

### Token-Based Chunking

**Creates token-optimized chunks with overlap:**

```python
from src.core.chunking.chunking import create_token_chunks

token_chunks = create_token_chunks(
    chunks=chunks,
    max_tokens=800,
    min_tokens=400,
    overlap=120
)
# Returns List[TokenChunkLike]
```

**When to Use:**

✅ **Good for:**
- Embedding generation (optimal token sizes)
- Vector retrieval (consistent dimensions)
- Managing context windows
- Cost control (predictable token usage)

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_tokens` | int | `800` | Maximum tokens per chunk |
| `min_tokens` | int | `400` | Minimum tokens per chunk |
| `overlap` | int | `120` | Overlapping tokens between chunks |
| `tokenizer` | Callable | `default_tokenizer` | Function to tokenize text |

---

## 🎯 Usage Examples

### Creating Domain-Specific Chunks

```python
from src.domain.tender.schemas.chunking import TenderChunk, TenderTokenChunk

# Create a tender chunk with domain metadata
chunk = TenderChunk(
    id="chunk_001",
    title="Technical Requirements",
    heading_level=2,
    text="Python 3.10+, FastAPI, PostgreSQL...",
    blocks=[
        {"type": "paragraph", "text": "Python 3.10+"},
        {"type": "list", "items": ["FastAPI", "PostgreSQL"]}
    ],
    page_numbers=[1, 2],
    tender_id="tender_123",
    lot_id="lot_456",
    section_type="requirements"
)

# Access core fields
print(chunk.title)  # "Technical Requirements"

# Access domain fields
print(chunk.tender_id)  # "tender_123"
print(chunk.section_type)  # "requirements"

# Serialize with all fields
data = chunk.to_dict()
assert "tender_id" in data
assert "section_type" in data
```

### Generic Processing with Protocols

```python
from typing import List
from src.core.chunking.types import ChunkLike

def extract_text(chunks: List[ChunkLike]) -> str:
    """Extract all text from chunks conforming to ChunkLike.
    
    Works with any implementation: TenderChunk, ContractChunk, etc.
    """
    return "\n\n".join(chunk.text for chunk in chunks)

# Works with tender chunks
tender_chunks: List[TenderChunk] = [...]
text = extract_text(tender_chunks)  # ✅ Type-safe
```

### Protocol Conformance Checking

```python
from src.core.chunking.types import ChunkLike, TokenChunkLike
from src.domain.tender.schemas.chunking import TenderChunk, TenderTokenChunk

# Runtime conformance checking
chunk = TenderChunk(
    id="1", title="Test", heading_level=1, 
    text="Content", blocks=[], page_numbers=[]
)
token_chunk = TenderTokenChunk(
    id="t1", text="Content", section_path="S1",
    metadata={}, page_numbers=[], source_chunk_id="1"
)

print(isinstance(chunk, ChunkLike))  # ✅ True
print(isinstance(token_chunk, TokenChunkLike))  # ✅ True
```

---

## 🔬 Comparison

| Feature | TokenChunker | DynamicChunker |
---

## 🎓 Best Practices

### 1. Use Protocols in Core Layer

Define protocols in `src/core/` for maximum reusability:

```python
# ✅ Good: Protocol in core layer
# src/core/chunking/types.py
@runtime_checkable
class ChunkLike(Protocol):
    id: str
    title: str
    # ... other protocol fields
```

### 2. Implement Concretely in Domain Layer

Create concrete implementations in domain layers with @dataclass:

```python
# ✅ Good: Concrete implementation in domain layer
# src/domain/tender/schemas/chunking.py
@dataclass
class TenderChunk:
    # Implements ChunkLike with domain-specific fields
    id: str
    title: str
    # ... protocol fields
    tender_id: str  # domain-specific field
```

### 3. Type Hints with Protocols

Use protocols in function signatures for flexibility:

```python
# ✅ Good: Accept any ChunkLike implementation
def process_chunks(chunks: List[ChunkLike]) -> Dict[str, Any]:
    ...

# ❌ Avoid: Requiring specific implementation
def process_chunks(chunks: List[TenderChunk]) -> Dict[str, Any]:
    ...
```

### 4. Maintain Backward Compatibility

Provide legacy aliases when introducing protocols:

```python
# Maintain compatibility with old code
Chunk = ChunkLike
TokenChunk = TokenChunkLike

__all__ = ["ChunkLike", "TokenChunkLike", "Chunk", "TokenChunk"]
```

---

## 🧪 Testing

### Protocol Conformance Tests

```python
from src.core.chunking.types import ChunkLike, TokenChunkLike
from src.domain.tender.schemas.chunking import TenderChunk, TenderTokenChunk

def test_protocol_conformance():
    """Test that implementations conform to protocols."""
    chunk = TenderChunk(
        id="1", title="Test", heading_level=1, 
        text="Content", blocks=[], page_numbers=[]
    )
    token_chunk = TenderTokenChunk(
        id="t1", text="Content", section_path="S1",
        metadata={}, page_numbers=[], source_chunk_id="1"
    )
    
    assert isinstance(chunk, ChunkLike)
    assert isinstance(token_chunk, TokenChunkLike)

def test_to_dict_includes_domain_fields():
    """Test that to_dict includes domain-specific fields."""
    chunk = TenderChunk(
        id="1", title="Test", heading_level=1, text="Content",
        blocks=[], page_numbers=[],
        tender_id="tender_123", section_type="requirements"
    )
    
    data = chunk.to_dict()
    assert data["tender_id"] == "tender_123"
    assert data["section_type"] == "requirements"
```

---

## 🚀 Creating New Implementations

### For a New Domain

```python
# src/domain/contract/schemas/chunking.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class ContractChunk:
    """Contract-specific implementation of ChunkLike."""
    
    # Core protocol fields
    id: str
    title: str
    heading_level: int
    text: str
    blocks: List[Dict[str, Any]] = field(default_factory=list)
    page_numbers: List[int] = field(default_factory=list)
    
    # Contract-specific fields
    contract_id: str = ""
    party: str = ""
    effective_date: Optional[datetime] = None
    clause_type: str = ""

    def to_dict(self, *, include_blocks: bool = True) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "title": self.title,
            "heading_level": self.heading_level,
            "text": self.text,
            "page_numbers": self.page_numbers,
            "contract_id": self.contract_id,
            "party": self.party,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "clause_type": self.clause_type,
        }
        if include_blocks:
            data["blocks"] = self.blocks
        return data
```

**Automatic Protocol Conformance:**

```python
from src.core.chunking.types import ChunkLike

contract_chunk = ContractChunk(
)

# Automatically conforms to ChunkLike
assert isinstance(contract_chunk, ChunkLike)  # ✅ True
```

---

## 📚 Related Documentation

- [Core Architecture](../../architecture.md) - Overall system architecture
- [Tender Domain](../domain/tender.md) - Tender-specific implementations
- [Infrastructure Layer](../infra/index.rst) - Infrastructure integrations
- [Indexing System](indexing.md) - How chunks are indexed

---

## 📖 API Reference

For detailed API documentation, see:

- {py:mod}`src.core.chunking.types` - Protocol definitions
- {py:mod}`src.core.chunking.chunking` - Token-based chunking
- {py:mod}`src.core.chunking.dynamic_chunker` - Heading-based chunking
- {py:mod}`src.domain.tender.schemas.chunking` - Tender implementations

---

**[⬅️ Core README](README.md) | [⬆️ Documentation Home](../index.rst) | [Embedding ➡️](embedding.md)**

*Last updated: 2025-12-18 - Protocol-based refactoring completed*
