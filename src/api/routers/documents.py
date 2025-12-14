from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db_dep
from src.schemas.documents import DocumentCreate, DocumentOut, DocumentUpdate
from src.services.documents import DocumentService


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def create_document(payload: DocumentCreate, db: AsyncSession = Depends(get_db_dep)) -> DocumentOut:
    obj = await DocumentService.create(db, payload)
    return obj


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(document_id: UUID, db: AsyncSession = Depends(get_db_dep)) -> DocumentOut:
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
    db: AsyncSession = Depends(get_db_dep),
) -> List[DocumentOut]:
    return await DocumentService.list(db, tender_id=tender_id, lot_id=lot_id, limit=limit, offset=offset)


@router.put("/{document_id}", response_model=DocumentOut)
async def update_document(document_id: UUID, payload: DocumentUpdate, db: AsyncSession = Depends(get_db_dep)) -> DocumentOut:
    obj = await DocumentService.update(db, document_id, payload)
    if obj is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return obj


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: UUID, db: AsyncSession = Depends(get_db_dep)) -> None:
    ok = await DocumentService.delete(db, document_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Document not found")
    return None


__all__ = ["router"]
