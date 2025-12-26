.. Tender-RAG-Lab documentation master file

=====================================
Tender-RAG-Lab Documentation
=====================================

.. image:: https://img.shields.io/badge/Python-3.11+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python Version

.. image:: https://img.shields.io/badge/License-MIT-green.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License

.. image:: https://img.shields.io/badge/Architecture-Clean-brightgreen.svg
   :alt: Clean Architecture

.. image:: https://img.shields.io/badge/RAG-Hybrid-orange.svg
   :alt: Hybrid RAG

**Tender-RAG-Lab** is a production-grade Retrieval-Augmented Generation system for analyzing Italian public procurement tender documents, built with clean architecture principles and the rag_toolkit library.

.. grid:: 2
    :gutter: 3

    .. grid-item-card:: Quick Start
        :link: guides/quickstart
        :link-type: doc

        Get the system running in 10 minutes with Docker Compose and basic configuration.

    .. grid-item-card:: Architecture
        :link: architecture/overview
        :link-type: doc

        Learn about clean architecture, rag_toolkit integration, and design principles.

    .. grid-item-card:: Implementation Guide
        :link: domain/README
        :link-type: doc

        Understand domain layer, services, and business logic implementation.

    .. grid-item-card:: Project Roadmap
        :link: roadmap
        :link-type: doc

        Complete 2025-2026 implementation plan with Graph RAG and external integrations.

    .. grid-item-card:: API Reference
        :link: api/index
        :link-type: doc

        Auto-generated API documentation from Python docstrings.

    .. grid-item-card:: rag_toolkit Integration
        :link: rag_toolkit/index
        :link-type: doc

        How Tender-RAG-Lab leverages rag_toolkit for generic RAG components.

Features
--------

**Hybrid RAG System**
   Combines classic vector search (Milvus) with graph-based reasoning (Neo4j in development) for comprehensive document analysis.

**Clean Architecture**
   Four-layer design with clear separation: Apps → Domain → Infrastructure → rag_toolkit, following dependency inversion principles.

**Document Processing**
   PDF, DOCX, and TXT parsing with OCR support for scanned documents. Multi-language support for Italian and English tenders.

**Business Workflows**
   Compliance checking, requirement extraction, and bid/no-bid decision support (planned).

**Vendor Agnostic**
   Protocol-based design allows swapping vector stores (Milvus ↔ Qdrant) and LLM providers (Ollama ↔ OpenAI) without code changes.

**Production Ready**
   Async-first architecture, comprehensive testing, Docker deployment, and PostgreSQL for structured data.

Quick Example
-------------

.. code-block:: bash

   # Clone and setup
   git clone https://github.com/gmottola00/Tender-RAG-Lab.git
   cd Tender-RAG-Lab
   
   # Install dependencies
   uv sync
   
   # Configure environment
   cp .env.example .env
   
   # Start services
   docker-compose up -d
   
   # Run application
   uv run uvicorn src.api.main:app --reload

.. code-block:: python

   # Upload and index a tender document
   from src.domain.tender.services.documents import DocumentService
   
   service = DocumentService()
   document = service.upload(
       file_path="tender.pdf",
       tender_id="TENDER-2025-001"
   )
   
   # Search with hybrid retrieval
   results = service.search(
       query="What are the mandatory requirements?",
       top_k=5
   )

Why Tender-RAG-Lab?
-------------------

**Domain-Specific**
   Purpose-built for Italian public procurement documents with specialized entity extraction and compliance workflows.

**Hybrid Retrieval**
   Combines vector similarity search with graph-based reasoning for better accuracy on structured tender data.

**Extensible Architecture**
   Generic RAG logic lives in rag_toolkit library, while tender-specific logic stays focused in the domain layer.

**Developer Experience**
   Clear documentation, working examples, type hints throughout, and comprehensive test coverage.

System Architecture
-------------------

Tender-RAG-Lab follows clean architecture with four layers:

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
   │    Database, factory functions              │
   └────────────────┬────────────────────────────┘
                    │
   ┌────────────────▼────────────────────────────┐
   │         rag_toolkit (Generic RAG)           │
   │    Protocols, chunking, vector search       │
   └─────────────────────────────────────────────┘

**Key Principle:** Outer layers depend on inner layers, never the reverse. Generic RAG components live in rag_toolkit, domain logic stays in the domain layer.

Table of Contents
=================

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   guides/quickstart
   guides/environment-setup
   architecture/overview

.. toctree::
   :maxdepth: 2
   :caption: Core Concepts

   rag_toolkit/index
   domain/README
   apps/README

.. toctree::
   :maxdepth: 2
   :caption: User Guides

   guides/indexing-documents
   guides/search-retrieval

.. toctree::
   :maxdepth: 1
   :caption: Reference

   roadmap
   api/index

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
