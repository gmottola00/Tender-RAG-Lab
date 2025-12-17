"""Backward compatibility module - imports redirected to domain.

DEPRECATED: This module is deprecated. Please import from:
- src.domain.tender.entities.documents
- src.domain.tender.entities.tenders
- src.domain.tender.entities.lots
"""

import warnings

# Redirect imports to new locations
from src.domain.tender.entities.documents import Document, DocumentType
from src.domain.tender.entities.tenders import Tender, TenderStatus
from src.domain.tender.entities.lots import Lot

warnings.warn(
    "Importing from src.models is deprecated. "
    "Use src.domain.tender.entities instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["Document", "DocumentType", "Tender", "TenderStatus", "Lot"]
