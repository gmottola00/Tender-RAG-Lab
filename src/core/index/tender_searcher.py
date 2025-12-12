"""Tender-specific search orchestrator (vector, keyword, hybrid)."""

from __future__ import annotations

from typing import Dict, List

from src.core.embedding import EmbeddingClient
from src.core.index.search.hybrid_searcher import HybridSearcher
from src.core.index.search.keyword_searcher import KeywordSearcher
from src.core.index.search.vector_searcher import VectorSearcher
from src.core.index.tender_indexer import TenderMilvusIndexer


class TenderSearcher:
    """High-level search orchestrator for tender chunks."""

    def __init__(
        self,
        indexer: TenderMilvusIndexer,
        embed_client: EmbeddingClient,
    ) -> None:
        self.indexer = indexer
        self.embed_client = embed_client
        self.vector_searcher = VectorSearcher(indexer, embed_client)
        self.keyword_searcher = KeywordSearcher(indexer)
        self.hybrid_searcher = HybridSearcher(self.vector_searcher, self.keyword_searcher)

    def vector_search(self, query: str, *, top_k: int = 5) -> List[Dict[str, object]]:
        return self.vector_searcher.search(query, top_k=top_k)

    def keyword_search(self, query: str, *, top_k: int = 5) -> List[Dict[str, object]]:
        return self.keyword_searcher.search(query, top_k=top_k)

    def hybrid_search(self, query: str, *, top_k: int = 5) -> List[Dict[str, object]]:
        return self.hybrid_searcher.search(query, top_k=top_k)


__all__ = ["TenderSearcher"]
