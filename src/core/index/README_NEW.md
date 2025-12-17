# Index Layer Overview

Infrastruttura vettoriale per ingestire e interrogare chunk vettoriali con architettura pulita e riusabile.

## 🏗️ Nuova Architettura (Refactored)

Il sistema index è stato refactorato seguendo i principi di clean architecture:

- **`base.py`**: Protocol definitions (astrazioni pure, zero dipendenze)
- **`service.py`**: `IndexService` generico con dependency injection
- **`search_strategies.py`**: Search generiche (VectorSearch, KeywordSearch, HybridSearch)
- **`tender_indexer_v2.py`**: Wrapper backward-compatible per tender chunks
- **`tender_searcher_v2.py`**: Orchestratore tender usando le nuove strategie
- **`../../infra/vectorstores/`**: Implementazioni concrete (Milvus isolato)
- **`../../infra/vectorstores/factory.py`**: Factory per creare servizi configurati

### Vecchia Architettura (Ancora Funzionante)

- `vector/`: Implementazioni Milvus originali (PRESERVATE per compatibilità)
- `tender_indexer.py`: Indicizzatore originale (PRESERVATO)
- `search/`: Searcher originali (PRESERVATI)
- `tender_searcher.py`: Orchestratore originale (PRESERVATO)

## 🚀 Utilizzo Rapido (Consigliato)

### Opzione 1: Factory Pattern (Nuovo - Raccomandato)

```python
from src.infra.vectorstores.factory import create_tender_stack
from src.core.embedding import OllamaEmbeddingClient

# 1. Crea embedding client
embed_client = OllamaEmbeddingClient()
embedding_dim = len(embed_client.embed("probe"))

# 2. Crea stack completo con una chiamata
indexer, searcher = create_tender_stack(
    embed_client=embed_client,
    embedding_dim=embedding_dim,
)

# 3. Indicizza
indexer.upsert_token_chunks(token_chunks)

# 4. Cerca (vector, keyword, o hybrid)
vector_results = searcher.vector_search("query text", top_k=5)
keyword_results = searcher.keyword_search("exact terms", top_k=5)
hybrid_results = searcher.hybrid_search("query text", top_k=5)
```

### Opzione 2: Codice Originale (Ancora Funziona)

```python
from src.core.index.vector.config import MilvusConfig
from src.core.index.vector.service import MilvusService
from src.core.index.tender_indexer import TenderMilvusIndexer
from src.core.embedding import OllamaEmbeddingClient

cfg = MilvusConfig(uri="http://localhost:19530")
service = MilvusService(cfg)
emb = OllamaEmbeddingClient()
indexer = TenderMilvusIndexer(
    service=service, 
    embedding_dim=len(emb.embed("probe")), 
    embed_fn=emb.embed_batch
)
indexer.upsert_token_chunks(token_chunks)
```

## 🔍 Ricerca

### Vector Search (Semantica)

```python
# Usa il searcher tender (nuovo modo)
results = searcher.vector_search("Qual è il valore del lotto?", top_k=5)

# O manualmente con strategie
from src.core.index.search_strategies import VectorSearch
vector_search = VectorSearch(index_service, embed_fn=embed_client.embed)
hits = vector_search.search("query", top_k=5)
```

### Keyword Search

```python
# Usa il searcher tender
results = searcher.keyword_search("energia elettrica", top_k=5)

# O manualmente
from src.core.index.search_strategies import KeywordSearch
keyword_search = KeywordSearch(index_service)
hits = keyword_search.search("energia elettrica", top_k=5)
```

### Hybrid Search (Vector + Keyword)

```python
# Usa il searcher tender (configurato con alpha=0.7)
results = searcher.hybrid_search("energia elettrica", top_k=5)

# O manualmente con custom alpha
from src.core.index.search_strategies import HybridSearch
hybrid = HybridSearch(
    vector_search=vector_search,
    keyword_search=keyword_search,
    alpha=0.7  # 70% vector, 30% keyword
)
hits = hybrid.search("query", top_k=5)
```

## 🎯 Vantaggi della Nuova Architettura

1. **🎯 Più Semplice**: Una factory call invece di 3-4 setup manuali
2. **🧪 Testabile**: Mock dei Protocol invece delle classi concrete
3. **🔄 Swappable**: Cambia da Milvus a Pinecone modificando solo la factory
4. **📦 Backward Compatible**: Tutto il codice vecchio continua a funzionare
5. **🌍 Env-Aware**: Configurazione automatica da variabili d'ambiente
6. **📚 Library-Ready**: Core abstractions pronte per estrazione

## 📚 Documentazione Completa

- **Guida Migrazione**: `../../MIGRATION_INDEX.md`
- **Esempi Completi**: `../../examples/index_usage.py`
- **Summary Refactor**: `../../REFACTOR_INDEX_SUMMARY.md`

## Schema Tender Chunks

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `id` | VARCHAR(64) | Primary key |
| `text` | VARCHAR(65535) | Testo del chunk |
| `section_path` | VARCHAR(2048) | Percorso della sezione |
| `tender_id` | VARCHAR(2048) | ID della gara |
| `metadata` | JSON | Metadati aggiuntivi |
| `page_numbers` | JSON | Numeri di pagina |
| `source_chunk_id` | VARCHAR(64) | ID chunk sorgente |
| `embedding` | FLOAT_VECTOR | Vettore embedding |

## Configurazione (Environment Variables)

```bash
# Milvus connection
MILVUS_URI=http://localhost:19530
MILVUS_USER=
MILVUS_PASSWORD=
MILVUS_DB=default

# Collection config
MILVUS_COLLECTION=tender_chunks
MILVUS_METRIC=IP
MILVUS_INDEX_TYPE=HNSW

# HNSW parameters
MILVUS_HNSW_M=24
MILVUS_HNSW_EF=200
```

## Design Rationale

### Nuova Architettura
- **Core**: Protocol-based abstractions (nessuna dipendenza da vendor)
- **Infra**: Implementazioni concrete isolate (Milvus, Pinecone, etc.)
- **Factory**: Produzione con sensible defaults + env vars
- **DI**: Dependency injection per massima testabilità

### Backward Compatibility
- Tutti i file originali preservati in `vector/`, `search/`
- Import vecchi continuano a funzionare
- Migrazione graduale e opzionale

---
[Torna al README core](../README.md)
