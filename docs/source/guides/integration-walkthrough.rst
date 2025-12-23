==========================
Integration Walkthrough
==========================

Complete end-to-end guide showing how a tender document flows through
the system from upload to searchable chunks.

----

Overview
========

The integration connects multiple ``rag_toolkit`` components in a pipeline:

.. mermaid::

   graph TB
       A[PDF Upload] --> B[Supabase Storage]
       B --> C[Parser]
       C --> D[DynamicChunker]
       D --> E[TokenChunker]
       E --> F[Embedding]
       F --> G[Milvus Index]
       
       style A fill:#e3f2fd
       style G fill:#c8e6c9

Each step leverages ``rag_toolkit`` with tender-specific customization.

Step 1: Document Upload
=======================

FastAPI endpoint receives file:

.. code-block:: python

   @router.post("/documents/upload")
   async def upload_document(
       file: UploadFile,
       tender_id: UUID,
       db: AsyncSession
   ):
       # 1. Store in Supabase
       storage = get_storage_client()  # rag_toolkit.infra.storage
       storage_path = f"{tender_id}/{file.filename}"
       storage.upload_bytes(storage_path, await file.read())
       
       # 2. Create DB record
       doc = await DocumentService.create(db, {
           "tender_id": tender_id,
           "filename": file.filename,
           "storage_path": storage_path
       })
       
       return {"document_id": doc.id}

Step 2: Parsing
===============

Extract structured content from PDF:

.. code-block:: python

   from rag_toolkit.infra.parsers.factory import create_ingestion_service
   
   parser = create_ingestion_service()
   
   # Download from storage
   file_bytes = storage.download_bytes(storage_path)
   
   # Parse document
   parsed = parser.parse_document(file_bytes, filename)
   
   # Result structure:
   # {
   #   "pages": [
   #     {
   #       "page_number": 1,
   #       "blocks": [
   #         {"type": "heading", "level": 1, "text": "..."},
   #         {"type": "paragraph", "text": "..."}
   #       ]
   #     }
   #   ]
   # }

Step 3: Dynamic Chunking
========================

Create structural chunks respecting document hierarchy:

.. code-block:: python

   from rag_toolkit.core.chunking import DynamicChunker
   
   chunker = DynamicChunker(
       include_tables=True,
       max_heading_level=6
   )
   
   pages = [page.model_dump() for page in parsed.pages]
   structural_chunks = chunker.build_chunks(pages)
   
   # Each chunk represents a logical section:
   # TenderChunk(
   #   id="chunk_001",
   #   title="Article 4: Technical Requirements",
   #   heading_level=2,
   #   text="Full section text...",
   #   page_numbers=[5, 6]
   # )

Step 4: Token Chunking
======================

Split into embedding-friendly sizes:

.. code-block:: python

   from rag_toolkit.core.chunking import TokenChunker
   
   token_chunker = TokenChunker(
       max_tokens=800,
       min_tokens=400,
       overlap_tokens=120
   )
   
   token_chunks = token_chunker.chunk(structural_chunks)
   
   # TenderTokenChunk(
   #   id="token_chunk_001",
   #   text="Technical requirements include...",
   #   section_path="Capitolato > Art. 4 > Requisiti",
   #   source_chunk_id="chunk_001",
   #   tender_id="abc-123"
   # )

Step 5: Embedding & Indexing
=============================

Generate vectors and store in Milvus:

.. code-block:: python

   from src.api.deps import get_indexer
   
   indexer = get_indexer()  # TenderMilvusIndexer
   
   # Batch embed and index
   indexer.upsert_token_chunks(token_chunks)
   
   # Internally:
   # 1. Extract texts
   # 2. Generate embeddings (batch)
   # 3. Build Milvus rows with schema
   # 4. Upsert to collection

Step 6: Querying
================

Search indexed chunks:

.. code-block:: python

   from src.api.deps import get_rag_pipeline
   
   pipeline = get_rag_pipeline()
   
   response = pipeline.run(
       question="What are the technical requirements?",
       top_k=5
   )
   
   # RagResponse(
   #   answer="The technical requirements include...",
   #   citations=[
   #     Citation(
   #       section_path="Capitolato > Art. 4",
   #       page_numbers=[5, 6]
   #     )
   #   ]
   # )

Complete API Flow
=================

Full ingestion endpoint:

.. code-block:: python

   @router.post("/{document_id}/ingest")
   async def ingest_document(document_id: UUID):
       # Get document
       doc = await DocumentService.get(db, document_id)
       
       # Download
       file_bytes = storage.download_bytes(doc.storage_path)
       
       # Parse
       parsed = parser.parse_document(file_bytes)
       pages = [p.model_dump() for p in parsed.pages]
       
       # Chunk (2 stages)
       dyn_chunks = dynamic_chunker.build_chunks(pages)
       token_chunks = token_chunker.chunk(dyn_chunks)
       
       # Index
       indexer.upsert_token_chunks(token_chunks)
       
       return {"indexed": len(token_chunks)}

Key Integration Points
======================

Dependency Injection
--------------------

Singletons manage expensive clients:

.. code-block:: python

   # src/api/deps.py
   
   _embedding_client: OllamaEmbeddingClient | None = None
   
   def get_embedding_client() -> OllamaEmbeddingClient:
       global _embedding_client
       if _embedding_client is None:
           _embedding_client = OllamaEmbeddingClient()
       return _embedding_client

Factory Usage
-------------

Complete stack creation:

.. code-block:: python

   from src.infra.factory import create_tender_stack
   
   def get_indexer():
       embed_client = get_embedding_client()
       embedding_dim = len(embed_client.embed("probe"))
       indexer, _ = create_tender_stack(embed_client, embedding_dim)
       return indexer

Error Handling
==============

Robust error handling at each stage:

.. code-block:: python

   try:
       parsed = parser.parse_document(file_bytes)
   except Exception as e:
       raise HTTPException(500, f"Parse failed: {e}")
   
   try:
       indexer.upsert_token_chunks(token_chunks)
   except CollectionError as e:
       raise HTTPException(500, f"Index failed: {e}")

Testing
=======

Mock rag_toolkit components:

.. code-block:: python

   @pytest.fixture
   def mock_parser():
       parser = Mock(spec=IngestionService)
       parser.parse_document.return_value = MockParsedDoc()
       return parser
   
   def test_ingestion_flow(mock_parser):
       # Test with mocked parser
       ...

Next Steps
==========

- :doc:`../rag_toolkit/pipeline` - RAG pipeline details
- :doc:`../rag_toolkit/search` - Search strategies
- :doc:`../api/index` - API reference
