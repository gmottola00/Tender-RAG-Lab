from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.tender.entities.lots import Lot
from src.domain.tender.schemas.lots import LotCreate, LotUpdate


class LotService:
    """Business logic for lots."""

    @staticmethod
    async def create(db: AsyncSession, data: LotCreate) -> Lot:
        obj = Lot(**data.dict())
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    @staticmethod
    async def get(db: AsyncSession, lot_id: UUID) -> Optional[Lot]:
        result = await db.execute(select(Lot).where(Lot.id == lot_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list(db: AsyncSession, tender_id: Optional[UUID] = None, limit: int = 100, offset: int = 0) -> List[Lot]:
        stmt = select(Lot)
        if tender_id:
            stmt = stmt.where(Lot.tender_id == tender_id)
        result = await db.execute(stmt.offset(offset).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def update(db: AsyncSession, lot_id: UUID, data: LotUpdate) -> Optional[Lot]:
        obj = await LotService.get(db, lot_id)
        if obj is None:
            return None
        for field, value in data.dict(exclude_unset=True).items():
            setattr(obj, field, value)
        await db.commit()
        await db.refresh(obj)
        return obj

    @staticmethod
    async def delete(db: AsyncSession, lot_id: UUID) -> bool:
        obj = await LotService.get(db, lot_id)
        if obj is None:
            return False
        await db.delete(obj)
        await db.commit()
        return True
