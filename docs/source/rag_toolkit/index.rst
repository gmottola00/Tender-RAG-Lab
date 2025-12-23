========================
rag_toolkit Integration
========================

This section documents how the Tender-RAG-Lab project integrates the **rag_toolkit** library
to implement a production-grade RAG system for Italian public procurement documents.

----

Overview
========

The integration follows a **protocol-based architecture** that cleanly separates:

- **Generic RAG components** (from ``rag_toolkit``) - Reusable across projects
- **Domain-specific logic** (in ``src/domain/``) - Tender-specific customization

This separation enables code reuse while maintaining the flexibility to customize
for the tender domain's unique requirements.

.. mermaid::

   graph TB
       A[FastAPI Layer] --> B[Domain Layer]
       B --> C[Infrastructure Layer]
       C --> D[rag_toolkit]
       
       style A fill:#e3f2fd
       style B fill:#fff3e0
       style C fill:#f3e5f5
       style D fill:#e8f5e9

Key Design Principles
=====================

Protocol-Based Design
---------------------

The library uses Python **Protocols** (PEP 544) instead of abstract base classes.
This provides:

- ✅ **Type safety** without inheritance
- ✅ **Structural subtyping** (duck typing with static checks)
- ✅ **Easy extension** in domain layer
- ✅ **Zero runtime overhead**

Example protocol:

.. code-block:: python

   from typing import Protocol
   
   class EmbeddingClient(Protocol):
       """Protocol for embedding generation."""
       
       def embed(self, text: str) -> list[float]:
           """Generate embedding vector for text."""
           ...

Clean Architecture Layers
--------------------------

**Dependency Rule**: Inner layers know nothing about outer layers.

.. code-block:: text

   ┌─────────────────────────────────────────┐
   │  API Layer (FastAPI, Routers)           │  ← HTTP, UI
   ├─────────────────────────────────────────┤
   │  Domain Layer (Business Logic)          │  ← Entities, Services
   ├─────────────────────────────────────────┤
   │  Infrastructure (Concrete Impl.)        │  ← Milvus, Supabase
   ├─────────────────────────────────────────┤
   │  rag_toolkit (Generic Components)       │  ← Protocols, Core
   └─────────────────────────────────────────┘

Factory Pattern
---------------

Centralized creation of complex component stacks:

.. code-block:: python

   from src.infra.factory import create_tender_stack
   
   # Creates indexer + searcher with proper configuration
   indexer, searcher = create_tender_stack(
       embed_client=embed_client,
       embedding_dim=768
   )

Core Components
===============

Chunking Pipeline
-----------------

**Two-stage process** for optimal retrieval:

1. **Dynamic Chunking** (``rag_toolkit.core.chunking.DynamicChunker``)
   
   - Splits by heading hierarchy (H1-H6)
   - Preserves document structure
   - Handles tables and lists

2. **Token Chunking** (``rag_toolkit.core.chunking.TokenChunker``)
   
   - Fixed token budget (400-800 tokens)
   - Overlap for context continuity
   - Ready for embedding

.. code-block:: python

   from rag_toolkit.core.chunking import DynamicChunker, TokenChunker
   
   # Stage 1: Structural chunks
   dyn_chunker = DynamicChunker(include_tables=True)
   structural_chunks = dyn_chunker.build_chunks(parsed_pages)
   
   # Stage 2: Token chunks
   token_chunker = TokenChunker(max_tokens=800, overlap_tokens=120)
   embeddable_chunks = token_chunker.chunk(structural_chunks)

Vector Store Integration
------------------------

**Milvus** via factory functions:

.. code-block:: python

   from rag_toolkit.infra.vectorstores.factory import (
       create_milvus_service,
       create_index_service
   )
   
   milvus = create_milvus_service()
   indexer = create_index_service(
       embedding_dim=768,
       embed_fn=embedding_function,
       collection_name="tender_chunks"
   )

RAG Pipeline
------------

Complete pipeline with rewriting, search, reranking, and generation:

.. code-block:: python

   from rag_toolkit.rag import RagPipeline
   from rag_toolkit.rag.rewriter import QueryRewriter
   from rag_toolkit.rag.rerankers import LLMReranker
   
   pipeline = RagPipeline(
       vector_searcher=vector_search,
       rewriter=QueryRewriter(llm),
       reranker=LLMReranker(llm),
       generator_llm=llm
   )
   
   response = pipeline.run(question="Find all requirements for Lot 2")

Domain Integration
==================

Custom Chunk Implementations
-----------------------------

Tender-specific chunks extend ``rag_toolkit`` protocols:

.. code-block:: python

   from dataclasses import dataclass
   from rag_toolkit.core.chunking.types import TokenChunkLike
   
   @dataclass
   class TenderTokenChunk:
       # Protocol-required fields
       id: str
       text: str
       section_path: str
       metadata: dict
       page_numbers: list[int]
       source_chunk_id: str
       
       # Domain extensions
       tender_id: str
       lot_id: str | None = None
       section_type: str = ""  # "requirements", "deadlines"

Domain Wrappers
---------------

**TenderMilvusIndexer** wraps generic ``IndexService``:

.. code-block:: python

   class TenderMilvusIndexer:
       def __init__(self, index_service: IndexService):
           self.index_service = index_service
       
       def upsert_token_chunks(self, chunks: Sequence[TokenChunkLike]):
           """Embed and index tender chunks."""
           # Custom schema mapping
           # Metadata extraction
           # Batch embedding
           ...

Configuration
=============

Environment Variables
---------------------

Key settings in ``.env``:

.. code-block:: bash

   # Milvus
   MILVUS_URI=http://localhost:19530
   MILVUS_COLLECTION=tender_chunks
   
   # Ollama
   OLLAMA_URL=http://localhost:11434
   OLLAMA_EMBED_MODEL=nomic-embed-text
   OLLAMA_LLM_MODEL=llama3.2

Managed in ``configs/config.py`` using ``pydantic-settings``.

Further Reading
===============

.. toctree::
   :maxdepth: 2
   
   pipeline
   search
   extending

----

**Next Steps**:

- :doc:`pipeline` - Deep dive into RAG pipeline components
- :doc:`search` - Search strategies and configuration
- :doc:`extending` - How to extend rag_toolkit protocols
