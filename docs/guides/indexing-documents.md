# Indexing Documents

!!! abstract "Complete Document Lifecycle"
    Learn how to **upload**, **process**, and **index** tender documents for semantic search.
    
    From raw PDFs to searchable vector embeddings in minutes.

---

## :material-chart-timeline: Overview

!!! info "Three-Stage Pipeline"
    The document indexing pipeline consists of three main stages:

```mermaid
graph LR
    A[📤 Upload] -->|Store| B[⚙️ Processing]
    B -->|Parse & OCR| C[📇 Indexing]
    C -->|Embed & Store| D[(🔍 Milvus)]
    
    style A fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style B fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style C fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style D fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
```

### Pipeline Stages

| Stage | Purpose | Tools |
|-------|---------|-------|
| 1️⃣ **Upload** | Store raw files | Supabase/S3/Local |
| 2️⃣ **Processing** | Extract & parse text | Docling, OCR |
| 3️⃣ **Indexing** | Generate embeddings | Ollama, Milvus |

---

## :material-rocket-launch: Quick Start

### Upload a Single Document

```python title="Simple document upload"
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

print(f"✅ Document uploaded: {document.id}")
print(f"📊 Status: {document.status}")
```

---

### Batch Upload

!!! tip "Process Multiple Documents"
    Upload all PDFs from a directory:

```python title="Batch processing"
import os
from pathlib import Path

# Upload all PDFs from directory
tender_dir = Path("data/input/tenders/2025/")

for pdf_file in tender_dir.glob("*.pdf"):
    document = service.upload(
        file_path=str(pdf_file),
        tender_id=f"TENDER-{pdf_file.stem}",
    )
    print(f"✅ {pdf_file.name} → {document.id}")
```

---

## :material-cog: Document Processing Pipeline

### :material-upload: Step 1: File Upload

!!! info "Storage Options"
    Documents are stored in the configured storage backend:

=== "Local Filesystem"

    ```python title="Local storage"
    from src.infra.storage import get_storage_client
    
    storage = get_storage_client()
    
    # Store file locally
    file_path = storage.upload(
        file_content=pdf_bytes,
        filename="tender_2025_001.pdf",
        folder="tenders/2025"
    )
    ```

=== "Supabase Storage"

    ```python title="Cloud storage with Supabase"
    from src.clients.supabase import get_supabase_client
    
    supabase = get_supabase_client()
    
    # Upload to Supabase bucket
    response = supabase.storage.from_("documents").upload(
        path="tenders/2025/tender_001.pdf",
        file=pdf_bytes,
        file_options={"content-type": "application/pdf"}
    )
    ```

=== "S3-Compatible"

    ```python title="AWS S3 or MinIO"
    import boto3
    
    s3 = boto3.client('s3')
    
    s3.upload_fileobj(
        file_obj,
        bucket_name='tender-documents',
        key='2025/tender_001.pdf'
    )
    ```

---

## :material-file-document-edit: Step 2: Document Parsing

!!! abstract "Text Extraction"
    Automatically detect format and extract structured content with metadata.

### Supported Formats

<div class="grid cards" markdown>

-   📄 **PDF**

    ---
    
    - Native text extraction
    - **OCR for scanned docs**
    - Layout preservation

-   📝 **DOCX**

    ---
    
    - Microsoft Word
    - Rich formatting
    - Tables & images

-   📃 **TXT**

    ---
    
    - Plain text
    - Fast processing
    - UTF-8 encoding

</div>

### Usage

```python title="Automatic format detection"
from src.domain.tender.services.documents import DocumentParser

parser = DocumentParser()

# Automatic format detection
parsed_data = parser.parse(file_path="tender.pdf")

print(f"Title: {parsed_data.title}")
print(f"Pages: {parsed_data.page_count}")
print(f"Extracted text length: {len(parsed_data.text)}")
```

!!! success "OCR Support"
    - **Automatic triggering** for scanned PDFs
    - **Tesseract OCR** for Italian/English
    - **Layout preservation** with page numbers

---

## :material-scissors-cutting: Step 3: Text Chunking

!!! abstract "Smart Document Splitting"
    Split text into overlapping chunks for optimal retrieval performance.

### Strategy

