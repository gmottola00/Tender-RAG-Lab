# 🔌 Infrastructure Layer: README

> **Concrete implementations: vendors, frameworks, and external services**

The infrastructure layer contains all concrete implementations of core abstractions.

---

## 🎯 Philosophy

**Infra principles:**

1. **Implement Core Protocols** - Concrete classes for abstract interfaces
2. **Vendor Integration** - OpenAI, Ollama, Milvus, Supabase, etc.
3. **Framework Wiring** - FastAPI, SQLAlchemy, Pydantic
4. **Configuration Management** - Environment variables, factories

**The infra layer is:**
- Where external dependencies live
- Swappable (change Milvus → Pinecone without touching core)
- Framework-specific (can use FastAPI, Click, etc.)

**See:** [Architecture Overview](../architecture/overview.md) for layer dependencies.

---

## 📁 Module Structure

```
src/infra/
├── embedding/       # Concrete embedding clients
├── llm/             # Concrete LLM clients
├── vectorstores/    # Milvus implementation
├── parsers/         # Document parser implementations
└── factories/       # Dependency injection
```

---

## 📦 Modules Overview

### Embedding Implementations

**Location:** `src/infra/embedding/`

**Implementations:**
- `ollama.py` - Ollama embeddings (local)
- `openai_embedding.py` - OpenAI embeddings (cloud)

**Protocol:** `EmbeddingClient` from `src/core/embedding/`

**Example:**
```python
from src.infra.embedding.ollama import OllamaEmbedding

embed_client = OllamaEmbedding(
    base_url="http://localhost:11434",
    model="nomic-embed-text"
)

vector = embed_client.embed_text("tender requirements")
```

**Read more:** [Embedding Implementations](embeddings.md)

---

### LLM Implementations

**Location:** `src/infra/llm/`

**Implementations:**
- `ollama.py` - Ollama LLMs (local)
- `openai_llm.py` - OpenAI LLMs (cloud)

**Protocol:** `LLMClient` from `src/core/llm/`

**Example:**
```python
from src.infra.llm.ollama import OllamaLLM

llm = OllamaLLM(
    base_url="http://localhost:11434",
    model="llama3.2"
)

answer = await llm.agenerate("Summarize this tender...")
```

**Read more:** [LLM Implementations](llm.md)

---

### [Milvus Vector Store](milvus.md)

**Location:** `src/core/index/vector/`

**Purpose:** Vector database for semantic search.

**Key components:**
- `MilvusConnection` - Connection management
- `MilvusCollection` - Collection operations
- `MilvusVectorStore` - Implements `VectorStore` Protocol

**Features:**
- Vector similarity search (HNSW index)
- Keyword search (BM25)
- Hybrid search (RRF fusion)
- Metadata filtering
- Batch operations

**Setup:**
```bash
docker-compose up -d  # Start Milvus
```

**Example:**
```python
from src.core.index.vector import get_milvus_service

service = get_milvus_service()

# Insert vectors
await service.insert(
    collection_name="tender_chunks",
    vectors=vectors,
    texts=texts,
    metadata=metadata_list
)

# Search
results = await service.search(
    collection_name="tender_chunks",
    query_vector=query_vec,
    top_k=10
)
```

**Read more:** [Milvus Setup & Configuration](milvus.md)

---

### [Document Parsers](parsers.md)

**Location:** Multiple implementations across codebase

**Purpose:** Extract text from various file formats.

**Implementations:**
- `PyPDFParser` - Digital PDFs
- `UnstructuredParser` - Multi-format (PDF, DOCX, HTML)
- `TesseractOCR` - Scanned documents
- `LangdetectDetector` - Language detection

**Example:**
```python
from src.infra.parsers import PyPDFParser

parser = PyPDFParser()
pages = parser.parse("tender.pdf")

for page in pages:
    print(f"Page {page.number}: {page.text[:100]}...")
```

**Read more:** [Parser Implementations](parsers.md)

---

### [Factories](factories.md)

**Location:** `src/infra/factories/`

