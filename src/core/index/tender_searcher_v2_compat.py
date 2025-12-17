"""Backward compatibility wrapper for TenderSearcher.

DEPRECATED: Import from src.domain.tender.search.searcher instead.
"""

import warnings

from src.domain.tender.search.searcher import TenderSearcher

warnings.warn(
    "Importing from src.core.index.tender_searcher_v2 is deprecated. "
    "Use src.domain.tender.search.searcher instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["TenderSearcher"]
