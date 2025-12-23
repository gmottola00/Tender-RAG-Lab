================
RAG Pipeline
================

The RAG pipeline orchestrates the complete query flow from user question to
generated answer with citations.

----

Pipeline Architecture
=====================

The ``RagPipeline`` class from ``rag_toolkit.rag`` implements a five-stage process:

.. mermaid::

   graph LR
       A[User Query] --> B[Query Rewriter]
       B --> C[Vector Search]
       C --> D[Reranker]
       D --> E[Context Assembler]
       E --> F[LLM Generator]
       F --> G[Answer + Citations]
       
       style A fill:#e3f2fd
       style G fill:#c8e6c9

Pipeline Stages
===============

1. Query Rewriting
------------------

**Purpose**: Expand and clarify the user's query for better retrieval.

.. code-block:: python

   from rag_toolkit.rag.rewriter import QueryRewriter
   
   rewriter = QueryRewriter(llm_client)
   expanded_query = rewriter.rewrite("Find requirements")
   # Output: "List all mandatory technical and administrative requirements"

2. Vector Search
----------------

**Purpose**: Retrieve top-k candidate chunks based on semantic similarity.

.. code-block:: python

   from rag_toolkit.core.index.search_strategies import VectorSearch
   
   searcher = VectorSearch(
       index_service=index_service,
       embed_fn=lambda q: embed_client.embed(q)
   )
   
   results = searcher.search(query, top_k=20)

3. Reranking
------------

**Purpose**: LLM-based relevance scoring of candidates.

.. code-block:: python

   from rag_toolkit.rag.rerankers import LLMReranker
   
   reranker = LLMReranker(llm_client, top_n=5)
   refined = reranker.rerank(query, candidates)

4. Context Assembly
-------------------

**Purpose**: Build prompt context respecting token budget.

.. code-block:: python

   from rag_toolkit.rag.assembler import ContextAssembler
   
   assembler = ContextAssembler(max_tokens=2000)
   context = assembler.assemble(chunks)

5. Answer Generation
--------------------

**Purpose**: Generate answer with source citations.

The LLM receives:
- Rewritten query
- Assembled context chunks
- System prompt for tender domain

Response Model
==============

.. code-block:: python

   @dataclass
   class RagResponse:
       answer: str                    # Generated answer
       citations: list[Citation]      # Source chunks
       metadata: dict[str, Any]       # Query info, timings

   @dataclass
   class Citation:
       id: str
       section_path: str              # "Capitolato > Art. 4"
       page_numbers: list[int]
       metadata: dict
       source_chunk_id: str

Configuration
=============

Pipeline Tuning
---------------

Key parameters to adjust:

.. code-block:: python

   pipeline = RagPipeline(
       vector_searcher=searcher,
       rewriter=rewriter,
       reranker=LLMReranker(llm, top_n=5),      # Keep top 5 after rerank
       assembler=ContextAssembler(max_tokens=2000),  # Token budget
       generator_llm=llm
   )

Performance Considerations
--------------------------

- **top_k**: Higher = better recall, slower retrieval (default: 20)
- **top_n**: Number after reranking (default: 5)
- **max_tokens**: Context window size (default: 2000)

Usage Example
=============

Complete pipeline usage:

.. code-block:: python

   from src.api.deps import get_rag_pipeline
   
   pipeline = get_rag_pipeline()
   response = pipeline.run(
       question="What are the mandatory requirements for Lot 2?",
       top_k=10
   )
   
   print(response.answer)
   for citation in response.citations:
       print(f"  [{citation.section_path}] (pages {citation.page_numbers})")

API Reference
=============

See the complete API documentation:

- :mod:`rag_toolkit.rag.pipeline`
- :mod:`rag_toolkit.rag.rewriter`
- :mod:`rag_toolkit.rag.rerankers`
- :mod:`rag_toolkit.rag.assembler`
