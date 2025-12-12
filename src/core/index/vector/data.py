"""Data operations (insert/search/query) for Milvus collections."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from .connection import MilvusConnectionManager
from .exceptions import DataOperationError

try:
    from pymilvus import Collection
except ImportError:  # pragma: no cover - optional dependency not installed
    Collection = None  # type: ignore


class MilvusDataManager:
    """Perform data-level operations on Milvus collections."""

    def __init__(self, connection: MilvusConnectionManager) -> None:
        if Collection is None:
            raise ImportError("pymilvus is required for Milvus operations")
        self.connection = connection

    def _collection(self, name: str) -> Collection:
        self.connection.ensure()
        try:
            return Collection(name=name, using=self.connection.get_alias())
        except Exception as exc:  # pragma: no cover - passthrough
            raise DataOperationError(f"Failed to open collection '{name}'") from exc

    def insert(
        self,
        collection_name: str,
        data: Sequence[Sequence[Any]] | Dict[str, Sequence[Any]],
        *,
        partition_name: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Insert entities into a collection."""
        col = self._collection(collection_name)
        try:
            return col.insert(data=data, partition_name=partition_name, timeout=timeout)
        except Exception as exc:  # pragma: no cover - passthrough
            raise DataOperationError(f"Insert failed for collection '{collection_name}'") from exc

    def upsert(
        self,
        collection_name: str,
        data: Sequence[Sequence[Any]] | Dict[str, Sequence[Any]],
        *,
        partition_name: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Upsert entities if supported; fallback to insert."""
        col = self._collection(collection_name)
        try:
            if hasattr(col, "upsert"):
                return col.upsert(data=data, partition_name=partition_name, timeout=timeout)  # type: ignore[attr-defined]
            return col.insert(data=data, partition_name=partition_name, timeout=timeout)
        except Exception as exc:  # pragma: no cover - passthrough
            raise DataOperationError(f"Upsert failed for collection '{collection_name}'") from exc

    def delete(
        self,
        collection_name: str,
        expr: str,
        *,
        partition_name: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Delete entities matching an expression."""
        col = self._collection(collection_name)
        try:
            return col.delete(expr=expr, partition_name=partition_name, timeout=timeout)
        except Exception as exc:  # pragma: no cover - passthrough
            raise DataOperationError(f"Delete failed for collection '{collection_name}'") from exc

    def search(
        self,
        collection_name: str,
        data: Sequence[Sequence[float]],
        anns_field: str,
        param: Dict[str, Any],
        limit: int,
        *,
        output_fields: Optional[List[str]] = None,
        expr: Optional[str] = None,
        partition_names: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        consistency_level: Optional[str] = None,
    ) -> Any:
        """Perform a vector search."""
        col = self._collection(collection_name)
        try:
            col.load()
            return col.search(
                data=data,
                anns_field=anns_field,
                param=param,
                limit=limit,
                expr=expr,
                output_fields=output_fields,
                partition_names=partition_names,
                timeout=timeout,
                consistency_level=consistency_level,
            )
        except Exception as exc:  # pragma: no cover - passthrough
            raise DataOperationError(f"Search failed for collection '{collection_name}'") from exc

    def query(
        self,
        collection_name: str,
        expr: str,
        *,
        output_fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        timeout: Optional[float] = None,
        consistency_level: Optional[str] = None,
    ) -> Any:
        """Run a scalar query on a collection."""
        col = self._collection(collection_name)
        try:
            col.load()
            return col.query(
                expr=expr,
                output_fields=output_fields,
                limit=limit,
                offset=offset,
                timeout=timeout,
                consistency_level=consistency_level,
            )
        except Exception as exc:  # pragma: no cover - passthrough
            raise DataOperationError(f"Query failed for collection '{collection_name}'") from exc

    def flush(self, collection_name: str) -> None:
        """Flush pending data to storage."""
        col = self._collection(collection_name)
        try:
            col.flush()
        except Exception as exc:  # pragma: no cover - passthrough
            raise DataOperationError(f"Flush failed for collection '{collection_name}'") from exc

