========================
Extending rag_toolkit
========================

Guide for implementing custom protocols and extending the library for domain-specific needs.

----

Protocol Implementation
=======================

Understanding Protocols
-----------------------

Protocols define **structural interfaces** without requiring inheritance.

Key benefits:

- ✅ Type-safe duck typing
- ✅ No inheritance required
- ✅ Add domain-specific fields
- ✅ Static type checking (mypy)

Implementing ChunkLike
----------------------

Custom structural chunk with tender metadata:

.. code-block:: python

   from dataclasses import dataclass
   from rag_toolkit.core.chunking.types import ChunkLike
   
   @dataclass
   class TenderChunk:
       # Protocol-required fields
       id: str
       title: str
       heading_level: int
       text: str
       blocks: list[dict]
       page_numbers: list[int]
       
       # Domain extensions
       tender_id: str = ""
       section_type: str = ""  # "requirements", "deadlines"
       
       def to_dict(self) -> dict:
           """Convert to dictionary for processing."""
           return asdict(self)

Implementing TokenChunkLike
---------------------------

Embeddable chunks with metadata:

.. code-block:: python

   from rag_toolkit.core.chunking.types import TokenChunkLike
   
   @dataclass
   class TenderTokenChunk:
       # Protocol-required
       id: str
       text: str
       section_path: str
       metadata: dict
       page_numbers: list[int]
       source_chunk_id: str
       
       # Domain extensions
       tender_id: str
       lot_id: str | None = None

Creating Domain Wrappers
=========================

Indexer Wrapper
---------------

Wrap generic ``IndexService`` with tender-specific logic:

.. code-block:: python

   class TenderMilvusIndexer:
       def __init__(self, index_service: IndexService):
           self.index_service = index_service
       
       def upsert_token_chunks(self, chunks: Sequence[TokenChunkLike]):
           """Index tender chunks with custom schema."""
           # Extract texts
           texts = [chunk.text for chunk in chunks]
           
           # Generate embeddings
           embeddings = self.embed_fn(texts)
           
           # Build Milvus rows
           rows = [
               {
                   "id": chunk.id,
                   "text": chunk.text,
                   "tender_id": getattr(chunk, "tender_id", ""),
                   "embedding": emb
               }
               for chunk, emb in zip(chunks, embeddings)
           ]
           
           self.index_service.upsert(rows)

Searcher Wrapper
----------------

Provide convenient domain-specific search API:

.. code-block:: python

   class TenderSearcher:
       def __init__(self, indexer, embed_client):
           self.vector = VectorSearch(...)
           self.keyword = KeywordSearch(...)
           self.hybrid = HybridSearch(...)
       
       def search_by_tender(self, query: str, tender_id: str):
           """Search within specific tender."""
           return self.hybrid.search(
               query,
               filter_expr=f'tender_id == "{tender_id}"'
           )

Factory Functions
=================

Create Complete Stacks
-----------------------

Centralize component creation:

.. code-block:: python

   def create_tender_stack(
       embed_client: EmbeddingClient,
       embedding_dim: int
   ) -> tuple[TenderMilvusIndexer, TenderSearcher]:
       """Create indexer + searcher."""
       
       # Generic services from rag_toolkit
       milvus = create_milvus_service()
       index_service = create_index_service(...)
       
       # Domain wrappers
       indexer = TenderMilvusIndexer(index_service)
       searcher = TenderSearcher(indexer, embed_client)
       
       return indexer, searcher

Custom Chunking
===============

Extending Chunkers
------------------

Customize chunking behavior:

.. code-block:: python

   from rag_toolkit.core.chunking import DynamicChunker
   
   class TenderDynamicChunker(DynamicChunker):
       def build_chunks(self, pages: list[dict]):
           """Override to add tender-specific logic."""
           chunks = super().build_chunks(pages)
           
           # Add section_type classification
           for chunk in chunks:
               chunk.section_type = self._classify_section(chunk.title)
           
           return chunks
       
       def _classify_section(self, title: str) -> str:
           if "requisiti" in title.lower():
               return "requirements"
           elif "scadenza" in title.lower():
               return "deadlines"
           return "other"

Best Practices
==============

Type Hints
----------

Always use proper type hints for protocol compliance:

.. code-block:: python

   def process_chunks(chunks: Sequence[TokenChunkLike]) -> None:
       """Works with any TokenChunkLike implementation."""
       for chunk in chunks:
           print(chunk.text)

Testing
-------

Mock protocol implementations in tests:

.. code-block:: python

   from unittest.mock import Mock
   
   def test_indexer():
       mock_embed = Mock(spec=EmbeddingClient)
       mock_embed.embed.return_value = [0.1] * 768
       
       indexer = TenderMilvusIndexer(mock_index_service)
       # Test indexer logic

Documentation
-------------

Document protocol requirements:

.. code-block:: python

   @dataclass
   class CustomChunk:
       """Custom chunk implementation.
       
       Implements ChunkLike protocol from rag_toolkit.
       
       Attributes:
           id: Unique identifier
           text: Full chunk text
           tender_id: Associated tender (domain-specific)
       """
       ...

API Reference
=============

- :mod:`rag_toolkit.core.chunking.types`
- :class:`src.domain.tender.schemas.chunking.TenderChunk`
- :class:`src.domain.tender.schemas.chunking.TenderTokenChunk`
- :class:`src.domain.tender.indexing.indexer.TenderMilvusIndexer`
