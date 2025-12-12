"""FastAPI application exposing the ingestion pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile

from src.core.ingestion.core.file_utils import temporary_directory
from src.schemas.ingestion import ParsedDocument
from src.core.ingestion.ingestion_service import IngestionService
from src.core.chunking import DynamicChunker, Chunk


ingestion = APIRouter()
service = IngestionService.singleton()
chunker = DynamicChunker()


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
    """Parse a document and return parsed pages plus dynamic chunks."""
    parsed = await parse_document(file)
    # Convert Pydantic models to dicts before chunking
    pages = [page.model_dump() for page in parsed.pages]
    chunks = chunker.build_chunks(pages)
    public_chunks = [chunk.to_dict(include_blocks=False) for chunk in chunks]
    return {"chunks": public_chunks}


__all__ = ["ingestion"]
