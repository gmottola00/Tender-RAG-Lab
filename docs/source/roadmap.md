# 🗺️ Tender-RAG-Lab Roadmap

**Professional Tender Analysis System — Production Roadmap 2025-2026**

> **Status:** Classic RAG ✅ Complete | Graph RAG 🚧 In Progress | Enterprise Features 📋 Planned

---

## 📊 Executive Summary

Tender-RAG-Lab è un sistema avanzato di analisi gare di appalto pubbliche italiane che combina:

- **Classic RAG** (Milvus + Reranking) — ✅ **COMPLETATO**
- **Graph RAG** (Neo4j Knowledge Graph) — 🚧 **IN SVILUPPO**
- **Business Workflows** — Compliance, Bid/No-Bid, Change Detection
- **External Integrations** — ANAC, TED, Fine-tuning pipeline
- **Production Deployment** — Multi-tenancy, monitoring, scalability

**Target Users:** Aziende che partecipano a gare pubbliche (PMI, grandi imprese, consorzi)

**Key Metrics:**
- 📈 Riduzione 60% tempo analisi documentale
- 🎯 Accuracy > 90% su requisiti obbligatori
- ⚡ Response time < 3s (p95)
- 📚 Supporto 100K+ documenti/client

---

## 🎯 Strategic Goals (2025-2026)

### Q1 2025 (Gen-Mar) — Graph RAG Foundation ✅ 60% Complete

**Obiettivo:** Implementare Knowledge Graph per query strutturate e reasoning multi-hop

**Deliverables:**
1. ✅ Neo4j schema design per dominio appalti
2. ✅ NER/RE extractors per entità (Tender, Lot, Requirement, Deadline)
3. 🚧 Graph-first retrieval strategies
4. 🚧 Hybrid RAG orchestrator (classic + graph)
5. 📋 Graph-based workflows (compliance checklist, bid/no-bid)

**Success Metrics:**
- Graph coverage: 80% entità chiave estratte correttamente
- Query strutturate: 95% accuracy su scadenze/requisiti
- Latency: <2s per query grafo + vector

### Q2 2025 (Apr-Giu) — External Integrations & Fine-tuning

**Obiettivo:** Automazione ingestion e ottimizzazione modelli per italiano/appalti

**Deliverables:**
1. ANAC API integration (import automatico bandi pubblici)
2. TED (Tenders Electronic Daily) scraper per gare EU
3. Fine-tuning pipeline per:
   - Embedding model (italian-tender-specific)
   - Reranker cross-encoder (domain adaptation)
   - LLM per estrazione entità (Llama 3.1 8B fine-tuned)
4. Dataset collection: 1000+ gare annotate per training
5. Evaluation harness per confronto modelli

**Success Metrics:**
- Auto-ingestion: 100 nuove gare/giorno da ANAC/TED
- Embedding recall: +15% vs base model
- Entity extraction F1: >0.92 per Requirement/Deadline

### Q3 2025 (Lug-Set) — Business Workflows & Analytics

**Obiettivo:** Strumenti pronti all'uso per decision-making gare

**Deliverables:**
1. **Compliance Checklist Generator**
   - Input: tender_code + lot_id
   - Output: checklist requisiti obbligatori con status (✅/❌/⚠️)
2. **Bid/No-Bid Assistant**
   - Score gara basato su: requisiti killer, scadenze, penali, criteri aggiudicazione
   - Raccomandazione: GO/NO-GO con confidence score
3. **Change Detection Engine**
   - Confronto gare simili (stesso ente/CPV)
   - Delta requisiti, scadenze, importi
4. **Tender Similarity Search**
   - Find gare storiche simili con esito (vinto/perso)
   - Transfer learning da offerte passate
5. **Analytics Dashboard**
   - KPI: gare monitorate, Q&A effectiveness, time-to-answer
   - Audit trail completo per compliance interna

**Success Metrics:**
- Compliance checklist: 100% coverage requisiti obbligatori
- Bid/No-Bid accuracy: 85% alignment con decisione umana finale
- Time-to-insight: <5 min per analisi gara completa

### Q4 2025 (Ott-Dic) — Production Hardening & Scale

**Obiettivo:** Enterprise-ready deployment per clienti paying

