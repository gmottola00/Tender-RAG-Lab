"""Factory for creating vector store services and index services.

This module provides production-ready factory functions for instantiating
vector stores with sensible defaults while allowing configuration overrides.
"""

from __future__ import annotations

import os
from typing import Callable, List, Optional

from src.core.embedding import EmbeddingClient
from src.core.index.service import IndexService
from src.domain.tender.indexing.indexer import TenderMilvusIndexer
from src.domain.tender.search.searcher import TenderSearcher
from src.infra.vectorstores.milvus.config import MilvusConfig
from src.infra.vectorstores.milvus.service import MilvusService


def create_milvus_service(
    *,
    uri: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    db_name: Optional[str] = None,
    secure: bool = False,
    timeout: Optional[float] = None,
    alias: str = "default",
) -> MilvusService:
    """Create a configured MilvusService instance.
    
    Args:
        uri: Milvus connection URI (defaults to MILVUS_URI env var or localhost:19530).
        user: Username for authentication (defaults to MILVUS_USER env var).
        password: Password for authentication (defaults to MILVUS_PASSWORD env var).
        db_name: Database name (defaults to MILVUS_DB env var or "default").
        secure: Use TLS encryption.
        timeout: Connection timeout in seconds.
        alias: Connection alias for management.
        
    Returns:
        Configured MilvusService instance.
        
    Example:
        ```python
        from src.infra.vectorstores.factory import create_milvus_service
        
        # Use environment variables
        service = create_milvus_service()
        
        # Override specific settings
        service = create_milvus_service(
            uri="http://localhost:19530",
            db_name="production"
        )
        ```
    """
    config = MilvusConfig(
        uri=uri or os.getenv("MILVUS_URI", "http://localhost:19530"),
        user=user or os.getenv("MILVUS_USER"),
        password=password or os.getenv("MILVUS_PASSWORD"),
        db_name=db_name or os.getenv("MILVUS_DB", "default"),
        secure=secure,
        timeout=timeout,
        alias=alias,
    )
    
    return MilvusService(config)


def create_index_service(
    embedding_dim: int,
    embed_fn: Callable[[List[str]], List[List[float]]],
    *,
    collection_name: Optional[str] = None,
    metric_type: Optional[str] = None,
    index_type: Optional[str] = None,
    vector_store: Optional[MilvusService] = None,
) -> IndexService:
    """Create a configured IndexService with Milvus backend.
    
    Args:
        embedding_dim: Dimensionality of embeddings.
        embed_fn: Function to generate embeddings from text.
        collection_name: Collection name (defaults to MILVUS_COLLECTION env var or "tender_chunks").
        metric_type: Distance metric (defaults to MILVUS_METRIC env var or "IP").
        index_type: Index type (defaults to MILVUS_INDEX_TYPE env var or "HNSW").
        vector_store: Optional pre-configured vector store (creates new if None).
        
    Returns:
        Configured IndexService instance.
        
    Example:
        ```python
        from src.infra.vectorstores.factory import create_index_service
        from src.core.embedding import EmbeddingClient
        
        # Create embedding client
        embed_client = EmbeddingClient(...)
        
        # Create index service
        index_service = create_index_service(
            embedding_dim=1536,
            embed_fn=lambda texts: embed_client.embed_batch(texts),
            collection_name="my_collection"
        )
        ```
    """
    if vector_store is None:
        vector_store = create_milvus_service()
    
    return IndexService(
        vector_store=vector_store,
        embedding_dim=embedding_dim,
        embed_fn=embed_fn,
        collection_name=collection_name or os.getenv("MILVUS_COLLECTION", "tender_chunks"),
        metric_type=metric_type or os.getenv("MILVUS_METRIC", "IP"),
        index_type=index_type or os.getenv("MILVUS_INDEX_TYPE", "HNSW"),
    )


def create_tender_stack(
    embed_client: EmbeddingClient,
    *,
    embedding_dim: int = 1536,
    collection_name: Optional[str] = None,
    metric_type: Optional[str] = None,
    index_type: Optional[str] = None,
) -> tuple[TenderMilvusIndexer, TenderSearcher]:
    """Create complete tender indexing and search stack.
    
    This is a convenience factory that creates both the indexer and searcher
    with proper wiring, ready for use in the tender application.
    
    Args:
        embed_client: Embedding client for text encoding.
        embedding_dim: Dimensionality of embeddings.
        collection_name: Collection name.
        metric_type: Distance metric.
        index_type: Index type.
        
    Returns:
        Tuple of (TenderMilvusIndexer, TenderSearcher).
        
    Example:
        ```python
        from src.infra.vectorstores.factory import create_tender_stack
        from src.infra.embedding.openai import OpenAIEmbeddingClient as OpenAIEmbedding
        
        # Create embedding client
        embed_client = OpenAIEmbedding(model="text-embedding-3-small")
        
        # Create complete stack
        indexer, searcher = create_tender_stack(
            embed_client=embed_client,
            embedding_dim=1536
        )
        
        # Use indexer to add chunks
        indexer.upsert_token_chunks(chunks)
        
        # Use searcher to query
        results = searcher.hybrid_search("query text")
        ```
    """
    # Create generic index service
    index_service = create_index_service(
        embedding_dim=embedding_dim,
        embed_fn=lambda texts: embed_client.embed_batch(texts),
        collection_name=collection_name,
        metric_type=metric_type,
        index_type=index_type,
    )
    
    # Create tender-specific indexer wrapper
    indexer = TenderMilvusIndexer(
        index_service=index_service,
        embedding_dim=embedding_dim,
        embed_fn=lambda texts: embed_client.embed_batch(texts),
        collection_name=collection_name or os.getenv("MILVUS_COLLECTION", "tender_chunks"),
        metric_type=metric_type or os.getenv("MILVUS_METRIC", "IP"),
        index_type=index_type or os.getenv("MILVUS_INDEX_TYPE", "HNSW"),
    )
    
    # Create tender searcher
    searcher = TenderSearcher(indexer=indexer, embed_client=embed_client)
    
    return indexer, searcher


__all__ = [
    "create_milvus_service",
    "create_index_service",
    "create_tender_stack",
]
