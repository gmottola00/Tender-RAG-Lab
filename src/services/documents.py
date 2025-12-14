from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.documents import Document
from src.schemas.documents import DocumentCreate, DocumentUpdate


class DocumentService:
    """Business logic for documents."""

    @staticmethod
    async def create(db: AsyncSession, data: DocumentCreate) -> Document:
        obj = Document(**data.dict())
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    @staticmethod
    async def get(db: AsyncSession, document_id: UUID) -> Optional[Document]:
        result = await db.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list(
        db: AsyncSession,
        tender_id: Optional[UUID] = None,
        lot_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Document]:
        stmt = select(Document)
        if tender_id:
            stmt = stmt.where(Document.tender_id == tender_id)
        if lot_id:
            stmt = stmt.where(Document.lot_id == lot_id)
        result = await db.execute(stmt.offset(offset).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def update(db: AsyncSession, document_id: UUID, data: DocumentUpdate) -> Optional[Document]:
        obj = await DocumentService.get(db, document_id)
        if obj is None:
            return None
        for field, value in data.dict(exclude_unset=True).items():
            setattr(obj, field, value)
        await db.commit()
        await db.refresh(obj)
        return obj

    @staticmethod
    async def delete(db: AsyncSession, document_id: UUID) -> bool:
        obj = await DocumentService.get(db, document_id)
        if obj is None:
            return False
        await db.delete(obj)
        await db.commit()
        return True
