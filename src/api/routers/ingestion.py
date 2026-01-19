"""FastAPI application exposing the ingestion pipeline."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from configs.logger import app_logger
from src.domain.tender.schemas.ingestion import ParsedDocument
from src.domain.tender.schemas.tenders import TenderCreate
from src.domain.tender.services.tenders import TenderService
from src.domain.tender.entities.documents import Document, DocumentType
from rag_toolkit.infra.parsers.factory import create_ingestion_service
from rag_toolkit.core.chunking import DynamicChunker, TokenChunker
from rag_toolkit.core.utils.file_utils import temporary_directory
from src.api.deps import get_embedding_client, get_indexer, get_searcher, get_rag_pipeline, get_db_session
from src.domain.tender.services.entity_extraction import create_entity_extraction_service
from src.domain.tender.services.graph_retriever import create_graph_enriched_retriever
from src.infra.graph import get_tender_graph_client
from src.domain.tender.preprocessing.text_cleaner import clean_tender_text


ingestion = APIRouter()
entity_service = create_entity_extraction_service()  # Singleton for entity extraction
log = app_logger.get_logger(__name__, extra_prefix="ingestion")
service = create_ingestion_service()  # Use factory instead of singleton
dynamic_chunker = DynamicChunker()
token_chunker = TokenChunker()


@ingestion.post("/parse", response_model=ParsedDocument)
async def parse_document(file: UploadFile = File(...)) -> ParsedDocument:
    """INTERNAL - Parse an uploaded PDF or DOCX and return a structured payload."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    log.info("parse_document received file", extra={"uploaded_filename": file.filename})

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    with temporary_directory() as tmp_dir:
        tmp_path = tmp_dir / file.filename
        tmp_path.write_bytes(file_bytes)

        try:
            parsed = service.parse_document(tmp_path)
            log.info("parse_document success", extra={"uploaded_filename": file.filename})
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover - passthrough
            raise HTTPException(status_code=500, detail="Failed to parse document") from exc

    return ParsedDocument(**parsed)


@ingestion.post("/parse-and-chunk")
async def parse_and_chunk(file: UploadFile = File(...)) -> dict:
    """Parse a document and return parsed pages plus dynamic and token chunks."""
    parsed = await parse_document(file)
    pages = [page.model_dump() for page in parsed.pages]
    dyn_chunks = dynamic_chunker.build_chunks(pages)
    dyn_public = [chunk.to_dict(include_blocks=False) for chunk in dyn_chunks]
    token_chunks = token_chunker.chunk(dyn_chunks)
    token_public = [
        {
            "id": tc.id,
            "text": tc.text,
            "section_path": tc.section_path,
            "metadata": tc.metadata,
            "page_numbers": tc.page_numbers,
            "source_chunk_id": tc.source_chunk_id,
        }
        for tc in token_chunks
    ]
    log.info(
        "parse_and_chunk completed",
        extra={"uploaded_filename": file.filename, "dynamic_chunks": len(dyn_chunks), "token_chunks": len(token_chunks)},
    )
    return {"dynamic_chunks": dyn_public, "token_chunks": token_public}


@ingestion.post("/parse-chunk-index")
async def parse_chunk_index(file: UploadFile = File(...), top_k: int = 5) -> dict:
    """Parse, chunk, embed, and insert into Milvus. Returns chunk ids and search sanity check."""
    log.info("parse_chunk_index received file", extra={"uploaded_filename": file.filename})
    parsed = await parse_document(file)
    pages = [page.model_dump() for page in parsed.pages]
    dyn_chunks = dynamic_chunker.build_chunks(pages)
    token_chunks = token_chunker.chunk(dyn_chunks)
    log.info(
        "chunking completed",
        extra={"uploaded_filename": file.filename, "dynamic_chunks": len(dyn_chunks), "token_chunks": len(token_chunks)},
    )

    # Obtain singletons via providers
    embedding_client = get_embedding_client()
    indexer = get_indexer()
    log.info("embedding client initialized", extra={"model": embedding_client.model_name})
    log.info("milvus indexer ready", extra={"collection": indexer.collection_name})

    # Upsert chunks
    try:
        indexer.upsert_token_chunks(token_chunks)
        log.info("chunks upserted", extra={"count": len(token_chunks)})
    except Exception as exc:  # pragma: no cover - passthrough
        raise HTTPException(status_code=500, detail=f"Failed to upsert chunks: {exc}") from exc

    # Simple search sanity check on first chunk text
    query_chunk = token_chunks[0]
    query_emb = embedding_client.embed(query_chunk.text)
    try:
        results = indexer.search(query_embedding=query_emb, top_k=top_k)
        log.info("search completed", extra={"top_k": top_k, "returned": len(results)})
    except Exception as exc:  # pragma: no cover - passthrough
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc

    return {
        "inserted": len(token_chunks),
        "sample_query_chunk_id": query_chunk.id,
        "search_results": results,
    }