**Purpose:** Dependency injection and object creation.

**Key factories:**
- `embedding_factory.py` - Get embedding client
- `llm_factory.py` - Get LLM client
- `rag_factory.py` - Get RAG pipeline
- `ingestion_factory.py` - Get ingestion service

**Pattern:**
```python
# src/infra/factories/embedding_factory.py
from functools import lru_cache

@lru_cache
def get_embedding_client() -> EmbeddingClient:
    provider = os.getenv("EMBEDDING_PROVIDER", "ollama")
    
    if provider == "ollama":
        return OllamaEmbedding(...)
    elif provider == "openai":
        return OpenAIEmbedding(...)
    else:
        raise ValueError(f"Unknown provider: {provider}")
```

**Usage:**
```python
from src.infra.factories import get_embedding_client

embed_client = get_embedding_client()  # Auto-configured from .env
```

**Read more:** [Factory Pattern & DI](factories.md)

---

## 🏗️ Design Patterns

### 1. Protocol Implementation

**Core defines interface, infra implements:**

**Core:**
```python
# src/core/embedding/base.py
class EmbeddingClient(Protocol):
    def embed_text(self, text: str) -> list[float]: ...
```

**Infra:**
```python
# src/infra/embedding/ollama.py
class OllamaEmbedding:
    """Implements EmbeddingClient Protocol"""
    
    def embed_text(self, text: str) -> list[float]:
        response = requests.post(...)
        return response["embedding"]
```

**No inheritance needed** - duck typing via Protocol.

---

### 2. Factory Pattern

**Centralized object creation:**

```python
# Instead of scattered instantiation
embed_client = OllamaEmbedding(
    base_url=os.getenv("OLLAMA_URL"),
    model=os.getenv("OLLAMA_EMBED_MODEL")
)

# Use factory
embed_client = get_embedding_client()  # Config from .env
```

**Benefits:**
- Single source of truth
- Easy testing (mock factory)
- Environment-based configuration
- Singleton caching via `@lru_cache`

---

### 3. Adapter Pattern

**Wrap external libraries to match protocols:**

```python
# External library (openai) has different interface
import openai

# Adapter wraps it to match our protocol
class OpenAIEmbedding:
    def __init__(self, api_key: str, model: str):
        self._client = openai.Client(api_key=api_key)
        self._model = model
    
    def embed_text(self, text: str) -> list[float]:
        # Adapt openai response to our interface
        response = self._client.embeddings.create(
            input=text,
            model=self._model
        )
        return response.data[0].embedding
```

---

## 🚀 Common Use Cases

### Use Case 1: Switch Embedding Provider

**Goal:** Change from Ollama to OpenAI.

**Steps:**
1. Update `.env`:
   ```bash
   # Change from:
   # EMBEDDING_PROVIDER=ollama
   # OLLAMA_URL=http://localhost:11434
   # OLLAMA_EMBED_MODEL=nomic-embed-text
   
   # To:
   EMBEDDING_PROVIDER=openai
   OPENAI_API_KEY=sk-proj-...
   OPENAI_EMBED_MODEL=text-embedding-3-small
   ```

2. Restart app

**That's it!** No code changes needed - factory handles wiring.

---

### Use Case 2: Add New Vector Store

**Goal:** Support Pinecone alongside Milvus.

**Steps:**

1. **Create implementation:**
   ```python
   # src/infra/vectorstores/pinecone_store.py
   import pinecone
   
   class PineconeVectorStore:
       """Implements VectorStore Protocol"""
       
       def __init__(self, api_key: str, index_name: str):
           self._client = pinecone.Pinecone(api_key=api_key)
           self._index = self._client.Index(index_name)
       
       async def insert(self, vectors, texts, metadata):
           # Implement protocol methods
           ...
       
       async def search(self, query_vector, top_k, filters):
           results = self._index.query(
               vector=query_vector,
               top_k=top_k,
               filter=filters
           )
           return [self._convert_result(r) for r in results]
   ```