**Deliverables:**
1. **Multi-tenancy completo**
   - Isolamento dati per client_id
   - RBAC (admin, analyst, viewer)
   - Quota management (docs/month, queries/day)
2. **High Availability Setup**
   - Kubernetes deployment (3+ replicas)
   - Postgres HA (Patroni/Stolon)
   - Milvus clustering (3 nodes)
   - Neo4j cluster (primary + replicas)
3. **Monitoring & Observability**
   - Prometheus + Grafana dashboards
   - Distributed tracing (Jaeger)
   - Error tracking (Sentry)
   - Cost tracking (embeddings, LLM calls)
4. **Security & Compliance**
   - Encryption at-rest/in-transit
   - GDPR compliance (data retention, right-to-delete)
   - Audit logs (chi ha letto cosa, quando)
   - SOC 2 Type II readiness
5. **Performance Optimization**
   - Caching layer (Redis) per query frequenti
   - Batch ingestion (100+ docs/min)
   - Query optimization (index tuning)

**Success Metrics:**
- Uptime: 99.9% (SLA)
- Concurrent users: 100+ per tenant
- Ingestion throughput: 500 docs/hour
- Query latency p95: <3s

---

## 📋 Detailed Implementation Plan

### Phase 1: Graph RAG Implementation (8 weeks)

#### Week 1-2: Neo4j Schema & Infrastructure

**Tasks:**
1. Setup Neo4j cluster (Docker Compose per dev, Aura/Enterprise per prod)
2. Definire schema completo:
   ```cypher
   // Node types
   (:Tender {code, title, publication_date, cpv_code, base_amount, buyer_name, buyer_cf})
   (:Lot {id, name, cpv_code, base_amount, description})
   (:Requirement {id, type, description, mandatory, penalty_if_missing})
   (:Deadline {id, type, date, time, location, notes})
   (:Penalty {id, description, amount, trigger_condition})
   (:Criterion {id, type, weight, max_points, description})
   (:DocumentSection {id, chunk_id, section_path, page_numbers})
   (:Organization {cf, name, type})
   (:CPV {code, description, level})
   
   // Relationships
   (Tender)-[:HAS_LOT]->(Lot)
   (Lot)-[:REQUIRES]->(Requirement)
   (Tender)-[:HAS_DEADLINE]->(Deadline)
   (Tender)-[:HAS_PENALTY]->(Penalty)
   (Tender)-[:HAS_CRITERION]->(Criterion)
   (Requirement|Deadline|Penalty)-[:MENTIONED_IN]->(DocumentSection)
   (Tender)-[:ISSUED_BY]->(Organization)
   (Tender|Lot)-[:CLASSIFIED_AS]->(CPV)
   (Requirement)-[:RELATED_TO]->(Requirement) // dependencies
   ```

3. Creare indici e constraints:
   ```cypher
   CREATE CONSTRAINT tender_code_unique ON (t:Tender) ASSERT t.code IS UNIQUE;
   CREATE INDEX tender_cpv ON :Tender(cpv_code);
   CREATE INDEX requirement_mandatory ON :Requirement(mandatory);
   CREATE INDEX deadline_date ON :Deadline(date);
   ```

4. Python Neo4j driver setup (`src/infra/graph/neo4j_client.py`)

**Deliverable:** Neo4j operational + schema documentato + test connection

---

#### Week 3-4: Entity Extraction Pipeline

**Tasks:**
1. **NER per entità appalti** (`src/kg/extractors/ner_extractor.py`)
   - Modello base: `dslim/bert-base-NER` fine-tuned su italiano + appalti
   - Entità target:
     - `LOT_ID`: "Lotto 1", "Lotto II", "CIG 123456"
     - `REQUIREMENT`: keyword patterns ("obbligatorio", "pena esclusione", "deve")
     - `DEADLINE`: date + context ("entro il", "scadenza", "termine")
     - `AMOUNT`: importi ("€ 100.000", "base d'asta")
     - `ORG`: enti appaltanti + partecipanti
   - Output: spans + confidence score

2. **Relation Extraction** (`src/kg/extractors/relation_extractor.py`)
   - Regole euristiche + LLM prompting:
     - Tender → Lot (parsing struttura documento)
     - Lot → Requirement (sezione "requisiti tecnici/economici")
     - Requirement → DocumentSection (chunk_id dove compare)
   - Validation: cross-reference con metadata chunk

