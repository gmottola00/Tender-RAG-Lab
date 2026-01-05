# Tender Services API

Domain services for tender document management.

## DocumentService

Manages tender documents with business logic:

```python
class DocumentService:
    """Service for tender document management."""
    
    def __init__(self, indexer: TenderMilvusIndexer):
        self.indexer = indexer
    
    async def upload(
        self,
        file: UploadFile,
        tender_id: str,
        title: str
    ) -> Document:
        """Upload and index document."""
        ...

## Usage Examples

### Document Upload

```python
from src.domain.tender.services.documents import DocumentService

service = DocumentService()

# Upload and index document
document = await service.upload(
    file=uploaded_file,
    tender_id="TENDER-2025-001",
    title="Capitolato Tecnico"
)

print(f"Uploaded: {document.id}")
```

### Search Documents

```python
# Vector search
results = await service.search(
    query="requisiti tecnici obbligatori",
    top_k=10
)

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Text: {result.text[:100]}...")
```

### Tender Management

```python
from src.domain.tender.services.tenders import TenderService

tender_service = TenderService()

# Create tender
tender = await tender_service.create(
    title="Servizi di Pulizia 2025",
    issuing_authority="Comune di Milano",
    deadline="2026-02-15"
)

# Get tender with documents
tender_full = await tender_service.get_with_documents(tender.id)
print(f"Documents: {len(tender_full.documents)}")
```

## See Also

- [Search System](../../domain/tender-search.md) - Hybrid search details
- [NER API](ner.md) - Entity extraction
- [API Endpoints](../../guides/quickstart.md) - HTTP routes
