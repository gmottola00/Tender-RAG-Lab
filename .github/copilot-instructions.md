# GitHub Copilot Instructions for Tender-RAG-Lab

## Project Overview

**Tender-RAG-Lab** is a production-ready Retrieval-Augmented Generation (RAG) system for tender and procurement documents. It follows **Clean Architecture** principles with strict layer separation and uses **rag-toolkit** as a generic RAG library.

**Tech Stack:**
- **FastAPI** (API layer)
- **Milvus** (vector database)
- **Neo4j** (knowledge graph)
- **SQLAlchemy** + PostgreSQL (relational data)
- **rag-toolkit** (generic RAG engine - installed in editable mode)
- **Docling** (document parsing)

---

## Architecture Principles

### Four-Layer Architecture (Strictly Enforced)

```
src/
├── core/      # ❌ DELETED - replaced by rag-toolkit
├── infra/     # 🔌 Infrastructure adapters (Milvus, storage, DB models)
├── domain/    # 💼 Business logic (tender-specific code)
└── api/       # 🌐 HTTP layer (FastAPI routers)
```

### Allowed Dependencies

```
api     →  domain, infra, rag-toolkit
domain  →  infra, rag-toolkit (interfaces only)
infra   →  rag-toolkit
```

### ❌ Forbidden Dependencies

- `infra` importing from `domain` or `api`
- `domain` importing FastAPI or HTTP protocols
- Any code importing from deleted `src/core/` modules

---

## rag-toolkit Integration

### Installation

**rag-toolkit** is installed in **editable mode** for local development:
```bash
uv pip install -e /path/to/Rag-Toolkit
```

### Import Mapping (Post-Migration)

| Old Import (DELETED) | New Import (rag-toolkit) |
|---------------------|--------------------------|
| `src.core.rag.pipeline` | `rag_toolkit.rag.pipeline` |
| `src.core.embedding.base` | `rag_toolkit.core.embedding` |
| `src.core.llm.base` | `rag_toolkit.core.llm` |
| `src.core.chunking.dynamic_chunker` | `rag_toolkit.core.chunking` |
| `src.core.index` | `rag_toolkit.core.index` |

### Key rag-toolkit Modules

```python
# Core protocols
from rag_toolkit.core.embedding import EmbeddingClient
from rag_toolkit.core.llm import LLMClient
from rag_toolkit.core.chunking.types import ChunkLike, TokenChunkLike

# RAG pipeline
from rag_toolkit.rag import RagPipeline
from rag_toolkit.rag.rewriter import QueryRewriter
from rag_toolkit.rag.assembler import ContextAssembler
from rag_toolkit.rag.rerankers import LLMReranker

# Infrastructure
from rag_toolkit.infra.vectorstores.factory import create_milvus_service, create_index_service
from rag_toolkit.infra.vectorstores.milvus.service import MilvusService
from rag_toolkit.infra.embedding import OllamaEmbeddingClient
from rag_toolkit.infra.llm import OllamaLLMClient
from rag_toolkit.infra.parsers.factory import create_ingestion_service

# Index service
from rag_toolkit.core.index.service import IndexService
from rag_toolkit.core.index.search_strategies import VectorSearch, HybridSearch
```

---

## Domain Extensions via Protocols

### Protocol Pattern

rag-toolkit uses **Protocols** (structural typing) for extensibility. Domain-specific code extends these protocols without modifying the library.

**Example: TenderChunk extends ChunkLike**

```python
# src/domain/tender/schemas/chunking.py
from rag_toolkit.core.chunking.types import ChunkLike, TokenChunkLike

@dataclass
class TenderChunk:
    """Conforms to ChunkLike Protocol with tender-specific fields."""
    
    # Required by ChunkLike Protocol
    id: str
    title: str
    heading_level: int
    text: str
    blocks: List[Dict[str, Any]] = field(default_factory=list)
    page_numbers: List[int] = field(default_factory=list)
    
    # Tender-specific extensions
    tender_id: str = ""
    lot_id: Optional[str] = None
    section_type: str = ""
```

**Key Protocols in rag-toolkit:**
- `ChunkLike` — Generic document chunk
- `TokenChunkLike` — Token-optimized chunk for embeddings
- `EmbeddingClient` — Embedding model interface
- `LLMClient` — Language model interface
- `VectorStoreClient` — Vector database interface

