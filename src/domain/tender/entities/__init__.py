"""Tender domain entities (ORM models)."""

from src.domain.tender.entities.documents import Document
from src.domain.tender.entities.lots import Lot
from src.domain.tender.entities.tenders import Tender

__all__ = ["Document", "Tender", "Lot"]