3. **Graph Builder** (`src/kg/builders/graph_builder.py`)
   ```python
   class GraphBuilder:
       def __init__(self, neo4j_client, ner_extractor, re_extractor):
           ...
       
       async def build_from_tender(self, tender_id: str, chunks: List[TenderChunk]):
           # Extract entities
           entities = await self.ner_extractor.extract(chunks)
           
           # Extract relations
           relations = await self.re_extractor.extract(entities, chunks)
           
           # Create nodes
           await self._create_tender_node(tender_id)
           await self._create_lot_nodes(entities['lots'])
           await self._create_requirement_nodes(entities['requirements'])
           await self._create_deadline_nodes(entities['deadlines'])
           
           # Create relationships
           await self._link_entities(relations)
           
           # Link to document sections
           await self._link_to_chunks(chunks)
   ```

4. **Sync Pipeline** (`src/kg/sync/sync_pipeline.py`)
   - Trigger: dopo ingestion completata
   - Idempotent: re-run sicuro su stesso tender
   - Logging: entità create/updated/skipped

**Deliverable:** Pipeline NER/RE funzionante + 10 gare test in grafo

---

#### Week 5-6: Hybrid Retrieval Strategies

**Tasks:**
1. **Graph-First Retrieval** (`src/domain/tender/search/graph_first_retriever.py`)
   ```python
   class GraphFirstRetriever:
       """Use Neo4j for structured queries, then retrieve chunk text"""
       
       async def retrieve_requirements(self, tender_code: str, lot_id: str = None):
           # Cypher query
           query = """
           MATCH (t:Tender {code: $tender_code})-[:HAS_LOT]->(l:Lot)
           MATCH (l)-[:REQUIRES]->(r:Requirement {mandatory: true})
           MATCH (r)-[:MENTIONED_IN]->(ds:DocumentSection)
           RETURN r.description, ds.chunk_id, ds.section_path, ds.page_numbers
           """
           results = await self.neo4j.query(query, {"tender_code": tender_code})
           
           # Retrieve full chunk text from Milvus metadata
           chunks = await self._fetch_chunks(results)
           return chunks
   ```

2. **Vector-First + Graph Enrichment** (`src/domain/tender/search/vector_first_retriever.py`)
   ```python
   class VectorFirstRetriever:
       """Vector search then enrich with graph context"""
       
       async def retrieve(self, query: str, tender_code: str):
           # Vector search
           vector_results = await self.milvus_searcher.search(
               query, 
               filters={"tender_code": tender_code},
               top_k=20
           )
           
           # Extract entities from results
           chunk_ids = [r['chunk_id'] for r in vector_results]
           
           # Graph enrichment: find related entities
           cypher = """
           MATCH (ds:DocumentSection)-[:MENTIONED_IN]-(entity)
           WHERE ds.chunk_id IN $chunk_ids
           RETURN entity, labels(entity), ds.chunk_id
           """
           graph_context = await self.neo4j.query(cypher, {"chunk_ids": chunk_ids})
           
           # Merge contexts
           enriched_results = self._merge_contexts(vector_results, graph_context)
           return enriched_results
   ```

3. **Graph-Only Queries** (`src/domain/tender/search/graph_only_retriever.py`)
   - Use cases:
     - "Elenca tutte le scadenze per questa gara"
     - "Quanti lotti ha questa gara?"
     - "Quali requisiti hanno pena esclusione?"
   - No embedding, pure Cypher

4. **Hybrid Orchestrator** (`src/domain/tender/search/hybrid_orchestrator.py`)
   ```python
   class HybridOrchestrator:
       """Route queries to best retrieval strategy"""
       
       def _classify_query(self, query: str) -> RetrievalStrategy:
           # Rule-based classifier
           if any(kw in query.lower() for kw in ["scadenza", "quando", "data"]):
               return RetrievalStrategy.GRAPH_ONLY
           elif any(kw in query.lower() for kw in ["requisiti", "obbligatorio"]):
               return RetrievalStrategy.GRAPH_FIRST
           else:
               return RetrievalStrategy.VECTOR_FIRST
       
       async def retrieve(self, query: str, tender_code: str, strategy: str = "auto"):
           if strategy == "auto":
               strategy = self._classify_query(query)
           
           retriever = self._get_retriever(strategy)
           return await retriever.retrieve(query, tender_code)
   ```

