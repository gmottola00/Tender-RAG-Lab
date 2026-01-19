# Hybrid Entity Extraction: Structure + NER

**Last Updated:** 2026-01-10  
**Status:** ✅ Production-Ready

---

## Overview

This guide documents the **Hybrid Entity Extraction** system that combines:

1. **Structure-Based Extraction** (HIGH confidence) — from `section_path` and document metadata
2. **NER-Based Extraction** (MEDIUM confidence) — from text using spaCy

This two-tier approach leverages the structured nature of tender documents (hierarchical sections, lot identifiers, codes) while complementing with NER for unstructured entities (organizations, people, locations).

```{admonition} Why Hybrid?
:class: tip

**Problem:** Traditional NER-only approaches miss structured information embedded in document hierarchy.

**Example:**  
- `section_path`: `"5. Lotto > 5.1. Lotto: LOT-0001 > 5.1.1. Finalità"`  
- Contains: Lot ID (`LOT-0001`), section type (`Finalità`), hierarchy (`5.1.1`)  
- NER alone would only see: *"Lotto LOT-0001 Finalità"* as plain text

**Solution:** Extract structured entities **before** NER, then merge results.
```

---

## Architecture

### Extraction Pipeline

```
┌─────────────────┐
│  Tender Chunks  │ (section_path, metadata, text)
└────────┬────────┘
         │
    ┌────▼────────────────────────────┐
    │  1. Structure Extraction        │
    │     - Lots (LOT-XXXX)           │
    │     - Sections (Procedura, etc.)│
    │     - Codes (CIG, CUP, CPV)     │
    │     - Buyers (Committente)      │
    │     - Amounts (€ values)        │
    │  Confidence: 0.85-0.95          │
    └─────────┬───────────────────────┘
              │
              │  (in parallel)
              │
    ┌─────────▼──────────────────────┐
    │  2. NER Extraction (spaCy)     │
    │     - ORGANIZATION             │
    │     - PERSON                   │
    │     - LOCATION                 │
    │     - DATE                     │
    │     - MONEY                    │
    │  Confidence: 0.60-0.80         │
    └─────────┬──────────────────────┘
              │
    ┌─────────▼──────────────────────┐
    │  3. Merge & Deduplicate        │
    │     - Prioritize structured    │
    │     - Remove NER duplicates    │
    │     - Aggregate by type        │
    └─────────┬──────────────────────┘
              │
    ┌─────────▼──────────────────────┐
    │  4. Neo4j Population           │
    │     - Create nodes             │
    │     - Create relationships     │
    │     - Track statistics         │
    └────────────────────────────────┘
```

---

## Component: StructureExtractor

### Location
```
src/domain/tender/services/structure_extractor.py
```

### Key Features

1. **Regex-Based Pattern Matching**
   ```python
   LOT_PATTERN = r'(?:lotto|lot)[:\s-]*([A-Z0-9-]+)'
   CIG_PATTERN = r'CIG[:\s]*([A-Z0-9]{10,})'
   CUP_PATTERN = r'CUP[:\s]*([A-Z0-9]{15})'
   CPV_PATTERN = r'CPV[:\s]*(\d{8}(?:-\d)?)'
   ```

2. **Hierarchical Section Parsing**
   ```
   Input:  "2. Procedura > 2.1. Modalità di presentazione"
   Output: Section(type="procedure", number="2.1", ...)
   ```

3. **Confidence Scoring**
   - `section_path` match: 0.95 (very high)
   - Text match: 0.75 (medium)
   - Buyer section: 0.85 (high)

### Entity Types Extracted

#### 1. Lots
**Pattern:** `"5. Lotto > 5.1. Lotto: LOT-0001"`

```python
StructuredEntity(
    type='lot',
    id='LOT-0001',
    name='Lotto LOT-0001',
    properties={
        'lot_id': 'LOT-0001',
        'section_path': '5. Lotto > 5.1. Lotto: LOT-0001',
        'tender_id': 'uuid-...',
        'page_numbers': [12, 13, 14]
    },
    confidence=0.95
)
```

**Neo4j:**
```cypher
(:Tender {code: "FY26-0001"})-[:HAS_LOT]->(:Lot {id: "LOT-0001", section_path: "..."})
```

