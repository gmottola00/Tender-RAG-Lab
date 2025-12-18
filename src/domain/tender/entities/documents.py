from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from src.infra.database import Base


class DocumentType(str, PyEnum):
    bando = "bando"
    capitolato = "capitolato"
    disciplinare = "disciplinare"
    rettifica = "rettifica"
    avviso = "avviso"
    chiarimenti = "chiarimenti"
    qa = "qa"
    altro = "altro"

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False, index=True)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id", ondelete="SET NULL"), nullable=True, index=True)
    filename = Column(String, nullable=False)
    document_type = Column(
        Enum(
            DocumentType,
            name="document_type_enum",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=True,
    )
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    storage_bucket = Column(String, nullable=True)
    storage_path = Column(String, nullable=True)
