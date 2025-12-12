"""Basic keyword search over Milvus collection using LIKE expressions."""

from __future__ import annotations

from typing import Dict, List, Optional

from src.core.index.vector.connection import MilvusConnectionManager
from src.core.index.tender_indexer import TenderMilvusIndexer
from src.core.index.vector.exceptions import DataOperationError

try:
    from pymilvus import Collection
except ImportError:  # pragma: no cover - optional dependency
    Collection = None  # type: ignore


class KeywordSearcher:
    """Performs simple LIKE-based keyword search on the `text` field."""

    def __init__(self, indexer: TenderMilvusIndexer) -> None:
        if Collection is None:
            raise ImportError("pymilvus is required for keyword search")
        self.indexer = indexer
        self.connection: MilvusConnectionManager = indexer.connection

    def search(self, query: str, *, top_k: int = 5) -> List[Dict[str, object]]:
        """Search by keyword using Milvus SQL-like expressions."""
        self.connection.ensure()
        try:
            col = Collection(name=self.indexer.collection_name, using=self.connection.get_alias())
            col.load()
            expr = _build_like_expression(query)
            results = col.query(expr=expr, output_fields=["text", "section_path", "metadata", "page_numbers", "source_chunk_id"], limit=top_k)
            return [
                {
                    "score": None,
                    "text": r.get("text"),
                    "section_path": r.get("section_path"),
                    "metadata": r.get("metadata"),
                    "page_numbers": r.get("page_numbers"),
                    "source_chunk_id": r.get("source_chunk_id"),
                    "id": r.get("id"),
                }
                for r in results
            ]
        except Exception as exc:  # pragma: no cover - passthrough
            raise DataOperationError(f"Keyword search failed: {exc}") from exc


def _build_like_expression(query: str) -> str:
    terms = [t.strip() for t in query.split() if t.strip()]
    if not terms:
        return ""
    clauses = [f'text like "%{term}%\"' for term in terms]
    return " and ".join(clauses)


__all__ = ["KeywordSearcher"]
