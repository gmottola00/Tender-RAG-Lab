# 🔍 Domain: Tender Search

> **Tender-specific search implementations combining vector, keyword, and hybrid strategies**

This module provides domain-specific search functionality for tender documents, orchestrating core RAG components with tender business logic.

---

## 📍 Location

**Directory:** `src/domain/tender/search/`

**Files:**
- `vector_searcher.py` - Vector/semantic search
- `keyword_searcher.py` - Keyword/lexical search
- `reranker.py` - Result reranking interface
- `hybrid_searcher.py` - Combines vector + keyword
- `searcher.py` - High-level orchestrator

---

## 🏗️ Architecture

These search components are **domain-specific** because they:
- Use `TenderMilvusIndexer` (tender document indexing)
- Work with tender-specific metadata (tender_id, lot_id)
- Orchestrate core components for tender use cases
- Not reusable without modification for other domains

```
┌─────────────────────────────────────┐
│   Domain Layer (Tender-Specific)   │
│  src/domain/tender/search/          │
│  ┌────────────────────────────┐    │
│  │  TenderSearcher            │    │
│  │  ├─ VectorSearcher         │    │
│  │  ├─ KeywordSearcher        │    │
│  │  └─ HybridSearcher         │    │
│  └────────────────────────────┘    │
└─────────────────────────────────────┘
           ↓ Uses
┌─────────────────────────────────────┐
│     Core Layer (Generic RAG)        │
│  - EmbeddingClient Protocol         │
│  - TenderMilvusIndexer              │
└─────────────────────────────────────┘
```

---

## 🔌 Components

### Vector Searcher

**Location:** `src/domain/tender/search/vector_searcher.py`

Semantic search using embeddings.

```python
from src.domain.tender.search import VectorSearcher
from src.core.embedding import EmbeddingClient
from src.domain.tender.indexing.indexer import TenderMilvusIndexer

# Initialize
indexer = TenderMilvusIndexer(...)
embed_client = EmbeddingClient(...)
searcher = VectorSearcher(indexer, embed_client)

# Search
results = searcher.search(
    query="renewable energy requirements",
    top_k=5
)

# Results format
[
    {
        "score": 0.89,
        "text": "chunk text...",
        "section_path": "Requirements > Energy",
        "metadata": {...},
        "page_numbers": [12, 13],
        "source_chunk_id": "uuid...",
        "id": 123
    }
]
```

---

### Keyword Searcher

**Location:** `src/domain/tender/search/keyword_searcher.py`

Lexical search using LIKE expressions on Milvus.

```python
from src.domain.tender.search import KeywordSearcher

# Initialize
searcher = KeywordSearcher(indexer)

# Search
results = searcher.search(
    query="ISO 27001 certification",
    top_k=5
)
```

**How it works:**
- Splits query into terms
- Builds `text LIKE "%term1%" AND text LIKE "%term2%"` expression
- Queries Milvus directly (no embeddings needed)
- Returns matching chunks

---

### Hybrid Searcher

**Location:** `src/domain/tender/search/hybrid_searcher.py`

Combines vector + keyword search with optional reranking.

```python
from src.domain.tender.search import HybridSearcher

# Initialize
hybrid = HybridSearcher(
    vector_searcher=vector_searcher,
    keyword_searcher=keyword_searcher,
    reranker=None,  # Optional
    alpha=0.7  # Weight: 0.7 vector + 0.3 keyword
)

# Search
results = hybrid.search(
    query="cybersecurity requirements",
    top_k=5
)
```

**Merging Logic:**
1. Run vector search → get scored results
2. Run keyword search → get matches
3. Merge by `alpha` weighting:
   - Vector score normalized × `alpha`
   - Keyword match gets `(1 - alpha)`
4. Optional reranking with cross-encoder
5. Return top-k

---

### Reranker

**Location:** `src/domain.tender.search/reranker.py`

Interface for result reranking (e.g., cross-encoder).

```python
from src.domain.tender.search import Reranker, IdentityReranker

# Protocol
class Reranker(Protocol):
    def rerank(
        self, 
        query: str, 
        candidates: List[Dict], 
        top_k: int
    ) -> List[Dict]:
        ...

# Default: no reranking
reranker = IdentityReranker()
```

