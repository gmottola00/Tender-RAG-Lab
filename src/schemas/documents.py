from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class DocumentBase(BaseModel):
    tender_id: UUID
    lot_id: Optional[UUID] = None
    filename: str
    document_type: Optional[str] = None
    file_hash: Optional[str] = None
    uploaded_by: Optional[str] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    lot_id: Optional[UUID] = None
    document_type: Optional[str] = None
    file_hash: Optional[str] = None
    uploaded_by: Optional[str] = None


class DocumentOut(DocumentBase):
    id: UUID
    uploaded_at: datetime

    class Config:
        orm_mode = True
