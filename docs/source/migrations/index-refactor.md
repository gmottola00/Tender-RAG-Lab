# Index System Refactor - Migration Guide

## Overview

The index system has been refactored to follow clean architecture principles, separating:
- **Abstractions** (`src/core/index/`) - Protocol definitions and generic services
- **Implementations** (`src/infra/vectorstores/`) - Concrete Milvus implementations
- **Business Logic** - Tender-specific wrappers maintaining backward compatibility

## What Changed

### New Structure

```
src/
├── core/index/
│   ├── base.py                    # Protocol definitions (NEW)
│   ├── service.py                 # Generic IndexService (NEW)
│   ├── search_strategies.py       # Generic search implementations (NEW)
│   ├── tender_indexer_v2.py       # Backward-compatible wrapper (NEW)
│   ├── tender_searcher_v2.py      # Backward-compatible wrapper (NEW)
│   ├── tender_indexer.py          # OLD - still works
│   ├── tender_searcher.py         # OLD - still works
│   └── vector/                    # OLD - kept for backward compatibility
│       └── (original files)
│
└── infra/vectorstores/
    ├── factory.py                 # Production factories (NEW)
    ├── __init__.py
    └── milvus/                    # Milvus implementations (NEW)
        ├── collection.py
        ├── config.py
        ├── connection.py
        ├── data.py
        ├── database.py
        ├── exceptions.py
        ├── explorer.py
        └── service.py
```

### Protocol Definitions (src/core/index/base.py)

New protocols define interfaces without coupling to Milvus:

```python
from src.core.index.base import (
    VectorStoreService,      # Main vector store interface
    VectorConnection,        # Connection management
    VectorCollectionManager, # Collection operations
    VectorDataManager,       # CRUD operations
    VectorDatabaseManager,   # Database management
    SearchStrategy,          # Search interface
    Reranker,               # Reranking interface
)
```

### Generic Services (src/core/index/service.py)

`IndexService` is the new generic orchestrator:

```python
from src.core.index.service import IndexService

# Works with any vector store implementing VectorStoreService protocol
index_service = IndexService(
    vector_store=milvus_service,  # Or pinecone, qdrant, etc.
    embedding_dim=1536,
    embed_fn=lambda texts: embed_client.embed_batch(texts),
    collection_name="my_collection"
)
```

### Search Strategies (src/core/index/search_strategies.py)

Generic search implementations:

```python
from src.core.index.search_strategies import (
    VectorSearch,    # Semantic search
    KeywordSearch,   # Keyword matching
    HybridSearch,    # Combined approach
)

# All strategies work with generic IndexService
vector_search = VectorSearch(index_service, embed_fn)
results = vector_search.search("query", top_k=5)
```

## Migration Paths

### Option 1: Zero Changes (Backward Compatible)

**Your existing code continues to work** - no changes needed:

```python
# OLD CODE - STILL WORKS
from src.core.index.vector.service import MilvusService
from src.core.index.tender_indexer import TenderMilvusIndexer
from src.core.index.tender_searcher import TenderSearcher

# Original usage unchanged
```

### Option 2: Use New Factory (Recommended)

Simplest migration - use `create_tender_stack`:

```python
# NEW CODE - RECOMMENDED
from src.infra.vectorstores.factory import create_tender_stack
from src.core.embedding.openai_embedding import OpenAIEmbedding

embed_client = OpenAIEmbedding(model="text-embedding-3-small")

# Single factory call creates both indexer and searcher
indexer, searcher = create_tender_stack(
    embed_client=embed_client,
    embedding_dim=1536,
    collection_name="tender_chunks"
)

# Same API as before
indexer.upsert_token_chunks(chunks)
results = searcher.hybrid_search("query")
```

### Option 3: Use Generic Services

For maximum flexibility and library extraction:

