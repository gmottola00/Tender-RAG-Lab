# Migration Guide: Integrating rag-toolkit into Tender-RAG-Lab

**Version:** 1.0.0  
**Date:** December 22, 2024  
**Target rag-toolkit version:** v0.1.0  
**Status:** Ready for execution

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Migration Checklist](#pre-migration-checklist)
3. [Migration Strategy](#migration-strategy)
4. [Phase 1: Protocol Imports (Week 1)](#phase-1-protocol-imports-week-1)
5. [Phase 2: RAG Modules (Week 2)](#phase-2-rag-modules-week-2)
6. [Phase 3: Chunking Modules (Week 3)](#phase-3-chunking-modules-week-3)
7. [Phase 4: Vector Store (Week 4)](#phase-4-vector-store-week-4)
8. [Phase 5: Cleanup (Week 5)](#phase-5-cleanup-week-5)
9. [Import Mapping Reference](#import-mapping-reference)
10. [Testing Strategy](#testing-strategy)
11. [Rollback Procedures](#rollback-procedures)
12. [Known Issues & Solutions](#known-issues--solutions)
13. [Quick Start Alternative](#quick-start-alternative)

---

## Overview

### Why Migrate?

The `rag-toolkit` package was extracted from Tender-RAG-Lab's core modules to provide:
- **Reusability**: Share RAG components across multiple projects
- **Maintainability**: Centralized updates and bug fixes
- **Testing**: Comprehensive test coverage (28 tests, 19% coverage)
- **Documentation**: Professional Sphinx documentation
- **Standards**: Protocol-based architecture for flexibility

### What Changes?

- ✅ **Zero Breaking Changes**: Protocol-based design ensures compatibility
- ✅ **Domain Code Preserved**: `TenderChunk`, `TenderService`, etc. remain untouched
- ✅ **Import Remapping**: Main change is updating import paths
- ⚠️ **One Exception**: `Chunk`/`TokenChunk` moved from `types.py` to `models.py`

### Compatibility Status

| Component | Status | Risk Level | Notes |
|-----------|--------|------------|-------|
| Protocols (EmbeddingClient, LLMClient) | ✅ 100% Compatible | ZERO | Type hints only |
| RAG Pipeline | ✅ 100% Compatible | LOW | Identical implementation |
| Chunking | ✅ 99% Compatible | MEDIUM | Import path change |
| Vector Store | ✅ 100% Compatible | HIGH | Database operations |
| Domain Models (TenderChunk) | ✅ 100% Compatible | ZERO | Protocol-compliant |

---

## Pre-Migration Checklist

### 1. Environment Setup

```bash
# Ensure rag-toolkit is installed
cd /Users/gianmarcomottola/Desktop/projects/Tender-RAG-Lab
source .venv/bin/activate
pip install -e /Users/gianmarcomottola/Desktop/projects/Rag-Toolkit

# Verify installation
python -c "import rag_toolkit; print(rag_toolkit.__version__)"
# Expected output: 0.1.0
```

### 2. Backup & Version Control

```bash
# Create migration branch
git checkout -b migration/rag-toolkit-integration

# Tag current state for rollback
git tag pre-migration-backup

# Create database backup (if applicable)
pg_dump tender_db > backups/pre_migration_$(date +%Y%m%d).sql
```

### 3. Test Suite Validation

```bash
# Run existing tests to establish baseline
pytest tests/ -v --tb=short

# Record current coverage
pytest tests/ --cov=src --cov-report=html
# Save coverage report: htmlcov/index.html
```

### 4. Documentation Review

Read the following before starting:
- [rag-toolkit Documentation](https://gmottola00.github.io/rag-toolkit/)
- [rag-toolkit CHANGELOG](https://github.com/gmottola00/rag-toolkit/blob/main/CHANGELOG.md)
- [Tender-RAG-Lab Architecture](docs/architecture/)

---

## Migration Strategy

### Recommended Approach: **Gradual Migration** (5 weeks)

Migrate in phases with testing after each step. This minimizes risk and allows for incremental validation.

### Alternative: **Quick Start** (2 hours + gradual)

See [Quick Start Alternative](#quick-start-alternative) section for rapid compatibility testing.

---

## Phase 1: Protocol Imports (Week 1)

**Risk Level:** 🟢 ZERO  
**Estimated Time:** 2-3 hours  
**Rollback Difficulty:** Easy

### Overview

Update Protocol imports in infrastructure layer (`src/infra/`). These are type hints only—no runtime behavior changes.

### Files to Update

#### 1.1 Embedding Clients

**File:** `src/infra/embedding/ollama.py`

```python
# BEFORE
from src.core.embedding.base import EmbeddingClient

# AFTER
from rag_toolkit.core.embedding import EmbeddingClient
```

**File:** `src/infra/embedding/openai_embedding.py`

```python
# BEFORE
from src.core.embedding.base import EmbeddingClient

# AFTER
from rag_toolkit.core.embedding import EmbeddingClient
```

#### 1.2 LLM Clients

**File:** `src/infra/llm/ollama.py`

```python
# BEFORE
from src.core.llm.base import LLMClient

# AFTER
from rag_toolkit.core.llm import LLMClient
```

**File:** `src/infra/llm/openai_llm.py`

```python
# BEFORE
from src.core.llm.base import LLMClient

# AFTER
from rag_toolkit.core.llm import LLMClient
```

#### 1.3 Vector Store Clients

**File:** `src/infra/vector/milvus_client.py` (if exists)

```python
# BEFORE
from src.core.index.vector.database import VectorStoreClient

# AFTER
from rag_toolkit.core.index.vector import VectorStoreClient
```

### Testing Phase 1

```bash
# Run type checking
mypy src/infra/ --strict

# Run unit tests for infrastructure layer
pytest tests/test_infra/ -v

# Verify imports work
python -c "
from src.infra.embedding.ollama import OllamaEmbedding
from src.infra.llm.ollama import OllamaLLM
print('✅ Phase 1 imports successful')
"
```

### Validation Checklist

- [ ] All type hints resolve correctly
- [ ] No import errors when loading modules
- [ ] Existing tests pass without modification
- [ ] IDE autocomplete works with new imports

### Rollback

```bash
# If issues arise, revert the branch
git checkout src/infra/
git clean -fd src/infra/
```

---

## Phase 2: RAG Modules (Week 2)

**Risk Level:** 🟡 LOW  
**Estimated Time:** 4-6 hours  
**Rollback Difficulty:** Easy

### Overview

Replace RAG module implementations with rag-toolkit equivalents. These are identical implementations, just changing the import source.

### Files to Update

#### 2.1 RAG Pipeline

**File:** `src/core/rag/pipeline.py`

**Action:** Delete entire file (will use rag-toolkit version)

Before deleting, verify no custom logic exists:

```bash
# Compare with rag-toolkit
diff src/core/rag/pipeline.py \
     /Users/gianmarcomottola/Desktop/projects/Rag-Toolkit/src/rag_toolkit/rag/pipeline.py

# If identical, safe to delete
git rm src/core/rag/pipeline.py
```

#### 2.2 RAG Models

**File:** `src/core/rag/models.py`

```bash
# Compare and delete if identical
diff src/core/rag/models.py \
     /Users/gianmarcomottola/Desktop/projects/Rag-Toolkit/src/rag_toolkit/rag/models.py

git rm src/core/rag/models.py
```

#### 2.3 Context Assembler

**File:** `src/core/rag/assembler.py`

```bash
git rm src/core/rag/assembler.py
```

#### 2.4 Rerankers

**File:** `src/core/rag/rerankers.py`

```bash
git rm src/core/rag/rerankers.py
```

#### 2.5 Query Rewriter

**File:** `src/core/rag/rewriter.py`

```bash
git rm src/core/rag/rewriter.py
```

### Update Import Statements

**Files to search and replace:**
- `src/services/*.py`
- `src/api/routers/*.py`
- `src/domain/tender/search/*.py`

**Search Pattern:**

```python
from src.core.rag.pipeline import RAGPipeline
from src.core.rag.models import RAGConfig, RAGRequest, RAGResponse
from src.core.rag.assembler import ContextAssembler
from src.core.rag.rerankers import Reranker, CrossEncoderReranker
from src.core.rag.rewriter import QueryRewriter
```

**Replace With:**

```python
from rag_toolkit.rag import RAGPipeline
from rag_toolkit.rag.models import RAGConfig, RAGRequest, RAGResponse
from rag_toolkit.rag.assembler import ContextAssembler
from rag_toolkit.rag.rerankers import Reranker, CrossEncoderReranker
from rag_toolkit.rag.rewriter import QueryRewriter
```

### Automated Search & Replace

```bash
# Find all files importing from src.core.rag
grep -r "from src.core.rag" src/ --include="*.py"

# Replace imports (macOS sed)
find src/ -name "*.py" -exec sed -i '' 's/from src\.core\.rag/from rag_toolkit.rag/g' {} +

# Linux sed (if applicable)
# find src/ -name "*.py" -exec sed -i 's/from src\.core\.rag/from rag_toolkit.rag/g' {} +
```

### Testing Phase 2

```bash
# Run RAG-related tests
pytest tests/test_rag/ -v
pytest tests/test_services/ -v -k "rag"

# Integration test
python -c "
from rag_toolkit.rag import RAGPipeline, RAGConfig
from src.infra.llm.ollama import OllamaLLM
from src.infra.embedding.ollama import OllamaEmbedding

config = RAGConfig(
    embedding_client=OllamaEmbedding(),
    llm_client=OllamaLLM(),
    top_k=5
)
pipeline = RAGPipeline(config)
print('✅ Phase 2 RAG pipeline instantiation successful')
"
```

### Validation Checklist

- [ ] RAG pipeline initializes without errors
- [ ] All RAG tests pass
- [ ] API endpoints using RAG still work
- [ ] No import errors in services layer

---

## Phase 3: Chunking Modules (Week 3)

**Risk Level:** 🟠 MEDIUM  
**Estimated Time:** 6-8 hours  
**Rollback Difficulty:** Medium

### Overview

Migrate chunking modules. **Critical:** `Chunk` and `TokenChunk` have moved from `types.py` (Protocol) to `models.py` (concrete implementation).

### Breaking Change Details

**What Changed:**

In rag-toolkit v0.1.0:
- `Chunk` and `TokenChunk` are now in `rag_toolkit.core.chunking.models` (dataclasses)
- Protocol definitions remain in `rag_toolkit.core.chunking.types` as `ChunkLike` and `TokenChunkLike`

**Why This Matters:**

```python
# OLD (won't work - Protocols can't be instantiated)
from src.core.chunking.types import Chunk
chunk = Chunk(content="text", metadata={})  # ❌ TypeError

# NEW (correct)
from rag_toolkit.core.chunking.models import Chunk
chunk = Chunk(content="text", metadata={})  # ✅ Works
```

### Files to Update

#### 3.1 Delete Core Chunking Files

```bash
# Verify files are identical before deleting
diff src/core/chunking/chunking.py \
     /Users/gianmarcomottola/Desktop/projects/Rag-Toolkit/src/rag_toolkit/core/chunking/chunking.py

diff src/core/chunking/dynamic_chunker.py \
     /Users/gianmarcomottola/Desktop/projects/Rag-Toolkit/src/rag_toolkit/core/chunking/dynamic_chunker.py

# If identical, delete
git rm src/core/chunking/types.py
git rm src/core/chunking/chunking.py
git rm src/core/chunking/dynamic_chunker.py
```

#### 3.2 Update Domain Schemas

**IMPORTANT:** `TenderChunk` and `TenderTokenChunk` stay in `src/schemas/chunking.py` but need updated imports.

**File:** `src/schemas/chunking.py`

```python
# BEFORE
from src.core.chunking.types import Chunk as BaseChunk, TokenChunk as BaseTokenChunk

# AFTER
from rag_toolkit.core.chunking.models import Chunk as BaseChunk, TokenChunk as BaseTokenChunk
from rag_toolkit.core.chunking.types import ChunkLike, TokenChunkLike  # For type hints

@dataclass
class TenderChunk(BaseChunk):
    """Domain-specific chunk with tender metadata."""
    tender_id: str
    lot_id: Optional[str] = None
    section_type: Optional[str] = None
    
    # ✅ Still Protocol-compatible due to inheritance

@dataclass
class TenderTokenChunk(BaseTokenChunk):
    """Domain-specific token chunk with tender metadata."""
    tender_id: str
    lot_id: Optional[str] = None
    section_type: Optional[str] = None
```

#### 3.3 Update Chunking Service

**File:** `src/services/chunking_service.py` (if exists)

```python
# BEFORE
from src.core.chunking import DynamicChunker, TokenChunker
from src.core.chunking.types import Chunk, TokenChunk

# AFTER
from rag_toolkit.core.chunking import DynamicChunker, TokenChunker
from rag_toolkit.core.chunking.models import Chunk, TokenChunk
```

#### 3.4 Update Ingestion Pipeline

**File:** `src/core/ingestion/ingestion_service.py`

Search for all chunking imports and replace:

```python
# BEFORE
from src.core.chunking.dynamic_chunker import DynamicChunker
from src.core.chunking.types import Chunk

# AFTER
from rag_toolkit.core.chunking import DynamicChunker
from rag_toolkit.core.chunking.models import Chunk
```

### Automated Migration Script

Create `scripts/migrate_chunking_imports.py`:

```python
#!/usr/bin/env python3
"""Migrate chunking imports from src.core to rag_toolkit."""

import re
from pathlib import Path

def update_file(file_path: Path) -> bool:
    """Update imports in a single file."""
    content = file_path.read_text()
    original = content
    
    # Replace types imports
    content = re.sub(
        r'from src\.core\.chunking\.types import (.*)',
        r'from rag_toolkit.core.chunking.models import \1',
        content
    )
    
    # Replace module imports
    content = re.sub(
        r'from src\.core\.chunking import (.*)',
        r'from rag_toolkit.core.chunking import \1',
        content
    )
    
    # Replace dynamic_chunker imports
    content = re.sub(
        r'from src\.core\.chunking\.dynamic_chunker import (.*)',
        r'from rag_toolkit.core.chunking import \1',
        content
    )
    
    if content != original:
        file_path.write_text(content)
        print(f"✅ Updated {file_path}")
        return True
    return False

def main():
    """Migrate all Python files."""
    src_dir = Path("src")
    updated = 0
    
    for py_file in src_dir.rglob("*.py"):
        if update_file(py_file):
            updated += 1
    
    print(f"\n🎉 Updated {updated} files")

if __name__ == "__main__":
    main()
```

Run the script:

```bash
python scripts/migrate_chunking_imports.py
```

### Testing Phase 3

```bash
# Test chunking directly
python -c "
from rag_toolkit.core.chunking import DynamicChunker
from rag_toolkit.core.chunking.models import Chunk
from src.schemas.chunking import TenderChunk

# Test base chunking
chunker = DynamicChunker(chunk_size=512, overlap=50)
chunks = chunker.build_chunks('Sample text', metadata={'source': 'test'})
print(f'✅ Created {len(chunks)} chunks')

# Test TenderChunk compatibility
tender_chunk = TenderChunk(
    content='Test content',
    metadata={'page': 1},
    tender_id='T123',
    lot_id='L456',
    section_type='description'
)
print(f'✅ TenderChunk created: {tender_chunk.tender_id}')
"

# Run full chunking test suite
pytest tests/test_chunking/ -v
pytest tests/test_ingestion/ -v -k "chunk"
```

### Validation Checklist

- [ ] Chunking service instantiates correctly
- [ ] `TenderChunk` and `TenderTokenChunk` work as before
- [ ] Ingestion pipeline processes documents successfully
- [ ] All chunking tests pass
- [ ] No import errors in domain layer

### Common Issues

**Issue:** `TypeError: Protocols cannot be instantiated`

**Solution:** Make sure you're importing from `models`, not `types`:

```python
# ❌ Wrong
from rag_toolkit.core.chunking.types import Chunk

# ✅ Correct
from rag_toolkit.core.chunking.models import Chunk
```

---

## Phase 4: Vector Store (Week 4)

**Risk Level:** 🔴 HIGH  
**Estimated Time:** 8-12 hours  
**Rollback Difficulty:** Hard

### Overview

Migrate Milvus vector store operations. **High risk** due to database interactions—proceed with caution.

### Pre-Phase 4 Backup

```bash
# Backup Milvus collections
python scripts/backup_milvus_collections.py

# Backup database metadata
pg_dump tender_db -t vector_metadata > backups/vector_metadata_$(date +%Y%m%d).sql
```

### Files to Update

#### 4.1 Vector Store Core Modules

All files in `src/core/index/vector/` are identical to rag-toolkit. Delete them:

```bash
# Verify first
for file in src/core/index/vector/*.py; do
    toolkit_file="/Users/gianmarcomottola/Desktop/projects/Rag-Toolkit/src/rag_toolkit/core/index/vector/$(basename $file)"
    if [ -f "$toolkit_file" ]; then
        echo "Comparing $file"
        diff "$file" "$toolkit_file" || echo "⚠️  Differences found in $file"
    fi
done

# If all identical, delete
git rm src/core/index/vector/collection.py
git rm src/core/index/vector/config.py
git rm src/core/index/vector/connection.py
git rm src/core/index/vector/data.py
git rm src/core/index/vector/database.py
git rm src/core/index/vector/exceptions.py
git rm src/core/index/vector/explorer.py
git rm src/core/index/vector/service.py
```

#### 4.2 Update TenderMilvusIndexer

**File:** `src/domain/tender/indexing/indexer.py`

This is a **wrapper** around Milvus operations. Update imports only:

```python
# BEFORE
from src.core.index.vector.database import MilvusVectorDatabase
from src.core.index.vector.config import MilvusConfig
from src.core.index.vector.data import VectorData

# AFTER
from rag_toolkit.core.index.vector import MilvusVectorDatabase, MilvusConfig, VectorData
```

**Review Custom Logic:** Check if `TenderMilvusIndexer` has any custom logic beyond standard CRUD operations. If yes, document it.

#### 4.3 Update Search Services

**File:** `src/domain/tender/search/vector_searcher.py`

```python
# BEFORE
from src.core.index.vector.database import MilvusVectorDatabase
from src.core.index.search.vector_searcher import VectorSearcher

# AFTER
from rag_toolkit.core.index.vector import MilvusVectorDatabase
from rag_toolkit.core.index.search import VectorSearcher
```

#### 4.4 Update API Routes

**File:** `src/api/routers/milvus_route.py`

```python
# BEFORE
from src.core.index.vector.explorer import MilvusExplorer
from src.core.index.vector.service import MilvusService

# AFTER
from rag_toolkit.core.index.vector import MilvusExplorer, MilvusService
```

### Migration Script

Create `scripts/migrate_vector_imports.py`:

```python
#!/usr/bin/env python3
"""Migrate vector store imports from src.core to rag_toolkit."""

import re
from pathlib import Path

def update_file(file_path: Path) -> bool:
    """Update vector imports in a single file."""
    content = file_path.read_text()
    original = content
    
    # Replace vector module imports
    patterns = [
        (r'from src\.core\.index\.vector\.(\w+) import', r'from rag_toolkit.core.index.vector import'),
        (r'from src\.core\.index\.vector import', r'from rag_toolkit.core.index.vector import'),
        (r'from src\.core\.index\.search\.(\w+) import', r'from rag_toolkit.core.index.search import'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    if content != original:
        file_path.write_text(content)
        print(f"✅ Updated {file_path}")
        return True
    return False

def main():
    """Migrate all vector-related files."""
    paths = [
        Path("src/domain/tender/indexing"),
        Path("src/domain/tender/search"),
        Path("src/api/routers"),
        Path("src/services"),
    ]
    
    updated = 0
    for base_path in paths:
        if not base_path.exists():
            continue
        for py_file in base_path.rglob("*.py"):
            if update_file(py_file):
                updated += 1
    
    print(f"\n🎉 Updated {updated} files")

if __name__ == "__main__":
    main()
```

Run:

```bash
python scripts/migrate_vector_imports.py
```

### Testing Phase 4

```bash
# Test Milvus connection
python -c "
from rag_toolkit.core.index.vector import MilvusVectorDatabase, MilvusConfig

config = MilvusConfig(
    host='localhost',
    port=19530,
    collection_name='test_collection'
)

db = MilvusVectorDatabase(config)
print('✅ Milvus connection successful')
"

# Test indexing operations
pytest tests/test_index/ -v
pytest tests/test_domain/test_indexing/ -v

# Integration test with real data (staging environment)
python scripts/test_vector_migration.py
```

### Validation Checklist

- [ ] Milvus connection works
- [ ] Can create/delete collections
- [ ] Can insert vectors
- [ ] Can search vectors
- [ ] TenderMilvusIndexer works as before
- [ ] No data loss in existing collections
- [ ] Performance benchmarks match baseline

### Rollback Procedure

If issues occur:

```bash
# Stop application
make stop

# Restore Milvus backup
python scripts/restore_milvus_collections.py

# Revert code changes
git checkout src/domain/tender/indexing/
git checkout src/domain/tender/search/
git checkout src/api/routers/milvus_route.py

# Restore src/core/index/vector/ from backup
git checkout pre-migration-backup -- src/core/index/vector/

# Restart application
make start
```

---

## Phase 5: Cleanup (Week 5)

**Risk Level:** 🟢 ZERO  
**Estimated Time:** 2-4 hours  
**Rollback Difficulty:** Easy

### Overview

Remove deprecated `src/core/` modules and finalize migration.

### 5.1 Remove Deprecated Directories

```bash
# Verify no remaining imports from src.core
grep -r "from src\.core\." src/ --include="*.py"
# Expected: No results (or only domain-specific code)

# If clean, remove directories
git rm -r src/core/chunking/
git rm -r src/core/embedding/
git rm -r src/core/llm/
git rm -r src/core/rag/
git rm -r src/core/index/vector/
git rm -r src/core/index/search/

# Keep domain-specific modules
# src/core/ingestion/ - keep (domain-specific logic)
# src/core/eval/ - keep (if exists, custom evaluation)
```

### 5.2 Update Documentation

Update the following files to reference rag-toolkit:

**File:** `README.md`

```markdown
## Architecture

Tender-RAG-Lab uses [rag-toolkit](https://github.com/gmottola00/rag-toolkit) 
for core RAG operations:

- **Chunking**: `rag-toolkit` DynamicChunker and TokenChunker
- **Embeddings**: Protocol-based embedding clients (Ollama, OpenAI)
- **Vector Store**: Milvus integration via `rag-toolkit`
- **RAG Pipeline**: Full pipeline with reranking and context assembly

Domain-specific extensions:
- `TenderChunk` / `TenderTokenChunk`: Tender metadata
- `TenderMilvusIndexer`: Specialized indexing for tender documents
- `TenderSearcher`: Hybrid search strategies for tenders
```

**File:** `docs/architecture.md`

Add section on rag-toolkit integration:

```markdown
## RAG Toolkit Integration

### Core Components from rag-toolkit

| Component | Source | Purpose |
|-----------|--------|---------|
| Protocols | `rag_toolkit.core.protocols` | EmbeddingClient, LLMClient, VectorStoreClient |
| Chunking | `rag_toolkit.core.chunking` | DynamicChunker, TokenChunker |
| RAG Pipeline | `rag_toolkit.rag` | Full RAG pipeline with reranking |
| Vector Store | `rag_toolkit.core.index.vector` | Milvus operations |

### Domain Extensions

| Component | Location | Purpose |
|-----------|----------|---------|
| TenderChunk | `src/schemas/chunking.py` | Tender-specific chunk metadata |
| TenderMilvusIndexer | `src/domain/tender/indexing/` | Specialized indexing logic |
| TenderSearcher | `src/domain/tender/search/` | Hybrid search for tenders |
```

### 5.3 Update Dependencies

**File:** `pyproject.toml`

Ensure rag-toolkit is listed:

```toml
[project]
dependencies = [
    "rag-toolkit @ git+https://github.com/gmottola00/rag-toolkit.git@v0.1.0",
    # ... other dependencies
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    # ... other dev dependencies
]
```

### 5.4 Update Import Statements in Tests

```bash
# Search for any remaining old imports in tests
grep -r "from src\.core\." tests/ --include="*.py"

# Update test imports
find tests/ -name "*.py" -exec sed -i '' 's/from src\.core/from rag_toolkit/g' {} +
```

### 5.5 Final Testing

```bash
# Run full test suite
pytest tests/ -v --tb=short

# Check coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Integration tests
make test-integration

# Load tests (if applicable)
make test-load
```

### 5.6 Commit Migration

```bash
# Stage all changes
git add -A

# Commit with detailed message
git commit -m "feat: migrate to rag-toolkit v0.1.0

- Replaced src/core modules with rag-toolkit imports
- Updated domain schemas to use rag-toolkit base classes
- Maintained domain-specific extensions (TenderChunk, TenderService)
- Removed deprecated src/core/ directories
- Updated documentation and dependencies

Breaking changes:
- None (Protocol-based design ensures compatibility)

Migration details:
- Phase 1: Protocol imports (zero risk)
- Phase 2: RAG modules (low risk)
- Phase 3: Chunking (medium risk - import path change)
- Phase 4: Vector store (high risk - validated)
- Phase 5: Cleanup (complete)

Tests: All passing (X tests, Y% coverage)
"

# Merge to main
git checkout main
git merge migration/rag-toolkit-integration

# Tag migration completion
git tag migration-complete-v0.1.0

# Push changes
git push origin main --tags
```

---

## Import Mapping Reference

Complete before/after reference for all imports.

### Protocols

| Before | After |
|--------|-------|
| `from src.core.embedding.base import EmbeddingClient` | `from rag_toolkit.core.embedding import EmbeddingClient` |
| `from src.core.llm.base import LLMClient` | `from rag_toolkit.core.llm import LLMClient` |
| `from src.core.index.vector.database import VectorStoreClient` | `from rag_toolkit.core.index.vector import VectorStoreClient` |

### Chunking

| Before | After |
|--------|-------|
| `from src.core.chunking import DynamicChunker` | `from rag_toolkit.core.chunking import DynamicChunker` |
| `from src.core.chunking import TokenChunker` | `from rag_toolkit.core.chunking import TokenChunker` |
| `from src.core.chunking.types import Chunk` | `from rag_toolkit.core.chunking.models import Chunk` ⚠️ |
| `from src.core.chunking.types import TokenChunk` | `from rag_toolkit.core.chunking.models import TokenChunk` ⚠️ |
| `from src.core.chunking.dynamic_chunker import DynamicChunker` | `from rag_toolkit.core.chunking import DynamicChunker` |

⚠️ **Critical:** Note the change from `types` to `models` for concrete classes.

### RAG

| Before | After |
|--------|-------|
| `from src.core.rag.pipeline import RAGPipeline` | `from rag_toolkit.rag import RAGPipeline` |
| `from src.core.rag.models import RAGConfig, RAGRequest, RAGResponse` | `from rag_toolkit.rag.models import RAGConfig, RAGRequest, RAGResponse` |
| `from src.core.rag.assembler import ContextAssembler` | `from rag_toolkit.rag.assembler import ContextAssembler` |
| `from src.core.rag.rerankers import Reranker, CrossEncoderReranker` | `from rag_toolkit.rag.rerankers import Reranker, CrossEncoderReranker` |
| `from src.core.rag.rewriter import QueryRewriter` | `from rag_toolkit.rag.rewriter import QueryRewriter` |

### Vector Store

| Before | After |
|--------|-------|
| `from src.core.index.vector.database import MilvusVectorDatabase` | `from rag_toolkit.core.index.vector import MilvusVectorDatabase` |
| `from src.core.index.vector.config import MilvusConfig` | `from rag_toolkit.core.index.vector import MilvusConfig` |
| `from src.core.index.vector.connection import MilvusConnection` | `from rag_toolkit.core.index.vector import MilvusConnection` |
| `from src.core.index.vector.data import VectorData` | `from rag_toolkit.core.index.vector import VectorData` |
| `from src.core.index.vector.service import MilvusService` | `from rag_toolkit.core.index.vector import MilvusService` |
| `from src.core.index.vector.explorer import MilvusExplorer` | `from rag_toolkit.core.index.vector import MilvusExplorer` |

### Search

| Before | After |
|--------|-------|
| `from src.core.index.search.vector_searcher import VectorSearcher` | `from rag_toolkit.core.index.search import VectorSearcher` |
| `from src.core.index.search.keyword_searcher import KeywordSearcher` | `from rag_toolkit.core.index.search import KeywordSearcher` |
| `from src.core.index.search.hybrid_searcher import HybridSearcher` | `from rag_toolkit.core.index.search import HybridSearcher` |
| `from src.core.index.search.reranker import Reranker` | `from rag_toolkit.core.index.search import Reranker` |

---

## Testing Strategy

### Unit Testing

After each phase, run unit tests for affected modules:

```bash
# Phase 1: Infrastructure tests
pytest tests/test_infra/ -v

# Phase 2: RAG tests
pytest tests/test_rag/ -v
pytest tests/test_services/ -v -k "rag"

# Phase 3: Chunking tests
pytest tests/test_chunking/ -v
pytest tests/test_ingestion/ -v

# Phase 4: Vector store tests
pytest tests/test_index/ -v
pytest tests/test_domain/test_indexing/ -v
```

### Integration Testing

Test end-to-end workflows after critical phases:

```bash
# Create integration test script
cat > scripts/test_rag_integration.py << 'EOF'
#!/usr/bin/env python3
"""Integration test for rag-toolkit migration."""

from rag_toolkit.rag import RAGPipeline, RAGConfig
from rag_toolkit.core.chunking import DynamicChunker
from src.infra.embedding.ollama import OllamaEmbedding
from src.infra.llm.ollama import OllamaLLM
from src.schemas.chunking import TenderChunk

def test_full_pipeline():
    """Test complete RAG pipeline with TenderChunk."""
    # Setup
    embedding = OllamaEmbedding(model="nomic-embed-text")
    llm = OllamaLLM(model="llama3.2")
    
    config = RAGConfig(
        embedding_client=embedding,
        llm_client=llm,
        top_k=5
    )
    
    pipeline = RAGPipeline(config)
    
    # Test chunking with TenderChunk
    chunker = DynamicChunker(chunk_size=512, overlap=50)
    chunks = chunker.build_chunks(
        text="Sample tender document content...",
        metadata={"source": "integration_test"}
    )
    
    # Convert to TenderChunk
    tender_chunks = [
        TenderChunk(
            content=chunk.content,
            metadata=chunk.metadata,
            tender_id="T-TEST-001",
            lot_id="L-001",
            section_type="description"
        )
        for chunk in chunks
    ]
    
    print(f"✅ Created {len(tender_chunks)} TenderChunks")
    
    # Test RAG query (mock)
    # In real test, would query actual indexed data
    print("✅ Integration test passed")

if __name__ == "__main__":
    test_full_pipeline()
EOF

python scripts/test_rag_integration.py
```

### Performance Benchmarking

Compare performance before and after migration:

```bash
# Create benchmark script
cat > scripts/benchmark_migration.py << 'EOF'
#!/usr/bin/env python3
"""Benchmark rag-toolkit performance vs old implementation."""

import time
from rag_toolkit.core.chunking import DynamicChunker

def benchmark_chunking():
    """Benchmark chunking performance."""
    text = "Sample text " * 10000  # ~100KB
    chunker = DynamicChunker(chunk_size=512, overlap=50)
    
    start = time.time()
    chunks = chunker.build_chunks(text, metadata={})
    elapsed = time.time() - start
    
    print(f"Chunked {len(text)} chars into {len(chunks)} chunks")
    print(f"Time: {elapsed:.3f}s")
    print(f"Throughput: {len(text) / elapsed:.0f} chars/sec")

if __name__ == "__main__":
    benchmark_chunking()
EOF

python scripts/benchmark_migration.py
```

### Regression Testing

Ensure no regressions in existing functionality:

```bash
# Run full test suite with coverage
pytest tests/ \
    --cov=src \
    --cov-report=html \
    --cov-report=term \
    --tb=short \
    -v

# Check for any failing tests
# Expected: All tests pass (or same failures as pre-migration)
```

---

## Rollback Procedures

### Emergency Rollback (Production Issue)

If critical issues arise in production:

```bash
# 1. Revert to pre-migration tag
git checkout pre-migration-backup

# 2. Restore database (if needed)
psql tender_db < backups/pre_migration_YYYYMMDD.sql

# 3. Restore Milvus collections (if needed)
python scripts/restore_milvus_collections.py

# 4. Rebuild and restart
make build
make restart

# 5. Verify system health
make health-check
```

### Partial Rollback (Single Phase)

If a specific phase fails:

```bash
# Example: Rollback Phase 3 (Chunking)
git checkout src/core/chunking/
git checkout src/schemas/chunking.py
git checkout src/services/chunking_service.py
git clean -fd src/core/chunking/

# Reinstall dependencies
pip install -e .

# Restart services
make restart
```

### Rollback Checklist

- [ ] Application stops gracefully
- [ ] Database restored (if applicable)
- [ ] Milvus collections restored (if applicable)
- [ ] Code reverted to stable tag
- [ ] Dependencies reinstalled
- [ ] Services restarted
- [ ] Health checks pass
- [ ] Monitoring alerts cleared

---

## Known Issues & Solutions

### Issue 1: Import Error - "cannot import name 'Chunk'"

**Error:**

```python
ImportError: cannot import name 'Chunk' from 'rag_toolkit.core.chunking.types'
```

**Cause:** Trying to import concrete class from Protocol module.

**Solution:**

```python
# ❌ Wrong
from rag_toolkit.core.chunking.types import Chunk

# ✅ Correct
from rag_toolkit.core.chunking.models import Chunk
```

### Issue 2: Type Checking Fails with mypy

**Error:**

```
error: Argument 1 has incompatible type "TenderChunk"; expected "Chunk"
```

**Cause:** mypy doesn't recognize Protocol compatibility.

**Solution:** Add type ignore or use Protocol type hints:

```python
from rag_toolkit.core.chunking.types import ChunkLike

def process_chunk(chunk: ChunkLike) -> None:
    """Process any chunk-like object."""
    # TenderChunk is compatible due to Protocol
    ...
```

### Issue 3: Milvus Connection Timeout

**Error:**

```
MilvusException: <MilvusException: (code=1, message=Fail connecting to server)>
```

**Cause:** Milvus not running or connection config incorrect.

**Solution:**

```bash
# Check Milvus status
docker ps | grep milvus

# Start Milvus if not running
docker-compose up -d milvus-standalone

# Verify connection
python -c "
from pymilvus import connections
connections.connect(host='localhost', port=19530)
print('✅ Milvus connected')
"
```

### Issue 4: Missing rag-toolkit Dependency

**Error:**

```
ModuleNotFoundError: No module named 'rag_toolkit'
```

**Cause:** Package not installed or virtual environment not activated.

**Solution:**

```bash
# Activate virtual environment
source .venv/bin/activate

# Install rag-toolkit
pip install -e /Users/gianmarcomottola/Desktop/projects/Rag-Toolkit

# Verify installation
python -c "import rag_toolkit; print(rag_toolkit.__version__)"
```

### Issue 5: Tests Fail After Phase 3

**Error:**

```
AttributeError: 'Chunk' object has no attribute 'to_dict'
```

**Cause:** Using old Chunk Protocol instead of new dataclass.

**Solution:** Ensure all code uses `rag_toolkit.core.chunking.models.Chunk`:

```python
from rag_toolkit.core.chunking.models import Chunk

chunk = Chunk(content="text", metadata={})
chunk.to_dict()  # ✅ Works
```

---

## Quick Start Alternative

For rapid validation before full migration, use the Quick Start approach:

### Step 1: Compatibility Test (30 minutes)

Create `tests/test_rag_toolkit_compatibility.py`:

```python
"""Quick compatibility test for rag-toolkit integration."""

import pytest
from rag_toolkit.core.chunking import DynamicChunker
from rag_toolkit.core.chunking.models import Chunk
from rag_toolkit.rag import RAGPipeline, RAGConfig
from src.schemas.chunking import TenderChunk
from src.infra.embedding.ollama import OllamaEmbedding
from src.infra.llm.ollama import OllamaLLM


def test_tender_chunk_protocol_compatibility():
    """Verify TenderChunk implements ChunkLike Protocol."""
    tender_chunk = TenderChunk(
        content="Test content",
        metadata={"page": 1},
        tender_id="T123",
        lot_id="L456",
        section_type="description"
    )
    
    # Should have all required ChunkLike attributes
    assert hasattr(tender_chunk, "content")
    assert hasattr(tender_chunk, "metadata")
    assert hasattr(tender_chunk, "to_dict")
    
    # Domain-specific fields should exist
    assert tender_chunk.tender_id == "T123"
    assert tender_chunk.lot_id == "L456"


def test_rag_toolkit_chunking():
    """Test rag-toolkit chunking works."""
    chunker = DynamicChunker(chunk_size=512, overlap=50)
    text = "Sample text " * 100
    
    chunks = chunker.build_chunks(text, metadata={"source": "test"})
    
    assert len(chunks) > 0
    assert all(isinstance(chunk, Chunk) for chunk in chunks)


def test_rag_pipeline_initialization():
    """Test RAG pipeline can initialize with Tender infrastructure."""
    embedding = OllamaEmbedding(model="nomic-embed-text")
    llm = OllamaLLM(model="llama3.2")
    
    config = RAGConfig(
        embedding_client=embedding,
        llm_client=llm,
        top_k=5
    )
    
    pipeline = RAGPipeline(config)
    assert pipeline is not None


@pytest.mark.integration
def test_full_rag_flow():
    """Integration test: Full RAG flow with TenderChunk."""
    # This would test actual indexing + search + RAG
    # Skip in unit tests, run separately
    pytest.skip("Run separately with: pytest -m integration")
```

Run the test:

```bash
pytest tests/test_rag_toolkit_compatibility.py -v
```

**Expected Result:** All tests pass ✅

### Step 2: Parallel Implementation (1 hour)

Use rag-toolkit for **new features only**, keep old code for existing features:

```python
# Example: New feature using rag-toolkit
from rag_toolkit.rag import RAGPipeline

def new_advanced_search(query: str) -> dict:
    """New search feature using rag-toolkit."""
    pipeline = RAGPipeline(config)
    return pipeline.query(query)

# Existing feature keeps old implementation
from src.core.rag.pipeline import RAGPipeline as OldRAGPipeline

def existing_search(query: str) -> dict:
    """Existing search using old implementation."""
    pipeline = OldRAGPipeline(config)
    return pipeline.query(query)
```

### Step 3: Gradual Migration (No Deadline)

After Quick Start validation, migrate gradually without pressure:

1. **Week 1-2:** Use rag-toolkit for all new code
2. **Week 3-4:** Migrate non-critical modules (RAG, chunking)
3. **Week 5-6:** Migrate critical modules (vector store)
4. **Week 7+:** Remove old code when confident

---

## Conclusion

### Migration Checklist Summary

- [ ] **Pre-Migration**
  - [ ] rag-toolkit installed and verified
  - [ ] Git branch created (`migration/rag-toolkit-integration`)
  - [ ] Database backup created
  - [ ] Baseline tests pass

- [ ] **Phase 1: Protocol Imports** (Week 1)
  - [ ] Update embedding client imports
  - [ ] Update LLM client imports
  - [ ] Update vector store client imports
  - [ ] Tests pass

- [ ] **Phase 2: RAG Modules** (Week 2)
  - [ ] Delete src/core/rag/ files
  - [ ] Update all RAG imports
  - [ ] RAG tests pass

- [ ] **Phase 3: Chunking** (Week 3)
  - [ ] Delete src/core/chunking/ files
  - [ ] Update Chunk/TokenChunk imports (models not types!)
  - [ ] Update TenderChunk imports
  - [ ] Chunking tests pass

- [ ] **Phase 4: Vector Store** (Week 4)
  - [ ] Backup Milvus collections
  - [ ] Delete src/core/index/vector/ files
  - [ ] Update TenderMilvusIndexer imports
  - [ ] Vector store tests pass
  - [ ] No data loss verified

- [ ] **Phase 5: Cleanup** (Week 5)
  - [ ] Remove deprecated src/core/ directories
  - [ ] Update documentation
  - [ ] Update pyproject.toml
  - [ ] All tests pass
  - [ ] Merge to main

### Success Criteria

✅ **All tests pass** (same or better than pre-migration)  
✅ **No import errors** in any module  
✅ **Domain models work** (TenderChunk, TenderService, etc.)  
✅ **Performance maintained** (benchmarks match baseline)  
✅ **Documentation updated** (README, architecture docs)  
✅ **Zero downtime** (if production deployment)

### Support & Resources

- **rag-toolkit Documentation:** https://gmottola00.github.io/rag-toolkit/
- **rag-toolkit GitHub:** https://github.com/gmottola00/rag-toolkit
- **rag-toolkit Issues:** https://github.com/gmottola00/rag-toolkit/issues
- **Tender-RAG-Lab Issues:** https://github.com/gmottola00/Tender-RAG-Lab/issues

### Questions?

If you encounter issues not covered in this guide:

1. Check [Known Issues](#known-issues--solutions)
2. Search rag-toolkit documentation
3. Review migration test results
4. Create an issue with details

---

**Good luck with the migration! 🚀**

**Last Updated:** December 22, 2024  
**Guide Version:** 1.0.0  
**Maintainer:** Gianmarco Mottola
