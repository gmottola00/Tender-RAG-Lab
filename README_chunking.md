# Chunking & Ingestion Pipeline Guide

Guida rapida per usare la pipeline di parsing, chunking dinamico e chunking per token, inclusa l’indicizzazione in Milvus.

## Componenti

- **Parsing**: `IngestionService` (`src/core/ingestion/ingestion_service.py`) + route `/parse` e `/parse-and-chunk` (`src/api/routers/ingestion.py`).
- **Chunk dinamici**: `DynamicChunker` (`src/core/chunking/dynamic_chunker.py`) — ancora H1, include heading livello >1 e paragrafi/table fino al prossimo H1. Popola `page_number` e `section_path` deriva dagli heading.
- **Chunk per token**: `TokenChunker` (`src/core/chunking/chunking.py`) — finestre 400–800 token con overlap ~120; arricchisce con `section_path` e metadati euristici (`tender_code`, `lot_id`, `document_type`, `clause_type`).

## API di test

`POST /parse-and-chunk` (vedi `src/api/routers/ingestion.py`)
- Input: file PDF/DOCX.
- Output:
  - `dynamic_chunks`: id, title, heading_level, text (senza l’H1 duplicato), page_numbers.
  - `token_chunks`: id, text, section_path, metadata, page_numbers, source_chunk_id.

## Uso in codice

```python
from src.infra.parsers import create_ingestion_service
from src.core.chunking import DynamicChunker, TokenChunker

# Crea servizio con factory (dependency injection)
service = create_ingestion_service(enable_ocr=True, detect_headings=True)
result = service.parse_document("file.pdf")
pages = result["pages"]

# Chunking
dyn = DynamicChunker().build_chunks(pages)
tok = TokenChunker().chunk(dyn)
```

## Strategia Token Chunking

- Target: 400–800 token, overlap 120 (configurabili).
- Tokenizer di default a whitespace; inietta un tokenizer custom se usi un modello specifico (es. tiktoken).
- `section_path`: concatenazione degli heading nel chunk (es. `Capitolato > Art. 4 > Requisiti minimi`).
- Metadati: euristici su testo/titolo (pattern `\d{6}-\d{4}` per tender_code, `LOT-...` per lot_id, keyword per document_type, “art.” per clause_type).

## Note sulla qualità

- Il parser rimuove marker di pagina e header/footer ripetuti, unisce label/valore, ordina per y/x per preservare il flusso.
- Heading detection usa font-size/bold e numerazione (`1.`, `1.1.`, ...).
- Page numbers vengono propagati nei blocchi e nei chunk.

## Indicizzazione in Milvus (linee guida)

- Embedding dimensione fissa (dipende dal modello, es. 768/1024/1536).
- Schema tipico:
  - `id` (VarChar/Int64), `embedding` (FloatVector dim), `doc_id`, `section_path`, `tender_code`, `lot_id`, `document_type`, `clause_type`, `page_numbers` (array o serializzato).
- Indice consigliato (esempi):
  - HNSW: `{"index_type": "HNSW", "metric_type": "IP", "params": {"M": 24, "efConstruction": 200}}`
  - IVF_SQ8: `{"index_type": "IVF_SQ8", "metric_type": "IP", "params": {"nlist": 1024}}` (regola `nlist` su N).
- Parametri di search:
  - HNSW: `{"ef": 100-200}`
  - IVF: `{"nprobe": 8-32}`
- Non serve separare i chunk per lunghezza: tutti i chunk producono embedding della stessa dimensione; opzionalmente puoi filtrare/penalizzare chunk troppo corti lato ranking.

## Checklist rapida

- [ ] Assicurati di avere `pymupdf`, `pdfplumber`, `ocrmypdf` (se OCR), `python-docx`.
- [ ] Posiziona il modello fastText se usi `lang_detect`.
- [ ] Verifica che `page_numbers` siano popolati nei blocchi (PDF/DOCX) prima del chunking.
- [ ] Se usi un tokenizer diverso, passa `tokenizer=` a `TokenChunker`.

---
[Torna al README core](src/core/README.md)
