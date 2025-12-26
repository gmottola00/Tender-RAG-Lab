# Architecture Overview

> **Clean Architecture for Production RAG Systems with rag_toolkit Integration**

Tender-RAG-Lab integrates the **rag_toolkit** library following **Clean Architecture** principles to ensure maximum reusability, clear separation of concerns, zero vendor lock-in, and easy migration between use cases.

---

## Design Philosophy

This architecture is built on **four core principles**:

1. **Maximum Reusability** — Generic RAG logic lives in rag_toolkit library
2. **Clear Separation** — Generic logic (rag_toolkit) separate from domain-specific code  
3. **Zero Lock-in** — Easy migration between use cases without painful refactors
4. **Protocol-Based** — Duck typing with type safety via Python Protocols

> **Note:** This structure is intentional and enforced. Violating these rules leads to tight coupling, vendor lock-in, and technical debt.

---

## High-Level Architecture

```
src/
├── domain/    # Business logic (tender-specific)
├── infra/     # Concrete integrations (Milvus, database, factories)
├── api/       # Application layer (FastAPI, UI)
└── (rag_toolkit library) # Generic RAG engine (external package)
```

### Dependency Rules

**Visual Dependency Flow:**

```
┌─────────────────────────────────────────┐
│        api/ (FastAPI Routers)           │
│         HTTP Layer                      │
└──────────────┬──────────────────────────┘
               │
               ↓
┌──────────────▼──────────────────────────┐
│        domain/ (Business Logic)         │
│    Tender-specific Services & Entities  │
└──────┬───────────────────────┬──────────┘
       │                       │
       ↓                       ↓
┌──────▼──────────┐    ┌──────▼──────────┐
│  infra/         │    │  rag_toolkit    │
│  (DB Models)    │    │  (External Lib) │
└─────────────────┘    └──────┬──────────┘
                              │
                              ↓
                       ┌──────▼──────────┐
                       │  Milvus, LLMs   │
                       │  Vector Stores  │
                       └─────────────────┘
```

**Key:**
- `→` Allowed dependency (imports from)
- `⊗` Forbidden dependency (cannot import from)

### Allowed Dependencies

```
api     →  domain, infra, rag_toolkit
domain  →  infra, rag_toolkit (protocols)
infra   →  rag_toolkit
rag_toolkit → NOTHING (external library)
```

### Forbidden Dependencies

