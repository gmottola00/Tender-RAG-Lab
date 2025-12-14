from __future__ import annotations

import uuid
from datetime import datetime, date
from enum import Enum as PyEnum

from sqlalchemy import Column, Date, DateTime, String, Enum
from sqlalchemy.dialects.postgresql import UUID

from db.base import Base


class TenderStatus(str, PyEnum):
    draft = "draft"
    published = "published"
    open = "open"
    closed = "closed"
    awarded = "awarded"
    cancelled = "cancelled"


class Tender(Base):
    __tablename__ = "tenders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    code = Column(String, nullable=False, unique=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(
        Enum(TenderStatus, name="tender_status", create_type=False, native_enum=True),
        nullable=True,
        default=TenderStatus.draft,
    )
    buyer = Column(String, nullable=True)
    publish_date = Column(Date, nullable=True)
    closing_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
