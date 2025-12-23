===============
API Reference
===============

Auto-generated documentation from codebase docstrings.

----

Overview
========

The API is organized by architectural layers following clean architecture principles.

**Layers**:

* **Domain** - Business logic and entities (tender, lot, document management)
* **Infrastructure** - Factories and database session management
* **API** - FastAPI routers and dependency injection

For ``rag_toolkit`` library documentation, see :doc:`../rag_toolkit/index`.

----

Domain Layer
============

Tender Entities
---------------

.. automodule:: src.domain.tender.entities.tenders
   :members:
   :show-inheritance:

.. automodule:: src.domain.tender.entities.lots
   :members:
   :show-inheritance:

.. automodule:: src.domain.tender.entities.documents
   :members:
   :show-inheritance:

Chunking Schemas
----------------

.. automodule:: src.domain.tender.schemas.chunking
   :members:
   :show-inheritance:

Indexing
--------

.. automodule:: src.domain.tender.indexing.indexer
   :members:
   :show-inheritance:

Search
------

.. automodule:: src.domain.tender.search.searcher
   :members:
   :show-inheritance:

Services
--------

.. automodule:: src.domain.tender.services.tenders
   :members:
   :show-inheritance:

.. automodule:: src.domain.tender.services.lots
   :members:
   :show-inheritance:

.. automodule:: src.domain.tender.services.documents
   :members:
   :show-inheritance:

----

Infrastructure Layer
====================

Factory Functions
-----------------

.. automodule:: src.infra.factory
   :members:
   :show-inheritance:

Database Session
----------------

.. automodule:: src.infra.database.session
   :members:
   :show-inheritance:

----

API Layer
=========

Dependency Injection
--------------------

.. automodule:: src.api.deps
   :members:
   :show-inheritance:

Routers
-------

.. automodule:: src.api.routers.tenders
   :members:
   :show-inheritance:

.. automodule:: src.api.routers.lots
   :members:
   :show-inheritance:

.. automodule:: src.api.routers.milvus_route
   :members:
   :show-inheritance:
