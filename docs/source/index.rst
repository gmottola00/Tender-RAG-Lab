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

* :doc:`roadmap` - **🗺️ Complete project roadmap (2025-2026)**
* :doc:`guides/quickstart` - Get running in 10 minutes
* :doc:`rag_toolkit/index` - rag_toolkit integration guide
* :doc:`guides/integration-walkthrough` - End-to-end document flow
* :doc:`architecture/overview` - Understand the system design
* :doc:`api/index` - Complete API reference

----

📚 Documentation Sections
=========================

Project Planning
----------------

Strategic roadmap and implementation plan.

.. toctree::
   :maxdepth: 2
   :caption: Planning

   roadmap

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
* ✅ **Classic RAG** - Vector similarity + BM25 keyword search with Milvus
* 🚧 **Graph RAG (In Progress)** - Neo4j Knowledge Graph for structured queries
* ✅ **Multi-Language Support** - Italian and English tender documents
* ✅ **Document Processing** - PDF, DOCX, TXT parsing with OCR support
* ✅ **RAG Pipeline** - Query rewriting, context assembly, answer generation
* 🚧 **External Integrations** - ANAC & TED auto-ingestion (planned)
* 🚧 **Business Workflows** - Compliance checking, Bid/No-Bid assistant (planned)
* ✅ **Vendor Agnostic** - Swap Ollama ↔ OpenAI, Milvus ↔ Qdrant without code changes
* ✅ **Async First** - Non-blocking I/O for high performance

**📅 Roadmap Status:** See :doc:`roadmap` for complete 2025-2026 implementation plan

----

🏗️ Architecture Overview
=========================

Tender-RAG-Lab is a **hybrid RAG system** combining classic vector search with graph-based reasoning:

.. code-block:: text

   ┌─────────────────────────────────────────────┐
   │         Apps Layer (FastAPI)                │
   │    HTTP routes, request/response handling   │
   └────────────────┬────────────────────────────┘
                    │
   ┌────────────────▼────────────────────────────┐
   │         Domain Layer                        │
   │    Tender management, workflows             │
   └────────────────┬────────────────────────────┘
                    │
   ┌────────────────▼────────────────────────────┐
   │         Infrastructure Layer                │
   │    Milvus, Neo4j, Postgres, Storage         │
   └────────────────┬────────────────────────────┘
                    │
   ┌────────────────▼────────────────────────────┐
   │         rag_toolkit (Generic RAG)           │
   │    Protocols, chunking, vector search       │
   └─────────────────────────────────────────────┘

**System Components:**

- **Classic RAG (✅ Operational):** Milvus vector store + reranking
- **Graph RAG (🚧 In Development):** Neo4j for structured tender entities
- **Hybrid Retrieval:** Intelligent routing between vector/graph strategies
- **External Data:** ANAC & TED integration for auto-ingestion
- **Business Logic:** Compliance checking, Bid/No-Bid analysis

**Dependency Rule:** Outer layers depend on inner layers, never the reverse.

Read more: :doc:`roadmap` | :doc:`rag_toolkit/index` | :doc:`architecture/overview`

----

🎓 Learning Paths
=================

Choose your path based on your role:

**For Project Stakeholders** (15 min)

1. :doc:`roadmap` - Strategic plan & timeline
2. Current system capabilities & future features
3. Expected business impact & ROI

**For New Developers** (30 min)

1. :doc:`guides/quickstart` - Get system running
2. :doc:`rag_toolkit/index` - Understand rag_toolkit integration
3. :doc:`guides/integration-walkthrough` - See document flow
4. :doc:`architecture/overview` - System design

**For Implementing Graph RAG** (60 min)

1. :doc:`roadmap` - Phase 1 implementation details (Week 1-8)
2. Neo4j schema design & entity extraction
3. Hybrid retrieval strategies
4. Testing & evaluation approach

**For External Integrations** (45 min)

1. :doc:`roadmap` - Phase 2 ANAC/TED integration
2. Auto-ingestion workflow design
3. Fine-tuning pipeline overview
4. API contracts & data formats

**For Adding Features** (30 min)

1. :doc:`domain/services` - Business logic patterns
2. :doc:`apps/README` - API implementation
3. :doc:`architecture/where-to-put-code` - Decision tree

**For Production Deployment** (60 min)

1. :doc:`roadmap` - Phase 4 infrastructure requirements
2. :doc:`guides/environment-setup` - Complete configuration
3. :doc:`infra/milvus` - Vector database setup
4. Multi-tenancy & security considerations

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
   
   **📅 Project Status (Dec 2025):**
   
   - ✅ **Classic RAG:** Operational with Milvus + reranking
   - 🚧 **Graph RAG:** Neo4j integration in progress (see :doc:`roadmap`)
   - 📋 **External Integrations:** ANAC/TED planned for Q2 2025
   - 📋 **Business Workflows:** Compliance & Bid/No-Bid planned for Q3 2025
   
   This documentation is auto-generated from Markdown source files using Sphinx + MyST-Parser.
   To contribute, edit the ``.md`` files in the ``docs/`` directory.

*Last updated: 24 December 2025*
