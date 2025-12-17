# Index Layer Overview

Infrastruttura Milvus per ingestire e interrogare chunk vettoriali con schema e search riusabili.

## Componenti e responsabilità

- `vector/config.py`: `MilvusConfig` (uri, alias, credenziali, db_name, secure).
- `vector/connection.py`: gestione alias/connessione (ensure/connect/disconnect).
- `vector/database.py`, `vector/collection.py`, `vector/data.py`: primitive su database, collection e operazioni dati (insert/upsert/delete/search/query/flush).
- `vector/exceptions.py`: errori semantici (ConnectionError, CollectionError, DataOperationError, ...).
- `tender_indexer.py`: indicizzatore specializzato per i token chunk dell’ingestion:
  - Schema: `id`, `text`, `section_path`, `metadata` (JSON), `page_numbers` (JSON), `source_chunk_id`, `embedding` (FLOAT_VECTOR).
  - Crea collection + indice (HNSW di default, configurabile via env: `MILVUS_COLLECTION`, `MILVUS_INDEX_TYPE`, `MILVUS_METRIC`, `MILVUS_HNSW_M`, `MILVUS_HNSW_EF`).
  - Upsert/search su embedding batch fornito.
- `search/`:
  - `vector_searcher.py`: semantico (embedding + Milvus).
  - `keyword_searcher.py`: LIKE semplice sul campo `text`.
  - `hybrid_searcher.py`: merge vector + keyword con peso `alpha` e reranker opzionale.
  - `reranker.py`: interfaccia base + Identity.
- `tender_searcher.py`: orchestratore per il dominio (vector/keyword/hybrid) pronto all’uso.

## Flusso tipico di indicizzazione

1. Instanzia embedding client.
2. Crea `MilvusService` con `MilvusConfig`.
3. Crea `TenderMilvusIndexer` con `embedding_dim` e `embed_fn`.
4. Chiama `upsert_token_chunks(chunks)` dove `chunks` sono quelli generati dal token chunker.

```python
from src.core.index.vector.config import MilvusConfig
from src.core.index.vector.service import MilvusService
from src.core.index.tender_indexer import TenderMilvusIndexer
from src.core.embedding import OllamaEmbeddingClient

cfg = MilvusConfig(uri="http://localhost:19530")
service = MilvusService(cfg)
emb = OllamaEmbeddingClient()
indexer = TenderMilvusIndexer(service, embedding_dim=len(emb.embed("probe")), embed_fn=emb.embed_batch)
indexer.upsert_token_chunks(token_chunks)
```

## Flusso tipico di ricerca

```python
from src.core.index.search.vector_searcher import VectorSearcher
searcher = VectorSearcher(indexer, emb)
hits = searcher.search("Qual è il valore del lotto?", top_k=5)
```

Hybrid (vector + keyword):
```python
from src.core.index.search.hybrid_searcher import HybridSearcher
from src.core.index.search.keyword_searcher import KeywordSearcher
hybrid = HybridSearcher(vector_searcher=searcher, keyword_searcher=KeywordSearcher(indexer))
hits = hybrid.search("energia elettrica", top_k=5)
```

## Design rationale

- Separazione chiara tra connessione, schema, dati, search: facilita testing e sostituzioni.
- `TenderMilvusIndexer` incapsula schema e indice per questo dominio, evitando boilerplate ripetuto.
- Searchers composabili: puoi aggiungere reranker/cross-encoder senza toccare l’indicizzatore.
- Configurazioni via env per passare da locale a ambienti diversi senza cambiare codice.

---
[Torna al README core](../README.md)
