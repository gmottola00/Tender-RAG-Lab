# 🧩 Core Layer: Chunking

> **Split documents into optimal chunks for embedding and retrieval**

The chunking module provides strategies for breaking documents into semantically meaningful chunks.

---

## 📍 Location

**Directory:** `src/core/chunking/`

**Files:**
- `chunking.py` - Base Protocol + simple chunker
- `dynamic_chunker.py` - Advanced semantic chunking

---

## 🎯 Purpose

**Why chunking matters:**
- Embeddings work best on focused, coherent text units
- Too small = loss of context
- Too large = diluted relevance scores
- Dynamic chunking adapts to document structure

**Core abstraction:** Split text while preserving semantic coherence.

---

## 🏗️ Architecture

### Protocol

```python
class DocumentChunker(Protocol):
    """Abstract chunking strategy"""
    def chunk(self, text: str, metadata: dict) -> list[ChunkResult]
```

**Layer:** Core (pure abstraction)

**Implementations:**
- `TokenChunker` - Fixed-size chunks with overlap
- `DynamicChunker` - Semantic boundary detection

---

## 📦 TokenChunker

**Strategy:** Fixed-size chunks with sliding window overlap.

### When to Use

✅ **Good for:**
- Consistent chunk sizes
- Simple documents (plain text, logs)
- Quick experimentation
- Cost control (predictable token usage)

❌ **Avoid for:**
- Documents with structure (sections, lists)
- Legal/technical docs (breaks context)
- Multi-language (splits mid-sentence)

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `chunk_size` | 512 | Max tokens per chunk |
| `overlap` | 128 | Overlapping tokens between chunks |
| `encoding` | `cl100k_base` | Tokenizer (for OpenAI) |

### Example Usage

```python
from src.core.chunking import TokenChunker

chunker = TokenChunker(chunk_size=512, overlap=128)
chunks = chunker.chunk(
    text="Long document...",
    metadata={"doc_id": "tender-123"}
)

for chunk in chunks:
    print(f"Chunk {chunk.index}: {chunk.text[:50]}...")
    print(f"Tokens: {chunk.metadata['token_count']}")
```

---

## 🧠 DynamicChunker

**Strategy:** Semantic boundary detection using embeddings and heuristics.

### How It Works

1. **Split into sentences** (using `nltk`)
2. **Compute sentence embeddings**
3. **Detect semantic breaks** (cosine similarity drops)
4. **Respect structural boundaries** (headings, lists)
5. **Merge small chunks** (enforce min size)

### When to Use

