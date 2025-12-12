# Core Architecture Guide

Indice centralizzato dei moduli core (ingestion, chunking, indexing, RAG).

- [Ingestion](ingestion/README.md): parsing PDF/DOCX, normalizzazione, heading/table detection, OCR opzionale, servizio di orchestrazione.
- [Chunking](../../README_chunking.md): chunk dinamici per heading e chunk token-based con metadati e suggerimenti per Milvus.
- [Index](index/README.md): infrastruttura Milvus (connessione, schema, indicizzatore tender, searchers vector/keyword/hybrid, tender_searcher).
- [RAG](rag/README.md): pipeline riscrittura → retrieval → rerank → assembly → generazione con citazioni.

Use case tipico:
1. Ingestione documento → parsed pages/blocks.
2. Chunk dinamici + token chunker → upsert su Milvus (TenderMilvusIndexer).
3. Ricerca vector/ibrida → RAG pipeline per risposta con citazioni.
