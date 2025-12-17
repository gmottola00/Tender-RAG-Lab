"""Tender-specific search orchestrator using generic search strategies.

This module provides backward compatibility while using the new
generic search implementations underneath.
"""

from __future__ import annotations

from typing import Dict, List

from src.core.embedding import EmbeddingClient
from src.core.index.search_strategies import HybridSearch, KeywordSearch, VectorSearch
from src.domain.tender.indexing.indexer import TenderMilvusIndexer


class TenderSearcher:
    """High-level search orchestrator for tender chunks.
    
    This class maintains backward compatibility while using generic
    search strategies underneath.
    """

    def __init__(
        self,
        indexer: TenderMilvusIndexer,
        embed_client: EmbeddingClient,
    ) -> None:
        """Initialize searcher with indexer and embedding client.
        
        Args:
            indexer: Tender indexer (wraps generic IndexService).
            embed_client: Embedding client for query encoding.
        """
        self.indexer = indexer
        self.embed_client = embed_client
        
        # Create generic search strategies
        self.vector_searcher = VectorSearch(
            index_service=indexer.index_service,
            embed_fn=lambda query: embed_client.embed(query),
        )
        self.keyword_searcher = KeywordSearch(
            index_service=indexer.index_service,
        )
        self.hybrid_searcher = HybridSearch(
            vector_search=self.vector_searcher,
            keyword_search=self.keyword_searcher,
        )

    def vector_search(self, query: str, *, top_k: int = 5) -> List[Dict[str, object]]:
        """Execute semantic vector search."""
        return self.vector_searcher.search(query, top_k=top_k)

    def keyword_search(self, query: str, *, top_k: int = 5) -> List[Dict[str, object]]:
        """Execute keyword search."""
        return self.keyword_searcher.search(query, top_k=top_k)

    def hybrid_search(self, query: str, *, top_k: int = 5) -> List[Dict[str, object]]:
        """Execute hybrid search combining vector and keyword."""
        return self.hybrid_searcher.search(query, top_k=top_k)


__all__ = ["TenderSearcher"]