**Deliverable:** 3 retrieval strategies + orchestrator + unit tests

---

#### Week 7-8: Integration & Testing

**Tasks:**
1. Update `RAGPipeline` per usare `HybridOrchestrator`
2. API endpoint `/ask-tender` con parametro `retrieval_strategy`
3. Evaluation su 50+ query test:
   - Precision@5, Recall@10, MRR
   - Latency benchmarking (graph vs vector vs hybrid)
   - A/B testing: classic vs hybrid RAG
4. Documentazione: architettura, query examples, troubleshooting

**Deliverable:** Graph RAG production-ready + evaluation report

---

### Phase 2: External Integrations (6 weeks)

#### Week 9-11: ANAC & TED Integration

**Tasks:**
1. **ANAC API Client** (`src/integrations/anac/client.py`)
   - Endpoint: https://dati.anticorruzione.it/opendata
   - Datasets:
     - Bandi di gara (CSV/JSON download)
     - Esiti gare
     - Operatori economici
   - Automazione:
     - Cron job: daily import nuove gare (filtro CPV rilevanti)
     - Parser: extract tender_code, title, buyer, amounts, dates
     - Trigger ingestion pipeline automatica

2. **TED Scraper** (`src/integrations/ted/scraper.py`)
   - Source: https://ted.europa.eu/TED/browse/browseByMap.do
   - Scraping:
     - BeautifulSoup/Scrapy per HTML parsing
     - Filter: Italy + relevant CPVs
     - Download PDF notices
   - Rate limiting: rispetto robots.txt

3. **Auto-Ingestion Workflow** (`src/workflows/auto_ingestion.py`)
   ```python
   async def auto_ingest_from_anac():
       # Fetch new tenders from ANAC
       new_tenders = await anac_client.fetch_new_tenders(since=last_sync_date)
       
       for tender_data in new_tenders:
           # Create tender record
           tender = await tender_service.create_tender(
               code=tender_data['cig'],
               title=tender_data['oggetto'],
               buyer_name=tender_data['amministrazione'],
               ...
           )
           
           # Download documents if available
           docs = await anac_client.download_documents(tender_data['cig'])
           
           for doc in docs:
               # Upload + ingest
               await document_service.upload_and_ingest(
                   tender_id=tender.id,
                   file=doc,
                   document_type="bando"
               )
           
           # Trigger graph building
           await graph_builder.build_from_tender(tender.id)
   ```

**Deliverable:** Auto-ingestion di 50+ gare/giorno da fonti esterne

---

#### Week 12-14: Fine-tuning Pipeline

**Tasks:**
1. **Dataset Creation** (`data/training/`)
   - Annotation tool (Prodigy/Label Studio)
   - Tasks:
     - NER: 500 documenti annotati (Requirement, Deadline, Amount)
     - Retrieval: 200 query-document pairs con relevance labels
     - QA: 300 question-answer pairs con citazioni
   - Format: JSONL per training

2. **Embedding Fine-tuning** (`src/ml/fine_tune_embeddings.py`)
   - Base model: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
   - Objective: contrastive learning
     - Positive pairs: (query, relevant_chunk)
     - Negative pairs: random chunks dallo stesso tender
   - Training:
     - 10K+ pairs da query logs storiche
     - 5 epochs, lr=2e-5
     - Evaluation: recall@10 su test set
   - Output: `models/tender-embedding-v1/`

3. **Reranker Fine-tuning** (`src/ml/fine_tune_reranker.py`)
   - Base: `cross-encoder/ms-marco-MiniLM-L-6-v2`
   - Training data: (query, chunk, relevance_score)
   - Metric: nDCG@10
   - Target: +10% vs base model

4. **NER Model Fine-tuning** (`src/ml/fine_tune_ner.py`)
   - Base: `dbmdz/bert-base-italian-cased`
   - Labels: LOT_ID, REQUIREMENT, DEADLINE, AMOUNT, ORG, CPV
   - Training: 500 documenti → 10K+ annotated sentences
   - Evaluation: F1 per entity type

