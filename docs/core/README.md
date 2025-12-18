# 🧩 Core Layer: README

> **The foundation: reusable, framework-agnostic abstractions**

The core layer contains pure business logic abstractions with zero external dependencies.

---

## 🎯 Philosophy

**Core principles:**

1. **Zero Dependencies** - Only stdlib, no frameworks/vendors
2. **Protocol-Based** - Duck typing, not inheritance
3. **Framework Agnostic** - Works in FastAPI, CLI, notebooks
4. **Copy-Paste Friendly** - Take core/ to any project

**The core never imports from:**
- `src/infra/` (no concrete implementations)
- `src/domain/` (no business entities)
- `src/api/` (no HTTP concerns)
- External vendors (no `openai`, `pymilvus`, etc.)

**See:** [Architecture Overview](../architecture/overview.md) for layer dependencies.

---

## 📁 Module Structure

```
src/core/
├── chunking/        # Document splitting strategies
├── embedding/       # Text → vector abstractions
├── llm/             # LLM client protocols
├── index/           # Vector search & indexing
├── ingestion/       # Document parsing protocols
└── rag/             # RAG pipeline orchestration
```

---

## 📦 Modules Overview

### [Chunking](chunking.md)

**Purpose:** Split documents into optimal chunks for embedding.

**Key abstractions:**
- `DocumentChunker` Protocol
- `TokenChunker` (fixed-size with overlap)
- `DynamicChunker` (semantic boundary detection)

**Use cases:**
- Prepare documents for vector indexing
- Balance chunk size vs context
- Handle structured documents (tender PDFs)

**Example:**
```python
from src.core.chunking import DynamicChunker

chunker = DynamicChunker(...)
chunks = chunker.chunk(text="...", metadata={})
```

**Read more:** [chunking.md](chunking.md)

---

### [Embedding](embedding.md)

**Purpose:** Transform text into dense vectors for semantic search.

**Key abstractions:**
- `EmbeddingClient` Protocol
- `.embed_text(text)` - Single embedding
- `.embed_batch(texts)` - Efficient batching
- `.dimension` - Vector size (768, 1536, etc.)

**Use cases:**
- Embed document chunks for indexing
- Embed queries for retrieval
- Vendor-agnostic (Ollama, OpenAI, Cohere)

**Example:**
```python
from src.infra.factories import get_embedding_client

embed_client = get_embedding_client()
vector = embed_client.embed_text("tender requirements")
```

**Read more:** [embedding.md](embedding.md)

---

### [LLM](llm.md)

**Purpose:** Language model interactions for generation and reasoning.

**Key abstractions:**
- `LLMClient` Protocol
- `.generate(prompt, **kwargs)` - Text generation
- `.stream(prompt, **kwargs)` - Streaming responses
- Model selection and configuration

**Use cases:**
- Answer generation in RAG
- Query rewriting
- Summarization
- Multi-turn conversations

**Example:**
```python
from src.infra.factories import get_llm_client

llm = get_llm_client()
answer = llm.generate("Based on context: {chunks}, answer: {question}")
```

**Read more:** [llm.md](llm.md)

---

### [Indexing](indexing.md)

**Purpose:** Vector database operations (index, search, manage).

**Key abstractions:**
- `VectorStore` Protocol - Database operations
- `IndexService` - High-level indexing logic
- `SearchStrategy` - Query strategies (vector, keyword, hybrid)
- `Reranker` - Re-score results

**Use cases:**
- Index document chunks with embeddings
- Semantic search (vector similarity)
- Keyword search (BM25)
- Hybrid retrieval (combine strategies)

**Example:**
```python
from src.core.index import IndexService

service = IndexService(vector_store=..., embed_client=...)
await service.index_documents(chunks)

results = await service.search("tender requirements", top_k=10)
```

**Read more:** [indexing.md](indexing.md)

---

### [Ingestion](ingestion.md)

**Purpose:** Document parsing and preprocessing abstractions.

**Key abstractions:**
- `DocumentParser` Protocol - Extract text from files
- `OCREngine` Protocol - OCR for images/scanned PDFs
- `LanguageDetector` Protocol - Detect text language

**Use cases:**
- Parse PDF, DOCX, TXT files
- Extract text from scanned documents
- Detect Italian vs English content
- Preprocessing pipeline

**Example:**
```python
from src.infra.factories import get_document_parser

parser = get_document_parser()
pages = parser.parse(file_path="tender.pdf")

for page in pages:
    print(page.text)
```

**Read more:** [ingestion.md](ingestion.md)

---

### [RAG](rag.md)

**Purpose:** End-to-end RAG pipeline orchestration.

**Key abstractions:**
- `RagPipeline` - Query → Answer flow
- `QueryRewriter` - Improve query quality
- `ContextAssembler` - Merge retrieved chunks
- `Reranker` - Re-score and filter results

**Use cases:**
- Question answering over documents
- Multi-step retrieval (query expansion)
- Context management (deduplication, formatting)
- Streaming responses

**Example:**
```python
from src.core.rag import RagPipeline

pipeline = RagPipeline(
    index_service=...,
    llm_client=...,
    reranker=...
)

answer = await pipeline.query(
    question="What are the technical requirements?",
    collection_name="tender_chunks"
)
```

**Read more:** [rag.md](rag.md)

---

## 🏗️ Design Patterns

### 1. Protocol-Based Design

**Why Protocols?**
- Duck typing (no inheritance needed)
- Easy mocking for tests
- Flexible implementations

**Example:**
```python
from typing import Protocol

class EmbeddingClient(Protocol):
    def embed_text(self, text: str) -> list[float]: ...
```