2. **Add to factory:**
   ```python
   # src/infra/factories/vector_store_factory.py
   def get_vector_store() -> VectorStore:
       provider = os.getenv("VECTOR_STORE", "milvus")
       
       if provider == "pinecone":
           return PineconeVectorStore(
               api_key=os.getenv("PINECONE_API_KEY"),
               index_name=os.getenv("PINECONE_INDEX")
           )
       # ... milvus
   ```

3. **Configure:**
   ```bash
   # .env
   VECTOR_STORE=pinecone
   PINECONE_API_KEY=...
   PINECONE_INDEX=tender-index
   ```

**Core layer:** No changes!

**See:** [Adding Integrations](adding-integrations.md) for complete guide.

---

### Use Case 3: Custom Parser

**Goal:** Support Markdown files.

**Steps:**

1. **Create parser:**
   ```python
   # src/infra/parsers/markdown_parser.py
   import markdown
   
   class MarkdownParser:
       def parse(self, file_path: str) -> list[Page]:
           with open(file_path) as f:
               content = f.read()
           
           # Convert markdown to text
           html = markdown.markdown(content)
           text = self._strip_html(html)
           
           return [Page(number=1, text=text, metadata={})]
       
       def supports(self, file_path: str) -> bool:
           return file_path.endswith((".md", ".markdown"))
   ```

2. **Add to factory:**
   ```python
   # src/infra/factories/parser_factory.py
   def get_parser(file_path: str) -> DocumentParser:
       if file_path.endswith((".md", ".markdown")):
           return MarkdownParser()
       # ... other formats
   ```

**Usage:**
```python
result = await ingestion_service.process_document("README.md")
```

---

## 🎓 Learning Path

### For New Contributors

**Start here:**
1. [Architecture Overview](../architecture/overview.md) - Understand layers
2. [Where to Put Code](../architecture/where-to-put-code.md) - Infra vs core
3. [Factories](factories.md) - Dependency injection
4. [Milvus Setup](milvus.md) - Vector database

### For Adding Integrations

**Focus on:**
1. [Adding Integrations](adding-integrations.md) - Step-by-step guide
2. Study existing implementations (Ollama, OpenAI)
3. Follow protocol interfaces (no deviation)
4. Use factories for wiring

---

## 🐛 Common Mistakes

### ❌ Business Logic in Infra

**Bad:**
```python
# src/infra/embedding/ollama.py
def validate_tender_format(self, doc: Document):  # ❌
    # Business logic doesn't belong here
```

**Good:**
```python
# src/domain/services/tender_service.py
def validate_tender_format(self, doc: Document):  # ✅
    # Domain logic belongs in domain layer
```

**Why?** Infra is for vendor integration, not business rules.

---

### ❌ Importing from Domain/Apps

**Bad:**
```python
# src/infra/embedding/ollama.py
from src.domain.models import Tender  # ❌
```

**Good:**
```python
# src/infra/embedding/ollama.py
# Only import from core (protocols)
from src.core.embedding import EmbeddingClient  # ✅
```

**Dependency rule:** Infra can import from core, but not domain/apps.

---

### ❌ Hardcoded Configuration

**Bad:**
```python
# src/infra/embedding/ollama.py
class OllamaEmbedding:
    def __init__(self):
        self.url = "http://localhost:11434"  # ❌ Hardcoded
```

**Good:**
```python
# src/infra/embedding/ollama.py
class OllamaEmbedding:
    def __init__(self, base_url: str):
        self.url = base_url  # ✅ Injected

# Factory provides config
def get_embedding_client():
    return OllamaEmbedding(base_url=os.getenv("OLLAMA_URL"))
```

---

## 📚 Related Documentation

- [Architecture Overview](../architecture/overview.md) - Layer dependencies
- [Core Layer](../core/README.md) - Protocol definitions
- [Adding Integrations](adding-integrations.md) - How to add new vendors
- [Factories](factories.md) - Dependency injection

---

**[⬆️ Documentation Home](../README.md) | [Milvus Setup ➡️](milvus.md)**

*Last updated: 2025-12-18*