✅ **Good for:**
- Structured documents (PDFs with sections)
- Italian tender documents (respects "Art.", "Lotto")
- Preserving context (doesn't split mid-topic)
- High-quality retrieval (semantic coherence)

❌ **Avoid for:**
- Simple plain text
- High-volume batch processing (slower)
- Tight latency requirements

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_chunk_size` | 200 | Minimum tokens per chunk |
| `max_chunk_size` | 800 | Maximum tokens per chunk |
| `similarity_threshold` | 0.65 | Cosine threshold for splits |
| `structural_markers` | Italian keywords | Heading detection (`Art.`, `Lotto`) |

### Example Usage

```python
from src.core.chunking import DynamicChunker
from src.infra.factories import get_embedding_client

embed_client = get_embedding_client()
chunker = DynamicChunker(
    embedding_client=embed_client,
    min_chunk_size=200,
    max_chunk_size=800
)

chunks = chunker.chunk(
    text="Art. 1 - Oggetto...\nArt. 2 - Requisiti...",
    metadata={"doc_id": "tender-456", "language": "it"}
)
```

**Structural detection:**
- Detects Italian tender sections (`Art.`, `Lotto`, `Allegato`)
- Preserves lists and tables
- Avoids mid-sentence splits

---

## 🔬 Comparison

| Feature | TokenChunker | DynamicChunker |
|---------|--------------|----------------|
| **Speed** | ⚡ Fast (no embeddings) | 🐢 Slower (embeddings + NLP) |
| **Quality** | 📄 Basic (fixed splits) | 🎯 High (semantic coherence) |
| **Consistency** | ✅ Predictable sizes | ⚠️ Variable sizes |
| **Structure Awareness** | ❌ Ignores structure | ✅ Respects boundaries |
| **Best For** | Simple docs, speed | Tender PDFs, quality |

---

## 🛠️ Implementation Details

### ChunkResult Schema

```python
@dataclass
class ChunkResult:
    text: str              # Chunk content
    index: int             # Chunk position (0-indexed)
    metadata: dict         # {token_count, start_idx, end_idx, ...}
```

### Token Counting

Uses `tiktoken` library:
- `cl100k_base` encoding (OpenAI models)
- UTF-8 aware (handles Italian text)
- Consistent with OpenAI API

### Overlap Strategy (TokenChunker)

**Example:** `chunk_size=512`, `overlap=128`

```
Chunk 1: [tokens 0-511]
Chunk 2: [tokens 384-895]  ← overlaps last 128 tokens
Chunk 3: [tokens 768-1279] ← overlaps last 128 tokens
```

**Why overlap?**
- Prevents context loss at boundaries
- Improves retrieval recall
- Helps with sentence fragments

---

## 🚀 Adding a New Chunker

### 1. Implement Protocol

```python
# src/core/chunking/my_chunker.py
from src.core.chunking import DocumentChunker, ChunkResult

class MyCustomChunker:
    def chunk(self, text: str, metadata: dict) -> list[ChunkResult]:
        # Your logic here
        return chunks
```

**Core layer:** No external dependencies (use only stdlib + protocols).

### 2. Add to Factory

```python
# src/infra/factories/chunking_factory.py
def get_chunker(strategy: str) -> DocumentChunker:
    if strategy == "custom":
        return MyCustomChunker(...)
```

**Infra layer:** Wiring and configuration.

### 3. Configuration

```python
# configs/config.py
CHUNKING_STRATEGY = "custom"  # or "token", "dynamic"
```

**See:** [Adding Integrations](../infra/adding-integrations.md) for complete guide.

---

## 📊 Performance Tuning

### TokenChunker

**Increase throughput:**
- Larger `chunk_size` (fewer chunks)
- Smaller `overlap` (less redundancy)

**Improve quality:**
- Smaller `chunk_size` (more focused)
- Larger `overlap` (better context)

### DynamicChunker

**Speed up:**
- Increase `min_chunk_size` (fewer splits)
- Reduce `similarity_threshold` (less sensitive)
- Cache sentence embeddings (if processing similar docs)

**Improve quality:**
- Lower `similarity_threshold` (more splits)
- Add domain-specific `structural_markers`
- Use better embedding model

---

## 🐛 Common Issues

### Issue: Chunks Too Small

**Symptom:** Many chunks < 100 tokens

**Solutions:**
- Increase `min_chunk_size`
- Reduce `similarity_threshold` (DynamicChunker)
- Check document quality (OCR errors?)

### Issue: Context Loss

**Symptom:** Retrieval misses relevant info

**Solutions:**
- Increase `overlap` (TokenChunker)
- Lower `similarity_threshold` (DynamicChunker)
- Use DynamicChunker instead of TokenChunker

### Issue: Slow Chunking

**Symptom:** Takes >5s per document

**Solutions:**
- Switch to TokenChunker
- Increase `min_chunk_size` (fewer chunks)
- Use faster embedding model (e.g., Ollama)

---

## 📚 Related Documentation

- [Core Layer Overview](README.md)
- [Embedding Module](embedding.md) - Embed chunks
- [Ingestion Service](../domain/ingestion.md) - Uses chunking
- [Adding Integrations](../infra/adding-integrations.md) - Custom chunkers

---

**[⬅️ Core README](README.md) | [⬆️ Documentation Home](../README.md) | [Embedding ➡️](embedding.md)**

*Last updated: 2025-12-18*