```python title="Token-based chunking"
from rag_toolkit.chunking import RecursiveTokenChunker

chunker = RecursiveTokenChunker(
    chunk_size=512,        # tokens per chunk
    chunk_overlap=50,      # overlap for context
    model="gpt-3.5-turbo"  # tokenizer model
)

chunks = chunker.chunk(parsed_data.text)
print(f"Created {len(chunks)} chunks")
```

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `chunk_size` | `512` | Target tokens per chunk |
| `chunk_overlap` | `50` | Overlapping tokens for context |
| `model` | `gpt-3.5-turbo` | Tokenizer model |

!!! tip "Chunking Features"
    - ✅ **Sentence boundary respect** (no mid-sentence cuts)
    - ✅ **Metadata preservation** (page numbers, headers)
    - ✅ **Configurable overlap** (maintain context)

---

## :material-vector-polygon: Step 4: Embedding Generation

!!! abstract "Convert Text to Vectors"
    Transform chunks into high-dimensional embeddings for semantic search.

### Generate Embeddings

```python title="Batch embedding generation"
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

### Supported Models

=== "🤖 Ollama (Local)"

    | Model | Dimensions | Size | Speed |
    |-------|-----------|------|-------|
    | `nomic-embed-text` | 768 | 274MB | ⚡⚡⚡ |
    | `mxbai-embed-large` | 1024 | 670MB | ⚡⚡ |
    
    **Best for**: Local development, privacy, cost-free

=== "☁️ OpenAI (Cloud)"

    | Model | Dimensions | Cost | Quality |
    |-------|-----------|------|---------|
    | `text-embedding-3-small` | 1536 | $ | ⭐⭐⭐ |
    | `text-embedding-3-large` | 3072 | $$$ | ⭐⭐⭐⭐⭐ |
    
    **Best for**: Production, highest quality, managed infrastructure

---

## :material-database-arrow-up: Step 5: Vector Store Indexing

!!! abstract "Store in Milvus"
    Index embeddings with metadata in Milvus vector database.

### Index Documents

```python title="Milvus indexing"
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
        "upload_date": "2025-12-26",
        "buyer_name": "Ministero dell'Interno",
        "cpv_code": "72000000"
    }
)

print(f"Indexed {len(chunks)} chunks in Milvus")
```

!!! success "What Gets Stored"
    - ✅ **Embeddings** (vector data)
    - ✅ **Original text** (for retrieval)
    - ✅ **Metadata** (tender_id, page numbers, etc.)
    - ✅ **Relationships** (chunk → document → tender)

---

## :material-code-block-tags: Complete Example

!!! example "End-to-End Indexing Pipeline"

```python title="Full indexing workflow"
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
    print(f"   → {parsed.page_count} pages, {len(parsed.text):,} chars")
    
    print(f"3. Chunking text...")
    chunks = doc_service.chunk(parsed)
    print(f"   → Created {len(chunks)} chunks")
    
    print(f"4. Generating embeddings...")
    doc_service.embed(chunks)
    print(f"   → {len(chunks)} embeddings ({stack.embedding_dim}d)")
    
    print(f"5. Indexing in Milvus...")
    result = doc_service.index(chunks, tender_id=tender_id)
    
    print(f"✅ Successfully indexed {result.chunk_count} chunks")
    print(f"   Collection: {result.collection_name}")
    print(f"   Document ID: {result.document_id}")
    
    return result

# Usage
result = index_tender(
    file_path="data/input/tender_2025_001.pdf",
    tender_id="TENDER-2025-001"
)
```

---

## :material-cog-refresh: Advanced Configuration

### Custom Chunking Strategy

!!! tip "Semantic Chunking"
    For documents with complex structure (tables, diagrams):

```python title="Semantic-based chunking"
from rag_toolkit.chunking import SemanticChunker

# Split by semantic similarity instead of fixed size
chunker = SemanticChunker(
    embedding_client=embedding_client,
    similarity_threshold=0.8,  # Merge similar paragraphs
    max_chunk_size=1024
)

chunks = chunker.chunk(parsed_data.text)
```

**When to use:**

- 📊 Documents with tables/charts
- 📋 Structured sections (requirements lists)
- 📖 Multi-topic documents

---

### Metadata Enrichment

!!! tip "Extract Entities"
    Add structured metadata to chunks:

```python title="Entity extraction"
from src.domain.tender.services.entities import EntityExtractor

extractor = EntityExtractor()

