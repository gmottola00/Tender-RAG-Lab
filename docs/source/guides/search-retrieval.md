# Search & Retrieval

> **Complete guide to querying indexed tender documents with hybrid search strategies**

This guide covers all search methods available in Tender-RAG-Lab: vector similarity, keyword search, and hybrid retrieval.

---

## Overview

Tender-RAG-Lab supports multiple search strategies:

- **Vector Search** - Semantic similarity using embeddings (Milvus)
- **Keyword Search** - Exact term matching with BM25
- **Hybrid Search** - Combines both methods with reranking

```text
┌──────────────┐
│ User Query   │
└──────┬───────┘
       │
       ├─────▶ Vector Search (Milvus)  ───┐
       │                                    │
       └─────▶ Keyword Search (BM25)   ────┤
                                            ▼
                                    ┌───────────────┐
                                    │   Reranker    │
                                    │ (merge results)│
                                    └───────┬───────┘
                                            │
                                            ▼
                                    ┌───────────────┐
                                    │ Final Results │
                                    └───────────────┘
```

---

## Quick Start

### Basic Semantic Search

```python
from src.domain.tender.services.search import TenderSearchService

search = TenderSearchService()

# Simple semantic search
results = search.search(
    query="What are the mandatory technical requirements?",
    top_k=5
)

for i, result in enumerate(results, 1):
    print(f"{i}. {result.text[:100]}...")
    print(f"   Score: {result.score:.3f}")
    print(f"   Source: {result.metadata['source_file']}\n")
```

### Search with Filters

```python
# Search within specific tender
results = search.search(
    query="budget constraints",
    top_k=10,
    filters={
        "tender_id": "TENDER-2025-001",
        "has_requirements": True
    }
)
```

---

## Search Strategies

### 1. Vector Search (Default)

Pure semantic similarity using embeddings:

```python
from src.domain.tender.search import TenderSearcher

searcher = TenderSearcher(
    vector_store=milvus_client,
    embedding_client=embedding_client
)

# Semantic search
results = searcher.vector_search(
    query="compliance requirements for data security",
    top_k=5,
    score_threshold=0.7  # Only return results with score > 0.7
)
```

**Best for:**
- Natural language queries
- Conceptual questions ("What is this tender about?")
- Synonym/paraphrase matching

**Example queries:**
```python
queries = [
    "What certifications are required?",
    "delivery timeline and milestones",
    "environmental sustainability criteria"
]
```

### 2. Keyword Search (BM25)

Exact term matching with TF-IDF weighting:

```python
# Keyword-based search
results = searcher.keyword_search(
    query="ISO 27001 AND GDPR",
    top_k=5
)
```

**Best for:**
- Specific terms (CIG codes, certification IDs)
- Boolean queries (AND, OR, NOT)
- Acronyms and technical jargon

**Example queries:**
```python
queries = [
    'CIG:"12345678AB"',
    "ISO 27001 OR ISO 9001",
    "ANAC compliance -optional"
]
```

### 3. Hybrid Search (Recommended)

Combines vector + keyword with reranking:

```python
# Hybrid search (best results)
results = searcher.hybrid_search(
    query="mandatory cybersecurity certifications ISO 27001",
    top_k=10,
    alpha=0.7  # 0.7 vector + 0.3 keyword
)
```

**Ranking formula:**
```
final_score = (alpha × vector_score) + ((1 - alpha) × keyword_score)
```

**Best for:**
- Production use cases
- Complex queries with both concepts and specific terms
- Maximum recall and precision

---

## Advanced Queries

### Query Rewriting

Automatically expand/clarify user queries:

```python
from src.domain.tender.services.query import QueryRewriter

rewriter = QueryRewriter(llm_client=llm)

# Original query
original = "What docs do I need?"

# Rewritten with context
rewritten = rewriter.rewrite(
    query=original,
    context="tender application requirements"
)
# → "What documentation is required for the tender application?"

results = search.search(query=rewritten, top_k=5)
```

### Multi-Query Fusion

Generate multiple query variations and merge results:

```python
# Generate query variations
queries = rewriter.generate_variations(
    query="submission deadlines",
    num_variations=3
)
# → [
#     "What are the submission deadlines?",
#     "When is the tender due?",
#     "Application deadline dates"
# ]

# Search with all variations
all_results = []
for q in queries:
    results = search.search(query=q, top_k=5)
    all_results.extend(results)

# Deduplicate and rerank
final_results = search.rerank(all_results, original_query="submission deadlines")
```

### Contextual Search

Search within previous results (chain queries):

```python
# First query
initial = search.search(
    query="technical requirements",
    top_k=10
)

# Narrow down results
refined = search.search(
    query="minimum server specifications",
    top_k=5,
    context_results=initial  # Search within these results only
)
```

---

## Filters and Metadata

### Filter by Tender

```python
results = search.search(
    query="budget breakdown",
    filters={"tender_id": "TENDER-2025-001"}
)
```

### Filter by Date Range

```python
from datetime import datetime, timedelta

# Tenders from last 30 days
cutoff = datetime.now() - timedelta(days=30)

results = search.search(
    query="infrastructure projects",
    filters={
        "upload_date": {"$gte": cutoff.isoformat()}
    }
)
```

### Filter by Entity Type

```python
# Only chunks with deadlines
results = search.search(
    query="submission process",
    filters={
        "has_deadlines": True,
        "entity_types": {"$contains": "deadline"}
    }
)
```

### Complex Filters

