# 🧩 Core Layer: Indexing

> **Vector search, keyword search, and hybrid retrieval**

The indexing module provides high-level abstractions for storing and searching document chunks.

---

## 📍 Location

**Directory:** `src/core/index/`

**Structure:**
```
src/core/index/
├── tender_indexer.py    # IndexService - high-level indexing
├── tender_searcher.py   # Search orchestration
└── search/
    ├── vector_searcher.py   # Vector similarity search
    ├── keyword_searcher.py  # BM25 keyword search
    ├── hybrid_searcher.py   # Combined strategy
    └── reranker.py          # Re-score results
└── vector/
    ├── database.py      # VectorStore Protocol
    ├── service.py       # Vector operations
    └── ...
```

---

## 🎯 Purpose

**What indexing does:**
- Store document chunks with embeddings
- Semantic search (vector similarity)
- Keyword search (BM25)
- Hybrid retrieval (combine strategies)
- Re-ranking results

**Core abstraction:** Store and retrieve documents, vendor-agnostic.

---

## 🏗️ Architecture

### Key Protocols

#### VectorStore Protocol

```python
class VectorStore(Protocol):
    """Abstract vector database"""
    
    async def insert(
        self,
        vectors: list[list[float]],
        texts: list[str],
        metadata: list[dict]
    ) -> list[str]:
        """Insert vectors with metadata → returns IDs"""
        ...
    
    async def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict | None = None
    ) -> list[SearchResult]:
        """Vector similarity search"""
        ...
    
    async def hybrid_search(
        self,
        query_vector: list[float],
        query_text: str,
        top_k: int = 10
    ) -> list[SearchResult]:
        """Combine vector + keyword search"""
        ...
```

**Layer:** Core abstraction

**Implementation:** `MilvusVectorStore` in `src/infra/vectorstores/`

---

#### SearchStrategy Protocol

```python
class SearchStrategy(Protocol):
    """Abstract search strategy"""
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict | None = None
    ) -> list[SearchResult]:
        """Execute search"""
        ...
```

**Implementations:**
- `VectorSearchStrategy` - Semantic similarity
- `KeywordSearchStrategy` - BM25 full-text
- `HybridSearchStrategy` - Combined (RRF fusion)

---

## 📦 IndexService

High-level service for indexing and searching.

### Core Methods

```python
class IndexService:
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_client: EmbeddingClient
    ):
        self._store = vector_store
        self._embed = embedding_client
    
    async def index_documents(
        self,
        chunks: list[Chunk],
        collection_name: str
    ) -> int:
        """Index document chunks → returns count"""
        ...
    
    async def search(
        self,
        query: str,
        collection_name: str,
        top_k: int = 10,
        strategy: str = "hybrid"
    ) -> list[SearchResult]:
        """Search with specified strategy"""
        ...
    
    async def delete_by_filter(
        self,
        collection_name: str,
        filters: dict
    ) -> int:
        """Delete documents matching filters"""
        ...
```

---

## 🔍 Search Strategies

### 1. Vector Search (Semantic)

**How it works:**
1. Embed query text → vector
2. Find nearest neighbors (cosine/IP similarity)
3. Return top-k results

**Strengths:**
- ✅ Semantic understanding
- ✅ Handles synonyms ("requisiti" = "requirements")
- ✅ Cross-language (IT query finds EN docs)

**Weaknesses:**
- ❌ Misses exact keyword matches
- ❌ Poor for rare terms (e.g., "CIG: 12345")

**Example:**
```python
from src.core.index.search_strategies import VectorSearch

strategy = VectorSearchStrategy(
    vector_store=vector_store,
    embedding_client=embed_client
)

results = await strategy.search(
    query="requisiti tecnici per la partecipazione",
    top_k=10
)
```

---

### 2. Keyword Search (BM25)

**How it works:**
1. Tokenize query → keywords
2. BM25 scoring (term frequency + inverse doc frequency)
3. Return top-k results

**Strengths:**
- ✅ Exact keyword matches
- ✅ Great for codes/IDs (CIG, CUP)
- ✅ Fast (no embedding needed)

**Weaknesses:**
- ❌ No semantic understanding
- ❌ Misses synonyms
- ❌ Language-specific

**Example:**
```python
from src.core.index.search_strategies import KeywordSearch

strategy = KeywordSearchStrategy(vector_store=vector_store)

results = await strategy.search(
    query="CIG 9876543210",
    top_k=10
)
```

