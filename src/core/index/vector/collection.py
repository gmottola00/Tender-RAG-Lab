"""Collection management utilities for Milvus."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .connection import MilvusConnectionManager
from .exceptions import CollectionError

try:
    from pymilvus import Collection, CollectionSchema, FieldSchema, utility
except ImportError:  # pragma: no cover - optional dependency not installed
    Collection = None  # type: ignore
    CollectionSchema = None  # type: ignore
    FieldSchema = None  # type: ignore
    utility = None  # type: ignore


class MilvusCollectionManager:
    """Create, drop, and manage Milvus collections."""

    def __init__(self, connection: MilvusConnectionManager) -> None:
        if Collection is None:
            raise ImportError("pymilvus is required for Milvus operations")
        self.connection = connection

    def ensure_collection(
        self,
        name: str,
        schema: CollectionSchema,
        *,
        consistency_level: str = "Bounded",
        shards_num: int = 2,
    ) -> Collection:
        """Create the collection if missing and return a loaded Collection object."""
        self.connection.ensure()
        try:
            if not utility.has_collection(name):
                Collection(
                    name=name,
                    schema=schema,
                    using=self.connection.get_alias(),
                    consistency_level=consistency_level,
                    shards_num=shards_num,
                )
            col = Collection(name=name, using=self.connection.get_alias(), schema=schema)
            col.load()
            return col
        except Exception as exc:  # pragma: no cover - passthrough
            raise CollectionError(f"Failed to ensure collection '{name}'") from exc

    def drop_collection(self, name: str) -> None:
        """Drop a collection if it exists."""
        self.connection.ensure()
        try:
            if utility.has_collection(name):
                utility.drop_collection(name)
        except Exception as exc:  # pragma: no cover - passthrough
            raise CollectionError(f"Failed to drop collection '{name}'") from exc

    def load(self, name: str) -> None:
        """Load a collection into memory."""
        self.connection.ensure()
        try:
            col = Collection(name=name, using=self.connection.get_alias())
            col.load()
        except Exception as exc:  # pragma: no cover - passthrough
            raise CollectionError(f"Failed to load collection '{name}'") from exc

    def release(self, name: str) -> None:
        """Release a collection from memory."""
        self.connection.ensure()
        try:
            col = Collection(name=name, using=self.connection.get_alias())
            col.release()
        except Exception as exc:  # pragma: no cover - passthrough
            raise CollectionError(f"Failed to release collection '{name}'") from exc

    def create_index(self, name: str, field_name: str, index_params: Dict[str, Any]) -> None:
        """Create an index on a field."""
        self.connection.ensure()
        try:
            col = Collection(name=name, using=self.connection.get_alias())
            col.create_index(field_name=field_name, index_params=index_params)
        except Exception as exc:  # pragma: no cover - passthrough
            raise CollectionError(f"Failed to create index on '{field_name}' for '{name}'") from exc


__all__ = ["MilvusCollectionManager"]
