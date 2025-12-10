# 📘 Tender-RAG-Lab — Hybrid RAG (Classic + Graph RAG) per Gare di Appalto

Sistema avanzato di Retrieval-Augmented Generation (RAG) progettato per supportare l’intero ciclo di vita delle **gare di appalto**:

* Scouting
* Bid / No-Bid
* Analisi documentale
* Drafting dell’offerta
* Compliance checking
* Q&A avanzata
* Reportistica

Il progetto combina:

* **Classic RAG** → chunking intelligente, vector search su **Milvus**, reranking, multi-step retrieval.
* **Graph RAG** → Knowledge Graph su **Neo4j** specifico per il dominio appalti (Tender / Lot / Requirement / Deadline / …).

Obiettivo: costruire **un sistema robusto, scalabile, production-grade**, estendibile nel tempo e valutabile con metriche chiare.

---

## 🚦 Roadmap per Fasi

### Phase 0 — Domain Understanding & Data Modeling

**Obiettivo:** capire cosa stai risolvendo (use case), come sono fatti i documenti, e come modellare dati + grafo in modo *minimo ma utile*.

#### 0.1 Catalogo documentale

Tipi di documento supportati:

* `bando`
* `disciplinare`
* `capitolato_tecnico`
* `capitolato_amministrativo`
* `qna_ufficiali` (chiarimenti)
* `addenda` / rettifiche
* `allegato_tecnico`
* `allegato_amministrativo`
* `offerta_passata`
* `template_interno`

Per ogni tipo: mappare struttura tipica (capitoli/articoli), sezione requisiti, criteri di aggiudicazione, scadenze, penali, ecc.

#### 0.2 Use case prioritari (v1)

Use case che guidano tutte le scelte:

* **UC1 – Requisiti obbligatori per lotto**

  * “Trova tutti i requisiti obbligatori per il Lotto 2 e dimmi se li soddisfiamo.”
* **UC2 – Compliance checklist**

  * “Genera una checklist di compliance per questa gara, per il Lotto X.”
* **UC3 – Confronto tra capitolati**

  * “Riassumi differenze chiave tra il capitolato corrente e quello della gara X-2023.”
* **UC4 – Scadenze & vincoli temporali**

  * “Elenca tutte le scadenze (Q&A, sopralluogo, presentazione offerta, ecc.).”
* **UC5 – Gare simili**

  * “Mostrami gare simili a questa dove abbiamo già partecipato.”

#### 0.3 Data Model v0 (documenti + chunk)

Database (SQL / document DB, da adattare al tuo stack).

**Tabella: `tender_documents`**

```sql
TABLE tender_documents (
  id               UUID PRIMARY KEY,
  source_system    TEXT,        -- es. "ANAC", "client_portal"
  client_id        TEXT,        -- per multi-tenant in futuro
  tender_code      TEXT,        -- CIG / codice interno
  document_type    TEXT,        -- "bando", "disciplinare", ...
  lot_id           TEXT NULL,   -- se riferito a un lotto specifico
  title            TEXT,
  language         TEXT,
  publication_date DATE NULL,
  url              TEXT NULL,
  file_path        TEXT,
  metadata         JSONB,       -- ente, cpv, categoria, ecc.
  created_at       TIMESTAMP,
  updated_at       TIMESTAMP
);
```

**Tabella: `chunks`**

```sql
TABLE chunks (
  id              UUID PRIMARY KEY,
  document_id     UUID REFERENCES tender_documents(id),
  chunk_index     INT,
  content         TEXT,
  section_path    TEXT,       -- es. "Capitolato > Art. 3 > Requisiti tecnici"
  page_start      INT NULL,
  page_end        INT NULL,
  embedding_id    TEXT,       -- id verso Milvus oppure campo logico
  metadata        JSONB,      -- lot_id, clause_type, etc.
  created_at      TIMESTAMP
);
```

Campi `metadata` tipici per i chunk:

* `tender_code`
* `document_type`
* `lot_id`
* `clause_type` (es. `requisito_tecnico`, `requisito_economico`, `scadenza`, `penale`, …)
* `heading_raw` (titolo articolo/paragrafo)

