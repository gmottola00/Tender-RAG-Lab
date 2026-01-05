# NER API

Named Entity Recognition for tender documents using spaCy.

## TenderNER Class

The `TenderNER` class provides entity extraction for Italian tender documents:

```python
class TenderNER:
    """NER for tender documents using spaCy Italian models."""
    
    def __init__(
        self,
        model_name: str = "it_core_news_lg",
        use_gpu: bool = False
    ):
        """Initialize with spaCy Italian model."""
        ...

## Usage Examples

### Basic Entity Extraction

```python
from src.domain.tender.ner import TenderNER

# Initialize (downloads spaCy model if needed)
ner = TenderNER()

# Extract entities from text
text = """
Il Comune di Milano indice gara per servizi di pulizia.
Importo: €500.000. Scadenza: 30 gennaio 2026.
RUP: Dott. Mario Rossi.
"""

entities = ner.extract_entities(text)
print(entities)
# {
#     "ORGANIZATION": ["Comune di Milano"],
#     "MONEY": ["€500.000"],
#     "DATE": ["30 gennaio 2026"],
#     "PERSON": ["Mario Rossi"]
# }
```

### With Position Information

```python
entities_with_pos = ner.extract_with_positions(text)

for entity in entities_with_pos:
    print(f"{entity['label']}: {entity['text']} @ {entity['start']}-{entity['end']}")
```

### Tender Metadata Extraction

```python
metadata = ner.extract_tender_metadata(tender_text)

print(f"Organizations: {metadata['organizations']}")
print(f"People: {metadata['people']}")
print(f"Dates: {metadata['dates']}")
print(f"Amounts: {metadata['amounts']}")
```

### Batch Processing

```python
# Process multiple chunks
enriched_chunks = ner.process_chunks(tender_chunks)

for chunk in enriched_chunks:
    print(f"Chunk {chunk['chunk_id']}")
    print(f"Entities: {chunk['entities']}")
```

## Supported Entity Types

| Type | Description | Examples |
|------|-------------|----------|
| `PERSON` | Names of people | "Mario Rossi", "Dott. Bianchi" |
| `ORGANIZATION` | Companies, institutions | "Comune di Milano", "ANAC" |
| `LOCATION` | Places, addresses | "Milano", "Via Roma 10" |
| `DATE` | Temporal expressions | "30 gennaio 2026", "15/02/2026" |
| `MONEY` | Monetary amounts | "€500.000", "1.2 milioni" |
| `PERCENT` | Percentages | "10%", "5 percento" |

## Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | str | "it_core_news_lg" | spaCy Italian model |
| `use_gpu` | bool | False | Enable GPU acceleration |
| `normalize_labels` | bool | True | Map to simplified labels |
| `min_length` | int | 2 | Minimum entity length |

## Installation

See [spaCy Installation Guide](../../INSTALL_SPACY.md) for setup instructions.

```bash
# Install spaCy
uv pip install spacy

# Download Italian model (large)
uv run python -m spacy download it_core_news_lg

# Or small model for testing
uv run python -m spacy download it_core_news_sm
```

## See Also

- [Tender Services](services.md) - Document service integration
- [Knowledge Graph](../../guides/knowledge-graph.md) - Neo4j with NER entities