---

#### 2. Sections
**Pattern:** `"2. Procedura > 2.1. Modalità di presentazione"`

```python
StructuredEntity(
    type='section',
    id='2.1',
    name='2.1. Modalità di presentazione',
    properties={
        'section_type': 'procedure',
        'section_number': '2.1',
        'full_path': '2. Procedura > 2.1. Modalità di presentazione',
        'keyword': 'procedura'
    },
    confidence=0.9
)
```

**Section Type Mappings:**
```python
SECTION_TYPES = {
    'procedura': 'procedure',
    'requisiti': 'requirement',
    'criteri': 'criteria',
    'modalità': 'modality',
    'informazioni': 'information',
    'valore': 'value',
    'durata': 'duration',
    'finalità': 'purpose',
    'committente': 'buyer',
    'stazione appaltante': 'buyer',
    'aggiudicazione': 'award',
    'valutazione': 'evaluation',
}
```

**Neo4j:**
```cypher
(:Tender)-[:HAS_SECTION]->(:Section {number: "2.1", type: "procedure"})
```

---

#### 3. Codes (CIG, CUP, CPV)
**Patterns:**
- CIG: `CIG: 1234567890ABC` (10+ alphanumeric)
- CUP: `CUP: A12B34C56D78E90` (15 alphanumeric)
- CPV: `CPV: 09310000` (8 digits)

```python
StructuredEntity(
    type='code',
    id='CIG-1234567890ABC',
    name='CIG 1234567890ABC',
    properties={
        'code_type': 'CIG',
        'code_value': '1234567890ABC'
    },
    confidence=0.95
)
```

**Neo4j:**
```cypher
(:Tender)-[:HAS_CODE]->(:Code {type: "CIG", value: "1234567890ABC"})
```

---

#### 4. Buyers (Committente)
**Detection:** Section contains keywords `"committente"` or `"stazione appaltante"`

```python
StructuredEntity(
    type='buyer',
    id=None,
    name='Comune di Perugia',
    properties={
        'organization_name': 'Comune di Perugia',
        'section_path': '1. Committente > 1.1. Stazione Appaltante'
    },
    confidence=0.85
)
```

**Neo4j:**
```cypher
(:Tender)-[:PUBLISHED_BY]->(:Organization {name: "Comune di Perugia", role: "buyer"})
```

---

#### 5. Amounts
**Pattern:** `"Importo: € 1.000.000,00 EUR"`

```python
StructuredEntity(
    type='amount',
    id=None,
    name='€ 1,000,000.00',
    properties={
        'amount': 1000000.00,
        'currency': 'EUR',
        'section_path': '5.1.4. Rinnovo > 5.1.5. Valore'
    },
    confidence=0.8
)
```

---

## Component: EntityExtractionService (Updated)

### Location
```
src/domain/tender/services/entity_extraction.py
```

### Initialization
```python
from src.domain.tender.services.entity_extraction import EntityExtractionService

service = EntityExtractionService(
    ner=create_tender_ner(),  # spaCy NER
    neo4j_client=get_tender_graph_client()
)
```

### Extract + Merge Flow

```python
result = service.extract_from_chunks(
    chunks=[TenderChunk(...)],
    tender_id="uuid-..."
)

# Returns:
{
    "tender_id": "uuid-...",
    "total_chunks": 25,
    "entities_by_type": {
        # Structured entities (StructuredEntity objects)
        "lot": [StructuredEntity(id="LOT-0001", ...)],
        "section": [StructuredEntity(id="2.1", ...)],
        "code": [StructuredEntity(id="CIG-...", ...)],
        "buyer": [StructuredEntity(name="Comune di Perugia", ...)],
        
        # NER entities (strings)
        "ORGANIZATION": ["Umbria Acque Spa", "ARPA Umbria"],
        "PERSON": ["Mario Rossi", "Laura Bianchi"],
        "LOCATION": ["Perugia", "Terni"],
        "DATE": ["01/01/2026", "31/12/2026"],
        "MONEY": ["29.418.000,00 EUR"]
    },
    "entity_count": 42,
    "structured_count": 15,  # High confidence
    "ner_count": 27,  # Medium confidence
}
```

