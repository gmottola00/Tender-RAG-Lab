"""Backward compatibility wrapper for TenderMilvusIndexer.

DEPRECATED: Import from src.domain.tender.indexing.indexer instead.
"""

import warnings

from src.domain.tender.indexing.indexer import TenderMilvusIndexer

warnings.warn(
    "Importing from src.core.index.tender_indexer_v2 is deprecated. "
    "Use src.domain.tender.indexing.indexer instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["TenderMilvusIndexer"]