#### 0.4 Knowledge Graph v0 (Neo4j)

Modello *minimo* ma già utile.

**Node types**

* `Tender`

  * `tender_code`, `title`, `publication_date`, `cpv_code`, `base_amount`, …
* `Lot`

  * `lot_id`, `name`, `cpv_code`, `base_amount`
* `Requirement`

  * `id`, `type` (tecnico/economico/amministrativo), `description`, `mandatory` (bool)
* `Deadline`

  * `id`, `type` (Q&A, sopralluogo, offerta,…), `date`, `notes`
* `Penalty`

  * `id`, `description`, `amount`, `type`
* `Criterion`

  * `id`, `type` (tecnico/economico), `weight`, `description`
* `DocumentSection`

  * `id`, `document_id`, `chunk_id`, `section_path`, `page_start`, `page_end`
* `Organization`

  * `name`, `role` (ente_appaltante, concorrente, RTI member,…)

**Relationships**

* `(Tender)-[:HAS_LOT]->(Lot)`
* `(Lot)-[:HAS_REQUIREMENT]->(Requirement)`
* `(Tender)-[:HAS_DEADLINE]->(Deadline)`
* `(Tender)-[:HAS_CRITERION]->(Criterion)`
* `(Requirement)-[:REFERENCED_IN]->(DocumentSection)`
* `(Deadline)-[:REFERENCED_IN]->(DocumentSection)`
* `(Penalty)-[:REFERENCED_IN]->(DocumentSection)`
* `(Tender)-[:ISSUED_BY]->(Organization)`

---

## Phase 1 — Classic RAG Baseline (Milvus + Reranker)

**Obiettivo:** Classic RAG forte, stabile, con metriche base, prima di introdurre il grafo.

### 1.1 Ingestion & Preprocessing

Path: `src/ingestion/`

Componenti:

* `pdf_parser.py` — estrazione testo da PDF (pdfplumber / pymupdf)
* `word_parser.py` — estrazione testo da .docx
* `ingestion_pipeline.py`

  * legge file da `data/raw/`
  * crea record `tender_documents`
  * salva testo strutturato (pagine, headings)

Aggiungere:

* Normalizzazione encoding
* Language detection (per eventuale multi-lingua)
* Logging robusto

### 1.2 Chunking Strategy v1

Path: `src/preprocessing/chunking.py`

Strategia iniziale:

* chunk per **token**, non per caratteri
* dimensione: **400–800 token**, overlap 100–150
* include nel chunk:

  * `section_path` (es. “Capitolato > Art. 4 > Requisiti minimi”)
  * pagine di origine
  * tutti i metadata rilevanti per filtri (tender_code, lot_id, document_type, clause_type)

### 1.3 Vector Indexing (Milvus)

Path: `src/indexing/vector/`

File:

* `milvus_client.py`

  * connessione a Milvus
  * creazione collection
  * gestione schema (embedding_dim, primary key, metadata)
* `indexer.py`

  * indicizzazione embeddings dei chunk
* `searcher.py`

  * ricerca top-k con:

    * filtri su `tender_code`, `lot_id`, `document_type`
    * opzione `client_id` per multi-tenant

### 1.4 Reranking

Path: `src/rag/reranking/cross_encoder.py`

* Modello tipo cross-encoder (es. `bge-reranker-large`)
* Input: query + top-N chunk (da Milvus)
* Output: lista di chunk riordinata per rilevanza

### 1.5 Classic RAG Pipeline

Path: `src/rag/pipelines/classic_rag.py`

Flow di base:

1. (Opzionale) Query rewriting con LLM (es. chiarire lotto/tender se mancano).
2. Vector retrieval via Milvus (top-k grezzo).
3. Reranking con cross-encoder.
4. Assemblaggio contesto (rispetto token budget).
5. Chiamata LLM:

   * risposta
   * citazioni (document_id, chunk_id, section_path, pagine)

### 1.6 API Baseline

Path: `src/api/`

* `app.py` — FastAPI (o simile)
* `routes.py` — definizione endpoint

