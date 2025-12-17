from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class LotBase(BaseModel):
    tender_id: UUID
    code: str
    title: str
    description: Optional[str] = None
    value_estimated: Optional[float] = None
    currency: Optional[str] = None
    status: Optional[str] = None


class LotCreate(LotBase):
    pass


class LotUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    value_estimated: Optional[float] = None
    currency: Optional[str] = None
    status: Optional[str] = None


class LotOut(LotBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
