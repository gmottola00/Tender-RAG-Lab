Core Layer API
==============

The core layer contains abstract protocols and interfaces with zero dependencies.

Chunking Module
---------------

.. automodule:: src.core.chunking.chunking
   :members:
   :undoc-members:
   :show-inheritance:

Embedding Module
----------------

Protocol Definition
^^^^^^^^^^^^^^^^^^^

.. automodule:: src.core.embedding.base
   :members:
   :undoc-members:
   :show-inheritance:

.. note::
   Concrete implementations (Ollama, OpenAI) are in the Infrastructure Layer.
   See :doc:`infra` for details.

LLM Module
----------

Protocol Definition
^^^^^^^^^^^^^^^^^^^

.. automodule:: src.core.llm.base
   :members:
   :undoc-members:
   :show-inheritance:

.. note::
   Concrete implementations (Ollama, OpenAI) are in the Infrastructure Layer.
   See :doc:`infra` for details.

.. note::
   Tender-specific indexing and search are in the Domain Layer.
   See :doc:`domain` for TenderMilvusIndexer and TenderSearcher.

Indexing Module
---------------

Vector Store
^^^^^^^^^^^^

.. automodule:: src.core.index.vector.collection
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: src.core.index.vector.service
   :members:
   :undoc-members:
   :show-inheritance:

Ingestion Module
----------------

.. automodule:: src.core.ingestion.ingestion_service
   :members:
   :undoc-members:
   :show-inheritance:

RAG Module
----------

Pipeline
^^^^^^^^

.. automodule:: src.core.rag.pipeline
   :members:
   :undoc-members:
   :show-inheritance:

Assembler
^^^^^^^^^

.. automodule:: src.core.rag.assembler
   :members:
   :undoc-members:
   :show-inheritance:

Rerankers
^^^^^^^^^

.. automodule:: src.core.rag.rerankers
   :members:
   :undoc-members:
   :show-inheritance:

Query Rewriter
^^^^^^^^^^^^^^

.. automodule:: src.core.rag.rewriter
   :members:
   :undoc-members:
   :show-inheritance:

Models
^^^^^^

.. automodule:: src.core.rag.models
   :members:
   :undoc-members:
   :show-inheritance:
