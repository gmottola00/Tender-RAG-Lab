from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db_session
from src.domain.tender.schemas.documents import DocumentCreate, DocumentOut, DocumentUpdate
from src.domain.tender.entities.documents import DocumentType
from src.domain.tender.services.documents import DocumentService
from src.infra.storage import get_storage_client
from src.api.routers.ingestion import parse_document, dynamic_chunker, token_chunker, get_embedding_client, get_indexer


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def create_document(
    tender_id: str = Form(...),
    lot_id: str | None = Form(None),
    document_type: DocumentType | None = Form(None),
    uploaded_by: str | None = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentOut:
    # Build DTO manually (filename from upload)
    payload = DocumentCreate(
        tender_id=tender_id,
        lot_id=lot_id,
        filename=file.filename,
        document_type=document_type,
        uploaded_by=uploaded_by,
    )
    file_bytes = await file.read()
    obj = await DocumentService.create_with_upload(db, payload, file_bytes, content_type=file.content_type)
    return obj


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(document_id: UUID, db: AsyncSession = Depends(get_db_session)) -> DocumentOut:
    obj = await DocumentService.get(db, document_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return obj


@router.get("", response_model=List[DocumentOut])
async def list_documents(
    tender_id: UUID | None = None,
    lot_id: UUID | None = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session),
) -> List[DocumentOut]:
    return await DocumentService.list(db, tender_id=tender_id, lot_id=lot_id, limit=limit, offset=offset)


@router.post("/{document_id}/ingest")
async def ingest_document(document_id: UUID, db: AsyncSession = Depends(get_db_session), top_k: int = 3) -> dict:
    """Download a stored document, parse, chunk and index into Milvus."""
    doc = await DocumentService.get(db, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.storage_bucket or not doc.storage_path:
        raise HTTPException(status_code=400, detail="Document has no storage info")

    storage = get_storage_client()
    if storage.bucket_name != doc.storage_bucket:
        raise HTTPException(status_code=400, detail="Document bucket does not match configured bucket")

    try:
        file_bytes = storage.download_bytes(doc.storage_path)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Failed to download document: {exc}") from exc

    # Reuse parsing pipeline with a temporary UploadFile
    from tempfile import SpooledTemporaryFile
    from starlette.datastructures import UploadFile as StarletteUploadFile

    tmp = SpooledTemporaryFile()
    tmp.write(file_bytes)
    tmp.seek(0)
    upload = StarletteUploadFile(file=tmp, filename=doc.filename)

    parsed = await parse_document(upload)
    pages = [page.model_dump() for page in parsed.pages]
    dyn_chunks = dynamic_chunker.build_chunks(pages)
    token_chunks = token_chunker.chunk(dyn_chunks)

    embedding_client = get_embedding_client()
    indexer = get_indexer()

    try:
        indexer.upsert_token_chunks(token_chunks)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Failed to upsert chunks: {exc}") from exc

    query_chunk = token_chunks[0]
    query_emb = embedding_client.embed(query_chunk.text)
    try:
        results = indexer.search(query_embedding=query_emb, top_k=top_k)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc

    return {
        "inserted": len(token_chunks),
        "document_id": str(document_id),
        "sample_query_chunk_id": query_chunk.id,
        "search_results": results,
    }


@router.put("/{document_id}", response_model=DocumentOut)
async def update_document(document_id: UUID, payload: DocumentUpdate, db: AsyncSession = Depends(get_db_session)) -> DocumentOut:
    obj = await DocumentService.update(db, document_id, payload)
    if obj is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return obj


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: UUID, db: AsyncSession = Depends(get_db_session)) -> None:
    ok = await DocumentService.delete(db, document_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Document not found")
    return None


__all__ = ["router"]