for chunk in chunks:
    entities = extractor.extract(chunk.text)
    chunk.metadata.update({
        "entities": entities,
        "has_deadlines": bool(entities.get("deadlines")),
        "has_requirements": bool(entities.get("requirements")),
        "cpv_codes": entities.get("cpv_codes", [])
    })
```

**Extracted entities:**

- 📅 Deadlines (submission, award dates)
- ✅ Requirements (technical, economic)
- 🔢 CPV codes
- 💰 Budget amounts
- 🏢 Organizations (buyers, suppliers)

---

### Parallel Processing

!!! tip "Bulk Upload"
    Process multiple files simultaneously:

```python title="Parallel batch indexing"
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

files = list(Path("data/input/").glob("*.pdf"))

def index_file(file_path: Path):
    tender_id = f"TENDER-{file_path.stem}"
    return index_tender(str(file_path), tender_id)

# Process 4 files in parallel
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(index_file, f) for f in files]
    
    for future in futures:
        result = future.result()
        print(f"✅ {result.document_id}: {result.chunk_count} chunks")
```

!!! warning "Resource Limits"
    - Limit workers based on CPU/memory
    - Ollama: 2-4 workers (GPU limited)
    - OpenAI: 8-16 workers (API rate limits)

---

## :material-alert-circle: Troubleshooting

??? failure "OCR Errors"

    **Problem**: Text extraction fails on scanned PDFs
    
    **Solutions**:
    
    1. **Install Tesseract**:
       ```bash
       # macOS
       brew install tesseract tesseract-lang
       
       # Ubuntu
       sudo apt-get install tesseract-ocr tesseract-ocr-ita
       ```
    
    2. **Check language support**:
       ```bash
       tesseract --list-langs
       ```
    
    3. **Force OCR**:
       ```python
       parsed = parser.parse(file_path="scan.pdf", force_ocr=True)
       ```

??? failure "Chunking Issues"

    **Problem**: Chunks too large/small or cut mid-sentence
    
    **Solutions**:
    
    1. **Adjust chunk size**:
       ```python
       chunker = RecursiveTokenChunker(
           chunk_size=256,  # Smaller chunks
           chunk_overlap=50
       )
       ```
    
    2. **Use semantic chunking**:
       ```python
       chunker = SemanticChunker(
           max_chunk_size=1024,
           similarity_threshold=0.75
       )
       ```
    
    3. **Check token counts**:
       ```python
       from rag_toolkit.chunking import count_tokens
       
       for chunk in chunks:
           tokens = count_tokens(chunk.text)
           print(f"Chunk {chunk.id}: {tokens} tokens")
       ```

??? failure "Milvus Connection Error"

    **Problem**: Cannot connect to Milvus
    
    **Solutions**:
    
    1. **Check Milvus is running**:
       ```bash
       docker ps | grep milvus
       ```
    
    2. **Verify connection**:
       ```python
       from pymilvus import connections
       
       connections.connect(
           alias="default",
           host="localhost",
           port="19530"
       )
       ```
    
    3. **Check environment**:
       ```bash
       echo $MILVUS_URI
       ```

??? warning "Out of Memory"

    **Problem**: Process crashes during embedding generation
    
    **Solutions**:
    
    1. **Reduce batch size**:
       ```python
       embedding_client.embed_batch(
           texts=chunk_texts,
           batch_size=32  # Smaller batches
       )
       ```
    
    2. **Process sequentially**:
       ```python
       vectors = [embedding_client.embed(c.text) for c in chunks]
       ```
    
    3. **Use smaller model**:
       ```bash
       # .env
       OLLAMA_EMBED_MODEL=all-minilm  # 45MB vs 274MB
       ```

---

## :material-arrow-right-circle: Next Steps

<div class="grid cards" markdown>

-   :material-robot-outline:{ .lg } **[RAG Pipeline](rag-pipeline.md)**

    ---
    
    **Complete end-to-end RAG** with retrieval, graph enrichment, and generation

-   :material-magnify:{ .lg } **[Search & Retrieval](search-retrieval.md)**

    ---
    
    Query indexed documents with vector, keyword, and hybrid search

-   :material-graph:{ .lg } **[Knowledge Graph](knowledge-graph.md)**

    ---
    
    Enhance retrieval with Neo4j graph relationships

-   :material-api:{ .lg } **API Reference**

    ---
    
    ```bash
    # View API docs
    uvicorn main:app --reload
    # Open http://localhost:8000/docs
    ```

</div>

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
