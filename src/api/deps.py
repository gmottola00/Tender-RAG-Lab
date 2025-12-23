"""FastAPI dependency injection providers.

Provides instances of services, clients, and database sessions for API routes.
Uses FastAPI's Depends() mechanism for proper lifecycle management.

IMPORTANT: No @lru_cache() singletons here - FastAPI manages lifecycle per request.
"""

from __future__ import annotations

from typing import AsyncGenerator, Callable, List

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database import get_db
from src.infra.factory import create_tender_stack
from rag_toolkit.infra.embedding import OllamaEmbeddingClient
from rag_toolkit.infra.llm import OllamaLLMClient
from rag_toolkit.core.llm import LLMClient
from rag_toolkit.infra.vectorstores.factory import create_milvus_service, create_index_service
from rag_toolkit.core.index.search_strategies import VectorSearch
from rag_toolkit.rag import RagPipeline
from rag_toolkit.rag.rewriter import QueryRewriter
from rag_toolkit.rag.assembler import ContextAssembler
from rag_toolkit.rag.rerankers import LLMReranker
from rag_toolkit.infra.vectorstores.milvus.service import MilvusService
from rag_toolkit.infra.vectorstores.milvus.explorer import MilvusExplorer
from src.domain.tender.indexing.indexer import TenderMilvusIndexer
from src.domain.tender.search.searcher import TenderSearcher


# ============================================================================
# Database Dependencies
# ============================================================================

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session for API routes.
    
    Usage:
        @router.get("/")
        async def list_items(db: AsyncSession = Depends(get_db_session)):
            return await db.execute(...)
    """
    async for session in get_db():
        yield session


# ============================================================================
# Infrastructure Client Dependencies (Singletons OK for stateless clients)
# ============================================================================

_embedding_client: OllamaEmbeddingClient | None = None
_llm_client: OllamaLLMClient | None = None


def get_embedding_client() -> OllamaEmbeddingClient:
    """Provide singleton embedding client (stateless).
    
    Singleton is acceptable here because:
    - Client is stateless (no session/connection state)
    - Expensive to initialize
    - Thread-safe
    """
    global _embedding_client
    if _embedding_client is None:
        try:
            _embedding_client = OllamaEmbeddingClient()
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize embedding client: {exc}"
            ) from exc
    return _embedding_client


def get_llm_client() -> LLMClient:
    """Provide singleton LLM client (stateless).
    
    Singleton is acceptable here because:
    - Client is stateless
    - Expensive to initialize
    - Thread-safe
    """
    global _llm_client
    if _llm_client is None:
        try:
            _llm_client = OllamaLLMClient()
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize LLM client: {exc}"
            ) from exc
    return _llm_client


# ============================================================================
# Vector Store Dependencies
# ============================================================================

_milvus_service: MilvusService | None = None
_milvus_explorer: MilvusExplorer | None = None
_index_service = None


def get_milvus_service() -> MilvusService:
    """Provide singleton MilvusService.
    
    Manages connection pool internally - singleton is safe.
    """
    global _milvus_service
    if _milvus_service is None:
        try:
            _milvus_service = create_milvus_service()
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create Milvus service: {exc}"
            ) from exc
    return _milvus_service


def get_milvus_explorer() -> MilvusExplorer:
    """Provide MilvusExplorer with Milvus service connection.
    
    Note: Creates singleton on first call, reuses connection from service.
    When used in FastAPI routes, inject service with Depends():
        explorer: MilvusExplorer = Depends(get_milvus_explorer)
    """
    global _milvus_explorer
    if _milvus_explorer is None:
        try:
            service = get_milvus_service()
            _milvus_explorer = MilvusExplorer(service.connection)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create Milvus explorer: {exc}"
            ) from exc
    return _milvus_explorer


def get_index_service():
    """Provide IndexService using rag-toolkit factory.
    
    Singleton for managing index operations.
    """
    global _index_service
    if _index_service is None:
        try:
            _index_service = create_index_service()
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create index service: {exc}"
            ) from exc
    return _index_service


# ============================================================================
# Domain Service Dependencies (Tender-specific)
# ============================================================================

_tender_indexer: TenderMilvusIndexer | None = None
_tender_searcher: TenderSearcher | None = None

def get_indexer() -> TenderMilvusIndexer:
    """Provide TenderMilvusIndexer with embedding client.
    
    Singleton is acceptable because indexer maintains connection pool internally.
    """
    global _tender_indexer
    if _tender_indexer is None:
        try:
            embedding_client = get_embedding_client()
            
            # Probe embedding dimension
            embedding_dim = len(embedding_client.embed("dimension_probe"))
            
            # Create tender stack
            indexer, _ = create_tender_stack(
                embed_client=embedding_client,
                embedding_dim=embedding_dim,
            )
            _tender_indexer = indexer
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize indexer: {exc}"
            ) from exc
    return _tender_indexer


def get_searcher() -> TenderSearcher:
    """Provide TenderSearcher with embedding client.
    
    Singleton is acceptable because searcher is stateless.
    """
    global _tender_searcher
    if _tender_searcher is None:
        try:
            embedding_client = get_embedding_client()
            
            # Probe embedding dimension
            embedding_dim = len(embedding_client.embed("dimension_probe"))
            
            # Create tender stack
            _, searcher = create_tender_stack(
                embed_client=embedding_client,
                embedding_dim=embedding_dim,
            )
            _tender_searcher = searcher
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create searcher: {exc}"
            ) from exc
    return _tender_searcher


# ============================================================================
# RAG Pipeline Dependencies
# ============================================================================

_rag_pipeline: RagPipeline | None = None


def get_rag_pipeline() -> RagPipeline:
    """Provide RAG pipeline with dependencies.
    
    Singleton is acceptable because pipeline is stateless.
    """
    global _rag_pipeline
    if _rag_pipeline is None:
        try:
            embedding_client = get_embedding_client()
            index_service = get_index_service()
            llm = get_llm_client()
            
            # Create vector search strategy
            vector_search = VectorSearch(
                index_service=index_service,
                embed_fn=lambda query: embedding_client.embed(query)
            )
            
            # Create RAG components
            rewriter = QueryRewriter(llm)
            reranker = LLMReranker(llm)
            assembler = ContextAssembler(max_tokens=2000)
            
            _rag_pipeline = RagPipeline(
                vector_searcher=vector_search,
                rewriter=rewriter,
                reranker=reranker,
                assembler=assembler,
                generator_llm=llm,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create RAG pipeline: {exc}"
            ) from exc
    return _rag_pipeline


__all__ = [
    "get_db_session",
    "get_embedding_client",
    "get_llm_client",
    "get_milvus_service",
    "get_milvus_explorer",
    "get_indexer",
    "get_index_service",
    "get_searcher",
    "get_rag_pipeline",
]
