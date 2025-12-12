"""FastAPI application exposing the ingestion pipeline."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile

from src.core.ingestion.core.file_utils import temporary_directory
from src.schemas.ingestion import ParsedDocument
from src.core.ingestion.ingestion_service import IngestionService
from src.core.chunking import DynamicChunker, TokenChunker
from src.core.index.tender_indexer import TenderMilvusIndexer
from src.core.embedding import OllamaEmbeddingClient


ingestion = APIRouter()
service = IngestionService.singleton()
dynamic_chunker = DynamicChunker()
token_chunker = TokenChunker()
embedding_client: OllamaEmbeddingClient | None = None
_indexer: TenderMilvusIndexer | None = None


@ingestion.post("/parse", response_model=ParsedDocument)
async def parse_document(file: UploadFile = File(...)) -> ParsedDocument:
    """INTERNAL - Parse an uploaded PDF or DOCX and return a structured payload."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

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
    return {"dynamic_chunks": dyn_public, "token_chunks": token_public}


@ingestion.post("/parse-chunk-index")
async def parse_chunk_index(file: UploadFile = File(...), top_k: int = 5) -> dict:
    """Parse, chunk, embed, and insert into Milvus. Returns chunk ids and search sanity check."""
    parsed = await parse_document(file)
    pages = [page.model_dump() for page in parsed.pages]
    dyn_chunks = dynamic_chunker.build_chunks(pages)
    token_chunks = token_chunker.chunk(dyn_chunks)

    # Initialize indexer once
    global _indexer
    global embedding_client
    if _indexer is None:
        if embedding_client is None:
            try:
                embedding_client = OllamaEmbeddingClient()
            except Exception as exc:  # pragma: no cover - passthrough
                raise HTTPException(status_code=500, detail=f"Failed to init embedding client: {exc}") from exc
        try:
            from src.core.index.vector.config import MilvusConfig
            from src.core.index.vector.service import MilvusService

            cfg = MilvusConfig(
                uri=os.getenv("MILVUS_URI", "http://localhost:19530"),
                alias=os.getenv("MILVUS_ALIAS", "default"),
                user=os.getenv("MILVUS_USER"),
                password=os.getenv("MILVUS_PASSWORD"),
                db_name=os.getenv("MILVUS_DB_NAME", "default"),
                secure=os.getenv("MILVUS_SECURE", "false").lower() == "true",
            )
            service = MilvusService(cfg)
            embedding_dim = len(embedding_client.embed("dimension_probe"))
            _indexer = TenderMilvusIndexer(
                service=service,
                embedding_dim=embedding_dim,
                embed_fn=embedding_client.embed_batch,
            )
        except Exception as exc:  # pragma: no cover - passthrough
            raise HTTPException(status_code=500, detail=f"Failed to initialize indexer: {exc}") from exc

    # Upsert chunks
    try:
        _indexer.upsert_token_chunks(token_chunks)
    except Exception as exc:  # pragma: no cover - passthrough
        raise HTTPException(status_code=500, detail=f"Failed to upsert chunks: {exc}") from exc

    # Simple search sanity check on first chunk text
    query_chunk = token_chunks[0]
    query_emb = embedding_client.embed(query_chunk.text)
    try:
        results = _indexer.search(query_embedding=query_emb, top_k=top_k)
    except Exception as exc:  # pragma: no cover - passthrough
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc

    return {
        "inserted": len(token_chunks),
        "sample_query_chunk_id": query_chunk.id,
        "search_results": results,
    }


__all__ = ["ingestion"]
