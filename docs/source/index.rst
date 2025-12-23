.. Tender-RAG-Lab documentation master file

=====================================
Tender-RAG-Lab Documentation
=====================================

**Production-grade RAG system for Italian public procurement documents**

.. image:: https://img.shields.io/badge/Python-3.11+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python Version

.. image:: https://img.shields.io/badge/License-MIT-green.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License

.. image:: https://img.shields.io/badge/Architecture-Clean-brightgreen.svg
   :alt: Clean Architecture

----

Welcome to Tender-RAG-Lab's comprehensive documentation! This project implements a production-grade 
Retrieval-Augmented Generation (RAG) system specifically designed for Italian public procurement 
tender documents, following clean architecture principles.

----

🚀 Quick Links
==============

* :doc:`guides/quickstart` - Get running in 10 minutes
* :doc:`rag_toolkit/index` - rag_toolkit integration guide
* :doc:`guides/integration-walkthrough` - End-to-end document flow
* :doc:`architecture/overview` - Understand the system design
* :doc:`api/index` - Complete API reference

----

📚 Documentation Sections
=========================

Getting Started
---------------

Essential guides to get you up and running quickly.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   guides/quickstart
   guides/environment-setup
   guides/integration-walkthrough

rag_toolkit Integration
-----------------------

Complete guide to using rag_toolkit in the Tender-RAG-Lab project.

.. toctree::
   :maxdepth: 2
   :caption: rag_toolkit Integration

   rag_toolkit/index
   rag_toolkit/pipeline
   rag_toolkit/search
   rag_toolkit/extending

Architecture
------------

Learn about the clean architecture design and key decisions.

.. toctree::
   :maxdepth: 2
   :caption: Architecture

   architecture/overview
   architecture/where-to-put-code
   architecture/decisions
   README

Core Layer
----------

Reusable, framework-agnostic abstractions (Protocols).

.. toctree::
   :maxdepth: 2
   :caption: Core Layer

   core/README
   core/chunking
   core/embedding
   core/llm
   core/indexing
   core/ingestion
   core/rag

Infrastructure Layer
--------------------

Concrete implementations of core protocols (vendors, frameworks).

.. toctree::
   :maxdepth: 2
   :caption: Infrastructure

   infra/README
   infra/database
   infra/storage
   infra/embeddings
   infra/llm
   infra/milvus
   infra/adding-integrations

Domain Layer
------------

Business logic for tender management.

.. toctree::
   :maxdepth: 2
   :caption: Domain Layer

   domain/README
   domain/services
   domain/tender-search

Apps Layer
----------

HTTP API layer with FastAPI.

.. toctree::
   :maxdepth: 2
   :caption: Apps Layer

   apps/README

API Reference
-------------

Auto-generated documentation from code.

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/index

Migration History
-----------------

Historical documentation of major refactoring efforts.

.. toctree::
   :maxdepth: 1
   :caption: Migrations

   migrations/README

----

🎯 Key Features
===============

* ✅ **Clean Architecture** - 4-layer design (Core → Infra → Domain → Apps)
* ✅ **Protocol-Based Design** - No inheritance, easy testing, flexible implementations
* ✅ **Hybrid Search** - Vector similarity + BM25 keyword search
* ✅ **Multi-Language Support** - Italian and English tender documents
* ✅ **Document Processing** - PDF, DOCX, TXT parsing with OCR support
* ✅ **RAG Pipeline** - Query rewriting, context assembly, answer generation
* ✅ **Vendor Agnostic** - Swap Ollama ↔ OpenAI, Milvus ↔ Pinecone without code changes
* ✅ **Async First** - Non-blocking I/O for high performance

----

🏗️ Architecture Overview
=========================

Tender-RAG-Lab integrates the **rag_toolkit** library following clean architecture principles:

.. code-block:: text

   ┌─────────────────────────────────────────────┐
   │         Apps Layer (FastAPI)                │
   │    HTTP routes, request/response handling   │
   └────────────────┬────────────────────────────┘
                    │
   ┌────────────────▼────────────────────────────┐
   │         Domain Layer                        │
   │    Business logic, tender management        │
   └────────────────┬────────────────────────────┘
                    │
   ┌────────────────▼────────────────────────────┐
   │         Infrastructure Layer                │
   │    Concrete implementations (Milvus, etc.)  │
   └────────────────┬────────────────────────────┘
                    │
   ┌────────────────▼────────────────────────────┐
   │         rag_toolkit (Generic RAG)           │
   │    Protocols, chunking, vector search       │
   └─────────────────────────────────────────────┘

**Dependency Rule:** Outer layers depend on inner layers, never the reverse.

Read more: :doc:`rag_toolkit/index` | :doc:`architecture/overview`

----

🎓 Learning Paths
=================

Choose your path based on your role:

**For New Developers** (30 min)

1. :doc:`guides/quickstart` - Get system running
2. :doc:`rag_toolkit/index` - Understand rag_toolkit integration
3. :doc:`guides/integration-walkthrough` - See document flow
4. :doc:`architecture/overview` - System design

**For Extending rag_toolkit** (45 min)

1. :doc:`rag_toolkit/extending` - Protocol implementation guide
2. :doc:`rag_toolkit/pipeline` - RAG pipeline details
3. :doc:`rag_toolkit/search` - Search strategies
4. :doc:`api/index` - API reference

**For Adding Features** (30 min)

1. :doc:`domain/services` - Business logic patterns
2. :doc:`apps/README` - API implementation
3. :doc:`architecture/where-to-put-code` - Decision tree

**For Production Deployment** (60 min)

1. :doc:`guides/environment-setup` - Complete configuration
2. :doc:`infra/milvus` - Vector database setup
3. Review scaling and monitoring considerations

----

📖 Additional Resources
=======================

* **GitHub Repository:** https://github.com/gmottola00/Tender-RAG-Lab
* **Issue Tracker:** https://github.com/gmottola00/Tender-RAG-Lab/issues
* **Discussions:** https://github.com/gmottola00/Tender-RAG-Lab/discussions

----

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

----

.. note::
   **Documentation Version:** |version| (|release|)
   
   This documentation is auto-generated from Markdown source files using Sphinx + MyST-Parser.
   To contribute, edit the ``.md`` files in the ``docs/`` directory.

*Last updated: 18 December 2025*
