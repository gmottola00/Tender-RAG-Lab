from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db_dep
from src.schemas.tenders import TenderCreate, TenderOut, TenderUpdate
from src.services.tenders import TenderService


router = APIRouter(prefix="/tenders", tags=["tenders"])


@router.post("", response_model=TenderOut, status_code=status.HTTP_201_CREATED)
async def create_tender(payload: TenderCreate, db: AsyncSession = Depends(get_db_dep)) -> TenderOut:
    obj = await TenderService.create(db, payload)
    return obj


@router.get("/{tender_id}", response_model=TenderOut)
async def get_tender(tender_id: UUID, db: AsyncSession = Depends(get_db_dep)) -> TenderOut:
    obj = await TenderService.get(db, tender_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Tender not found")
    return obj


@router.get("", response_model=List[TenderOut])
async def list_tenders(limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db_dep)) -> List[TenderOut]:
    return await TenderService.list(db, limit=limit, offset=offset)


@router.put("/{tender_id}", response_model=TenderOut)
async def update_tender(tender_id: UUID, payload: TenderUpdate, db: AsyncSession = Depends(get_db_dep)) -> TenderOut:
    obj = await TenderService.update(db, tender_id, payload)
    if obj is None:
        raise HTTPException(status_code=404, detail="Tender not found")
    return obj


@router.delete("/{tender_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tender(tender_id: UUID, db: AsyncSession = Depends(get_db_dep)) -> None:
    ok = await TenderService.delete(db, tender_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Tender not found")
    return None


__all__ = ["router"]