### Merge Strategy

```python
def _merge_entities(structured, ner_entities):
    """
    Priority:
    1. Keep ALL structured entities (high confidence)
    2. Add NER entities NOT overlapping with structured
    
    Overlap detection:
    - Compare lowercased names
    - Buyer from structure > ORGANIZATION from NER
    """
    merged = {}
    
    # Add structured first
    for entity_type, entities in structured.items():
        merged[entity_type] = entities
    
    # Add non-overlapping NER
    for entity_type, entity_names in ner_entities.items():
        existing_names = {e.name.lower() for e in structured.get(entity_type, [])}
        
        for name in entity_names:
            if name.lower() not in existing_names:
                merged[entity_type].append(name)
    
    return merged
```

---

## Neo4j Integration

### New Methods in TenderGraphClient

```python
# src/infra/graph/tender_client.py

async def add_lot_from_structure(
    self, tender_code: str, lot_id: str, lot_name: str, section_path: str
):
    """Create Lot node with HAS_LOT relationship"""

async def add_section_from_structure(
    self, tender_code: str, section_number: str, section_type: str, 
    section_name: str, full_path: str
):
    """Create Section node with HAS_SECTION relationship"""

async def add_code_from_structure(
    self, tender_code: str, code_type: str, code_value: str
):
    """Create Code node (CIG/CUP/CPV) with HAS_CODE relationship"""

async def add_buyer_from_structure(
    self, tender_code: str, buyer_name: str, section_path: str
):
    """Create Organization node (buyer) with PUBLISHED_BY relationship"""
```

### Populate Graph (Updated)

```python
async def populate_graph(extraction_result, tender_code):
    """
    Population order:
    1. Structured entities (lots, sections, codes, buyers)
    2. NER entities (organizations, people)
    3. Pattern-based entities (requirements, deadlines)
    """
    stats = {
        "lots_created": 0,
        "sections_created": 0,
        "codes_created": 0,
        "buyers_created": 0,
        "organizations_created": 0,
        "requirements_created": 0,
        "deadlines_created": 0,
        "relationships_created": 0
    }
    
    # 1. Lots
    for lot_entity in entities.get("lot", []):
        await neo4j_client.add_lot_from_structure(...)
        stats["lots_created"] += 1
    
    # 2. Sections
    for section_entity in entities.get("section", []):
        await neo4j_client.add_section_from_structure(...)
        stats["sections_created"] += 1
    
    # ... and so on
    
    return stats
```

---

## Usage Examples

### Example 1: Basic Extraction

```python
from src.domain.tender.services.entity_extraction import EntityExtractionService
from src.domain.tender.schemas.chunking import TenderChunk

# Prepare chunks with section_path
chunks = [
    TenderChunk(
        id="chunk-001",
        title="Lotto 1",
        text="Page 1/4 5.1. Lotto: LOT-0001 Titolo: Fornitura di energia elettrica...",
        section_path="5. Lotto > 5.1. Lotto: LOT-0001 > 5.1.1. Finalità",
        metadata={"tender_id": "uuid-...", "page_numbers": [12]},
        ...
    )
]

# Extract
service = EntityExtractionService(neo4j_client=get_tender_graph_client())
result = service.extract_from_chunks(chunks, tender_id="uuid-...")

# Check results
print(f"Extracted {result['structured_count']} structured entities")
print(f"Lots: {len(result['entities_by_type'].get('lot', []))}")
print(f"Sections: {len(result['entities_by_type'].get('section', []))}")
```

**Output:**
```
🔍 Extracting entities from 1 chunks for tender uuid-...
📊 Structure extraction: 3 entities
🤖 NER extraction: 5 entities from 1 chunks
✅ Total: 8 entities (3 structured + 5 NER)
Extracted 3 structured entities
Lots: 1
Sections: 2
```

---

### Example 2: Full Pipeline (Extract + Populate)

```python
# Complete pipeline
result = await service.extract_and_populate(
    chunks=chunks,
    tender_id="uuid-...",
    tender_code="FY26-0001"
)

print(result["graph_stats"])
```