- `rag_toolkit` importing from `domain`, `infra`, or `api` (it's external)
- `domain` knowing about FastAPI or HTTP protocols
- `infra` containing business logic
- `api` accessing database models directly

---

## rag_toolkit Library — Generic RAG Engine

**Purpose:** Generic, reusable RAG components. Zero domain knowledge. Zero vendor lock-in.

### What rag_toolkit Provides

- **Protocols** — `EmbeddingClient`, `LLMClient`, `ChunkLike`, `TokenChunkLike`
- **Chunking** — `DynamicChunker`, `TokenChunker` for document processing
- **Vector Stores** — Milvus integration via factories
- **RAG Pipeline** — `RagPipeline` with rewriting, search, reranking, generation
- **Search Strategies** — `VectorSearch`, `KeywordSearch`, `HybridSearch`
- **Storage** — Supabase integration
- **Parsers** — PDF/DOCX parsing with OCR support

### Integration in Tender-RAG-Lab

The project **extends** rag_toolkit with domain-specific customizations:

- `TenderChunk` / `TenderTokenChunk` — Implement rag_toolkit protocols
- `TenderMilvusIndexer` — Wraps generic `IndexService` with tender schema
- `TenderSearcher` — Facade for search strategies
- Factory functions — Create complete stacks with configuration

**See:** [rag_toolkit Integration Guide](../rag_toolkit/index.rst)

**Key Principle:** If another project needs this code, it belongs in rag_toolkit library (external).

---

## Layer 2: Infrastructure Layer (`infra/`)

**Purpose:** Domain-specific infrastructure including database models and factory functions.

### What Belongs Here

- **Database Models** — SQLAlchemy ORM models specific to tender domain
- **Factory Functions** — `create_milvus_service()`, `create_ingestion_service()`
- **Configuration** — Environment-specific settings

**Note:** Generic infrastructure (Milvus client, parsers, embeddings) is now in **rag_toolkit**.

### What Does NOT Belong

- Business logic
- RAG orchestration
- HTTP request handling
- Generic RAG components (those go in rag_toolkit)

### Structure

```
infra/
├── factory.py           # Domain-specific factories
└── database/            # Database infrastructure
    ├── connection.py    # DB connection management
    └── models/          # SQLAlchemy models (if not in domain/entities)
```

**Key Principle:** Only tender-specific infrastructure lives here. Generic infra is in rag_toolkit.

---

## Layer 3: Domain Layer (`domain/`)

**Purpose:** Use-case specific business logic. This layer contains tender-specific implementations.

### What Belongs Here

- **Domain Entities** — `Tender`, `Lot`, `Document` (SQLAlchemy models)
- **Business Services** — CRUD operations + domain rules
- **Domain Validation** — Business constraints
- **Orchestration** — Coordinating `core` and `infra` for domain needs
- **Domain Schemas** — Pydantic DTOs (TenderCreate, TenderOut)

### What Does NOT Belong

- FastAPI routers
- HTTP Request/Response handling
- Direct vector store or database clients
- Generic RAG logic

### Structure

```
domain/
└── tender/
    ├── entities/            # SQLAlchemy models
    │   ├── tenders.py
    │   ├── lots.py
    │   └── documents.py
    ├── schemas/             # Pydantic DTOs
    │   ├── tenders.py
    │   ├── lots.py
    │   └── documents.py
    ├── services/            # Business services
    │   ├── tenders.py       # TenderService (CRUD)
    │   ├── lots.py
    │   └── documents.py
    ├── search/              # Domain-specific search
    │   └── searcher.py      # TenderSearcher
    └── indexing/            # Domain-specific indexing
        └── indexer.py       # TenderMilvusIndexer
```

**Key Principle:** If it's specific to Tender business, it belongs here.

---

## Layer 4: Application Layer (`apps/`)

**Purpose:** Entry points for HTTP, CLI, and UI. Coordinates services and handles external communication.

### What Belongs Here

- **FastAPI Routers** — HTTP endpoints
- **Dependency Injection** — `providers.py` with `@lru_cache` singletons
- **Authentication & Middleware** — JWT, rate limiting
- **Request/Response DTOs** — (optional, can reuse domain schemas)
- **Admin UIs** — Milvus Explorer, monitoring dashboards

### What Does NOT Belong

- Business logic
- Direct database or vector store access
- RAG orchestration (use `core/rag/pipeline.py`)
- Document parsing (use `infra/parsers/`)

### Structure

```
api/
├── deps.py              # FastAPI dependencies
├── providers.py         # Singleton service providers
└── routers/
    ├── ingestion.py     # /api/ingestion/*
    ├── tenders.py       # /api/tenders
    ├── lots.py          # /api/lots
    ├── documents.py     # /api/documents
    ├── milvus_route.py  # /api/milvus (admin)
    └── ui.py            # HTML page serving
```

**Key Principle:** Routers should be thin. Delegate to domain services.

---

## Import Rules

### Valid Imports

```python
# apps → domain
from src.domain.tender.services.tenders import TenderService

# domain → rag_toolkit
from rag_toolkit.core.rag.pipeline import RagPipeline
from rag_toolkit.core.chunking.dynamic import DynamicChunker

# domain → infra (domain-specific)
from src.infra.factory import create_tender_service
```

### Invalid Imports

```python
# rag_toolkit importing domain (FORBIDDEN - it's external library)l library)
from src.domain.tender.entities.tenders import Tender

# domain importing FastAPI (FORBIDDEN)
from fastapi import APIRouter

# api bypassing domain (FORBIDDEN)
from rag_toolkit.core.rag.pipeline import RagPipeline  # Should go through domain service
```

---

## Example: Document Upload Flow

**Sequence Diagram:**

```
Client                API              Domain           rag_toolkit        Milvus
  |                    |                  |                  |                |
  |--POST /documents-->|                  |                  |                |
  |                    |                  |                  |                |
  |                    |--upload()------->|                  |                |
  |                    |                  |                  |                |
  |                    |                  |--parse()-------->|                |
  |                    |                  |<--ParsedDoc------|                |
  |                    |                  |                  |                |
  |                    |                  |--chunk()-------->|                |
  |                    |                  |<--Chunks---------|                |
  |                    |                  |                  |                |
  |                    |                  |--upsert()------->|                |
  |                    |                  |                  |--store()------>|
  |                    |                  |                  |<--OK-----------|
  |                    |                  |<--Success--------|                |
  |                    |                  |                  |                |
  |                    |<--Document-------|                  |                |
  |                    |                  |                  |                |
  |<--201 Created------|                  |                  |                |
```

**Flow Steps:**

1. **Client** sends file via POST `/documents`
2. **API Router** delegates to `DocumentService.upload()`
3. **Domain Service** uses rag_toolkit's `IngestionService.parse()` for PDF/DOCX parsing
4. **rag_toolkit** returns structured `ParsedDocument`
5. **Domain** chunks via rag_toolkit's `DynamicChunker`
6. **Domain** stores vectors via rag_toolkit's `IndexService.upsert()`
7. **rag_toolkit** writes to Milvus vector database
8. **Success** propagates back through layers
9. **API** returns 201 Created with document metadata

**Notice:** Each layer stays in its lane. API doesn't parse, Domain orchestrates via rag_toolkit.

---

## Naming Conventions

Consistent naming across layers prevents confusion when the same concept appears in multiple contexts.

| Layer      | Type                  | Naming Convention      | Example |
|------------|-----------------------|------------------------|---------|
| `domain`   | Database model        | `{Entity}`             | `Document` (SQLAlchemy) |
| `domain`   | Business service      | `{Entity}Service`      | `DocumentService` |
| `domain`   | Pydantic DTO          | `{Entity}Create/Out`   | `DocumentCreate` |
| `api`      | HTTP request/response | `{Entity}Request/Response` | `DocumentRequest` |

**Why?** Prevents confusion when the same concept appears in multiple layers.

---

## Core Principle

> **"Domain logic changes per use case. Generic RAG components stay in rag_toolkit."**

If you need something in multiple projects, **it's not domain logic** — it belongs in `rag_toolkit` library.

---

## Related Documentation

- [rag_toolkit Integration Guide](../rag_toolkit/index.rst) - External library integration patterns
- [Domain Layer Documentation](../domain/README.md) - Tender-specific business logic
- [Main Documentation](../README.md) - Complete documentation index

---

**[Documentation Home](../README.md) | [rag_toolkit Guide](../rag_toolkit/index.rst)**

*Last updated: 2025-12-25*
