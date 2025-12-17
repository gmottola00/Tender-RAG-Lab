"""Backward compatibility module - imports redirected to domain.

DEPRECATED: This module is deprecated. Please import from:
- src.domain.tender.schemas.documents
- src.domain.tender.schemas.tenders
- src.domain.tender.schemas.lots
- src.domain.tender.schemas.ingestion
- src.core.chunking.types (for Chunk, TokenChunk)
"""

import warnings

# Redirect common imports to new locations
from src.domain.tender.schemas.documents import (
    DocumentBase,
    DocumentCreate,
    DocumentUpdate,
    DocumentOut,
)
from src.domain.tender.schemas.tenders import (
    TenderBase,
    TenderCreate,
    TenderUpdate,
    TenderOut,
)
from src.domain.tender.schemas.lots import (
    LotBase,
    LotCreate,
    LotUpdate,
    LotOut,
)
from src.domain.tender.schemas.ingestion import Block, Page, ParsedDocument
from src.core.chunking.types import Chunk, TokenChunk

warnings.warn(
    "Importing from src.schemas is deprecated. "
    "Use src.domain.tender.schemas or src.core.chunking.types instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    "DocumentBase",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentOut",
    "TenderBase",
    "TenderCreate",
    "TenderUpdate",
    "TenderOut",
    "LotBase",
    "LotCreate",
    "LotUpdate",
    "LotOut",
    "Block",
    "Page",
    "ParsedDocument",
    "Chunk",
    "TokenChunk",
]