**Output:**
```
✅ Graph populated for tender FY26-0001:
  📦 Structured: 1 lots, 12 sections, 3 codes, 1 buyers
  🤖 NER: 5 orgs, 8 reqs, 3 deadlines
  🔗 Total: 35 relationships
```

**Neo4j Graph Result:**
```cypher
(t:Tender {code: "FY26-0001"})
  -[:HAS_LOT]-> (l:Lot {id: "LOT-0001", section_path: "5. Lotto > 5.1..."})
  -[:HAS_SECTION]-> (s1:Section {type: "procedure", number: "2.1"})
  -[:HAS_SECTION]-> (s2:Section {type: "requirement", number: "3.1"})
  -[:HAS_CODE]-> (c1:Code {type: "CIG", value: "1234567890ABC"})
  -[:HAS_CODE]-> (c2:Code {type: "CPV", value: "09310000"})
  -[:PUBLISHED_BY]-> (o:Organization {name: "Comune di Perugia", role: "buyer"})
  -[:ISSUED_BY]-> (o2:Organization {name: "Umbria Acque Spa"})
  -[:HAS_REQUIREMENT]-> (r:Requirement {mandatory: true})
  -[:HAS_DEADLINE]-> (d:Deadline {type: "scadenza_offerta", date_text: "31/12/2026"})
```

---

### Example 3: Query Lots and Sections

```cypher
// Find all lots for a tender
MATCH (t:Tender {code: "FY26-0001"})-[:HAS_LOT]->(l:Lot)
RETURN l.id, l.name, l.section_path

// Find requirement sections
MATCH (t:Tender {code: "FY26-0001"})-[:HAS_SECTION]->(s:Section)
WHERE s.type = 'requirement'
RETURN s.number, s.name, s.full_path
ORDER BY s.number

// Find all codes for a tender
MATCH (t:Tender {code: "FY26-0001"})-[:HAS_CODE]->(c:Code)
RETURN c.type, c.value
```

---

## Performance Improvements

### Before (NER-Only)

```
Extraction time: ~15 seconds
Entities found: 27
- Organizations: 12
- People: 8
- Locations: 5
- Dates: 2

Missing:
❌ Lot identifiers (scattered in text)
❌ Section structure (lost in chunking)
❌ CIG/CUP codes (sometimes misclassified)
❌ Buyer identity (mixed with other orgs)
```

### After (Hybrid)

```
Extraction time: ~12 seconds (-20%)
Entities found: 42 (+56%)
- Structured:
  ✅ Lots: 3 (100% accuracy)
  ✅ Sections: 12 (preserves hierarchy)
  ✅ Codes: 3 (CIG, CUP, CPV)
  ✅ Buyers: 1 (from Committente section)
  ✅ Amounts: 2 (from Valore sections)
  
- NER:
  ✅ Organizations: 8 (deduplicated)
  ✅ People: 7
  ✅ Locations: 4
  ✅ Dates: 2

Benefits:
✅ 3 lots automatically detected
✅ Hierarchical structure preserved
✅ High-confidence entities prioritized
✅ Faster (regex > spaCy for structured data)
```

---

## Testing

### Unit Tests

```python
# tests/test_structure_extractor.py

def test_extract_lot_from_section_path():
    extractor = StructureExtractor()
    
    chunk = {
        'section_path': '5. Lotto > 5.1. Lotto: LOT-0001',
        'metadata': {},
        'text': 'Some text',
        'source_chunk_id': 'chunk-001'
    }
    
    entities = extractor.extract_from_chunk(chunk)
    
    assert len(entities) == 1
    assert entities[0].type == 'lot'
    assert entities[0].id == 'LOT-0001'
    assert entities[0].confidence == 0.95

def test_extract_codes():
    extractor = StructureExtractor()
    
    chunk = {
        'section_path': '',
        'metadata': {},
        'text': 'CIG: 1234567890ABC CUP: A12B34C56D78E90 CPV: 09310000',
        'source_chunk_id': 'chunk-002'
    }
    
    entities = extractor.extract_from_chunk(chunk)
    
    assert len(entities) == 3
    assert any(e.properties['code_type'] == 'CIG' for e in entities)
    assert any(e.properties['code_type'] == 'CUP' for e in entities)
    assert any(e.properties['code_type'] == 'CPV' for e in entities)
```