---

## Factory Pattern for Domain Infrastructure

### src/infra/factory.py

Domain-specific infrastructure is created via **factory functions** that wrap rag-toolkit components with business logic.

```python
# src/infra/factory.py
from rag_toolkit.core.embedding import EmbeddingClient
from rag_toolkit.core.index.service import IndexService
from rag_toolkit.infra.vectorstores.factory import create_milvus_service, create_index_service

from src.domain.tender.indexing.indexer import TenderMilvusIndexer
from src.domain.tender.search.searcher import TenderSearcher


def create_tender_stack(
    embed_client: EmbeddingClient,
    embedding_dim: int,
    collection_name: str = "tender_chunks",
) -> Tuple[TenderMilvusIndexer, TenderSearcher]:
    """Create tender-specific indexer and searcher stack.
    
    Wraps rag-toolkit's Milvus components with domain-specific logic.
    """
    def embed_fn(texts: list[str]) -> list[list[float]]:
        return [embed_client.embed(t) for t in texts]
    
    # Use rag-toolkit factories
    milvus_service = create_milvus_service()
    index_service = create_index_service(
        embedding_dim=embedding_dim,
        embed_fn=embed_fn,
        collection_name=collection_name,
        vector_store=milvus_service,
    )
    
    # Wrap with domain-specific classes
    indexer = TenderMilvusIndexer(
        index_service=index_service,
        embed_fn=embed_fn,
        embedding_dim=embedding_dim,
        collection_name=collection_name,
    )
    
    searcher = TenderSearcher(
        indexer=indexer,
        embed_client=embed_client,
    )
    
    return indexer, searcher
```

**Pattern:**
1. Use rag-toolkit factories to create generic components
2. Wrap generic components with domain-specific classes
3. Return domain-specific objects to application code

---

## Domain Layer (src/domain/tender/)

**Purpose:** Tender-specific business logic. This layer changes between projects.

```
src/domain/tender/
├── schemas/
│   ├── chunking.py          # TenderChunk, TenderTokenChunk (Protocol-compliant)
│   ├── documents.py         # Document domain entity
│   └── tenders.py           # Tender, Lot domain entities
├── services/
│   ├── documents.py         # DocumentService (CRUD + business logic)
│   ├── lots.py              # LotService
│   └── tenders.py           # TenderService
├── indexing/
│   └── indexer.py           # TenderMilvusIndexer (wraps IndexService)
└── search/
    ├── searcher.py          # TenderSearcher (hybrid search)
    ├── vector_searcher.py   # Vector search implementation
    └── keyword_searcher.py  # BM25 keyword search
```

**Key Files:**
- **schemas/chunking.py**: Protocol-compliant domain chunks
- **indexing/indexer.py**: Wraps `rag_toolkit.core.index.service.IndexService`
- **search/searcher.py**: Orchestrates hybrid search (vector + keyword + reranking)

---

## API Layer (src/api/)

**Purpose:** Thin HTTP layer. No business logic.

```
src/api/
├── deps.py                  # FastAPI dependency injection
└── routers/
    ├── documents.py         # Document CRUD endpoints
    ├── tenders.py           # Tender CRUD endpoints
    ├── ingestion.py         # Document ingestion pipeline
    └── milvus_route.py      # Vector search endpoints
```

**Key Patterns:**
- **deps.py**: Provides dependency injection for services
- **Routers**: Thin layer calling domain services
- **No business logic**: All logic delegated to `domain/`

---

## Development Workflows

### Running the Application

```bash
# Install dependencies
make install

# Run FastAPI server
make api

# Run tests
pytest tests/
```

### Environment Setup

**Required Environment Variables:**
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/tender_rag
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=tender_chunks

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=xxx

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_LLM_MODEL=llama3
```

### Adding New Domain Features

1. **Create domain entity** in `src/domain/tender/schemas/`
2. **Implement business service** in `src/domain/tender/services/`
3. **Add API router** in `src/api/routers/`
4. **Update factory** in `src/infra/factory.py` if needed

### Extending rag-toolkit Components

**Use Protocols for compatibility:**
```python
# ✅ Correct: Extend Protocol with domain fields
@dataclass
class TenderChunk:
    # Protocol fields
    id: str
    text: str
    # Domain extensions
    tender_id: str
    lot_id: Optional[str]

