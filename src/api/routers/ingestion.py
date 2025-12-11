"""FastAPI application exposing the ingestion pipeline."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile

from src.core.ingestion.core.file_utils import temporary_directory
from src.schemas.ingestion import ParsedDocument
from core.ingestion.ingestion_service import IngestionService


ingestion = FastAPI(title="Tender Ingestion API")
service = IngestionService.singleton()


@ingestion.post("/parse", response_model=ParsedDocument)
async def parse_document(file: UploadFile = File(...)) -> ParsedDocument:
    """Parse an uploaded PDF or DOCX and return a structured payload."""
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


__all__ = ["app"]
