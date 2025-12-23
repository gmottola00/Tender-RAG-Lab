# 🏗️ Architecture Overview

> **Clean Architecture for Production RAG Systems with rag_toolkit Integration**

Tender-RAG-Lab integrates the **rag_toolkit** library following **Clean Architecture** principles to ensure maximum reusability, clear separation of concerns, zero vendor lock-in, and easy migration between use cases.

---

## 🎯 Design Philosophy

This architecture is built on **four core principles**:

1. **🔄 Maximum Reusability** — Generic RAG logic lives in rag_toolkit library
2. **🎭 Clear Separation** — Generic logic (rag_toolkit) separate from domain-specific code  
3. **📦 Zero Lock-in** — Easy migration between use cases without painful refactors
4. **🚀 Protocol-Based** — Duck typing with type safety via Python Protocols

> ⚠️ **This structure is intentional.** Violating these rules leads to tight coupling, vendor lock-in, and technical debt.

---

## 📐 High-Level Architecture

```
src/
├── domain/    # 💼 Business logic (tender-specific)
├── infra/     # 🔌 Concrete integrations (Milvus, database, factories)
├── api/       # 🌐 Application layer (FastAPI, UI)
└── (rag_toolkit library) # 🧠 Generic RAG engine (external package)
```

### Dependency Rules

```mermaid
flowchart TB
    Apps[🌐 api/] --> Domain[💼 domain/]
    Domain --> Infra[🔌 infra/]
    Infra --> RAG[🧠 rag_toolkit]
    Domain --> RAG
    
    RAG -.x Apps
    RAG -.x Domain
    RAG -.x Infra
    
    style RAG fill:#e1f5e1
    style Infra fill:#e1e5f5
    style Domain fill:#f5e1e1
    style Apps fill:#f5f5e1
```

### ✅ Allowed Dependencies

```
api     →  domain, infra, rag_toolkit
domain  →  infra, rag_toolkit (protocols)
infra   →  rag_toolkit
rag_toolkit → NOTHING ⛔ (external library)
```

### ❌ Forbidden Dependencies

- `rag_toolkit` importing from `domain`, `infra`, or `api` (it's external)
- `domain` knowing about FastAPI or HTTP protocols
- `infra` containing business logic
- `api` accessing database models directly

---

## 🧠 rag_toolkit Library — Generic RAG Engine

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

See: [rag_toolkit Integration Guide](../rag_toolkit/index.rst)
└── utils/           # Generic utilities
```

**Key Principle:** If another project needs this code, it belongs in `core/`.

---

## 🔌 Layer 2: `infra/` — Infrastructure & Adapters

**Purpose:** Concrete implementations of `core/` interfaces. Vendor-specific code.

### What Belongs Here

- **Vector Store Adapters** — Milvus, Pinecone, Weaviate implementations
- **Database Adapters** — Supabase, Postgres, SQLite connections
- **Storage Adapters** — S3, Azure Blob, Supabase Storage
- **Document Parsers** — PyMuPDF, python-docx, Tesseract OCR
- **Language Detectors** — fastText integration
- **Factory Functions** — `create_milvus_service()`, `create_ingestion_service()`

### What Does NOT Belong

- Business logic
- RAG orchestration
- Domain concepts
- HTTP request handling

### Structure

```
infra/
├── vectorstores/
│   ├── factory.py           # Production factories
│   └── milvus/              # Milvus implementation
│       ├── service.py       # MilvusService (facade)
│       ├── connection.py    # Connection management
│       ├── collection.py    # Collection operations
│       ├── data.py          # Data operations
│       └── config.py        # Configuration
└── parsers/
    ├── factory.py           # Parser factories
    ├── pdf/                 # PDF parsing
    ├── docx/                # DOCX parsing
    └── text/                # Language detection
```

**Key Principle:** Implementations of `core/` Protocols live here.

---

## 💼 Layer 3: `domain/` — Business Logic

**Purpose:** Use-case specific logic. **This layer changes between projects.**

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

## 🌐 Layer 4: `apps/` — Application Layer

**Purpose:** Thin entry points. HTTP, CLI, UI. **Glues everything together.**

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

## 📜 Import Rules (Strictly Enforced)

### ✅ Valid Imports

```python
# apps → domain
from domain.tender.services.tenders import TenderService

# domain → core / infra
from core.rag.pipeline import RagPipeline
from infra.vectorstores.factory import create_milvus_service

# infra → core
from core.index.base import VectorStore
```

### ❌ Invalid Imports

```python
# core importing domain ❌
from domain.tender.entities.tenders import Tender

# domain importing FastAPI ❌
from fastapi import APIRouter

# core importing infra ❌
from infra.vectorstores.milvus import MilvusService
```

---

## 🔀 Example: Document Upload Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as apps/api/routers
    participant Domain as domain/services
    participant Infra as infra/parsers
    participant Core as core/chunking
    participant Vector as infra/vectorstores
    
    Client->>API: POST /documents (file)
    API->>Domain: DocumentService.upload()
    Domain->>Infra: IngestionService.parse()
    Infra-->>Domain: ParsedDocument
    Domain->>Core: DynamicChunker.chunk()
    Core-->>Domain: Chunks
    Domain->>Vector: MilvusService.upsert()
    Vector-->>Domain: Success
    Domain-->>API: Document
    API-->>Client: 201 Created
```

**Notice:** Each layer stays in its lane. API doesn't parse, Domain doesn't know HTTP details.

---

## 🏷️ Naming Conventions

The same concept exists in multiple layers. **Naming prevents chaos.**

| Layer      | Type                  | Naming Convention      | Example |
|------------|-----------------------|------------------------|---------|
| `infra`    | Database model        | `{Entity}ORM`          | `DocumentORM` |
| `domain`   | Domain entity         | `{Entity}`             | `Document` |
| `domain`   | Business service      | `{Entity}Service`      | `DocumentService` |
| `domain`   | Pydantic DTO          | `{Entity}Create/Out`   | `DocumentCreate` |
| `apps`     | HTTP request/response | `{Entity}Request/Response` | `DocumentRequest` |

**Why?** Prevents confusion when the same concept appears in multiple layers.

---

## 🎓 Guiding Principle

> **"The domain changes. The core survives."**

If you need something in multiple use cases, **it's not domain logic** — it belongs in `core` or `infra`.

---

## 📚 Related Documentation

- [Layer Responsibilities](layers.md) - Deep dive on each layer
- [Design Decisions](decisions.md) - Why we chose this architecture
- [File Placement Guide](where-to-put-code.md) - Decision tree for new code

---

**[⬆️ Documentation Home](../README.md) | [Layer Details ➡️](layers.md)**

*Last updated: 2025-12-18*
