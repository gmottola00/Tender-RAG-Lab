"""FastAPI application exposing the ingestion pipeline."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile

from configs.logger import app_logger
from src.core.utils.file_utils import temporary_directory
from src.domain.tender.schemas.ingestion import ParsedDocument
from src.infra.parsers.factory import create_ingestion_service
from src.core.chunking import DynamicChunker, TokenChunker
from src.api.deps import get_embedding_client, get_indexer, get_searcher, get_rag_pipeline


ingestion = APIRouter()
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


__all__ = ["ingestion"]
