from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.tender.entities.tenders import Tender
from src.domain.tender.schemas.tenders import TenderCreate, TenderUpdate


class TenderService:
    """Business logic for tenders."""

    @staticmethod
    async def create(db: AsyncSession, data: TenderCreate) -> Tender:
        obj = Tender(**data.dict())
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    @staticmethod
    async def get(db: AsyncSession, tender_id: UUID) -> Optional[Tender]:
        result = await db.execute(select(Tender).where(Tender.id == tender_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list(db: AsyncSession, limit: int = 100, offset: int = 0) -> List[Tender]:
        result = await db.execute(select(Tender).offset(offset).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def update(db: AsyncSession, tender_id: UUID, data: TenderUpdate) -> Optional[Tender]:
        obj = await TenderService.get(db, tender_id)
        if obj is None:
            return None
        for field, value in data.dict(exclude_unset=True).items():
            setattr(obj, field, value)
        await db.commit()
        await db.refresh(obj)
        return obj

    @staticmethod
    async def delete(db: AsyncSession, tender_id: UUID) -> bool:
        obj = await TenderService.get(db, tender_id)
        if obj is None:
            return False
        await db.delete(obj)
        await db.commit()
        return True
