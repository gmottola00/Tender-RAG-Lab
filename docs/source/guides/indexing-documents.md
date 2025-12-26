# Indexing Documents

> **Complete guide to uploading, processing, and indexing tender documents**

This guide covers the full document lifecycle: from uploading files to indexing them in the vector store for semantic search.

---

## Overview

The document indexing pipeline consists of three main stages:

1. **Upload** - Store raw files (PDF, DOCX, TXT)
2. **Processing** - Extract text, parse structure, OCR if needed
3. **Indexing** - Chunk text, generate embeddings, store in Milvus

```text
┌─────────────┐    ┌──────────────┐    ┌───────────────┐
│   Upload    │───▶│  Processing  │───▶│   Indexing    │
│  (Storage)  │    │  (Parsing)   │    │  (Milvus)     │
└─────────────┘    └──────────────┘    └───────────────┘
```

---

## Quick Start

### Upload a Single Document

```python
from src.domain.tender.services.documents import DocumentService

service = DocumentService()

# Upload tender document
document = service.upload(
    file_path="path/to/tender.pdf",
    tender_id="TENDER-2025-001",
    metadata={
        "authority": "Ministero dell'Interno",
        "deadline": "2025-03-15",
        "cig": "12345678AB"
    }
)

print(f"Document uploaded: {document.id}")
print(f"Status: {document.status}")
```

### Batch Upload

```python
import os
from pathlib import Path

# Upload all PDFs from a directory
tender_dir = Path("data/input/tenders/2025/")

for pdf_file in tender_dir.glob("*.pdf"):
    document = service.upload(
        file_path=str(pdf_file),
        tender_id=f"TENDER-{pdf_file.stem}",
    )
    print(f"Uploaded: {pdf_file.name} → {document.id}")
```

---

## Document Processing Pipeline

### Step 1: File Upload

Documents are stored in the configured storage backend (local filesystem or S3):

```python
from src.infra.storage import get_storage_client

storage = get_storage_client()

# Store file
file_url = storage.upload(
    file_path="tender.pdf",
    bucket="tenders",
    prefix="2025/01/"
)
```

**Supported formats:**
- PDF (including scanned with OCR)
- DOCX (Microsoft Word)
- TXT (plain text)

### Step 2: Text Extraction

The system automatically detects file type and applies appropriate parsing:

```python
from src.domain.tender.services.documents import DocumentParser

parser = DocumentParser()

# Automatic format detection
parsed_data = parser.parse(file_path="tender.pdf")

print(f"Title: {parsed_data.title}")
print(f"Pages: {parsed_data.page_count}")
print(f"Extracted text length: {len(parsed_data.text)}")
```

**OCR Support:**
- Automatically triggered for scanned PDFs
- Uses Tesseract OCR for Italian/English
- Preserves layout and page numbers

### Step 3: Text Chunking

Text is split into overlapping chunks for better retrieval:

```python
from rag_toolkit.chunking import RecursiveTokenChunker

chunker = RecursiveTokenChunker(
    chunk_size=512,        # tokens per chunk
    chunk_overlap=50,      # overlap for context
    model="gpt-3.5-turbo"  # tokenizer model
)

chunks = chunker.chunk(parsed_data.text)
print(f"Created {len(chunks)} chunks")
```

**Chunking strategy:**
- Default: 512 tokens per chunk with 50 token overlap
- Respects sentence boundaries (no mid-sentence cuts)
- Preserves metadata (page numbers, section headers)

### Step 4: Embedding Generation

Each chunk is converted to a vector embedding:

```python
from src.infra.factory import create_tender_stack

stack = create_tender_stack()
embedding_client = stack.embedding_client

# Generate embeddings
vectors = embedding_client.embed_batch(
    texts=[chunk.text for chunk in chunks]
)

print(f"Generated {len(vectors)} embeddings")
print(f"Embedding dimension: {len(vectors[0])}")
```

**Models supported:**
- Ollama: `nomic-embed-text` (768d, local)
- OpenAI: `text-embedding-3-small` (1536d, API)

### Step 5: Vector Store Indexing

Embeddings are stored in Milvus with metadata:

