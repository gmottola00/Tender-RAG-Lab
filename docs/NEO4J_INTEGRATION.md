# Neo4j Knowledge Graph Integration for Advanced RAG

**Complete guide for integrating Neo4j Knowledge Graph in a production-grade Tender RAG system**

## 📚 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Phase 1: Schema & Data Model](#phase-1-schema--data-model)
3. [Phase 2: Ingestion Pipeline](#phase-2-ingestion-pipeline)
4. [Phase 3: Graph-Enhanced Retrieval](#phase-3-graph-enhanced-retrieval)
5. [Phase 4: Context Assembly](#phase-4-context-assembly)
6. [Phase 5: Advanced Graph Queries](#phase-5-advanced-graph-queries)
7. [Production Considerations](#production-considerations)

---

## Architecture Overview

### Knowledge Graph Structure

```
Tender (CIG: unique code)
  ├─ HAS_CHUNK ──> Chunk (from document)
  ├─ HAS_LOT ────> Lot (sub-tenders)
  ├─ HAS_REQUIREMENT ──> Requirement (technical/economic)
  ├─ HAS_DEADLINE ────> Deadline (submission dates)
  └─ PUBLISHED_BY ───> Organization (buyer)

Chunk
  ├─ text_preview (first 200 chars)
  ├─ page_number
  ├─ chunk_index
  ├─ section_type (requirements, evaluation, etc.)
  └─ tender_id (link back to parent)
```

### Integration Points in RAG Pipeline

```
PDF Document
    ↓
[1. Chunking] → TenderTokenChunk (semantic chunks)
    ↓
[2. Embedding] → Milvus (vector store)
    ↓                    ↓
[3. Graph Indexing] → Neo4j (knowledge graph)
    ↓                    ↓
[Query] → Vector Search + Graph Context
    ↓
[4. Assembly] → Enriched Context for LLM
    ↓
[Generation] → Answer with citations
```

---

## Phase 1: Schema & Data Model

### 1.1 Neo4j Schema Setup

**Constraints (Uniqueness):**
```cypher
CREATE CONSTRAINT tender_code_unique IF NOT EXISTS
FOR (t:Tender) REQUIRE t.code IS UNIQUE;

CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS
FOR (c:Chunk) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT lot_id_unique IF NOT EXISTS
FOR (l:Lot) REQUIRE l.id IS UNIQUE;
```

**Indexes (Query Performance):**
```cypher
CREATE INDEX tender_cpv IF NOT EXISTS
FOR (t:Tender) ON (t.cpv_code);

CREATE INDEX tender_buyer IF NOT EXISTS
FOR (t:Tender) ON (t.buyer_name);

CREATE INDEX chunk_section_type IF NOT EXISTS
FOR (c:Chunk) ON (c.section_type);
```

### 1.2 Tender Domain Model

**Core Entities:**

```python
# Tender Node
{
    code: str            # CIG (unique identifier)
    title: str           # Tender title
    cpv_code: str        # Classification (72000000 = IT)
    base_amount: float   # €
    buyer_name: str      # Contracting authority
    publication_date: date
}

# Chunk Node (linked to Tender)
{
    id: str                  # UUID
    text_preview: str        # First 200 chars
    page_number: int         # PDF page
    chunk_index: int         # Position in document
    section_type: str        # "requirements" | "evaluation" | "technical"
    tender_id: str           # Parent tender
    lot_id: str | null       # If chunk belongs to specific lot
}

# Lot Node (sub-tender)
{
    id: str                  # Lot code
    name: str                # Lot description
    cpv_code: str            # Specific CPV for lot
    base_amount: float       # Lot budget
}
```

### 1.3 Initialize Schema

```python
from src.infra.graph import get_tender_graph_client

async def setup_neo4j():
    """Run once during deployment"""
    client = get_tender_graph_client()
    
    try:
        await client.verify_connectivity()
        await client.create_tender_schema()
        print("✅ Schema created")
    finally:
        await client.close()
```

---

## Phase 2: Ingestion Pipeline

### 2.1 Standard RAG Flow (Existing)

```python
# Current pipeline: PDF → Chunks → Embeddings → Milvus
from src.domain.tender.schemas.chunking import TenderTokenChunk
from rag_toolkit.indexer import MilvusIndexer

async def ingest_tender_document(file_path: str, tender_code: str):
    # 1. Extract and chunk document
    chunks: List[TenderTokenChunk] = await chunk_document(file_path)
    
    # 2. Generate embeddings
    embeddings = await embed_chunks(chunks)
    
    # 3. Index to Milvus (vector store)
    indexer = MilvusIndexer()
    await indexer.index(chunks, embeddings)
    
    return chunks
```

### 2.2 Enhanced with Knowledge Graph

```python
from src.infra.graph.graph_indexer import index_tender_to_graph

async def ingest_tender_with_graph(
    file_path: str,
    tender_code: str,
    tender_metadata: dict
):
    """
    Complete ingestion: Vector + Graph
    """
    # Standard RAG flow
    chunks = await ingest_tender_document(file_path, tender_code)
    
    # NEW: Index to Knowledge Graph
    await index_tender_to_graph(
        tender_code=tender_code,
        tender_metadata={
            "title": tender_metadata["title"],
            "cpv_code": tender_metadata["cpv_code"],
            "base_amount": tender_metadata["base_amount"],
            "buyer_name": tender_metadata["buyer_name"],
            "publication_date": tender_metadata["publication_date"],
        },
        chunks=[
            {
                "id": chunk.id,
                "text": chunk.text,
                "metadata": {
                    "page_number": chunk.page_numbers[0] if chunk.page_numbers else 0,
                    "chunk_index": idx,
                    "section_type": chunk.section_type,
                    "tender_id": chunk.tender_id,
                    "lot_id": chunk.lot_id,
                }
            }
            for idx, chunk in enumerate(chunks)
        ]
    )
    
    print(f"✅ Indexed {len(chunks)} chunks to Milvus + Neo4j")
```

### 2.3 Batch Ingestion

```python
async def batch_ingest_tenders(tender_files: List[dict]):
    """
    Ingest multiple tenders efficiently
    """
    for tender_data in tender_files:
        try:
            await ingest_tender_with_graph(
                file_path=tender_data["file_path"],
                tender_code=tender_data["code"],
                tender_metadata=tender_data["metadata"]
            )
            print(f"✅ {tender_data['code']}")
        except Exception as e:
            print(f"❌ {tender_data['code']}: {e}")
            continue
```

---

## Phase 3: Graph-Enhanced Retrieval

### 3.1 Hybrid Search: Vector + Graph

```python
from src.infra.graph.graph_indexer import get_tender_context_for_chunks

async def search_with_graph_enrichment(
    query: str,
    top_k: int = 5
) -> List[dict]:
    """
    Hybrid retrieval with graph context
    """
    # Step 1: Vector search (existing)
    from rag_toolkit.indexer import MilvusIndexer
    
    indexer = MilvusIndexer()
    vector_results = await indexer.search(query, top_k=top_k * 2)  # Over-fetch
    
    # Step 2: Get graph context for chunks
    chunk_ids = [result.id for result in vector_results]
    graph_contexts = await get_tender_context_for_chunks(chunk_ids)
    
    # Step 3: Enrich results
    enriched_results = []
    for result in vector_results:
        context = graph_contexts.get(result.id)
        
        if context:
            enriched_results.append({
                # Original vector search data
                "chunk_id": result.id,
                "text": result.text,
                "score": result.score,
                "section_path": result.section_path,
                
                # Graph enrichment
                "tender_code": context["tender_code"],
                "tender_title": context["tender_title"],
                "buyer_name": context["buyer_name"],
                "cpv_code": context["cpv_code"],
                "base_amount": context["base_amount"],
                "publication_date": context["publication_date"],
            })
    
    # Step 4: Rerank with graph features
    return rerank_with_tender_context(enriched_results)[:top_k]
```

### 3.2 Graph-Based Reranking

```python
def rerank_with_tender_context(results: List[dict]) -> List[dict]:
    """
    Boost results based on tender metadata
    """
    for result in results:
        boost = 0.0
        
        # Boost recent tenders
        pub_date = result.get("publication_date", "")
        if pub_date and pub_date >= "2025-01-01":
            boost += 0.1
        
        # Boost high-value tenders
        if result.get("base_amount", 0) > 1_000_000:
            boost += 0.05
        
        # Boost specific sections
        if result.get("section_type") == "requirements":
            boost += 0.15
        
        # Apply boost
        result["score"] = result["score"] * (1 + boost)
    
    # Re-sort by adjusted score
    return sorted(results, key=lambda x: x["score"], reverse=True)
```

### 3.3 Query Expansion with Graph

```python
async def expand_query_with_similar_tenders(
    query: str,
    initial_results: List[dict]
) -> List[dict]:
    """
    Find additional chunks from related tenders
    """
    from src.infra.graph.graph_indexer import find_related_tenders
    
    # Get tender codes from initial results
    tender_codes = set(r["tender_code"] for r in initial_results)
    
    # Find related tenders
    related = []
    for code in list(tender_codes)[:3]:  # Top 3 tenders
        similar = await find_related_tenders(code, limit=2)
        related.extend(similar)
    
    # Search in related tenders
    expanded_results = []
    for tender in related:
        # Query graph for relevant chunks from related tender
        graph = get_tender_graph_client()
        try:
            chunks = await graph.execute_query("""
                MATCH (t:Tender {code: $tender_code})-[:HAS_CHUNK]->(c:Chunk)
                WHERE c.section_type = 'requirements'
                RETURN c.id as chunk_id, c.text_preview as preview
                LIMIT 3
            """, {"tender_code": tender["code"]})
            
            expanded_results.extend(chunks)
        finally:
            await graph.close()
    
    return expanded_results
```

---

## Phase 4: Context Assembly

### 4.1 Structured Context for LLM

```python
async def assemble_rag_context(
    query: str,
    search_results: List[dict]
) -> str:
    """
    Build rich, structured context from graph-enriched results
    """
    context_parts = []
    
    # Group by tender
    tenders = {}
    for result in search_results:
        code = result["tender_code"]
        if code not in tenders:
            tenders[code] = {
                "title": result["tender_title"],
                "buyer": result["buyer_name"],
                "amount": result["base_amount"],
                "chunks": []
            }
        tenders[code]["chunks"].append(result)
    
    # Build structured context
    for tender_code, tender_data in tenders.items():
        context_parts.append(f"""
{'='*70}
📋 TENDER: {tender_data['title']}
{'='*70}
🆔 Code: {tender_code}
🏢 Buyer: {tender_data['buyer']}
💰 Amount: €{tender_data['amount']:,.0f}

📄 Relevant Sections:
""")
        
        for idx, chunk in enumerate(tender_data["chunks"], 1):
            context_parts.append(f"""
{idx}. Section: {chunk['section_path']}
   Relevance: {chunk['score']:.2%}
   
   {chunk['text']}

""")
    
    return "\n".join(context_parts)
```

### 4.2 Citation Tracking

```python
@dataclass
class RAGAnswer:
    """Answer with source attribution"""
    text: str
    citations: List[dict]
    confidence: float

async def generate_answer_with_citations(
    query: str,
    context: str,
    search_results: List[dict]
) -> RAGAnswer:
    """
    Generate answer and track sources
    """
    from rag_toolkit.llms import get_llm
    
    llm = get_llm()
    
    prompt = f"""
Based on the following tender documents, answer the question.
Cite specific tender codes for each claim.

CONTEXT:
{context}

QUESTION: {query}

ANSWER (with tender code citations):
"""
    
    answer_text = await llm.generate(prompt)
    
    # Build citation metadata
    citations = [
        {
            "tender_code": r["tender_code"],
            "tender_title": r["tender_title"],
            "chunk_id": r["chunk_id"],
            "section": r["section_path"],
            "relevance_score": r["score"],
        }
        for r in search_results
    ]
    
    return RAGAnswer(
        text=answer_text,
        citations=citations,
        confidence=sum(r["score"] for r in search_results) / len(search_results)
    )
```

---

## Phase 5: Advanced Graph Queries

### 5.1 Cross-Tender Analysis

```python
async def find_common_requirements(
    tender_codes: List[str]
) -> List[dict]:
    """
    Find requirements that appear across multiple tenders
    (useful for identifying standard clauses)
    """
    graph = get_tender_graph_client()
    
    try:
        results = await graph.execute_query("""
            MATCH (t:Tender)-[:HAS_CHUNK]->(c:Chunk)
            WHERE t.code IN $tender_codes 
              AND c.section_type = 'requirements'
            WITH c.text_preview as requirement_text, 
                 collect(DISTINCT t.code) as tender_codes
            WHERE size(tender_codes) >= 2
            RETURN requirement_text, tender_codes, size(tender_codes) as frequency
            ORDER BY frequency DESC
            LIMIT 10
        """, {"tender_codes": tender_codes})
        
        return results
    finally:
        await graph.close()
```

### 5.2 Buyer Portfolio Analysis

```python
async def get_buyer_tender_portfolio(
    buyer_name: str
) -> dict:
    """
    Analyze all tenders from a specific buyer
    """
    graph = get_tender_graph_client()
    
    try:
        stats = await graph.execute_query("""
            MATCH (t:Tender)
            WHERE toLower(t.buyer_name) CONTAINS toLower($buyer_name)
            WITH t
            OPTIONAL MATCH (t)-[:HAS_CHUNK]->(c:Chunk)
            RETURN t.buyer_name as buyer,
                   count(DISTINCT t) as total_tenders,
                   sum(t.base_amount) as total_budget,
                   collect(DISTINCT t.cpv_code) as cpv_codes,
                   count(c) as total_chunks
        """, {"buyer_name": buyer_name})
        
        return stats[0] if stats else {}
    finally:
        await graph.close()
```

### 5.3 Temporal Analysis

```python
async def get_tender_timeline(
    cpv_code_prefix: str,
    start_date: str,
    end_date: str
) -> List[dict]:
    """
    Get tenders in a category over time
    """
    graph = get_tender_graph_client()
    
    try:
        results = await graph.execute_query("""
            MATCH (t:Tender)
            WHERE t.cpv_code STARTS WITH $cpv_prefix
              AND t.publication_date >= date($start_date)
              AND t.publication_date <= date($end_date)
            RETURN t.code as code,
                   t.title as title,
                   t.publication_date as date,
                   t.base_amount as amount,
                   t.buyer_name as buyer
            ORDER BY t.publication_date DESC
        """, {
            "cpv_prefix": cpv_code_prefix,
            "start_date": start_date,
            "end_date": end_date
        })
        
        return results
    finally:
        await graph.close()
```

### 5.4 Chunk Section Distribution

```python
async def get_section_distribution(
    tender_code: str
) -> dict:
    """
    Analyze document structure
    """
    graph = get_tender_graph_client()
    
    try:
        results = await graph.execute_query("""
            MATCH (t:Tender {code: $tender_code})-[:HAS_CHUNK]->(c:Chunk)
            WITH c.section_type as section, count(c) as chunk_count
            RETURN section, chunk_count
            ORDER BY chunk_count DESC
        """, {"tender_code": tender_code})
        
        return {r["section"]: r["chunk_count"] for r in results}
    finally:
        await graph.close()
```

---

## Production Considerations

### 6.1 Performance Optimization

**Connection Pooling:**
```python
# Already configured in base_client.py
Neo4jClient(
    max_connection_lifetime=3600,      # 1 hour
    max_connection_pool_size=50        # Adjust based on load
)
```

**Batch Operations:**
```python
async def batch_create_chunks(tender_code: str, chunks: List[dict]):
    """Create multiple chunks in single transaction"""
    graph = get_tender_graph_client()
    
    try:
        await graph.execute_write("""
            MATCH (t:Tender {code: $tender_code})
            UNWIND $chunks as chunk_data
            CREATE (c:Chunk {
                id: chunk_data.id,
                text_preview: chunk_data.preview,
                page_number: chunk_data.page,
                section_type: chunk_data.section
            })
            CREATE (t)-[:HAS_CHUNK]->(c)
        """, {
            "tender_code": tender_code,
            "chunks": chunks
        })
    finally:
        await graph.close()
```

### 6.2 Error Handling

```python
from neo4j.exceptions import ConstraintError, ServiceUnavailable

async def safe_index_tender(tender_code: str, data: dict):
    """Index with retry and error handling"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            await index_tender_to_graph(tender_code, data)
            return True
            
        except ConstraintError:
            # Tender already exists - update instead
            await update_tender_in_graph(tender_code, data)
            return True
            
        except ServiceUnavailable:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
            
        except Exception as e:
            logger.error(f"Failed to index {tender_code}: {e}")
            return False
```

### 6.3 Monitoring

```python
async def get_indexing_health() -> dict:
    """Monitor graph health"""
    graph = get_tender_graph_client()
    
    try:
        stats = await graph.get_database_stats()
        
        # Check for orphaned chunks
        orphaned = await graph.execute_query("""
            MATCH (c:Chunk)
            WHERE NOT (c)<-[:HAS_CHUNK]-(:Tender)
            RETURN count(c) as orphaned_chunks
        """)
        
        return {
            "total_tenders": stats.get("nodes_Tender", 0),
            "total_chunks": stats.get("nodes_Chunk", 0),
            "total_relationships": stats.get("relationships_total", 0),
            "orphaned_chunks": orphaned[0]["orphaned_chunks"],
            "avg_chunks_per_tender": (
                stats.get("nodes_Chunk", 0) / max(stats.get("nodes_Tender", 1), 1)
            )
        }
    finally:
        await graph.close()
```

### 6.4 Multi-Environment Setup

```bash
# .env configuration

# Local Development (Docker)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=tendergraph2025
NEO4J_DATABASE=neo4j
NEO4J_ENV=local

# Production (Neo4j Aura)
# NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=your-aura-password
# NEO4J_DATABASE=neo4j
# NEO4J_ENV=aura
```

---

## Quick Reference Commands

```bash
# Setup schema
uv run python scripts/setup_neo4j.py

# Clean database (development only)
uv run python scripts/clean_neo4j.py

# Run examples
PYTHONPATH=$PWD uv run python examples/graph_integration_examples.py

# Check graph health
curl http://localhost:7474  # Neo4j Browser
```

## Key Files Reference

```
src/infra/graph/
├── base_client.py          # Generic Neo4j client (→ rag_toolkit future)
├── tender_client.py        # Tender-specific graph operations
├── graph_indexer.py        # Ingestion helpers
└── __init__.py             # Factory functions

examples/
└── graph_integration_examples.py  # Full integration demo

scripts/
├── setup_neo4j.py          # Schema setup + tests
└── clean_neo4j.py          # Database cleanup
```

---

## Summary

**3-Step Integration:**
1. **Ingestion**: `ingest_tender_with_graph()` → Milvus + Neo4j
2. **Retrieval**: `search_with_graph_enrichment()` → Vector + Graph context
3. **Generation**: `assemble_rag_context()` → Structured LLM input

**Key Benefits:**
- ✅ **Structured metadata** (tender code, buyer, amount, dates)
- ✅ **Cross-document analysis** (find similar tenders, common requirements)
- ✅ **Better citations** (link answers to specific tenders)
- ✅ **Query expansion** (explore related tenders automatically)
- ✅ **Performance** (pre-computed relationships, indexed lookups)

**Next Steps (Q1 2025):**
- Entity extraction (NER for organizations, amounts, dates)
- Requirement classification (mandatory vs optional)
- Lot-level relationships (subdivide tenders)
- Evaluation criteria linking (scoring requirements)