```python
# Multiple conditions
results = search.search(
    query="evaluation criteria",
    filters={
        "$and": [
            {"tender_id": {"$in": ["TENDER-2025-001", "TENDER-2025-002"]}},
            {"has_requirements": True},
            {"page_number": {"$lte": 50}}
        ]
    }
)
```

---

## RAG Pipeline (Retrieval + Generation)

Combine search with LLM generation for answers:

```python
from src.domain.tender.services.rag import TenderRAGService

rag = TenderRAGService(
    searcher=searcher,
    llm_client=llm
)

# Ask a question
response = rag.query(
    query="What are the mandatory requirements for this tender?",
    tender_id="TENDER-2025-001"
)

print(f"Answer: {response.answer}")
print(f"\nSources:")
for source in response.sources:
    print(f"  - {source.metadata['source_file']} (page {source.metadata['page_number']})")
```

### Streaming Responses

For better UX in web applications:

```python
# Stream answer token by token
for chunk in rag.query_stream(query="Explain the evaluation process"):
    print(chunk, end="", flush=True)
```

### Citation Tracking

Get exact source quotes:

```python
response = rag.query(
    query="What is the project budget?",
    include_citations=True
)

for citation in response.citations:
    print(f'"{citation.text}"')
    print(f"  → {citation.source} (score: {citation.score:.3f})\n")
```

---

## Performance Optimization

### Caching

Cache frequent queries:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query: str, tender_id: str):
    return search.search(query=query, filters={"tender_id": tender_id})

# Subsequent calls are instant
results1 = cached_search("requirements", "TENDER-2025-001")  # 200ms
results2 = cached_search("requirements", "TENDER-2025-001")  # <1ms
```

### Batch Queries

Process multiple queries efficiently:

```python
queries = [
    "budget constraints",
    "technical specifications",
    "submission deadlines"
]

# Batch search (parallel execution)
results = search.batch_search(
    queries=queries,
    top_k=5,
    filters={"tender_id": "TENDER-2025-001"}
)

for query, result_list in zip(queries, results):
    print(f"{query}: {len(result_list)} results")
```

### Index Optimization

Tune Milvus parameters for faster search:

```python
# Create optimized index
from pymilvus import Collection

collection = Collection("tender_documents")

# IVF_FLAT for speed/accuracy balance
collection.create_index(
    field_name="embedding",
    index_params={
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 1024}
    }
)
```

---

## Complete Example

End-to-end search workflow:

```python
from src.domain.tender.services.search import TenderSearchService
from src.infra.factory import create_tender_stack

# Initialize
stack = create_tender_stack()
search = TenderSearchService(
    searcher=stack.searcher,
    llm_client=stack.llm_client
)

def answer_tender_question(tender_id: str, question: str):
    """Complete RAG pipeline"""
    
    print(f"Question: {question}\n")
    
    # 1. Rewrite query
    print("1. Rewriting query...")
    rewritten = search.rewrite_query(question)
    print(f"   → {rewritten}\n")
    
    # 2. Hybrid search
    print("2. Searching documents...")
    results = search.hybrid_search(
        query=rewritten,
        top_k=10,
        filters={"tender_id": tender_id},
        alpha=0.7
    )
    print(f"   Found {len(results)} relevant chunks\n")
    
    # 3. Rerank
    print("3. Reranking results...")
    top_results = search.rerank(results, query=question, top_k=5)
    
    # 4. Generate answer
    print("4. Generating answer...\n")
    answer = search.generate_answer(
        query=question,
        context=top_results
    )
    
    print(f"Answer: {answer.text}\n")
    print("Sources:")
    for i, source in enumerate(answer.sources, 1):
        print(f"  {i}. {source.metadata['source_file']} (page {source.metadata['page_number']})")
        print(f"     Score: {source.score:.3f}")
        print(f"     \"{source.text[:100]}...\"")
    
    return answer

# Usage
answer = answer_tender_question(
    tender_id="TENDER-2025-001",
    question="What are the minimum technical requirements for server infrastructure?"
)
```

---

## Troubleshooting

### No Results Found

```python
# Check if documents are indexed
from pymilvus import Collection

collection = Collection("tender_documents")
print(f"Total documents: {collection.num_entities}")

# Try relaxing filters
results = search.search(
    query="budget",
    score_threshold=0.5,  # Lower threshold
    top_k=20  # More results
)
```

### Poor Result Quality

```python
# Analyze query embedding
query_vec = embedding_client.embed(query)

# Check embedding quality
print(f"Query embedding norm: {np.linalg.norm(query_vec)}")

# Try different search strategy
results_vector = search.vector_search(query, top_k=10)
results_hybrid = search.hybrid_search(query, top_k=10, alpha=0.5)

print(f"Vector only: {len(results_vector)} results")
print(f"Hybrid: {len(results_hybrid)} results")
```

### Slow Queries

```python
import time

start = time.time()
results = search.search(query="requirements", top_k=5)
duration = time.time() - start

print(f"Search took {duration:.2f}s")

if duration > 1.0:
    print("Consider:")
    print("  - Reduce top_k")
    print("  - Add more specific filters")
    print("  - Optimize Milvus index (IVF_FLAT → HNSW)")
```

---

## Related Documentation

- [Indexing Documents](indexing-documents.md) - Upload and index documents
- [rag_toolkit Integration](../rag_toolkit/index.rst) - Generic search components
- [Domain Layer](../domain/README.md) - Tender-specific search logic