5. **Model Registry** (`models/registry.json`)
   ```json
   {
     "embedding": {
       "version": "v1.2.0",
       "model_path": "models/tender-embedding-v1/",
       "performance": {"recall@10": 0.87},
       "training_date": "2025-06-15"
     },
     "reranker": {
       "version": "v1.1.0",
       "model_path": "models/tender-reranker-v1/",
       "performance": {"ndcg@10": 0.82}
     }
   }
   ```

6. **A/B Testing Framework** (`src/ml/ab_testing.py`)
   - Randomized split: 50% base model, 50% fine-tuned
   - Metrics tracking: latency, accuracy, user feedback
   - Statistical significance testing

**Deliverable:** Fine-tuned models deployed + 15% improvement vs baseline

---

### Phase 3: Business Workflows (6 weeks)

#### Week 15-16: Compliance Checklist Generator

**File:** `src/workflows/compliance_checker.py`

```python
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class ComplianceItem:
    requirement_id: str
    description: str
    mandatory: bool
    status: str  # "compliant", "non_compliant", "unclear", "not_checked"
    evidence: List[str]  # chunk_ids with proof
    recommendation: str

class ComplianceChecker:
    """Generate compliance checklist for tender participation"""
    
    async def generate_checklist(
        self, 
        tender_code: str, 
        lot_id: str = None,
        company_profile: Dict = None
    ) -> List[ComplianceItem]:
        # 1. Get all mandatory requirements from graph
        requirements = await self._fetch_mandatory_requirements(tender_code, lot_id)
        
        checklist = []
        for req in requirements:
            # 2. Check if we have evidence of compliance
            status = await self._check_compliance(req, company_profile)
            
            # 3. Get supporting chunks
            evidence = await self._get_evidence_chunks(req.id)
            
            # 4. Generate recommendation
            recommendation = self._generate_recommendation(status, req)
            
            checklist.append(ComplianceItem(
                requirement_id=req.id,
                description=req.description,
                mandatory=req.mandatory,
                status=status,
                evidence=[e.chunk_id for e in evidence],
                recommendation=recommendation
            ))
        
        return checklist
    
    async def _check_compliance(self, requirement, company_profile):
        # Use LLM to compare requirement vs company capabilities
        prompt = f"""
        Requisito: {requirement.description}
        Profilo azienda: {company_profile}
        
        Domanda: L'azienda soddisfa questo requisito?
        Rispondi: "compliant", "non_compliant", "unclear"
        """
        
        response = await self.llm.generate(prompt)
        return response.strip().lower()
```

**API Endpoint:** `POST /workflows/compliance-checklist`

```json
{
  "tender_code": "CIG-12345",
  "lot_id": "LOT-01",
  "company_profile": {
    "certifications": ["ISO 9001", "ISO 27001"],
    "revenue_2024": 5000000,
    "employees": 50,
    "past_experience": ["PA digitalization", "Cloud migration"]
  }
}
```

**Response:**
```json
{
  "checklist": [
    {
      "requirement_id": "req-001",
      "description": "Certificazione ISO 9001 in corso di validità",
      "mandatory": true,
      "status": "compliant",
      "evidence": ["chunk-abc123"],
      "recommendation": "✅ OK - Certificazione posseduta"
    },
    {
      "requirement_id": "req-002",
      "description": "Fatturato minimo €10M negli ultimi 3 anni",
      "mandatory": true,
      "status": "non_compliant",
      "evidence": ["chunk-def456"],
      "recommendation": "❌ KO - Fatturato insufficiente (€5M < €10M). Valutare RTI."
    }
  ],
  "summary": {
    "total_requirements": 15,
    "compliant": 12,
    "non_compliant": 2,
    "unclear": 1
  },
  "recommendation": "NO-GO - Requisiti killer non soddisfatti"
}
```

---

#### Week 17-18: Bid/No-Bid Assistant

**File:** `src/workflows/bid_no_bid.py`

