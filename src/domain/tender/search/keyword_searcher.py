"""Basic keyword search over Milvus collection using LIKE expressions."""

from __future__ import annotations

from typing import Dict, List

from rag_toolkit.infra.vectorstores.milvus.connection import MilvusConnectionManager
from src.domain.tender.indexing import TenderMilvusIndexer
from rag_toolkit.core.index.vector.exceptions import DataOperationError


class KeywordSearcher:
    """Performs simple LIKE-based keyword search on the `text` field."""

    def __init__(self, indexer: TenderMilvusIndexer) -> None:
        self.indexer = indexer
        self.connection: MilvusConnectionManager = indexer.connection

    def search(self, query: str, *, top_k: int = 5) -> List[Dict[str, object]]:
        """Search by keyword using Milvus SQL-like expressions."""
        self.connection.ensure()
        try:
            expr = _build_like_expression(query)
            results = self.indexer.service.data.query(
                collection_name=self.indexer.collection_name,
                expr=expr or "1 == 1",
                output_fields=["text", "section_path", "metadata", "page_numbers", "source_chunk_id", "id"],
                limit=top_k,
            )
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
    clauses = [f'text like "%{term}%"' for term in terms]
    return " and ".join(clauses)


__all__ = ["KeywordSearcher"]