**Endpoint: `/ask-tender`**

```json
POST /ask-tender
{
  "query": "Trova tutti i requisiti obbligatori per il Lotto 2",
  "tender_code": "CIG-12345",
  "lot_id": "LOTTO-2",
  "client_id": "acme-spa",
  "debug": true
}
```

**Response:**

```json
{
  "answer": "Per il Lotto 2 i requisiti obbligatori sono...",
  "sources": [
    {
      "document_id": "uuid",
      "chunk_id": "uuid",
      "document_type": "disciplinare",
      "section_path": "Art. 5 - Requisiti di partecipazione",
      "page_start": 10,
      "page_end": 11
    }
  ],
  "retrieval_debug": {
    "top_k_initial": 20,
    "top_k_reranked": 5
  }
}
```

---

## Phase 2 — Graph RAG (Neo4j) + Hybrid Retrieval

**Obiettivo:** usare Neo4j per migliorare *davvero* alcune domande strutturate (requisiti, scadenze, multi-hop).

### 2.1 Neo4j Schema & Setup

Path: `src/kg/schema/kg_schema.cypher`

Contiene statement per:

* creazione label nodi
* creazione constraints / indici
* esempi di MERGE per:

  * Tender + Lot
  * Requirement
  * Deadline
  * DocumentSection

### 2.2 KG Builder Pipeline

Path: `src/kg/builders/`

File:

* `ner_extractor.py`

  * estrazione entità da chunk:

    * riconoscere lotti (Lotto 1, Lotto II, …)
    * requisiti (`deve`, `obbligatorio`, `pena esclusione`, etc.)
    * scadenze (date con pattern + contesto)
* `relation_extractor.py`

  * collega entità:

    * Lot → Requirement
    * Tender → Deadline
    * Requirement/Deadline → DocumentSection
* `kg_builder.py`

  * prende output NER/RE
  * effettua `MERGE` su Neo4j (via driver Python)

### 2.3 Sync Documents ↔ KG

Path: `src/kg/sync/sync_pipeline.py`

Responsabilità:

* dopo ingestion + chunking:

  * creare/aggiornare nodi Tender/Lot/etc.
  * collegare DocumentSection ai chunk
* gestione versioni:

  * `valid_from` / `valid_to` se necessario
  * evitare duplicati grafo su re-ingestion

### 2.4 Retrieval Strategies Ibride

Path: `src/rag/retrieval_strategies/`

**Graph → Vector (graph-first)**

* file: `graph_then_vector.py`
* es. UC1: requisiti mandatory per lotto X:

  1. query in Neo4j:

     * `(lot:Lot {lot_id: ...})-[:HAS_REQUIREMENT]->(r:Requirement {mandatory: true})`
  2. per ogni requisito: recuperi i `DocumentSection` collegati
  3. recuperi i `chunk_id` e fai RAG solo su quei chunk

**Vector → Graph (vector-first)**

* file: `vector_then_graph.py`
* es. confronto tra gare:

  1. vector retrieval su capitolato corrente
  2. da chunk trovati → risali a Requirement/Deadline/… nel grafo
  3. da lì navighi verso nodi legati ad altre gare (`Tender` collegati)
  4. arricchisci contesto per l’LLM

**Graph-only**

* file: `graph_only.py`
* per domande strutturate tipo:

  * tutte le scadenze
  * elenco lotti e requisiti mandatory
  * liste di criteri e pesi

### 2.5 Hybrid RAG Pipeline

Path: `src/rag/pipelines/hybrid_rag.py`

* orchestratore che sceglie la strategia:

  * classic_rag
  * graph_then_vector
  * vector_then_graph
  * graph_only

---

## Phase 3 — Workflows Specifici per Gare

**Obiettivo:** trasformare il motore RAG in strumenti realmente usabili dal business.

### 3.1 Compliance Checklist Generator

Path: `src/workflows/compliance_checklist.py`

Pipeline:

1. Neo4j:

   * tutti i `Requirement` mandatory per `tender_code` + `lot_id`
