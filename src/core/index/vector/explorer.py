from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.core.index.vector.connection import MilvusConnectionManager
from src.core.index.vector.data import MilvusDataManager
from src.core.index.vector.exceptions import CollectionError

try:
    from pymilvus import Collection, utility
except ImportError as exc:  # pragma: no cover
    Collection = None  # type: ignore
    utility = None  # type: ignore
    _pymilvus_import_error = exc


class MilvusExplorer:
    """Utility class for inspecting Milvus collections and previewing data."""

    def __init__(self, connection: MilvusConnectionManager) -> None:
        if Collection is None or utility is None:
            raise ImportError("pymilvus is required for Milvus operations") from _pymilvus_import_error
        self.connection = connection
        self.data = MilvusDataManager(connection)

    def list_collections(self) -> List[Dict[str, Any]]:
        """List collections with basic metadata."""
        self.connection.ensure()
        colls = utility.list_collections(using=self.connection.get_alias())
        results: List[Dict[str, Any]] = []
        for name in colls:
            try:
                col = Collection(name=name, using=self.connection.get_alias())
                results.append(
                    {
                        "name": name,
                        "description": col.description,
                        "loaded": col.is_loaded,
                        "row_count": col.num_entities,
                    }
                )
            except Exception:
                results.append({"name": name, "description": None, "loaded": False, "row_count": None})
        return results

    def collection_schema(self, name: str) -> Dict[str, Any]:
        """Return schema details for a collection."""
        self.connection.ensure()
        try:
            col = Collection(name=name, using=self.connection.get_alias())
            fields = []
            for f in col.schema.fields:
                fields.append(
                    {
                        "name": f.name,
                        "dtype": str(f.dtype),
                        "is_primary": f.is_primary,
                        "description": f.description,
                    }
                )
            return {
                "name": name,
                "description": col.description,
                "auto_id": col.schema.auto_id,
                "fields": fields,
            }
        except Exception as exc:  # pragma: no cover
            raise CollectionError(f"Failed to read schema for collection '{name}'") from exc

    def _build_default_expr(self, col: Collection) -> str:
        """Choose a permissive expr based on primary key type."""
        pk = col.schema.primary_field
        if pk is None:
            return "1 == 1"
        # crude type check
        dtype_str = str(pk.dtype).lower()
        if "varchar" in dtype_str or "string" in dtype_str:
            return f"{pk.name} != ''"
        return f"{pk.name} >= 0"

    def preview(self, name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Return the first N entities from a collection (excluding vector fields)."""
        self.connection.ensure()
        col = Collection(name=name, using=self.connection.get_alias())
        expr = self._build_default_expr(col)
        # choose non-vector fields for readability
        output_fields: List[str] = []
        for f in col.schema.fields:
            dtype_str = str(f.dtype).lower()
            if "float_vector" in dtype_str or "binary_vector" in dtype_str:
                continue
            output_fields.append(f.name)
        try:
            results = self.data.query(collection_name=name, expr=expr, limit=limit, output_fields=output_fields)
            return results or []
        except Exception:
            # fallback: try without expr
            try:
                results = self.data.query(collection_name=name, expr="1 == 1", limit=limit, output_fields=output_fields)
                return results or []
            except Exception as exc:  # pragma: no cover
                raise CollectionError(f"Failed to preview collection '{name}': {exc}") from exc

    def get_collection_data(
        self,
        name: str,
        *,
        output_fields: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch up to `limit` rows from a collection (all fields unless specified).

        This is a simple helper for UI/debug; it loads the collection and runs a query
        with a permissive expression.
        """
        self.connection.ensure()
        col = Collection(name=name, using=self.connection.get_alias())
        expr = self._build_default_expr(col)
        try:
            results = self.data.query(collection_name=name, expr=expr, limit=limit, output_fields=output_fields)
            return results or []
        except Exception:
            try:
                results = self.data.query(collection_name=name, expr="1 == 1", limit=limit, output_fields=output_fields)
                return results or []
            except Exception as exc:  # pragma: no cover
                raise CollectionError(f"Failed to read collection '{name}': {exc}") from exc


__all__ = ["MilvusExplorer"]
