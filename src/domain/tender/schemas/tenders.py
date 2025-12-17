from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from src.domain.tender.entities.tenders import TenderStatus


class TenderBase(BaseModel):
    code: str
    title: str
    description: Optional[str] = None
    status: Optional[TenderStatus] = None
    buyer: Optional[str] = None
    publish_date: Optional[date] = None
    closing_date: Optional[date] = None


class TenderCreate(TenderBase):
    pass


class TenderUpdate(BaseModel):
    code: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TenderStatus] = None
    buyer: Optional[str] = None
    publish_date: Optional[date] = None
    closing_date: Optional[date] = None


class TenderOut(TenderBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
