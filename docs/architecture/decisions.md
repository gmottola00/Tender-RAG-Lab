# 🎨 Design Decisions

> **Architecture Decision Records (ADRs) explaining key design choices**

This document explains **why** we made specific architectural decisions and the trade-offs involved.

---

## 📋 Table of Contents

1. [Why Protocols Instead of Abstract Base Classes](#1-why-protocols-instead-of-abstract-base-classes)
2. [Why Factory Pattern for Dependency Injection](#2-why-factory-pattern-for-dependency-injection)
3. [Why Clean Architecture with 4 Layers](#3-why-clean-architecture-with-4-layers)
4. [Why Milvus Over Pinecone](#4-why-milvus-over-pinecone)
5. [Why Domain Layer Separate from Apps](#5-why-domain-layer-separate-from-apps)
6. [Why No FastAPI in Domain](#6-why-no-fastapi-in-domain)
7. [Why Async SQLAlchemy](#7-why-async-sqlalchemy)
8. [Why Pydantic for Configuration](#8-why-pydantic-for-configuration)

---

## 1. Why Protocols Instead of Abstract Base Classes

**Decision:** Use Python `Protocol` (PEP 544) for interfaces instead of `ABC` (Abstract Base Classes).

### Context

We needed a way to define interfaces for `EmbeddingClient`, `LLMClient`, `VectorStore`, etc. that concrete implementations would follow.

### Options Considered

**Option A: Abstract Base Classes (ABC)**
```python
from abc import ABC, abstractmethod

class EmbeddingClient(ABC):
    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        pass
```

**Option B: Protocols (Structural Typing)**
```python
from typing import Protocol

class EmbeddingClient(Protocol):
    async def embed_text(self, text: str) -> list[float]: ...
```

### Decision: Protocols

**Rationale:**
- **No inheritance required** — implementations don't need to inherit from Protocol
- **Duck typing with type safety** — if it quacks like an EmbeddingClient, it is one
- **Easier to mock in tests** — no need to inherit from ABC in mocks
- **More flexible** — third-party classes can be adapted without modification
- **Cleaner** — separates interface definition from implementation

**Trade-offs:**
- ✅ More flexible, easier to test
- ✅ Better for dependency injection
- ⚠️ Less explicit (no `isinstance(obj, Protocol)` checks)
- ⚠️ Requires runtime_checkable for isinstance (rarely needed)

**Example:**
```python
# core/embedding/base.py
class EmbeddingClient(Protocol):
    async def embed_text(self, text: str) -> list[float]: ...

# infra/embedding/ollama.py
class OllamaEmbeddingClient:  # No inheritance!
    async def embed_text(self, text: str) -> list[float]:
        # Implementation
        pass

# Works! Duck typing FTW
client: EmbeddingClient = OllamaEmbeddingClient()
```

---

## 2. Why Factory Pattern for Dependency Injection

**Decision:** Use factory functions with `@lru_cache` instead of DI frameworks like `dependency-injector`.

### Context

We needed a way to manage dependencies (services, clients) across the application with singleton behavior.

### Options Considered

**Option A: Dependency Injection Framework**
```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    embedding_client = providers.Singleton(
        OllamaEmbeddingClient,
        config=config.ollama
    )
```

**Option B: Factory Functions + @lru_cache**
```python
from functools import lru_cache

@lru_cache
def get_embedding_client() -> EmbeddingClient:
    config = OllamaConfig.from_env()
    return OllamaEmbeddingClient(config)
```

### Decision: Factory Pattern

**Rationale:**
- **Simplicity** — no new framework to learn
- **Explicit** — easy to see what's being created
- **Testable** — easy to override with `@patch` or manual injection
- **Standard library** — uses built-in `functools.lru_cache`
- **FastAPI compatible** — works naturally with `Depends()`

**Trade-offs:**
- ✅ Simple, explicit, no magic
- ✅ Easy to understand and debug
- ⚠️ Manual cache clearing in tests (lru_cache.cache_clear())
- ⚠️ No automatic lifecycle management (but we don't need it)

**Pattern:**
```python
# infra/vectorstores/factory.py
def create_milvus_service() -> MilvusService:
    config = MilvusConfig.from_env()
    return MilvusService(config)

# apps/api/providers.py
@lru_cache
def get_index_service() -> IndexService:
    return create_milvus_service()

# apps/api/routers/documents.py
@router.post("/")
def create_doc(service: IndexService = Depends(get_index_service)):
    # Service is singleton via lru_cache
    pass
```

---

## 3. Why Clean Architecture with 4 Layers

**Decision:** Strict 4-layer architecture: `core` → `infra` → `domain` → `apps`

### Context

RAG systems can become monolithic quickly. We needed structure that prevents coupling and enables reusability.

### Rationale

**Layer Isolation:**
- `core` = Generic RAG engine (reusable across projects)
- `infra` = Vendor implementations (swap Milvus for Pinecone easily)
- `domain` = Business logic (Tender-specific rules)
- `apps` = Entry points (HTTP API, future CLI)

**Benefits:**
1. **Reusability** — `core` can be extracted to separate library
2. **Testability** — Each layer tested independently
3. **Flexibility** — Swap Milvus for Pinecone without touching `core`
4. **Clarity** — No confusion about where code belongs
5. **Migration** — Move Tender domain to new project easily

**Alternative Considered:** Flat structure (everything in `src/`)
- ❌ Would lead to tangled dependencies
- ❌ Hard to extract reusable components
- ❌ Difficult to understand boundaries

---

## 4. Why Milvus Over Pinecone

**Decision:** Use Milvus as primary vector database (with Pinecone as future option).

### Context

Need vector database for RAG system with:
- Metadata filtering
- Hybrid search (vector + keyword)
- High performance
- Production-grade reliability

### Options Considered

| Feature | Milvus | Pinecone | Weaviate |
|---------|--------|----------|----------|
| **Cost** | Free (self-hosted) | Paid | Free (self-hosted) |
| **Metadata Filtering** | ✅ Excellent | ✅ Good | ✅ Good |
| **Hybrid Search** | ✅ Built-in | ❌ Separate | ✅ Built-in |
| **Scalability** | ✅ Excellent | ✅ Excellent | ✅ Good |
| **Community** | ✅ Large | ✅ Large | ✅ Growing |
| **Learning Curve** | ⚠️ Moderate | ✅ Easy | ✅ Easy |

### Decision: Milvus

**Rationale:**
- **Free** — Self-hosted, no vendor costs
- **Hybrid search** — BM25 + vector in one query
- **Metadata filtering** — Essential for tender_id, lot_id scoping
- **Scalability** — Production-proven at scale
- **Control** — Full control over deployment and data

**Trade-offs:**
- ✅ Cost-effective, full control
- ✅ Built-in hybrid search
- ⚠️ More complex setup (docker-compose with etcd, minio)
- ⚠️ Self-managed (but we have docker-compose)

**Future-proof:** Architecture allows adding Pinecone via Protocol implementation.

---

## 5. Why Domain Layer Separate from Apps

**Decision:** Business logic in `domain/`, HTTP handling in `apps/`.

### Rationale

**Separation Benefits:**
1. **Reusability** — Domain logic can be used in CLI, batch jobs, not just API
2. **Testability** — Test business logic without HTTP mocking
3. **Clarity** — Clear boundary between business rules and HTTP protocol
4. **Migration** — Move to GraphQL/gRPC without rewriting business logic

**Example:**
```python
# ✅ Good: Domain logic in service
# domain/tender/services/tenders.py
class TenderService:
    def close_tender(self, id: UUID) -> Result:
        if self.has_open_lots(id):
            return Failure("Cannot close: has open lots")
        return self.update_status(id, TenderStatus.CLOSED)

# apps/api/routers/tenders.py
@router.post("/{id}/close")
def close_tender(id: UUID):
    result = service.close_tender(id)
    if result.is_failure:
        raise HTTPException(400, result.error)
    return result.value
```

**Alternative Considered:** Business logic in routers
- ❌ Can't reuse in CLI/batch jobs
- ❌ Hard to test without HTTP mocking
- ❌ Violates single responsibility

---

## 6. Why No FastAPI in Domain

**Decision:** `domain/` layer never imports FastAPI.

### Rationale

**Principle:** Domain layer should be framework-agnostic.

**Benefits:**
1. **Framework independence** — Can switch from FastAPI to Flask/Django
2. **Reusability** — Domain logic usable in CLI, Celery tasks, Lambda
3. **Testability** — No HTTP framework in unit tests
4. **Clarity** — Domain concerns separate from HTTP concerns

**What if I need HTTP exceptions?**

Use Result types or custom domain exceptions:

```python
# domain/tender/exceptions.py
class TenderNotFoundException(Exception):
    pass

# domain/tender/services/tenders.py
def get_tender(self, id: UUID) -> Tender:
    tender = self.repository.get(id)
    if not tender:
        raise TenderNotFoundException(id)
    return tender

# apps/api/routers/tenders.py
@router.get("/{id}")
def get_tender(id: UUID):
    try:
        return service.get_tender(id)
    except TenderNotFoundException:
        raise HTTPException(404)  # HTTP at API layer
```

---

## 7. Why Async SQLAlchemy

**Decision:** Use async SQLAlchemy with `asyncpg` driver.

### Context

Application needs to:
- Handle concurrent requests efficiently
- Not block on database operations
- Scale to many simultaneous users

### Options Considered

**Option A: Sync SQLAlchemy**
- ❌ Blocks event loop
- ❌ Poor concurrency
- ✅ Simpler code

**Option B: Async SQLAlchemy**
- ✅ Non-blocking I/O
- ✅ Better concurrency
- ⚠️ Async/await everywhere

### Decision: Async SQLAlchemy

**Rationale:**
- **Non-blocking** — Doesn't block event loop during DB queries
- **Concurrency** — Handle many requests simultaneously
- **Future-proof** — Async is the way forward for Python web
- **Consistency** — FastAPI is async, LLM calls are async, why not DB?

**Trade-offs:**
- ✅ Better performance under load
- ✅ More scalable
- ⚠️ More complex (async/await, session management)
- ⚠️ Requires `asyncpg` driver

---

## 8. Why Pydantic for Configuration

**Decision:** Use Pydantic `BaseSettings` for all configuration.

### Rationale

**Benefits:**
- **Type safety** — Catch config errors at startup
- **Validation** — Ensure required env vars are set
- **Documentation** — Config schema is self-documenting
- **IDE support** — Autocomplete for config fields
- **Environment variables** — Automatic `.env` loading

**Example:**
```python
# configs/config.py
class MilvusConfig(BaseSettings):
    uri: str = "http://localhost:19530"
    user: str = "root"
    password: str = "Milvus"
    db: str = "default"
    collection: str = "tender_chunks"
    
    class Config:
        env_prefix = "MILVUS_"  # MILVUS_URI, MILVUS_USER, etc.
```

**Alternative Considered:** Manual `os.getenv()`
- ❌ No type safety
- ❌ No validation
- ❌ Easy to miss required vars

---

## 📚 Related Documentation

- [Architecture Overview](overview.md) - Clean architecture principles
- [Layer Responsibilities](layers.md) - Deep dive on each layer
- [File Placement Guide](where-to-put-code.md) - Decision tree for new code

---

**[⬅️ Overview](overview.md) | [⬆️ Documentation Home](../README.md) | [Layers ➡️](layers.md)**

*Last updated: 2025-12-18*