# ❌ Wrong: Modify rag-toolkit directly
# Never edit rag-toolkit source code
```

---

## Migration Status (Phases 1-3 Complete)

### ✅ Completed Phases

- **Phase 1**: Protocol imports (`EmbeddingClient`, `LLMClient`) → `rag_toolkit.core`
- **Phase 2**: RAG modules (`pipeline`, `rerankers`) → `rag_toolkit.rag`
- **Phase 3**: Chunking modules → `rag_toolkit.core.chunking`

### ⚠️ Pending Work

- **Phase 4**: Vector store migration (verify all Milvus operations)
- **Phase 5**: Cleanup (remove any remaining `src/core/` references)

### Deleted Modules (replaced by rag-toolkit)

```
src/core/rag/          → rag_toolkit.rag
src/core/chunking/     → rag_toolkit.core.chunking
src/core/embedding/    → rag_toolkit.core.embedding
src/core/llm/          → rag_toolkit.core.llm
```

**Result:** ~17 files eliminated, ~60% code reduction in core logic.

---

## Common Patterns & Conventions

### 1. Dependency Injection (src/api/deps.py)

```python
from rag_toolkit.infra.embedding import OllamaEmbeddingClient
from src.infra.factory import create_tender_stack

def get_tender_indexer():
    embed_client = OllamaEmbeddingClient()
    embedding_dim = len(embed_client.embed("test"))
    indexer, _ = create_tender_stack(embed_client, embedding_dim)
    return indexer
```

### 2. Protocol Compliance

Always implement required Protocol methods:
```python
class TenderChunk:
    def to_dict(self, *, include_blocks: bool = True) -> Dict[str, Any]:
        """Required by ChunkLike Protocol."""
        return {...}
```

### 3. Factory Usage

Use factories from `rag_toolkit.infra.vectorstores.factory`:
```python
from rag_toolkit.infra.vectorstores.factory import create_milvus_service, create_index_service

# ✅ Correct
milvus_service = create_milvus_service()

# ❌ Wrong: Direct instantiation
from rag_toolkit.infra.vectorstores.milvus.service import MilvusService
milvus_service = MilvusService()  # Don't do this
```

---

## Critical Rules for AI Agents

### ❌ DO NOT

1. Import from deleted `src/core/` modules
2. Modify rag-toolkit source code directly
3. Put business logic in `src/api/` or `src/infra/`
4. Use incorrect rag-toolkit import paths (e.g., `rag_toolkit.core.index.base` → use `rag_toolkit.core.index.service`)
5. Return objects with methods from FastAPI endpoints (use `.to_dict()` or Pydantic models)

### ✅ DO

1. Use rag-toolkit protocols for domain extensions
2. Keep domain logic in `src/domain/tender/`
3. Use factory pattern in `src/infra/factory.py` for infrastructure
4. Verify import paths match rag-toolkit structure
5. Return JSON-serializable dictionaries from API endpoints

---

## Debugging Tips

### Import Errors

If you see `ImportError: cannot import name 'X' from 'rag_toolkit.core.Y'`:
1. Check rag-toolkit source for correct module path
2. Common mistake: `rag_toolkit.core.index.base` → should be `rag_toolkit.core.index.service`

### Pydantic Serialization Errors

If FastAPI throws `Unable to serialize unknown type: <class 'method'>`:
1. Check API route return type
2. Convert objects to dictionaries: `obj.to_dict()` or use Pydantic response models

### Milvus Connection Issues

1. Verify Milvus is running: `docker-compose up -d`
2. Check environment variables: `MILVUS_HOST`, `MILVUS_PORT`
3. Use `create_milvus_service()` factory from rag-toolkit

---

## Additional Resources

- **Architecture**: `architecture.md` (detailed layer documentation)
- **README**: `README.md` (project overview, use cases, roadmap)
- **rag-toolkit docs**: Check editable installation path for source code

---

**Last Updated:** 2025-01-22  
**Migration Status:** Phase 1-3 Complete | Phase 4-5 Pending
