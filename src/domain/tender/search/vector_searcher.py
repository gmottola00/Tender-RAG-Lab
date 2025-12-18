"""Vector search helper built on top of TenderMilvusIndexer."""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from src.core.embedding import EmbeddingClient
from src.domain.tender.indexing import TenderMilvusIndexer


class VectorSearcher:
    """Encapsulates vector search using an embedding client and Milvus indexer."""

    def __init__(self, indexer: TenderMilvusIndexer, embed_client: EmbeddingClient) -> None:
        self.indexer = indexer
        self.embed_client = embed_client

    def search(self, query: str, *, top_k: int = 5, search_params: Optional[Dict[str, object]] = None) -> List[Dict[str, object]]:
        """Run a semantic search returning scored hits."""
        query_vec = self.embed_client.embed(query)
        return self.indexer.search(query_embedding=query_vec, top_k=top_k, search_params=search_params)


__all__ = ["VectorSearcher"]