```python
@dataclass
class BidNoB idScore:
    overall_score: float  # 0-100
    recommendation: str  # "GO", "NO-GO", "EVALUATE"
    confidence: float
    factors: Dict[str, Dict]
    risks: List[str]
    opportunities: List[str]

class BidNoBidAssistant:
    """Intelligent bid/no-bid decision support"""
    
    async def analyze(self, tender_code: str, lot_id: str = None) -> BidNoBidScore:
        # 1. Compliance analysis
        compliance = await self.compliance_checker.generate_checklist(tender_code, lot_id)
        compliance_score = self._score_compliance(compliance)
        
        # 2. Deadlines feasibility
        deadlines = await self._analyze_deadlines(tender_code)
        timeline_score = self._score_timeline(deadlines)
        
        # 3. Penalties risk
        penalties = await self._fetch_penalties(tender_code)
        penalty_score = self._score_penalties(penalties)
        
        # 4. Evaluation criteria match
        criteria = await self._fetch_criteria(tender_code, lot_id)
        criteria_score = self._score_criteria_match(criteria)
        
        # 5. Competition analysis (similar past tenders)
        competition = await self._analyze_competition(tender_code)
        competition_score = self._score_competition(competition)
        
        # 6. Profitability estimate
        base_amount = await self._get_base_amount(tender_code, lot_id)
        profitability_score = self._score_profitability(base_amount, criteria)
        
        # Weighted scoring
        overall_score = (
            compliance_score * 0.35 +
            timeline_score * 0.15 +
            penalty_score * 0.10 +
            criteria_score * 0.20 +
            competition_score * 0.10 +
            profitability_score * 0.10
        )
        
        # Decision logic
        if overall_score > 70 and compliance_score > 80:
            recommendation = "GO"
        elif overall_score < 40 or compliance_score < 50:
            recommendation = "NO-GO"
        else:
            recommendation = "EVALUATE"
        
        return BidNoBidScore(
            overall_score=overall_score,
            recommendation=recommendation,
            confidence=self._calculate_confidence(compliance, criteria),
            factors={
                "compliance": {"score": compliance_score, "weight": 0.35},
                "timeline": {"score": timeline_score, "weight": 0.15},
                # ...
            },
            risks=self._identify_risks(penalties, deadlines),
            opportunities=self._identify_opportunities(criteria, competition)
        )
```

---

#### Week 19-20: Change Detection & Tender Similarity

**Tasks:**
1. **Change Detection** (`src/workflows/change_detection.py`)
   - Compare tender T1 vs T2 (stesso ente/CPV)
   - Graph diff: Requirement/Deadline/Penalty deltas
   - Text diff: clausole modificate

2. **Similarity Search** (`src/workflows/tender_similarity.py`)
   - Embedding tender-level: aggregate chunk embeddings
   - Vector search su tenders storici
   - Filter: CPV, buyer, amount range
   - Rank by: similarity + outcome (won/lost)

**Deliverable:** API endpoints + UI integration

---

### Phase 4: Production Deployment (8 weeks)

#### Week 21-24: Infrastructure & Security

**Tasks:**
1. **Kubernetes Manifests** (`k8s/`)
   - Deployments: API (3 replicas), workers (5 replicas)
   - StatefulSets: Postgres, Neo4j
   - Services: LoadBalancer, ClusterIP
   - ConfigMaps: environment configs
   - Secrets: DB passwords, API keys

2. **Multi-tenancy**
   - Row-level security (Postgres RLS)
   - Milvus partitions per client_id
   - Neo4j database per tenant (Enterprise) o labels
   - API: middleware per tenant isolation

3. **Auth & RBAC**
   - JWT tokens (access + refresh)
   - Roles: admin, analyst, viewer
   - Permissions: read_tender, write_tender, manage_users
   - OAuth2 integration (Google/Azure AD)