2. Recupero chunk collegati con RAG (per arricchire il contesto)
3. LLM:

   * genera checklist con:

     * descrizione requisito
     * riferimenti ad articoli/pagine
     * campo sì/no
     * eventuali note

### 3.2 Bid / No-Bid Assistant

Path: `src/workflows/bid_no_bid.py`

Usa:

* grafo per:

  * requisiti killer (mandatory – tipo “pena esclusione”)
  * scadenze critiche
  * penali pesanti
  * criteri e pesi
* RAG per estrarre testo originale

Output: mini-report con pro/contro + raccomandazione qualitativa.

### 3.3 Change Detection tra gare

Path: `src/workflows/change_detection.py`

* confronta entità nel grafo:

  * `Requirement`, `Deadline`, `Penalty`, `Criterion`
* identifica:

  * nuovi requisiti
  * requisiti rimossi
  * modifiche su date/importi/pesi
* usa RAG per mostrare testo completo delle clausole modificate

---

## Phase 4 — Evaluation, Hardening & Productionization

**Obiettivo:** misurare, ottimizzare, produrre.

### 4.1 Retrieval Evaluation

Path: `src/eval/retrieval_eval.py`

Dataset (es. `data/eval/retrieval.json`):

```json
[
  {
    "query": "Requisiti obbligatori per il Lotto 2",
    "tender_code": "CIG-12345",
    "lot_id": "LOT-2",
    "relevant_chunk_ids": ["uuid1", "uuid2", "uuid3"]
  }
]
```

Metriche:

* Precision@k
* Recall@k
* MRR
* nDCG

Confronto:

* classic_rag vs hybrid_rag (graph_then_vector / vector_then_graph)

### 4.2 LLM Evaluation

Path: `src/eval/llm_eval.py`

* LLM-judge con rubric:

  * accuratezza
  * aderenza ai documenti (grounding)
  * correttezza citazioni
  * completezza
* eventuale human-in-the-loop per casi critici

### 4.3 Monitoring & Logging

* log di:

  * query
  * revisione pipeline usata (classic / hybrid / graph-only)
  * tempi di:

    * retrieval Milvus
    * query Neo4j
    * chiamata LLM
* tracking di errori, timeouts, fallback

### 4.4 Productionization

* Config:

  * `configs/dev.yaml`
  * `configs/staging.yaml`
  * `configs/prod.yaml`
* Docker + Kubernetes (se serve)
* Feature flag:

  * abilitare/disabilitare Graph RAG per specifici client / use case
* Versioning:

  * modelli
  * schema KG
  * dataset di eval

---

## 📁 Folder Structure Proposta

```bash
tender-rag-lab/
  README.md
  configs/
    dev.yaml
    prod.yaml
  data/
    raw/
    processed/
    kg/
    eval/
  src/
    ingestion/
      pdf_parser.py
      word_parser.py
      ingestion_pipeline.py
    preprocessing/
      chunking.py
      headings.py
      tables.py
    indexing/
      vector/
        milvus_client.py
        indexer.py
        searcher.py
    kg/
      schema/
        kg_schema.cypher
      builders/
        ner_extractor.py
        relation_extractor.py
        kg_builder.py
      sync/
        sync_pipeline.py
    rag/
      pipelines/
        classic_rag.py
        hybrid_rag.py
      retrieval_strategies/
        graph_then_vector.py
        vector_then_graph.py
        graph_only.py
      reranking/
        cross_encoder.py
    workflows/
      compliance_checklist.py
      bid_no_bid.py
      change_detection.py
    api/
      app.py
      routes.py
    eval/
      retrieval_eval.py
      llm_eval.py
    utils/
      logging.py
      config.py
  tests/
    ...
  docs/
    data_model_v0.md
    kg_design_v0.md
```

---

## ✅ Next 3 Concrete Actions

1. **Salva questo file come `README.md` alla root del repo** (`tender-rag-lab/`).
2. **Crea `docs/data_model_v0.md`** copiando e raffinando gli schemi di documenti/chunk/KG.
3. **Implementa Phase 1: ingestion + chunking + Milvus + classic_rag pipeline**, ignorando il grafo finché non hai risposte decenti su 20–50 query di test.