---

### 3. Hybrid Search (Best of Both)

**How it works:**
1. Run vector search → results_v
2. Run keyword search → results_k
3. Fuse with RRF (Reciprocal Rank Fusion)
4. Return merged top-k

**Strengths:**
- ✅ Best quality (semantic + exact match)
- ✅ Handles all query types
- ✅ Robust to query phrasing

**Weaknesses:**
- ⚠️ Slightly slower (2 searches)
- ⚠️ Tuning required (weight balance)

**Example:**
```python
from src.core.index.search_strategies import HybridSearch

strategy = HybridSearchStrategy(
    vector_store=vector_store,
    embedding_client=embed_client,
    vector_weight=0.6,  # 60% vector, 40% keyword
    keyword_weight=0.4
)

results = await strategy.search(
    query="tender for IT services in Milan",
    top_k=10
)
```

**RRF Formula:**
```
score(doc) = Σ [ 1 / (k + rank_i) ]
```
where `rank_i` is doc's rank in search i, `k=60` (constant)

---

## 🎯 Usage Examples

### Example 1: Index Documents

```python
from src.core.index import IndexService
from src.infra.factories import get_index_service

service = get_index_service()

# Prepare chunks
chunks = [
    Chunk(
        text="Requisiti tecnici: esperienza minima 5 anni",
        metadata={"doc_id": "tender-123", "page": 3}
    ),
    Chunk(
        text="Budget: 500.000 EUR",
        metadata={"doc_id": "tender-123", "page": 5}
    )
]

# Index
count = await service.index_documents(
    chunks=chunks,
    collection_name="tender_chunks"
)

print(f"Indexed {count} chunks")
```

---

### Example 2: Semantic Search

```python
# Find semantically similar chunks
results = await service.search(
    query="quali sono i requisiti per partecipare?",
    collection_name="tender_chunks",
    top_k=5,
    strategy="vector"
)

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Text: {result.text[:100]}...")
    print(f"Metadata: {result.metadata}")
    print("---")
```

---

### Example 3: Filter by Metadata

```python
# Search within specific tender
results = await service.search(
    query="budget information",
    collection_name="tender_chunks",
    top_k=10,
    filters={"doc_id": "tender-123"}  # Only this tender
)
```

**Milvus filter syntax:**
```python
filters = {
    "doc_id": "tender-123",              # Exact match
    "page": {"$gte": 5},                 # Page >= 5
    "language": {"$in": ["it", "en"]},   # Italian or English
}
```

---

### Example 4: Delete Documents

```python
# Delete all chunks from a tender
deleted = await service.delete_by_filter(
    collection_name="tender_chunks",
    filters={"doc_id": "tender-123"}
)

print(f"Deleted {deleted} chunks")
```

---

## 🔄 Re-ranking

**Purpose:** Improve result quality by re-scoring with more expensive model.

### Process

1. **Initial retrieval:** Fast search (top-100)
2. **Re-ranking:** Expensive model (top-10)
3. **Final results:** Best 10 after re-ranking

### Reranker Protocol

```python
class Reranker(Protocol):
    """Abstract re-ranker"""
    
    async def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int = 10
    ) -> list[SearchResult]:
        """Re-score and filter results"""
        ...
```

**Implementations:**
- `CrossEncoderReranker` - Sentence transformer
- `LLMReranker` - Use LLM for relevance scoring

### Example

```python
from src.core.rag.rerankers import CrossEncoderReranker

reranker = CrossEncoderReranker(model="cross-encoder/ms-marco-MiniLM-L-6-v2")

# Initial search (top-100)
results = await service.search(query, top_k=100)

# Re-rank to top-10
final_results = await reranker.rerank(
    query=query,
    results=results,
    top_k=10
)
```

**Performance:**
- Initial search: ~50ms (fast)
- Re-ranking: ~200ms (10x slower)
- Total: ~250ms (acceptable for top-10)

---

## 📊 Performance Tuning

### Vector Search Tuning

**Milvus HNSW parameters:**

| Parameter | Default | Effect |
|-----------|---------|--------|
| `M` | 24 | Connections per node (higher = better quality, slower) |
| `efConstruction` | 200 | Build quality (higher = better index, slower build) |
| `ef` | 100 | Search quality (higher = better recall, slower search) |

**Example configuration:**
```python
# High quality, slower
index_params = {"M": 32, "efConstruction": 300}
search_params = {"ef": 200}

# Fast, lower quality
index_params = {"M": 16, "efConstruction": 100}
search_params = {"ef": 50}
```

