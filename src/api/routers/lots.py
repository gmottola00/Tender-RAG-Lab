from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db_dep
from src.schemas.lots import LotCreate, LotOut, LotUpdate
from src.services.lots import LotService


router = APIRouter(prefix="/lots", tags=["lots"])


@router.post("", response_model=LotOut, status_code=status.HTTP_201_CREATED)
async def create_lot(payload: LotCreate, db: AsyncSession = Depends(get_db_dep)) -> LotOut:
    obj = await LotService.create(db, payload)
    return obj


@router.get("/{lot_id}", response_model=LotOut)
async def get_lot(lot_id: UUID, db: AsyncSession = Depends(get_db_dep)) -> LotOut:
    obj = await LotService.get(db, lot_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Lot not found")
    return obj


@router.get("", response_model=List[LotOut])
async def list_lots(
    tender_id: UUID | None = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_dep),
) -> List[LotOut]:
    return await LotService.list(db, tender_id=tender_id, limit=limit, offset=offset)


@router.put("/{lot_id}", response_model=LotOut)
async def update_lot(lot_id: UUID, payload: LotUpdate, db: AsyncSession = Depends(get_db_dep)) -> LotOut:
    obj = await LotService.update(db, lot_id, payload)
    if obj is None:
        raise HTTPException(status_code=404, detail="Lot not found")
    return obj


@router.delete("/{lot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lot(lot_id: UUID, db: AsyncSession = Depends(get_db_dep)) -> None:
    ok = await LotService.delete(db, lot_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Lot not found")
    return None


__all__ = ["router"]
