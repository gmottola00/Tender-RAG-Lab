# Tender Management Plan & Roadmap

Proposta di struttura dati e roadmap per una web app di gestione gare con Q/A RAG.

## Obiettivi
- Gestire gare e lotti con documenti associati.
- Consentire Q/A e ricerca (vector/keyword/hybrid) scoped per gara/lotto.
- Estrarre e mostrare dati chiave (importi, scadenze, email, ecc.).
- Audit e history delle query/risposte con citazioni.

## Schema dati (DB relazionale o Supabase/Postgres)
- `tenders`:
  - `id` (uuid), `code` (es. 821062-2025), `title`, `description`, `status`, `created_at`, `updated_at`.
  - `publish_date`, `closing_date`, `buyer` (ente).
- `lots`:
  - `id` (uuid), `tender_id` (fk), `code` (es. LOT-0001), `title`, `description`, `value_estimated`, `currency`, `status`.
- `documents`:
  - `id` (uuid), `tender_id` (fk), `lot_id` (fk nullable), `filename`, `document_type` (bando, capitolato, disciplinare, rettifica, avviso, ecc.), `hash`, `uploaded_by`, `uploaded_at`.
- `chunks` (metadati per riferimento rapido al vector DB):
  - `id` (uuid), `document_id` (fk), `tender_id` (fk), `lot_id` (fk nullable), `section_path`, `page_numbers` (json/int[]), `metadata` (json), `vector_id` (id usato in Milvus), `created_at`.
  - Nota: il testo/embedding resta in Milvus, qui salviamo i riferimenti e i metadati filtrabili.
- `extractions` (dati chiave):
  - `id`, `tender_id`, `lot_id` (nullable), `document_id`, `field_name` (es. email, importo, scadenza), `value`, `confidence`, `source_chunk_id`, `page_numbers`, `created_at`.
- `qa_logs`:
  - `id`, `tender_id`, `lot_id` (nullable), `question`, `answer`, `citations` (json con chunk_id/section_path/pagine), `score`, `created_at`, `user_id`.

## Vector DB (Milvus)
- Collection `tender_chunks` (già definita):
  - Campi: `id`, `text`, `section_path`, `metadata` (JSON), `page_numbers` (JSON), `source_chunk_id`, `embedding`.
  - Usa `metadata` per includere `tender_id`, `lot_id`, `document_type` e altri filtri (cig/tender_code).
- Quando indicizzi:
  - Aggiungi `metadata` coerenti con le FK del DB (tender_id, lot_id, document_type, filename).
  - Salva `id`/`source_chunk_id` in `chunks` (DB) per cross-ref.

## Flusso MVP
1) Creazione gara (tender) e lotti (facoltativi).
2) Upload documenti → ingestione → chunking → indicizzazione in Milvus con metadata (`tender_id`, `lot_id`, `document_type`).
3) UI gara: tab Documenti, tab Q/A, tab Dati estratti, tab Log.
4) Q/A: filtra sempre per `tender_id` (e `lot_id` se selezionato), restituisci citazioni con pagina/path.
5) Salva query/risposte in `qa_logs` + citazioni.

## Roadmap sintetica
- **Sprint 1**: Schemi DB (tenders, lots, documents, chunks, qa_logs). API upload + ingest + indicizzazione con metadata. UI base gara/lista documenti.
- **Sprint 2**: Q/A e ricerca (vector + filtri tender/lotto). UI Q/A con citazioni. Estrattori base (regex/LLM) per email/importi/date → salva in `extractions`.
- **Sprint 3**: Hybrid search + reranker migliore (cross-encoder). Faceted search per document_type/lot. Audit/log UI.
- **Sprint 4**: Notifiche/monitoring ingestion, retry OCR. Autorizzazioni multi-utente (scope per team).
- **Sprint 5** (opzionale): Fine-tuning/reranker cross-encoder, analyzer testuale in Milvus, caching contesti RAG.

## Considerazioni
- Mantieni testo/embedding in Milvus; metadati e relazioni nel DB relazionale.
- Sincronizza `chunks.vector_id` con `id` in Milvus per tracciabilità.
- Filtri standard nelle query Milvus: `metadata.tender_id == <id>` e `metadata.lot_id == <id>` se presente.
- Estrattori: costruisci da chunk (regex/LLM) e salva in `extractions` con riferimento a chunk/pagina.

## Demo Web (HTML/CSS + FastAPI routing)

### File/struttura suggerita
- `src/api/routers/ui.py` (o simile): router FastAPI per pagine HTML (render template Jinja).
- Template HTML (es. `templates/`):
  - `base.html`: layout base, navbar (gare, upload, Q/A).
  - `tenders.html`: elenco gare + form creazione gara.
  - `tender_detail.html`: dettaglio gara (documenti, upload, Q/A/chat, dati estratti).
  - `chat.html` (se separato) per la sezione Q/A.
- Static (es. `static/`):
  - `styles.css`: stile leggero per dashboard, card, tabelle.
  - Eventuale JS minimale per chiamate fetch verso API (upload, Q/A, estrazioni).

### Flusso demo
1. **Creazione gara**: form su `tenders.html` → POST API `/tenders` (crea record DB).
2. **Upload documenti**: form/file input su `tender_detail.html` → POST `/tenders/{id}/documents` → ingestione + indicizzazione (metadata con `tender_id`).
3. **Q/A / Chat**: pannello su `tender_detail.html`:
   - selezione lotto/filtro (opzionale), campo domanda, chiama `/rag/pipeline` con `tender_id` (e `lot_id` se selezionato).
   - mostra risposta + citazioni (chunk id, section_path, pagina).
4. **Dati estratti**: tab che chiama `/tenders/{id}/extractions` (creati via pipeline LLM/regex) e li mostra con link ai chunk.

### Roadmap front/back per la demo
- **Backend**:
  - Router UI (template Jinja) per servire le pagine.
  - API CRUD: `tenders`, `lots`, `documents`, `extractions`, `qa_logs`.
  - Integrazione con ingest/chunk/index esistenti (riuso endpoint upload o nuovo endpoint scoped per `tender_id`).
  - Q/A endpoint che accetta `tender_id` (e `lot_id`) e passa i filtri al searcher.
- **Frontend (HTML/CSS)**:
  - Layout base e navbar.
  - Pagina elenco/crea gare.
  - Pagina dettaglio gara con sezioni: upload, documenti, Q/A, dati estratti.
  - JS minimale per chiamare API e popolare le sezioni (fetch).

### Note
- Usa metadata `tender_id` (e `lot_id`) nelle query Milvus per scope Q/A.
- Aggiungi estrazione dati di gara nella pipeline RAG (post-processing del contesto) e salvala in `extractions`.
- Mantieni lo stile semplice (HTML/CSS base) per la demo, concentrandoti su flusso e funzionalità.
