from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.tender.entities.tenders import Tender
from src.domain.tender.schemas.tenders import TenderCreate, TenderUpdate


class TenderService:
    """Business logic for tenders."""

    @staticmethod
    async def generate_next_code(db: AsyncSession, fiscal_year: Optional[str] = None) -> str:
        """Generate next incremental tender code (e.g., FY26-0004).

        Args:
            db: Database session
            fiscal_year: Fiscal year prefix (default: current year as FY{YY})

        Returns:
            Next tender code in format FY{YY}-{NNNN}

        Example:
            If last code is FY26-0003, returns FY26-0004
            If no codes exist, returns FY26-0001
        """
        if fiscal_year is None:
            current_year = datetime.now().year
            fiscal_year = f"FY{str(current_year)[2:]}"  # FY26 for 2026

        # Query ultimo tender code per l'anno fiscale
        result = await db.execute(
            select(Tender.code)
            .where(Tender.code.like(f"{fiscal_year}-%"))
            .order_by(Tender.code.desc())
            .limit(1)
        )
        last_code = result.scalar_one_or_none()

        if last_code:
            # Estrai numero: FY26-0003 → 3
            try:
                num = int(last_code.split("-")[1])
                next_num = num + 1
            except (IndexError, ValueError):
                # Fallback se il formato non è valido
                next_num = 1
        else:
            next_num = 1

        return f"{fiscal_year}-{next_num:04d}"  # FY26-0004

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
