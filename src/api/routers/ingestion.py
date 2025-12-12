"""FastAPI application exposing the ingestion pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile

from src.core.ingestion.core.file_utils import temporary_directory
from src.schemas.ingestion import ParsedDocument
from src.core.ingestion.ingestion_service import IngestionService
from src.core.chunking import DynamicChunker, TokenChunker


ingestion = APIRouter()
service = IngestionService.singleton()
dynamic_chunker = DynamicChunker()
token_chunker = TokenChunker()


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


__all__ = ["ingestion"]
