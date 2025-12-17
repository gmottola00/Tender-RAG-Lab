"""Backward compatibility module - imports redirected to domain.

DEPRECATED: This module is deprecated. Please import from:
- src.domain.tender.services.documents
- src.domain.tender.services.tenders
- src.domain.tender.services.lots

Note: This uses lazy imports to avoid circular dependencies.
"""

import warnings


def __getattr__(name):
    """Lazy import to avoid circular dependencies."""
    if name == "DocumentService":
        from src.domain.tender.services.documents import DocumentService
        warnings.warn(
            "Importing DocumentService from src.services is deprecated. "
            "Use src.domain.tender.services.documents instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return DocumentService
    elif name == "TenderService":
        from src.domain.tender.services.tenders import TenderService
        warnings.warn(
            "Importing TenderService from src.services is deprecated. "
            "Use src.domain.tender.services.tenders instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return TenderService
    elif name == "LotService":
        from src.domain.tender.services.lots import LotService
        warnings.warn(
            "Importing LotService from src.services is deprecated. "
            "Use src.domain.tender.services.lots instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return LotService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["DocumentService", "TenderService", "LotService"]