@ingestion.post("/rag/vector-search")
async def rag_vector_search(question: str, top_k: int = 3) -> dict:
    """Answer a user question with vector search over tender chunks."""
    log.info("rag_vector_search received question", extra={"question": question, "top_k": top_k})
    searcher = get_searcher()
    try:
        results = searcher.vector_search(question, top_k=top_k)
    except Exception as exc:  # pragma: no cover - passthrough
        raise HTTPException(status_code=500, detail=f"Vector search failed: {exc}") from exc

    return {"question": question, "results": results}


@ingestion.post("/extract-entities")
async def extract_entities(file: UploadFile = File(...), tender_id: str = "unknown") -> dict:
    """Parse document, chunk, and extract named entities using spaCy NER.
    
    Returns entities grouped by type (ORGANIZATION, PERSON, LOCATION, etc.)
    """
    log.info("extract_entities received file", extra={"uploaded_filename": file.filename, "tender_id": tender_id})
    
    # Parse and chunk
    parsed = await parse_document(file)
    pages = [page.model_dump() for page in parsed.pages]
    dyn_chunks = dynamic_chunker.build_chunks(pages)
    
    # Convert to TenderChunk format (simplified)
    from src.domain.tender.schemas.chunking import TenderChunk
    tender_chunks = [
        TenderChunk(
            id=chunk.id,
            title=chunk.title,
            heading_level=chunk.heading_level,
            text=chunk.text,
            blocks=chunk.blocks,
            page_numbers=chunk.page_numbers,
            section_path=getattr(chunk, 'section_path', ''),  # Propagate for StructureExtractor
            metadata=getattr(chunk, 'metadata', {}),  # Propagate metadata
            tender_id=tender_id,
        )
        for chunk in dyn_chunks
    ]
    
    # Extract entities
    try:
        extraction_result = entity_service.extract_from_chunks(tender_chunks, tender_id)
        log.info(
            "entity extraction completed",
            extra={
                "uploaded_filename": file.filename,
                "tender_id": tender_id,
                "entity_count": extraction_result.get("entity_count", 0),
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Entity extraction failed: {exc}") from exc
    
    return extraction_result


@ingestion.post("/extract-entities-and-populate-graph")
async def extract_entities_and_populate_graph(
    file: UploadFile = File(...),
    tender_id: str = "unknown",
    tender_code: str = "TENDER-001",
    populate_graph: bool = True,
) -> dict:
    """Parse document, chunk, extract entities, AND populate Neo4j knowledge graph.

    Complete NER → Graph pipeline:
    1. Parse document (PDF/DOCX)
    2. Chunk text
    3. Extract entities (ORG, PERSON, LOCATION, DATE, MONEY)
    4. Extract requirements (pattern matching)
    5. Extract deadlines (DATE + context)
    6. Populate Neo4j graph

    Args:
        file: Document file to process
        tender_id: Internal tender ID
        tender_code: Tender code (CIG/CUP) for graph linking
        populate_graph: Whether to populate Neo4j (default: True)

    Returns:
        {
            "tender_id": "...",
            "tender_code": "...",
            "entities_extracted": 42,
            "graph_populated": true,
            "graph_stats": {
                "organizations_created": 5,
                "requirements_created": 8,
                "deadlines_created": 3,
                "relationships_created": 16
            }
        }
    """
    log.info(
        "extract_entities_and_populate_graph",
        extra={
            "uploaded_filename": file.filename,
            "tender_id": tender_id,
            "tender_code": tender_code,
            "populate_graph": populate_graph,
        }
    )

    # Parse and chunk
    parsed = await parse_document(file)
    pages = [page.model_dump() for page in parsed.pages]
    dyn_chunks = dynamic_chunker.build_chunks(pages)

    # Convert to TenderChunk format with text cleaning
    from src.domain.tender.schemas.chunking import TenderChunk
    tender_chunks = [
        TenderChunk(
            id=chunk.id,
            title=chunk.title,
            heading_level=chunk.heading_level,
            text=clean_tender_text(chunk.text),  # Clean text before processing
            blocks=chunk.blocks,
            page_numbers=chunk.page_numbers,
            section_path=getattr(chunk, 'section_path', ''),  # Propagate for StructureExtractor
            metadata=getattr(chunk, 'metadata', {}),  # Propagate metadata
            tender_id=tender_id,
        )
        for chunk in dyn_chunks
    ]

    # Create service with or without Neo4j client
    neo4j_client = get_tender_graph_client() if populate_graph else None
    service = create_entity_extraction_service(neo4j_client=neo4j_client)

    # Extract and populate
    try:
        result = await service.extract_and_populate(
            chunks=tender_chunks,
            tender_id=tender_id,
            tender_code=tender_code,
        )

        log.info(
            "extraction and graph population completed",
            extra={
                "uploaded_filename": file.filename,
                "tender_id": tender_id,
                "entity_count": result.get("entity_count", 0),
                "graph_stats": result.get("graph_stats", {}),
            }
        )
    except Exception as exc:
        log.error(f"Failed to extract and populate: {exc}")
        raise HTTPException(status_code=500, detail=f"Entity extraction and graph population failed: {exc}") from exc

    return {
        "tender_id": tender_id,
        "tender_code": tender_code,
        "entities_extracted": result.get("entity_count", 0),
        "graph_populated": populate_graph,
        "graph_stats": result.get("graph_stats", {}),
        "entities_by_type": result.get("entities_by_type", {}),
    }


@ingestion.post("/rag/search-with-graph")
async def search_with_graph_context(
    query: str,
    tender_code: str,
    top_k: int = 5,
    use_graph_enrichment: bool = True,
) -> dict:
    """Hybrid search: vector search + graph context enrichment.

    Pipeline:
    1. Vector search (Milvus) for semantic similarity
    2. For each chunk, retrieve connected entities from Neo4j
    3. Return enriched results with requirements, deadlines, organizations

    Args:
        query: User question
        tender_code: Tender code to filter search
        top_k: Number of results
        use_graph_enrichment: Whether to add graph context

    Returns:
        {
            "query": "...",
            "tender_code": "...",
            "results": [
                {
                    "chunk_id": "...",
                    "text": "...",
                    "score": 0.85,
                    "graph_context": {
                        "requirements": [...],
                        "deadlines": [...],
                        "organizations": [...]
                    }
                }
            ]
        }
    """
    log.info(
        "search_with_graph_context",
        extra={
            "query": query,
            "tender_code": tender_code,
            "top_k": top_k,
            "use_graph_enrichment": use_graph_enrichment,
        }
    )

    # Get searcher and create graph retriever
    searcher = get_searcher()
    retriever = create_graph_enriched_retriever(vector_searcher=searcher)

    try:
        results = await retriever.search_with_graph_context(
            query=query,
            tender_code=tender_code,
            top_k=top_k,
            use_graph_enrichment=use_graph_enrichment,
        )

        log.info(
            "search_with_graph_context completed",
            extra={
                "query": query,
                "results_count": len(results),
            }
        )
    except Exception as exc:
        log.error(f"Graph-enriched search failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Graph-enriched search failed: {exc}") from exc
    finally:
        await retriever.close()

    return {
        "query": query,
        "tender_code": tender_code,
        "top_k": top_k,
        "results": results,
    }


@ingestion.get("/graph/requirements/{tender_code}")
async def get_requirements_for_tender(
    tender_code: str,
    lot_id: str = None,
    mandatory_only: bool = True,
) -> dict:
    """Graph-first query: Get all requirements for a tender.

    Use case: UC1 from roadmap - "Lista tutti i requisiti obbligatori per lotto X"

    Args:
        tender_code: Tender code (CIG/CUP)
        lot_id: Optional lot ID to filter
        mandatory_only: If True, return only mandatory requirements

    Returns:
        {
            "tender_code": "...",
            "lot_id": "...",
            "mandatory_only": true,
            "requirements": [
                {
                    "requirement_id": "req-001",
                    "description": "Certificazione ISO 27001 obbligatoria",
                    "type": "extracted",
                    "mandatory": true,
                    "chunk_ids": ["chunk-abc"]
                }
            ]
        }
    """
    log.info(
        "get_requirements_for_tender",
        extra={
            "tender_code": tender_code,
            "lot_id": lot_id,
            "mandatory_only": mandatory_only,
        }
    )

    retriever = create_graph_enriched_retriever()

    try:
        requirements = await retriever.search_requirements(
            tender_code=tender_code,
            lot_id=lot_id,
            mandatory_only=mandatory_only,
        )

        log.info(
            "requirements retrieved",
            extra={"tender_code": tender_code, "count": len(requirements)}
        )
    except Exception as exc:
        log.error(f"Failed to get requirements: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to get requirements: {exc}") from exc
    finally:
        await retriever.close()

    return {
        "tender_code": tender_code,
        "lot_id": lot_id,
        "mandatory_only": mandatory_only,
        "count": len(requirements),
        "requirements": requirements,
    }


@ingestion.post("/debug/chunks")
async def debug_chunks(file: UploadFile = File(...)) -> dict:
    """Debug endpoint: parse and show chunk texts for inspection."""
    parsed = await parse_document(file)
    pages = [page.model_dump() for page in parsed.pages]
    dyn_chunks = dynamic_chunker.build_chunks(pages)

    return {
        "total_chunks": len(dyn_chunks),
        "chunks": [
            {
                "id": chunk.id,
                "title": chunk.title,
                "text_preview": chunk.text[:300] + "..." if len(chunk.text) > 300 else chunk.text,
                "text_length": len(chunk.text),
                "page_numbers": chunk.page_numbers,
            }
            for chunk in dyn_chunks[:10]  # First 10 chunks
        ]
    }


@ingestion.post("/debug/text-cleaning")
async def debug_text_cleaning(file: UploadFile = File(...)) -> dict:
    """Debug endpoint: compare raw vs cleaned chunk texts."""
    parsed = await parse_document(file)
    pages = [page.model_dump() for page in parsed.pages]
    dyn_chunks = dynamic_chunker.build_chunks(pages)

    comparisons = []
    for chunk in dyn_chunks[:5]:  # First 5 chunks
        raw_text = chunk.text
        cleaned_text = clean_tender_text(raw_text)

        comparisons.append({
            "chunk_id": chunk.id,
            "raw_length": len(raw_text),
            "cleaned_length": len(cleaned_text),
            "raw_preview": raw_text[:200],
            "cleaned_preview": cleaned_text[:200],
            "diff": {
                "removed_chars": len(raw_text) - len(cleaned_text),
                "has_page_numbers": "Page" in raw_text or "page" in raw_text,
                "has_excessive_newlines": "\n\n" in raw_text,
            }
        })

    return {
        "total_chunks": len(dyn_chunks),
        "samples": comparisons,
    }


@ingestion.post("/debug/pattern-matching")
async def debug_pattern_matching(file: UploadFile = File(...)) -> dict:
    """Debug endpoint: test pattern matching on chunks."""
    parsed = await parse_document(file)
    pages = [page.model_dump() for page in parsed.pages]
    dyn_chunks = dynamic_chunker.build_chunks(pages)

    # Requirement patterns (same as in entity_extraction.py)
    requirement_patterns = [
        "obbligatorio", "obbligatoria", "pena esclusione", "deve", "devono",
        "è richiesto", "è richiesta", "requisito", "requisiti", "necessario",
        "in possesso di", "possedere", "certificare", "documentare"
    ]

    # Deadline patterns
    deadline_patterns = [
        "scadenza", "entro", "termine", "data limite", "presentazione",
        "sopralluogo", "chiarimenti", "apertura buste"
    ]

    chunks_with_requirements = []
    chunks_with_deadlines = []

    for chunk in dyn_chunks:
        text_lower = chunk.text.lower()

        # Check requirements
        matched_req_patterns = [p for p in requirement_patterns if p in text_lower]
        if matched_req_patterns:
            chunks_with_requirements.append({
                "chunk_id": chunk.id,
                "matched_patterns": matched_req_patterns,
                "text_preview": chunk.text[:200],
            })

        # Check deadlines
        matched_deadline_patterns = [p for p in deadline_patterns if p in text_lower]
        if matched_deadline_patterns:
            chunks_with_deadlines.append({
                "chunk_id": chunk.id,
                "matched_patterns": matched_deadline_patterns,
                "text_preview": chunk.text[:200],
            })

    return {
        "total_chunks": len(dyn_chunks),
        "chunks_with_requirements": len(chunks_with_requirements),
        "chunks_with_deadlines": len(chunks_with_deadlines),
        "requirement_examples": chunks_with_requirements[:5],
        "deadline_examples": chunks_with_deadlines[:5],
    }


@ingestion.post("/debug/test-with-mock-tender")
async def test_with_mock_tender() -> dict:
    """Test extraction with realistic mock tender data containing requirements and deadlines."""
    from src.domain.tender.schemas.chunking import TenderChunk

    # Realistic mock chunks from a real tender document
    mock_chunks = [
        TenderChunk(
            id="chunk-req-001",
            title="Requisiti di partecipazione",
            heading_level=2,
            text="""
            Requisiti di partecipazione obbligatori:
            1. Possesso della certificazione ISO 9001:2015 in corso di validità
            2. Fatturato minimo annuo di € 500.000 negli ultimi tre esercizi finanziari
            3. Esecuzione di almeno 3 servizi analoghi negli ultimi 5 anni
            4. Iscrizione alla Camera di Commercio obbligatoria
            5. Possesso dei requisiti di cui all'art. 80 del D.Lgs 50/2016 pena esclusione
            """,
            section_path="3. Requisiti > 3.1. Requisiti di partecipazione",  # For StructureExtractor
            metadata={"tender_code": "TEST-MOCK-001", "page_number": 5},
            tender_id="test-mock",
        ),
        TenderChunk(
            id="chunk-req-002",
            title="Requisiti tecnici",
            heading_level=2,
            text="""
            Ulteriori requisiti tecnici:
            - Il concorrente deve dimostrare esperienza nel settore IT
            - È richiesta certificazione di sicurezza ISO 27001
            - Necessario possedere almeno 10 dipendenti qualificati
            La mancanza anche di uno solo dei requisiti obbligatori comporta l'esclusione dalla gara.
            """,
            section_path="3. Requisiti > 3.2. Requisiti tecnici",  # For StructureExtractor
            metadata={"tender_code": "TEST-MOCK-001", "page_number": 6},
            tender_id="test-mock",
        ),
        TenderChunk(
            id="chunk-deadline-001",
            title="Scadenze",
            heading_level=2,
            text="""
            Scadenze importanti:
            - Sopralluogo obbligatorio: 15 febbraio 2026 ore 10:00
            - Termine ultimo per richiesta di chiarimenti: entro il 20 febbraio 2026
            - Scadenza presentazione offerte: entro e non oltre il 28 febbraio 2026 ore 12:00
            - Apertura delle buste: 1 marzo 2026 ore 14:00 presso la sede della stazione appaltante
            CIG: 1234567890ABC
            CUP: B12C34567890123
            """,
            section_path="4. Modalità > 4.1. Scadenze e codici",  # For StructureExtractor
            metadata={"tender_code": "TEST-MOCK-001", "page_number": 12},
            tender_id="test-mock",
        ),
        TenderChunk(
            id="chunk-orgs-001",
            title="Stazione appaltante",
            heading_level=2,
            text="""
            Il Comune di Milano, in qualità di stazione appaltante, indice la presente gara.
            L'Autorità Nazionale Anticorruzione (ANAC) è l'ente di vigilanza.
            Per informazioni contattare il RUP Dott. Mario Rossi presso l'Ufficio Gare.
            CPV: 72000000
            Importo: € 500.000,00
            """,
            section_path="1. Committente > 1.1. Stazione appaltante",  # For StructureExtractor
            metadata={"tender_code": "TEST-MOCK-001", "page_number": 1},
            tender_id="test-mock",
        ),
        TenderChunk(
            id="chunk-lot-001",
            title="Lotto 1",
            heading_level=2,
            text="""
            5. Lotto > 5.1. Lotto: LOT-0001
            Descrizione: Servizi di sviluppo software per sistema di gestione documentale.
            Importo base d'asta: € 250.000,00
            Durata: 12 mesi
            CIG: 9876543210ZYX
            """,
            section_path="5. Lotto > 5.1. Lotto: LOT-0001",  # For StructureExtractor (LOT extraction!)
            metadata={"tender_code": "TEST-MOCK-001", "page_number": 8},
            tender_id="test-mock",
        ),
    ]

    # Run extraction
    neo4j_client = get_tender_graph_client()
    service = create_entity_extraction_service(neo4j_client=neo4j_client)

    try:
        # First ensure tender exists in graph
        await neo4j_client.create_tender(
            code="TEST-MOCK-001",
            title="Gara test per servizi IT - Mock Data",
            cpv_code="72000000",
            base_amount=500000.0,
            buyer_name="Comune di Milano",
            publication_date="2026-01-01",
        )

        # Extract and populate
        result = await service.extract_and_populate(
            chunks=mock_chunks,
            tender_id="test-mock",
            tender_code="TEST-MOCK-001",
        )

        return {
            "message": "Mock tender processed successfully",
            "tender_code": "TEST-MOCK-001",
            "entities_extracted": result.get("entity_count", 0),
            "graph_stats": result.get("graph_stats", {}),
            "entities_by_type": result.get("entities_by_type", {}),
            "next_steps": [
                "Check Neo4j browser: MATCH (t:Tender {code: 'TEST-MOCK-001'}) RETURN t",
                f"GET /graph/requirements/TEST-MOCK-001?mandatory_only=true",
                f"GET /graph/deadlines/TEST-MOCK-001",
            ]
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to process mock tender - check if tender already exists"
        }
    finally:
        await neo4j_client.close()


@ingestion.get("/graph/deadlines/{tender_code}")
async def get_deadlines_for_tender(tender_code: str) -> dict:
    """Graph-first query: Get all deadlines for a tender.

    Use case: UC4 from roadmap - "Elenca tutte le scadenze"

    Args:
        tender_code: Tender code (CIG/CUP)

    Returns:
        {
            "tender_code": "...",
            "deadlines": [
                {
                    "deadline_id": "deadline-001",
                    "type": "scadenza_offerta",
                    "date_text": "31 marzo 2025",
                    "chunk_ids": ["chunk-xyz"]
                }
            ]
        }
    """
    log.info("get_deadlines_for_tender", extra={"tender_code": tender_code})

    retriever = create_graph_enriched_retriever()

    try:
        deadlines = await retriever.search_deadlines(tender_code=tender_code)

        log.info(
            "deadlines retrieved",
            extra={"tender_code": tender_code, "count": len(deadlines)}
        )
    except Exception as exc:
        log.error(f"Failed to get deadlines: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to get deadlines: {exc}") from exc
    finally:
        await retriever.close()

    return {
        "tender_code": tender_code,
        "count": len(deadlines),
        "deadlines": deadlines,
    }


@ingestion.post("/rag/pipeline")
async def rag_pipeline(question: str, top_k: int = 5) -> dict:
    """Run the full RAG pipeline (rewrite -> vector -> rerank -> assemble -> generate)."""
    log.info("rag_pipeline received question", extra={"question": question, "top_k": top_k})
    pipeline = get_rag_pipeline()
    try:
        response = pipeline.run(question, top_k=top_k)
    except Exception as exc:  # pragma: no cover - passthrough
        raise HTTPException(status_code=500, detail=f"RAG pipeline failed: {exc}") from exc

    return {
        "question": question,
        "answer": response.answer,
        "citations": [
            {
                "id": c.id,
                "section_path": c.section_path,
                "page_numbers": c.page_numbers,
                "metadata": c.metadata,
                "source_chunk_id": c.source_chunk_id,
            }
            for c in response.citations
        ],
    }


@ingestion.post("/extract-all")
async def extract_all(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Complete one-shot pipeline for tender document processing.

    This endpoint performs the complete end-to-end extraction and indexing:

    1. **Generate Tender Code**: Auto-increment code (FY26-0001, FY26-0002, ...)
    2. **Parse Document**: Extract text from PDF/DOCX
    3. **Chunking**: Create dynamic and token chunks
    4. **Create Tender in PostgreSQL**: Store tender metadata in relational DB
    5. **Create Tender in Neo4j**: Create knowledge graph node
    6. **NER + Graph Population**: Extract entities (ORG, PERSON, LOCATION, DATE, MONEY)
       and populate requirements, deadlines, organizations in Neo4j
    7. **Embedding + Milvus Indexing**: Generate embeddings and index for vector search
    8. **Link Graph**: Create HAS_CHUNK relationships in Neo4j

    Args:
        file: PDF or DOCX document to process
        db: Database session (injected)

    Returns:
        Complete extraction summary:
        {
            "tender_id": "uuid...",
            "tender_code": "FY26-0004",
            "chunks_created": 25,
            "entities_extracted": 42,
            "graph_populated": true,
            "milvus_indexed": true,
            "graph_stats": {
                "organizations_created": 5,
                "requirements_created": 8,
                "deadlines_created": 3,
                "relationships_created": 16,
                "chunks_linked": 25
            },
            "entities_by_type": {
                "ORGANIZATION": [...],
                "PERSON": [...],
                "LOCATION": [...],
                "DATE": [...],
                "MONEY": [...]
            }
        }

    Example:
        ```bash
        curl -X POST "http://localhost:8000/ingestion/extract-all" \\
          -F "file=@tender_document.pdf"
        ```
    """
    log.info("=== extract_all endpoint called ===")
    log.info(f"File object received: {file}")
    log.info(f"File type: {type(file)}")
    log.info(f"File filename: {file.filename if file else 'NO FILE'}")
    log.info(f"File content_type: {file.content_type if file else 'NO FILE'}")
    
    if not file:
        log.error("No file received!")
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    if not file.filename:
        log.error("File has no filename!")
        raise HTTPException(status_code=400, detail="Filename is required")

    log.info("extract_all received file", extra={"uploaded_filename": file.filename})

    # Validate file type
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    try:
        # Step 1: Generate next tender code
        tender_code = await TenderService.generate_next_code(db)
        log.info(f"Generated tender code: {tender_code}")

        # Step 2: Parse document
        parsed = await parse_document(file)
        pages = [page.model_dump() for page in parsed.pages]

        # Step 3: Chunking
        dyn_chunks = dynamic_chunker.build_chunks(pages)
        token_chunks = token_chunker.chunk(dyn_chunks)
        log.info(f"Created {len(dyn_chunks)} dynamic chunks, {len(token_chunks)} token chunks")

        # Convert to TenderChunk format
        from src.domain.tender.schemas.chunking import TenderChunk
        tender_chunks = [
            TenderChunk(
                id=chunk.id,
                title=chunk.title,
                heading_level=chunk.heading_level,
                text=clean_tender_text(chunk.text),
                blocks=chunk.blocks,
                page_numbers=chunk.page_numbers,
                section_path=getattr(chunk, 'section_path', ''),  # Propagate for StructureExtractor
                metadata=getattr(chunk, 'metadata', {}),  # Propagate metadata
                tender_id=tender_code,  # Use tender_code as tender_id
            )
            for chunk in dyn_chunks
        ]

        # Step 4: Create tender in PostgreSQL
        tender_data = TenderCreate(
            code=tender_code,
            title=f"Tender {tender_code}",  # Default title, can be enhanced
            description=f"Auto-generated from {file.filename}",
            status="draft",
        )
        tender_obj = await TenderService.create(db, tender_data)
        log.info(f"Created tender in PostgreSQL: {tender_obj.id}")

        # Step 4b: Create document in PostgreSQL
        document = Document(
            tender_id=tender_obj.id,
            filename=file.filename,
            document_type=DocumentType.bando,  # Default, could be inferred
            storage_bucket="local",  # Default storage bucket
            storage_path=f"tenders/{tender_code}/{file.filename}",  # Logical path
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)
        log.info(f"Created document in PostgreSQL: {document.id}")

        # Step 5: Create tender in Neo4j
        graph_client = get_tender_graph_client()
        try:
            await graph_client.create_tender(
                code=tender_code,
                title=f"Tender {tender_code}",
                cpv_code=None,  # Could be extracted from document in future
                base_amount=None,
                buyer_name=None,  # Could be extracted from entities
                publication_date=None,
            )
            log.info(f"Created tender in Neo4j: {tender_code}")

            # Step 6: NER + Graph Population
            extraction_service = create_entity_extraction_service(neo4j_client=graph_client)
            extraction_result = await extraction_service.extract_and_populate(
                chunks=tender_chunks,
                tender_id=str(tender_obj.id),
                tender_code=tender_code,
            )
            log.info(f"Extracted {extraction_result.get('entity_count', 0)} entities")

            # Step 7: Link chunks to tender in Neo4j (HAS_CHUNK relationships)
            chunks_linked = 0
            for idx, chunk in enumerate(tender_chunks):
                try:
                    link_query = """
                    MATCH (t:Tender {code: $tender_code})
                    MERGE (c:Chunk {id: $chunk_id})
                    ON CREATE SET
                        c.text_preview = substring($text, 0, 200),
                        c.page_number = $page_number,
                        c.chunk_index = $chunk_index
                    MERGE (t)-[:HAS_CHUNK]->(c)
                    """
                    await graph_client.execute_write(
                        link_query,
                        {
                            "tender_code": tender_code,
                            "chunk_id": chunk.id,
                            "text": chunk.text,
                            "page_number": chunk.page_numbers[0] if chunk.page_numbers else 0,
                            "chunk_index": idx,  # Use enumeration index instead of parsing UUID
                        }
                    )
                    chunks_linked += 1
                except Exception as e:
                    log.warning(f"Failed to link chunk {chunk.id}: {e}")

            log.info(f"Linked {chunks_linked} chunks to tender in Neo4j")

        finally:
            await graph_client.close()

        # Step 8: Embedding + Milvus indexing
        indexer = get_indexer()

        # Add tender_code to metadata for filtering in Milvus
        for tc in token_chunks:
            tc.metadata["tender_code"] = tender_code
            tc.metadata["tender_id"] = str(tender_obj.id)
            tc.metadata["document_id"] = str(document.id)

        # Use upsert_token_chunks method which handles embedding internally
        indexer.upsert_token_chunks(token_chunks)
        log.info(f"Indexed {len(token_chunks)} chunks in Milvus with tender_code={tender_code}")

        # Build response
        graph_stats = extraction_result.get("graph_stats", {})
        graph_stats["chunks_linked"] = chunks_linked

        return {
            "tender_id": str(tender_obj.id),
            "tender_code": tender_code,
            "filename": file.filename,
            "chunks_created": len(token_chunks),
            "entities_extracted": extraction_result.get("entity_count", 0),
            "graph_populated": True,
            "milvus_indexed": True,
            "graph_stats": graph_stats,
            "entities_by_type": extraction_result.get("entities_by_type", {}),
            "next_steps": [
                f"View tender in Neo4j: MATCH (t:Tender {{code: '{tender_code}'}}) RETURN t",
                f"GET /graph/requirements/{tender_code}",
                f"GET /graph/deadlines/{tender_code}",
                f"POST /rag/search-with-graph with tender_code='{tender_code}'",
            ]
        }

    except Exception as exc:
        log.error(f"extract_all failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Complete extraction pipeline failed: {exc}"
        ) from exc


__all__ = ["ingestion"]