**Custom Reranker:**
```python
class CrossEncoderReranker(Reranker):
    def __init__(self, model_name: str):
        self.model = CrossEncoder(model_name)
    
    def rerank(self, query, candidates, top_k):
        pairs = [(query, c["text"]) for c in candidates]
        scores = self.model.predict(pairs)
        # Sort by score, return top-k
        ...
```

---

### Tender Searcher

**Location:** `src/domain/tender/search/searcher.py`

High-level orchestrator exposing all search modes.

```python
from src.domain.tender.search import TenderSearcher

# Initialize
searcher = TenderSearcher(indexer, embed_client)

# Vector search
results = searcher.vector_search("query", top_k=5)

# Keyword search
results = searcher.keyword_search("query", top_k=5)

# Hybrid search
results = searcher.hybrid_search("query", top_k=5)
```

**Benefits:**
- Single interface for all search modes
- Manages searcher initialization
- Used by RAG pipeline and API endpoints

---

## 🎯 Usage in RAG Pipeline

```python
from src.domain.tender.search import TenderSearcher
from src.core.rag import RAGPipeline

# Setup
searcher = TenderSearcher(indexer, embed_client)

# RAG Pipeline
pipeline = RAGPipeline(
    retriever=searcher.hybrid_search,  # Use hybrid
    llm=llm_client,
    reranker=None
)

# Query
answer = pipeline.query("What are the energy requirements?")
```

---

## 🔄 Migration from Old Structure

**Before (Old):**
```python
# ❌ Was in core layer (wrong)
from src.core.index.search.vector_searcher import VectorSearcher
from src.core.index.search.keyword_searcher import KeywordSearcher
from src.core.index.search.hybrid_searcher import HybridSearcher
```

**After (New):**
```python
# ✅ Now in domain layer (correct)
from src.domain.tender.search import VectorSearcher
from src.domain.tender.search import KeywordSearcher
from src.domain.tender.search import HybridSearcher
```

**Why the move?**
- These classes are **tender-specific** (use TenderMilvusIndexer, DocumentORM)
- Not generic RAG components (can't reuse for other domains)
- Domain layer is the correct home per Clean Architecture

---

## 📊 Comparison with Search Strategies

| Component | Location | Purpose | Reusability |
|-----------|----------|---------|-------------|
| `VectorSearcher` | `domain/tender/search/` | Tender vector search | Tender-specific |
| `KeywordSearcher` | `domain/tender/search/` | Tender keyword search | Tender-specific |
| `HybridSearcher` | `domain/tender/search/` | Tender hybrid search | Tender-specific |
| `VectorSearch` | `core/index/search_strategies.py` | Generic vector search | Reusable Protocol |
| `KeywordSearch` | `core/index/search_strategies.py` | Generic keyword search | Reusable Protocol |
| `HybridSearch` | `core/index/search_strategies.py` | Generic hybrid search | Reusable Protocol |

**Key Difference:** 
- Domain classes = concrete implementations for tender use case
- Core strategies = abstract Protocols for any domain

---

## 🛠️ Testing

```python
# Test vector search
def test_vector_search():
    searcher = VectorSearcher(indexer, embed_client)
    results = searcher.search("test query", top_k=3)
    assert len(results) <= 3
    assert all("score" in r for r in results)

# Test keyword search
def test_keyword_search():
    searcher = KeywordSearcher(indexer)
    results = searcher.search("ISO 27001", top_k=5)
    assert all("text" in r for r in results)

# Test hybrid
def test_hybrid_search():
    hybrid = HybridSearcher(vec_searcher, kw_searcher, alpha=0.6)
    results = hybrid.search("security", top_k=10)
    assert len(results) <= 10
```

---

## 📚 See Also

- [Core Indexing](../core/indexing.md) - Generic search strategies
- [RAG Pipeline](../core/rag.md) - Using search in RAG
- [Milvus Vector Store](../infra/milvus.md) - Backend storage
- [Architecture Overview](../architecture/overview.md) - Layer separation
