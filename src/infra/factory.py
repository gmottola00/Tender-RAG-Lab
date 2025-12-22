"""Factory functions for creating Tender-RAG-Lab infrastructure components.

This module provides factory functions for domain-specific infrastructure
that wraps and extends rag-toolkit components.
"""

from __future__ import annotations

import os
from typing import Tuple

from rag_toolkit.core.embedding import EmbeddingClient
from rag_toolkit.infra.vectorstores.factory import create_milvus_service

from src.domain.tender.indexing.indexer import TenderMilvusIndexer
from src.domain.tender.search.searcher import TenderSearcher


DEFAULT_COLLECTION = os.getenv("MILVUS_COLLECTION", "tender_chunks")


def create_tender_stack(
    embed_client: EmbeddingClient,
    embedding_dim: int,
    collection_name: str = DEFAULT_COLLECTION,
) -> Tuple[TenderMilvusIndexer, TenderSearcher]:
    """Create Tender-specific indexer and searcher stack.
    
    This factory creates a complete indexing and search stack for tender documents,
    wrapping rag-toolkit's Milvus components with domain-specific logic.
    
    Args:
        embed_client: Embedding client for vectorization
        embedding_dim: Dimension of embeddings (e.g., 768 for nomic-embed-text)
        collection_name: Name of Milvus collection to use
    
    Returns:
        Tuple of (TenderMilvusIndexer, TenderSearcher)
    
    Example:
        >>> from rag_toolkit.infra.embedding import OllamaEmbeddingClient
        >>> embed_client = OllamaEmbeddingClient()
        >>> embedding_dim = len(embed_client.embed("test"))
        >>> indexer, searcher = create_tender_stack(embed_client, embedding_dim)
    """
    # Create Milvus service using rag-toolkit factory
    milvus_service = create_milvus_service()
    
    # Create tender-specific indexer
    indexer = TenderMilvusIndexer(
        embed_fn=lambda texts: [embed_client.embed(t) for t in texts] if isinstance(texts, list) else embed_client.embed(texts),
        embedding_dim=embedding_dim,
        collection_name=collection_name,
    )
    
    # Create tender-specific searcher
    searcher = TenderSearcher(
        indexer=indexer,
        embed_client=embed_client,
    )
    
    return indexer, searcher


__all__ = [
    "create_tender_stack",
]