4. **Encryption**
   - TLS certificates (Let's Encrypt)
   - At-rest: Postgres pgcrypto, Milvus encryption
   - Secrets management: HashiCorp Vault

5. **GDPR Compliance**
   - Data retention policies (delete after N years)
   - Right-to-delete API endpoint
   - Audit logs: chi ha acceduto a cosa
   - Data export (JSON per portability)

**Deliverable:** Secure, multi-tenant production environment

---

#### Week 25-28: Monitoring & Optimization

**Tasks:**
1. **Observability Stack**
   - Prometheus: metrics (latency, throughput, errors)
   - Grafana: dashboards
     - RAG Pipeline Performance
     - Database Health (Postgres, Milvus, Neo4j)
     - Cost Tracking (LLM tokens, embeddings)
   - Jaeger: distributed tracing
   - Sentry: error tracking + alerting

2. **Performance Tuning**
   - Redis cache: frequent queries (TTL 5min)
   - Postgres: query optimization, indexes
   - Milvus: index tuning (IVF_FLAT vs HNSW)
   - Neo4j: query profiling, index on hot paths
   - Connection pooling: asyncpg, pymilvus

3. **Load Testing**
   - Locust scenarios:
     - 100 concurrent users
     - Mixed workload (80% read, 20% write)
   - Target: <3s p95 latency, 99.9% success rate

4. **Cost Optimization**
   - Model caching: avoid re-embedding same text
   - Batch processing: group LLM calls
   - Spot instances: non-critical workloads

**Deliverable:** Observable, optimized production system

---

## 📊 Success Metrics & KPIs

### Technical Metrics

| Metric | Baseline | Target Q2 | Target Q4 |
|--------|----------|-----------|-----------|
| **Retrieval Precision@5** | 0.75 | 0.85 | 0.90 |
| **Retrieval Recall@10** | 0.65 | 0.80 | 0.88 |
| **Graph Entity Extraction F1** | - | 0.85 | 0.92 |
| **Query Latency (p95)** | 5s | 3s | 2s |
| **System Uptime** | 95% | 99% | 99.9% |
| **Concurrent Users** | 10 | 50 | 100 |
| **Docs Ingested/Hour** | 50 | 200 | 500 |

### Business Metrics

| Metric | Target |
|--------|--------|
| **Time-to-Analyze Tender** | 60% reduction vs manual |
| **Compliance Checklist Accuracy** | 95% |
| **Bid/No-Bid Decision Alignment** | 85% with human decision |
| **Auto-Ingestion Coverage** | 100 tenders/day from ANAC |
| **User Satisfaction (NPS)** | > 50 |

---

## 🔄 Continuous Improvement

### Post-Launch Roadmap (2026)

**Q1 2026:**
- Advanced analytics: tender outcome prediction (ML model)
- Collaborative features: team annotations, comments
- Mobile app: iOS/Android for on-the-go access

**Q2 2026:**
- Multi-language: English, French for EU tenders
- Voice interface: speech-to-text Q&A
- Integration: CRM systems (Salesforce), document managers (SharePoint)

**Q3 2026:**
- Generative features: auto-draft technical responses
- Competitive intelligence: scrape public bids from competitors
- Financial modeling: ROI calculator per gara

**Q4 2026:**
- AI agents: autonomous bid preparation assistant
- Blockchain: tamper-proof audit trail for compliance
- Marketplace: template marketplace per offerte tipo

---

## 📚 Documentation & Training

### Developer Documentation
- Architecture deep-dive (this file + /docs/architecture/)
- API reference (OpenAPI/Swagger)
- Deployment guide (k8s, Docker Compose)
- Contributing guide (PR process, code style)

### User Documentation
- Getting started guide
- Feature tutorials (compliance, bid/no-bid)
- Video demos
- FAQ

### Training Materials
- Onboarding checklist per nuovi dev
- Lunch & Learn sessions: Graph RAG, Fine-tuning
- External talks: conferences, meetups

---

## 🎯 Next Actions (This Week)

### High Priority
1. ✅ Create roadmap document (questo file)
2. 🚧 Setup Neo4j development instance
3. 🚧 Design NER annotation schema for training data
4. 📋 Draft ANAC API integration requirements

### Medium Priority
5. 📋 Research TED scraping legal constraints
6. 📋 Evaluate fine-tuning vs prompt engineering for entity extraction
7. 📋 Create compliance checker UI mockups

### Low Priority
8. 📋 Benchmark Neo4j vs other graph DBs (Amazon Neptune, TigerGraph)
9. 📋 Investigate GDPR implications for public tender data
10. 📋 Plan conference talk submission (PyCon Italia 2026)

---

## 📞 Stakeholders & Communication

**Project Lead:** Gianmarco Mottola  
**Target Users:** Uffici gare, consulenti appalti  
**Review Cadence:** Bi-weekly sprint planning  
**Feedback Channels:** GitHub Discussions, user interviews  

---

*Last Updated: 24 December 2025*  
*Version: 1.0.0*  
*Status: 🚀 Ready for Execution*
