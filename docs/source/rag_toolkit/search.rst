===================
Search Strategies
===================

Tender-RAG-Lab implements three search strategies from ``rag_toolkit`` for flexible
retrieval: vector search, keyword search, and hybrid search.

----

Available Strategies
====================

Vector Search
-------------

**Semantic similarity** using embeddings.

**When to use**:
- Natural language queries
- Conceptual matching
- Synonyms and paraphrasing

.. code-block:: python

   from rag_toolkit.core.index.search_strategies import VectorSearch
   
   searcher = VectorSearch(
       index_service=index_service,
       embed_fn=lambda q: embed_client.embed(q)
   )
   
   results = searcher.search("technical requirements", top_k=5)

Keyword Search
--------------

**Full-text matching** (BM25-style).

**When to use**:
- Exact term matching
- Code identifiers (CIG, CUP)
- Legal references

.. code-block:: python

   from rag_toolkit.core.index.search_strategies import KeywordSearch
   
   searcher = KeywordSearch(index_service=index_service)
   results = searcher.search("CIG: Z1234567890", top_k=5)

Hybrid Search
-------------

**Combined scoring** (alpha-weighted).

**When to use**:
- Best of both worlds
- Production default
- Balanced precision/recall

.. code-block:: python

   from rag_toolkit.core.index.search_strategies import HybridSearch
   
   hybrid = HybridSearch(
       vector_search=vector_searcher,
       keyword_search=keyword_searcher,
       alpha=0.7  # 0.7 vector + 0.3 keyword
   )
   
   results = hybrid.search(query, top_k=5)

Domain Integration
==================

TenderSearcher Facade
---------------------

The ``TenderSearcher`` class wraps all strategies:

.. code-block:: python

   from src.domain.tender.search.searcher import TenderSearcher
   
   searcher = TenderSearcher(indexer, embed_client)
   
   # Use any strategy
   results = searcher.vector_search(query, top_k=5)
   results = searcher.keyword_search(query, top_k=5)
   results = searcher.hybrid_search(query, top_k=5)

Filtering by Metadata
---------------------

Search within specific tenders or lots:

.. code-block:: python

   results = searcher.vector_search(
       query="requirements",
       top_k=10,
       filter_expr='tender_id == "abc-123"'
   )

Milvus Configuration
====================

Index Types
-----------

**HNSW** (default):
- High accuracy
- Fast search
- Memory intensive

.. code-block:: python

   index_params = {
       "index_type": "HNSW",
       "metric_type": "IP",  # Inner Product
       "params": {"M": 24, "efConstruction": 200}
   }

**IVF_SQ8** (large scale):
- Scalar quantization
- Lower memory
- Slightly slower

.. code-block:: python

   index_params = {
       "index_type": "IVF_SQ8",
       "metric_type": "IP",
       "params": {"nlist": 1024}
   }

Search Parameters
-----------------

Tuning retrieval quality:

.. code-block:: python

   search_params = {
       "metric_type": "IP",
       "params": {"ef": 64}  # Higher = better recall
   }

Performance Tuning
==================

Recommended Settings
--------------------

**Development**:

- top_k: 5-10
- HNSW: M=16, ef=32
- Small dataset (<100K vectors)

**Production**:

- top_k: 20-50
- HNSW: M=24, ef=64
- Hybrid search with alpha=0.7

Trade-offs
----------

+---------------+-------------+-------------+----------------+
| Strategy      | Accuracy    | Speed       | Use Case       |
+===============+=============+=============+================+
| Vector        | High        | Fast        | Semantic       |
+---------------+-------------+-------------+----------------+
| Keyword       | Medium      | Very Fast   | Exact match    |
+---------------+-------------+-------------+----------------+
| Hybrid        | Very High   | Medium      | Production     |
+---------------+-------------+-------------+----------------+

API Reference
=============

- :mod:`rag_toolkit.core.index.search_strategies`
- :class:`src.domain.tender.search.searcher.TenderSearcher`