**Implementations can be anywhere:**
- `src/infra/embedding/ollama.py`
- `src/infra/embedding/openai_embedding.py`
- `tests/mocks/fake_embedding.py`

**See:** [ADR: Protocols vs ABC](../architecture/decisions.md#adr-001-protocols-vs-abc)

---

### 2. Dependency Injection via Factories

**Core defines abstractions, infra provides implementations:**

**Core:**
```python
# src/core/rag/pipeline.py
class RagPipeline:
    def __init__(
        self,
        index_service: IndexService,
        llm_client: LLMClient,
        reranker: Reranker | None = None
    ):
        self._index = index_service
        self._llm = llm_client
        self._reranker = reranker
```

**Infra (wiring):**
```python
# src/infra/factories/rag_factory.py
def get_rag_pipeline() -> RagPipeline:
    return RagPipeline(
        index_service=get_index_service(),
        llm_client=get_llm_client(),
        reranker=get_reranker()
    )
```

**See:** [ADR: Factory Pattern](../architecture/decisions.md#adr-002-factory-pattern)

---

### 3. Async-First

**All I/O operations are async:**
- Embedding API calls
- Vector database queries
- LLM generation
- Database operations

**Benefits:**
- Non-blocking concurrency
- Better throughput
- Handles many requests simultaneously

**Example:**
```python
async def index_documents(self, chunks: list[Chunk]):
    # Embed all chunks concurrently
    tasks = [self._embed_client.embed_text(c.text) for c in chunks]
    vectors = await asyncio.gather(*tasks)
    
    # Batch insert to vector DB
    await self._vector_store.insert(vectors)
```

---

## 🚀 Common Use Cases

### Use Case 1: Add New Embedding Provider

**Goal:** Support HuggingFace embeddings.

**Steps:**
1. Create implementation in `src/infra/embedding/huggingface.py`
2. Implement `EmbeddingClient` Protocol
3. Add to factory in `src/infra/factories/embedding_factory.py`
4. Configure in `.env`

**Core layer:** No changes needed!

**See:** [Adding Integrations](../infra/adding-integrations.md)

---

### Use Case 2: Custom Chunking Strategy

**Goal:** Split by paragraphs instead of tokens.

**Steps:**
1. Create chunker in `src/core/chunking/paragraph_chunker.py`
2. Implement `DocumentChunker` Protocol
3. Use in ingestion service

**Example:**
```python
# src/core/chunking/paragraph_chunker.py
class ParagraphChunker:
    def chunk(self, text: str, metadata: dict) -> list[ChunkResult]:
        paragraphs = text.split("\n\n")
        return [
            ChunkResult(text=p, index=i, metadata={...})
            for i, p in enumerate(paragraphs)
        ]
```

**No external dependencies** - pure core logic.

---

### Use Case 3: New Search Strategy

**Goal:** Add BM25 keyword search.

**Steps:**
1. Create `BM25SearchStrategy` in `src/core/index/search/`
2. Implement `SearchStrategy` Protocol
3. Use in `IndexService`

**Core defines interface, infra provides BM25 implementation (e.g., via Milvus).**

**See:** [Indexing](indexing.md)

---

## 🎓 Learning Path

### For New Contributors

**Start here:**
1. [Architecture Overview](../architecture/overview.md) - Understand 4-layer design
2. [Where to Put Code](../architecture/where-to-put-code.md) - Decision guide
3. [Embedding](embedding.md) - Simplest module
4. [Chunking](chunking.md) - Next simplest
5. [RAG Pipeline](rag.md) - Orchestration example

### For Core Development

**Focus on:**
- Protocol design (interfaces, not implementations)
- Avoiding external dependencies
- Comprehensive docstrings
- Type hints (mypy strict mode)

---

## 🐛 Common Mistakes

### ❌ Importing from Infra

**Bad:**
```python
# src/core/rag/pipeline.py
from src.infra.embedding.ollama import OllamaEmbedding  # ❌
```

**Good:**
```python
# src/core/rag/pipeline.py
from src.core.embedding import EmbeddingClient  # ✅ Protocol
```

**Why?** Core must remain framework-agnostic.

---

### ❌ Concrete Implementations in Core

**Bad:**
```python
# src/core/embedding/base.py
import openai  # ❌

class OpenAIEmbedding:
    def __init__(self, api_key: str):
        self._client = openai.Client(api_key)
```

**Good:**
```python
# src/core/embedding/base.py
from typing import Protocol

class EmbeddingClient(Protocol):  # ✅
    def embed_text(self, text: str) -> list[float]: ...
```

**Concrete implementation belongs in:** `src/infra/embedding/openai_embedding.py`

---

### ❌ Business Logic in Core

**Bad:**
```python
# src/core/rag/pipeline.py
def validate_tender_format(self, doc: Document):  # ❌
    # Tender-specific validation
```

**Good:**
```python
# src/domain/services/tender_service.py
def validate_tender_format(self, doc: Document):  # ✅
    # Domain-specific logic
```

**Why?** Core is reusable across domains. Tender validation is domain logic.

---

## 📚 Related Documentation

- [Architecture Overview](../architecture/overview.md) - Layer dependencies
- [Where to Put Code](../architecture/where-to-put-code.md) - Decision guide
- [Infra Layer](../infra/README.md) - Concrete implementations
- [Domain Layer](../domain/README.md) - Business logic

---

**[⬆️ Documentation Home](../README.md) | [Chunking ➡️](chunking.md)**

*Last updated: 2025-12-18*
