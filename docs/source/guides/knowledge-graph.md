# Knowledge Graph (Neo4j)

The Tender-RAG-Lab system uses Neo4j as a Knowledge Graph to store structured tender entities and their relationships, enabling graph-based reasoning alongside vector search.

## Overview

The Knowledge Graph complements the vector store (Milvus) by maintaining explicit relationships between:

- **Tenders** and their metadata (buyer, CPV code, amount, dates)
- **Chunks** from tender documents
- **Lots** (sub-tenders)
- **Requirements** (technical, economic, administrative)
- **Deadlines** (submission, clarification, award)
- **Organizations** (buyers, suppliers)

## Quick Start

### 1. Start Neo4j

```bash
# Start Neo4j container
docker-compose up -d neo4j

# Wait for initialization (~30 seconds)
docker logs -f tender-neo4j
```

### 2. Initialize Schema

```bash
# Run setup script
uv run python scripts/setup_neo4j.py
```

This creates:
- ✅ Uniqueness constraints (tender codes, chunk IDs)
- ✅ Performance indexes (CPV codes, buyer names, dates)
- ✅ Test data and validation

### 3. Access Neo4j Browser

Open [http://localhost:7474](http://localhost:7474)

**Credentials:**
- Username: `neo4j`
- Password: `tendergraph2025`

## Architecture

### Graph Structure

```
Tender (CIG code)
  ├─ HAS_CHUNK ──> Chunk (document sections)
  ├─ HAS_LOT ────> Lot (sub-tenders)
  ├─ HAS_REQUIREMENT ──> Requirement
  ├─ HAS_DEADLINE ────> Deadline
  └─ PUBLISHED_BY ───> Organization (buyer)
```

### Integration with RAG Pipeline

```
Document Ingestion:
  PDF → Chunks → Embeddings → Milvus (vector)
                            ↘ Neo4j (graph metadata)

Query Processing:
  Question → Vector Search (Milvus)
          ↘ Graph Context (Neo4j)
          → Enriched Results → LLM
```

## Usage Patterns

### Pattern 1: Index Tender with Graph

```python
from src.infra.graph.graph_indexer import index_tender_to_graph

# After indexing to Milvus, also index to graph
await index_tender_to_graph(
    tender_code="2025-001-IT",
    tender_metadata={
        "title": "IT Infrastructure Services",
        "cpv_code": "72000000",
        "base_amount": 500000.0,
        "buyer_name": "Ministero dell'Interno",
        "publication_date": "2025-01-15"
    },
    chunks=chunks  # Already indexed to Milvus
)
```

### Pattern 2: Enrich Search Results

```python
from src.infra.graph.graph_indexer import get_tender_context_for_chunks

# After vector search
vector_results = await milvus_search(query, top_k=10)

# Get graph context
chunk_ids = [r.id for r in vector_results]
contexts = await get_tender_context_for_chunks(chunk_ids)

# Enrich results with tender metadata
for result in vector_results:
    context = contexts.get(result.id)
    if context:
        result.tender_title = context["tender_title"]
        result.buyer_name = context["buyer_name"]
        result.base_amount = context["base_amount"]
```

### Pattern 3: Find Related Tenders

```python
from src.infra.graph.graph_indexer import find_related_tenders

# Find tenders with similar CPV code or same buyer
related = await find_related_tenders(
    tender_code="2025-001-IT",
    limit=5
)

# Use for query expansion or recommendations
for tender in related:
    print(f"{tender['code']}: {tender['title']}")
    print(f"  Similarity: {tender['similarity_score']}")
```

## Configuration

### Local Development (Docker)

```bash
# .env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=tendergraph2025
NEO4J_DATABASE=neo4j
NEO4J_ENV=local
```

### Production (Neo4j Aura Cloud)

```bash
# .env
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-secure-password
NEO4J_DATABASE=neo4j
NEO4J_ENV=aura
```

The client automatically detects the environment based on the URI scheme:
- `bolt://` → Local mode (unencrypted)
- `neo4j+s://` → Aura mode (TLS encrypted)

## Next Steps

- See [Neo4j Setup](neo4j-setup.md) for detailed configuration
- See [Neo4j Integration](neo4j-integration.md) for advanced RAG patterns
- Try the examples: `uv run python examples/graph_integration_examples.py`

## Reference

```{toctree}
:maxdepth: 1

neo4j-setup
neo4j-integration
```
