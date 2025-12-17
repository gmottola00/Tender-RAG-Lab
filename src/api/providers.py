"""Shared providers for API dependencies (embedding client, indexer).

UPDATED: Now uses the refactored architecture with dependency injection.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Callable, List

from fastapi import HTTPException

from src.core.embedding import OllamaEmbeddingClient
from src.core.index.search.vector_searcher import VectorSearcher
from src.core.rag.pipeline import RagPipeline
from src.core.rag.rewriter import QueryRewriter
from src.core.rag.assembler import ContextAssembler
from src.core.rag.rerankers import LLMReranker
from src.core.llm import OllamaLLMClient, LLMClient

# NEW: Import from refactored modules
from src.infra.vectorstores.factory import (
    create_milvus_service,
    create_tender_stack,
)
from src.infra.vectorstores.milvus.service import MilvusService
from src.infra.vectorstores.milvus.explorer import MilvusExplorer
from src.core.index.tender_indexer_v2 import TenderMilvusIndexer
from src.core.index.tender_searcher_v2 import TenderSearcher


@lru_cache(maxsize=1)
def get_embedding_client() -> OllamaEmbeddingClient:
    """Singleton embedding client."""
    try:
        return OllamaEmbeddingClient()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to init embedding client: {exc}") from exc


@lru_cache(maxsize=1)
def get_indexer() -> TenderMilvusIndexer:
    """Singleton Milvus indexer for tender chunks.
    
    UPDATED: Now uses factory pattern from refactored architecture.
    """
    embedding_client = get_embedding_client()
    
    try:
        embedding_dim = len(embedding_client.embed("dimension_probe"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to probe embedding dimension: {exc}") from exc

    try:
        # Use new factory to create tender stack
        indexer, _ = create_tender_stack(
            embed_client=embedding_client,
            embedding_dim=embedding_dim,
        )
        return indexer
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to initialize indexer: {exc}") from exc


@lru_cache(maxsize=1)
def get_milvus_service() -> MilvusService:
    """Provide an instance of MilvusService.
    
    UPDATED: Now uses factory pattern from refactored architecture.
    """
    try:
        return create_milvus_service()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Milvus service: {exc}"
        ) from exc


@lru_cache(maxsize=1)
def get_milvus_explorer() -> MilvusExplorer:
    """Singleton explorer for Milvus collections.
    
    UPDATED: Now uses MilvusService from refactored architecture.
    """
    try:
        service = get_milvus_service()
        return MilvusExplorer(service.connection)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Milvus explorer: {exc}"
        ) from exc


@lru_cache(maxsize=1)
def get_searcher() -> TenderSearcher:
    """Singleton tender searcher orchestrator.
    
    UPDATED: Now uses factory pattern from refactored architecture.
    """
    embedding_client = get_embedding_client()
    
    try:
        embedding_dim = len(embedding_client.embed("dimension_probe"))
        
        # Use factory to create complete stack
        _, searcher = create_tender_stack(
            embed_client=embedding_client,
            embedding_dim=embedding_dim,
        )
        return searcher
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create searcher: {exc}"
        ) from exc


@lru_cache(maxsize=1)
def get_llm() -> LLMClient:
    """Singleton LLM client for RAG generation/rewriting."""
    try:
        return OllamaLLMClient()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to init LLM client: {exc}") from exc


@lru_cache(maxsize=1)
def get_rag_pipeline() -> RagPipeline:
    """Singleton RAG pipeline (vector-only for now).
    
    UPDATED: Now uses refactored searcher.
    """
    embedding_client = get_embedding_client()
    indexer = get_indexer()
    llm = get_llm()
    
    # VectorSearcher still uses indexer (backward compatible)
    vector_searcher = VectorSearcher(
        indexer=indexer, 
        embed_client=embedding_client
    )
    
    rewriter = QueryRewriter(llm)
    reranker = LLMReranker(llm)
    assembler = ContextAssembler(max_tokens=2000)
    
    return RagPipeline(
        vector_searcher=vector_searcher,
        rewriter=rewriter,
        reranker=reranker,
        assembler=assembler,
        generator_llm=llm,
    )


__all__ = [
    "get_embedding_client",
    "get_indexer",
    "get_milvus_service",
    "get_milvus_explorer",
    "get_searcher",
    "get_llm",
    "get_rag_pipeline",
]
