# 🏗️ Architecture & Design Principles

> **Clean Architecture for Production RAG Systems**  
> A battle-tested, scalable architecture designed for real-world Retrieval-Augmented Generation applications.

---

## 🎯 Design Philosophy

This architecture is built on **four core principles**:

1. **🔄 Maximum Reusability** — Core RAG logic can be extracted and reused across projects
2. **🎭 Clear Separation** — Generic logic lives separate from domain-specific code  
3. **📦 Zero Lock-in** — Easy migration between use cases without painful refactors
4. **🚀 Copy-Paste Friendly** — Domain code can be moved between projects seamlessly

> ⚠️ **This structure is intentional.** Violating these rules leads to tight coupling, vendor lock-in, and technical debt.

---

## 📐 High-Level Architecture

```
src/
├── core/      # 🧠 Generic RAG engine (reusable everywhere)
├── infra/     # 🔌 Concrete integrations (Milvus, Supabase, storage)
├── domain/    # 💼 Business logic (use-case specific)
└── apps/      # 🌐 Application layer (API, UI, CLI)
```

### ✅ Allowed Dependencies

```
apps    →  domain, core, infra
domain  →  core, infra (interfaces only)
infra   →  core
core    →  NOTHING ⛔
```

### ❌ Forbidden Dependencies

- `core` importing from `domain`, `infra`, or `apps`
- `domain` knowing about FastAPI or HTTP protocols
- `infra` containing business logic

---

## 🧠 Layer 1: `core/` — RAG Engine

**Purpose:** Generic, reusable RAG logic. Zero domain knowledge.

### ✅ What belongs in `core/`

- **RAG Pipeline** — retrieve → rerank → answer orchestration
- **Abstract Interfaces** — `VectorStore`, `Embedder`, `Chunker`, `LLMClient`
- **Query Engine** — RAGService, pipeline coordination
- **Evaluation** — citation builder, scoring, metrics
- **Domain-agnostic utilities**

### ❌ What does NOT belong

- Concrete Milvus clients
- Supabase/Postgres SDKs
- FastAPI dependencies
- Database models
- Business rules

### 📁 Structure Example

```python
core/
├── rag/
│   ├── pipeline.py      # RAGPipeline orchestration
│   ├── retriever.py     # Retriever interface
│   └── reranker.py      # Reranker interface
├── llm/
│   └── base.py          # LLMClient (abstract)
├── vectorstore/
│   └── base.py          # VectorStore (abstract)
└── embedding/
    └── base.py          # Embedder (abstract)
```

---

## 🔌 Layer 2: `infra/` — Infrastructure & Adapters

**Purpose:** Concrete implementations of `core/` interfaces.

### ✅ What belongs in `infra/`

- **Vector Store Adapters** — Milvus, Pinecone, Weaviate implementations
- **Database Adapters** — Supabase, Postgres, SQLite
- **Storage Adapters** — S3, Azure Blob, Supabase Storage
- **Document Parsers** — Docling, PDF, DOCX parsers
- **ORM Models** — Database schema definitions

### ❌ What does NOT belong

- Business logic
- RAG orchestration
- Domain concepts

### 📁 Structure Example

```python
infra/
├── vectorstores/
│   ├── milvus.py        # MilvusVectorStore(VectorStore)
│   └── pinecone.py      # PineconeVectorStore(VectorStore)
├── db/
│   ├── models/
│   │   └── document.py  # DocumentORM
│   └── repository.py
└── storage/
    └── supabase.py      # SupabaseStorageAdapter
```

---

## 💼 Layer 3: `domain/` — Business Logic

**Purpose:** Use-case specific logic. **This layer changes between projects.**

### ✅ What belongs in `domain/`

- **Domain Entities** — `Document`, `Tender`, `Lot`
- **Business Services** — CRUD operations + domain rules
- **Domain Validation** — business constraints
- **Orchestration** — coordinating `core` and `infra`

### ❌ What does NOT belong

- FastAPI routers
- HTTP Request/Response handling
- Direct database or vector store clients
- Generic RAG logic

### 📁 Structure Example (Tender Use Case)

```python
domain/
└── tender/
    ├── services/
    │   ├── document_service.py    # DocumentService
    │   └── tender_service.py      # TenderService
    └── schemas/
        ├── document.py            # Document, DocumentCreate
        └── tender.py              # Tender, TenderCreate
```

---

## 🌐 Layer 4: `apps/` — Application Layer

**Purpose:** Thin entry points. HTTP, CLI, UI.

### ✅ What belongs in `apps/`

- **FastAPI Routers** — HTTP endpoints
- **Dependency Injection** — `Depends()` setup
- **Authentication & Middleware**
- **Request/Response DTOs**
- **Admin UIs** — Milvus Explorer, monitoring dashboards

### ❌ What does NOT belong

- Business logic
- Direct database or vector store access
- RAG orchestration

### 📁 Structure Example

```python
apps/
└── api/
    ├── routers/
    │   ├── documents.py         # HTTP endpoints
    │   └── tenders.py
    └── schemas/
        └── documents.py         # DocumentRequest, DocumentResponse
```

---

## 📜 Import Rules (Strictly Enforced)

### ✅ Valid Imports

```python
# apps → domain
from domain.tender.services.document_service import DocumentService

# domain → core / infra
from core.rag.pipeline import RAGPipeline
from infra.vectorstores.milvus import MilvusVectorStore

# infra → core
from core.vectorstore.base import VectorStore
```

### ❌ Invalid Imports

```python
# core importing domain ❌
from domain.tender.schemas import Document

# domain importing FastAPI ❌
from fastapi import APIRouter

# core importing infra ❌
from infra.vectorstores.milvus import MilvusVectorStore
```

---

## 🏷️ Naming Conventions

The same concept exists in multiple layers. **Naming prevents chaos.**

| Layer      | Type                  | Naming Convention      |
|------------|-----------------------|------------------------|
| `infra`    | Database model        | `DocumentORM`          |
| `domain`   | Domain entity         | `Document`             |
| `domain`   | Business service      | `DocumentService`      |
| `apps`     | HTTP request/response | `DocumentRequest`      |

---

## 🔀 Multi-Repository Strategy

### `rag-lab` (Core Library)

**Contains:**
- `core/` — Generic RAG engine
- `infra/` — Reusable adapters
- `apps/api/` — Generic API base
- `examples/` — Demonstrations

**Does NOT contain:**
- Domain-specific logic
- Business schemas
- Use-case configurations

### `tender-lab` (Use Case)

**Contains:**
- `domain/tender/` — Tender-specific logic
- Custom API routers
- Domain policies and configurations

**Imports `rag-lab` as dependency:**

```bash
pip install -e ../rag-lab
```

---

## 🔗 Development Workflow

### Local Development Setup

```bash
# Install rag-lab in editable mode
cd rag-lab && pip install -e .

# Link to tender-lab
cd ../tender-lab && pip install -e ../rag-lab
```

**Benefits:**
- ✅ Instant refactor feedback
- ✅ Zero build step
- ✅ Shared development environment

### When to Extract to Core

**Rule:** If something is needed in **two or more use cases**, it's not domain logic.

**Process:**
1. Move generic code from `domain/` to `rag-lab/core/` or `rag-lab/infra/`
2. Update imports in use-case projects
3. Done ✅

---

## 🎓 Guiding Principle

> **"The domain changes. The core survives."**

If you need something in multiple use cases, **it's not domain logic** — it belongs in `core` or `infra`.

---

## 📚 Additional Resources

- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [Clean Architecture (Uncle Bob)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)

---

> **This is not descriptive documentation.**  
> **This is an architectural contract with your future self.**