from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from src.domain.tender.entities.documents import DocumentType


class DocumentBase(BaseModel):
    tender_id: UUID
    lot_id: Optional[UUID] = None
    filename: str
    storage_bucket: str = None
    storage_path: str = None
    document_type: Optional[DocumentType] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    lot_id: Optional[UUID] = None
    document_type: Optional[str] = None

class DocumentOut(DocumentBase):
    id: UUID
    uploaded_at: datetime

    class Config:
        orm_mode = True
