"""Vector stores infrastructure package.

This package contains concrete implementations of vector database protocols
and factory functions for creating configured instances.
"""

from src.infra.vectorstores.factory import (
    create_index_service,
    create_milvus_service,
)

__all__ = [
    "create_milvus_service",
    "create_index_service",
]