**See:** [Milvus Setup](../infra/milvus.md) for complete tuning guide.

---

### Hybrid Search Tuning

**Weight adjustment:**

```python
# More semantic, less exact match
HybridSearchStrategy(vector_weight=0.8, keyword_weight=0.2)

# Balanced
HybridSearchStrategy(vector_weight=0.6, keyword_weight=0.4)

# More exact match, less semantic
HybridSearchStrategy(vector_weight=0.4, keyword_weight=0.6)
```

**Guidelines:**
- Technical docs (codes, IDs) → higher keyword weight
- Natural language queries → higher vector weight
- General use → 60/40 split

---

## 🐛 Common Issues

### Issue: Low Recall

**Symptom:** Relevant documents not returned

**Solutions:**
1. **Increase top_k:**
   ```python
   results = await service.search(query, top_k=50)  # Instead of 10
   ```

2. **Use hybrid search:**
   ```python
   strategy="hybrid"  # Instead of "vector"
   ```

3. **Lower similarity threshold:**
   ```python
   # Return results with lower scores
   results = [r for r in results if r.score > 0.3]  # Instead of 0.5
   ```

4. **Check embedding quality:**
   - Use better embedding model
   - Improve chunking strategy

---

### Issue: Slow Search

**Symptom:** Search takes >1 second

**Solutions:**
1. **Reduce top_k:**
   ```python
   top_k=10  # Instead of 100
   ```

2. **Optimize index params:**
   ```python
   search_params = {"ef": 50}  # Lower ef value
   ```

3. **Use vector-only:**
   ```python
   strategy="vector"  # Faster than hybrid
   ```

4. **Add filters early:**
   ```python
   filters={"doc_id": "tender-123"}  # Reduce search space
   ```

---

### Issue: Duplicate Results

**Symptom:** Same chunk appears multiple times

**Solutions:**
1. **Deduplicate by ID:**
   ```python
   seen = set()
   unique_results = []
   for r in results:
       if r.id not in seen:
           unique_results.append(r)
           seen.add(r.id)
   ```

2. **Check chunking overlap:**
   - High overlap → similar chunks indexed
   - Reduce overlap parameter

---

## 🛠️ Implementation Details

### SearchResult Schema

```python
@dataclass
class SearchResult:
    id: str                  # Chunk ID in vector DB
    text: str                # Chunk content
    score: float             # Similarity score (0-1)
    metadata: dict           # {doc_id, page, language, ...}
    vector: list[float] | None = None  # Optional embedding
```

### Batch Operations

**Efficient bulk indexing:**
```python
BATCH_SIZE = 100

for i in range(0, len(chunks), BATCH_SIZE):
    batch = chunks[i:i+BATCH_SIZE]
    await service.index_documents(batch, collection_name)
```

**Progress tracking:**
```python
from tqdm import tqdm

for i in tqdm(range(0, len(chunks), BATCH_SIZE)):
    batch = chunks[i:i+BATCH_SIZE]
    await service.index_documents(batch, collection_name)
```

---

## 🚀 Adding a New Search Strategy

**Example:** Add graph-based search.

### 1. Implement Protocol

```python
# src/core/index/search/graph_searcher.py
from src.core.index.base import SearchStrategy

class GraphSearchStrategy:
    """Graph-based search with node relationships"""
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict | None = None
    ) -> list[SearchResult]:
        # 1. Find initial nodes (vector search)
        initial = await self._vector_search(query, top_k=50)
        
        # 2. Expand graph (find connected chunks)
        expanded = await self._expand_graph(initial)
        
        # 3. Score by centrality
        scored = self._score_by_centrality(expanded)
        
        return scored[:top_k]
```

### 2. Use in IndexService

```python
# src/core/index/tender_searcher.py
if strategy == "graph":
    search_strategy = GraphSearchStrategy(...)
    return await search_strategy.search(query, top_k)
```

---

## 📚 Related Documentation

- [Core Layer Overview](README.md)
- [Embedding Module](embedding.md) - Generate query vectors
- [RAG Pipeline](rag.md) - Uses indexing for retrieval
- [Milvus Setup](../infra/milvus.md) - Vector database config

---

**[⬅️ LLM](llm.md) | [⬆️ Documentation Home](../README.md) | [Ingestion ➡️](ingestion.md)**

*Last updated: 2025-12-18*