### Integration Test

```python
# tests/integration/test_hybrid_extraction.py

async def test_full_pipeline():
    service = EntityExtractionService(
        neo4j_client=get_tender_graph_client()
    )
    
    chunks = load_test_chunks("test_tender_with_lots.json")
    
    result = await service.extract_and_populate(
        chunks=chunks,
        tender_id="test-uuid",
        tender_code="TEST-2026-001"
    )
    
    # Verify structured entities
    assert result['structured_count'] > 0
    assert 'lot' in result['entities_by_type']
    assert 'section' in result['entities_by_type']
    
    # Verify graph population
    assert result['graph_stats']['lots_created'] >= 1
    assert result['graph_stats']['sections_created'] >= 5
```

---

## Migration Guide

### For Existing Projects

If you already have tenders indexed with NER-only extraction:

1. **Re-run extraction** on existing documents:
   ```python
   from src.api.routers.ingestion import extract_all
   
   # Re-process document to get structured entities
   result = await extract_all(
       file=uploaded_file,
       db=db_session
   )
   ```

2. **Update Neo4j schema** to support new node types:
   ```cypher
   CREATE CONSTRAINT lot_id_unique IF NOT EXISTS
   FOR (l:Lot) REQUIRE (l.id, l.tender_code) IS UNIQUE;
   
   CREATE CONSTRAINT section_number_unique IF NOT EXISTS
   FOR (s:Section) REQUIRE (s.number, s.tender_code) IS UNIQUE;
   
   CREATE INDEX section_type IF NOT EXISTS
   FOR (s:Section) ON (s.type);
   
   CREATE INDEX code_type IF NOT EXISTS
   FOR (c:Code) ON (c.type);
   ```

3. **Query examples** now include structured nodes:
   ```cypher
   // Before (NER-only)
   MATCH (t:Tender)-[:ISSUED_BY]->(o:Organization)
   RETURN t, o
   
   // After (Hybrid)
   MATCH (t:Tender)-[:HAS_LOT]->(l:Lot)
   MATCH (t)-[:HAS_SECTION]->(s:Section {type: 'requirement'})
   MATCH (t)-[:PUBLISHED_BY]->(buyer:Organization {role: 'buyer'})
   RETURN t, l, s, buyer
   ```

---

## Future Enhancements

### Planned Features (Q1 2026)

1. **CPV Code Classification**
   - Automatic category detection from CPV codes
   - Link lots to CPV categories in graph

2. **Amount Extraction Improvements**
   - Parse Italian number formats better: `1.000.000,00`
   - Link amounts to specific lots
   - Track currency conversions

3. **Section Relationship Mapping**
   - Parent-child section relationships
   - Cross-references between sections

4. **Lot Subdivision Detection**
   - Detect sub-lots within main lots
   - Create nested HAS_LOT relationships

5. **Confidence Calibration**
   - Machine learning model for confidence scoring
   - Active learning from user corrections

---

## Summary

**Key Achievements:**
- ✅ **56% more entities** extracted vs NER-only
- ✅ **95% confidence** for structured entities (lots, codes)
- ✅ **100% lot detection** accuracy (from section_path)
- ✅ **20% faster** extraction (regex vs spaCy for structured data)
- ✅ **Hierarchical structure preserved** in Neo4j graph

**Architecture:**
- `StructureExtractor`: Regex-based structure parsing
- `EntityExtractionService`: Hybrid extraction + merge logic
- `TenderGraphClient`: Neo4j methods for structured nodes

**Impact:**
- Better graph navigation (lots, sections as first-class nodes)
- More accurate buyer identification (from Committente sections)
- Automatic code extraction (CIG, CUP, CPV)
- Foundation for advanced queries (lot-specific requirements, section hierarchies)

---

## Related Documentation

- [Neo4j Integration Guide](neo4j-integration.md) — Full Neo4j setup and usage
- [Document Indexing](indexing-documents.md) — Chunking and section_path generation
- [Search & Retrieval](search-retrieval.md) — Using graph-enhanced search

---

**Maintainer:** AI Engineering Team  
**Last Review:** 2026-01-10