```python
from src.domain.tender.indexing import TenderMilvusIndexer

indexer = TenderMilvusIndexer(
    collection_name="tender_documents",
    embedding_client=embedding_client
)

# Index all chunks
indexer.index_documents(
    documents=chunks,
    tender_id="TENDER-2025-001",
    metadata={
        "source_file": "tender.pdf",
        "upload_date": "2025-12-26"
    }
)

print(f"Indexed {len(chunks)} chunks in Milvus")
```

---

## Complete Example

Here's a full end-to-end indexing workflow:

```python
from pathlib import Path
from src.domain.tender.services.documents import DocumentService
from src.infra.factory import create_tender_stack

# Initialize services
stack = create_tender_stack()
doc_service = DocumentService(
    storage_client=stack.storage_client,
    indexer=stack.indexer
)

# Index a tender document
def index_tender(file_path: str, tender_id: str):
    """Complete indexing pipeline"""
    
    print(f"1. Uploading {file_path}...")
    document = doc_service.upload(
        file_path=file_path,
        tender_id=tender_id
    )
    
    print(f"2. Parsing document...")
    parsed = doc_service.parse(document.id)
    
    print(f"3. Chunking text ({len(parsed.text)} chars)...")
    chunks = doc_service.chunk(parsed)
    
    print(f"4. Generating embeddings for {len(chunks)} chunks...")
    doc_service.embed(chunks)
    
    print(f"5. Indexing in Milvus...")
    result = doc_service.index(chunks, tender_id=tender_id)
    
    print(f"✅ Successfully indexed {result.chunk_count} chunks")
    return result

# Usage
result = index_tender(
    file_path="data/input/tender_2025_001.pdf",
    tender_id="TENDER-2025-001"
)
```

---

## Advanced Configuration

### Custom Chunking Strategy

For technical documents with tables/diagrams:

```python
from rag_toolkit.chunking import SemanticChunker

# Split by semantic similarity instead of fixed size
chunker = SemanticChunker(
    embedding_client=embedding_client,
    similarity_threshold=0.8,  # Merge similar paragraphs
    max_chunk_size=1024
)

chunks = chunker.chunk(parsed_data.text)
```

### Metadata Enrichment

Add custom metadata to chunks:

```python
# Extract entities and add to metadata
from src.domain.tender.services.entities import EntityExtractor

extractor = EntityExtractor()

for chunk in chunks:
    entities = extractor.extract(chunk.text)
    chunk.metadata.update({
        "entities": entities,
        "has_deadlines": bool(entities.get("deadlines")),
        "has_requirements": bool(entities.get("requirements"))
    })
```

### Parallel Processing

For bulk uploads:

```python
from concurrent.futures import ThreadPoolExecutor

files = list(Path("data/input/").glob("*.pdf"))

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(index_tender, str(f), f"TENDER-{f.stem}")
        for f in files
    ]
    
    for future in futures:
        result = future.result()
        print(f"Indexed: {result.tender_id}")
```

---

## Monitoring & Troubleshooting

### Check Indexing Status

```python
# Get document status
document = doc_service.get(document_id="doc_123")

print(f"Status: {document.status}")
print(f"Chunks: {document.chunk_count}")
print(f"Indexed at: {document.indexed_at}")
```

### Re-index Failed Documents

```python
# Find failed uploads
failed = doc_service.get_failed_documents()

for doc in failed:
    print(f"Retrying: {doc.id} (error: {doc.error})")
    doc_service.reindex(doc.id)
```

### Validate Embeddings

```python
# Check embedding quality
from src.domain.tender.services.validation import validate_embeddings

validation = validate_embeddings(
    collection_name="tender_documents",
    sample_size=100
)

print(f"Valid embeddings: {validation.valid_count}/{validation.total}")
print(f"Average similarity: {validation.avg_similarity:.3f}")
```

---

## Related Documentation

- [Search & Retrieval](search-retrieval.md) - Query indexed documents
- [rag_toolkit Integration](../rag_toolkit/index.rst) - Generic RAG components
- [Environment Setup](environment-setup.md) - Configure Milvus and storage