```python
# NEW CODE - MOST FLEXIBLE
from src.infra.vectorstores.factory import (
    create_milvus_service,
    create_index_service
)
from src.core.index.search_strategies import HybridSearch, VectorSearch, KeywordSearch
from src.core.embedding.openai_embedding import OpenAIEmbedding

# 1. Create components
embed_client = OpenAIEmbedding(model="text-embedding-3-small")
milvus_service = create_milvus_service()

# 2. Create generic index service
index_service = create_index_service(
    embedding_dim=1536,
    embed_fn=lambda texts: embed_client.embed_batch(texts),
    vector_store=milvus_service
)

# 3. Create search strategies
vector_search = VectorSearch(index_service, embed_client.embed)
keyword_search = KeywordSearch(index_service)
hybrid_search = HybridSearch(vector_search, keyword_search, alpha=0.7)

# 4. Use
results = hybrid_search.search("query", top_k=5)
```

## Factory Functions

### `create_milvus_service()`

Creates configured MilvusService with environment variable support:

```python
from src.infra.vectorstores.factory import create_milvus_service

# Use environment variables (MILVUS_URI, MILVUS_USER, etc.)
service = create_milvus_service()

# Or override
service = create_milvus_service(
    uri="http://localhost:19530",
    db_name="production",
    user="admin",
    password="secret"
)
```

### `create_index_service()`

Creates generic IndexService:

```python
from src.infra.vectorstores.factory import create_index_service

index_service = create_index_service(
    embedding_dim=1536,
    embed_fn=lambda texts: embed_client.embed_batch(texts),
    collection_name="my_collection",  # Optional
    metric_type="IP",                  # Optional
    index_type="HNSW"                  # Optional
)
```

### `create_tender_stack()`

One-liner for complete tender indexing/search setup:

```python
from src.infra.vectorstores.factory import create_tender_stack

indexer, searcher = create_tender_stack(
    embed_client=embed_client,
    embedding_dim=1536
)
```

## Key Benefits

### 1. **Testability**
- Mock protocols instead of concrete Milvus classes
- Dependency injection enables easy test doubles

### 2. **Swappable Implementations**
- Switch from Milvus to Pinecone by changing factory
- No changes to business logic

### 3. **Library Extraction**
- Core abstractions are vendor-agnostic
- Easy to extract as standalone RAG library

### 4. **Backward Compatibility**
- All existing code continues to work
- Gradual migration at your own pace

### 5. **Clear Separation**
- Core = abstractions (what)
- Infra = implementations (how)
- Apps = business logic (why)

## Testing

All imports validated:

```bash
# Protocol definitions
python -c "from src.core.index.base import VectorStoreService; print('✅')"

# Generic service
python -c "from src.core.index.service import IndexService; print('✅')"

# Milvus implementation
python -c "from src.infra.vectorstores.milvus import MilvusService; print('✅')"

# Factories
python -c "from src.infra.vectorstores.factory import create_tender_stack; print('✅')"

# Search strategies
python -c "from src.core.index.search_strategies import HybridSearch; print('✅')"

# Tender wrappers
python -c "from src.core.index.tender_indexer_v2 import TenderMilvusIndexer; print('✅')"
```

## Examples

See `examples/index_usage.py` for comprehensive usage examples:
- Factory usage
- Generic service usage
- Custom search strategies
- Low-level Milvus operations

## Old vs New Import Paths

| Old Import | New Import (Recommended) | Status |
|------------|-------------------------|---------|
| `from src.core.index.vector.service import MilvusService` | `from src.infra.vectorstores.milvus import MilvusService` | Both work |
| `from src.core.index.tender_indexer import TenderMilvusIndexer` | `from src.core.index.tender_indexer_v2 import TenderMilvusIndexer`<br>OR<br>`from src.infra.vectorstores.factory import create_tender_stack` | Both work |
| `from src.core.index.tender_searcher import TenderSearcher` | `from src.core.index.tender_searcher_v2 import TenderSearcher` | Both work |
| `from src.core.index.search.vector_searcher import VectorSearcher` | `from src.core.index.search_strategies import VectorSearch` | Both work |

## Next Steps

1. ✅ **Keep using existing code** - No urgency to migrate
2. 📝 **Try factory functions** - Test `create_tender_stack()` in new code
3. 🔄 **Gradual migration** - Update modules one at a time
4. 🧪 **Add tests** - Use protocols for easy mocking
5. 🚀 **Extract library** - Core abstractions ready for standalone package

## Questions?

- Protocol definitions: `src/core/index/base.py`
- Generic services: `src/core/index/service.py`
- Factories: `src/infra/vectorstores/factory.py`
- Examples: `examples/index_usage.py`
