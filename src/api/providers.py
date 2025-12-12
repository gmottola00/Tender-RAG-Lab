"""Shared providers for API dependencies (embedding client, indexer)."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Callable, List

from fastapi import HTTPException

from src.core.embedding import OllamaEmbeddingClient
from src.core.index.vector.config import MilvusConfig
from src.core.index.vector.service import MilvusService
from src.core.index.tender_indexer import TenderMilvusIndexer
from src.core.index.tender_searcher import TenderSearcher
from src.core.index.search.vector_searcher import VectorSearcher
from src.core.rag.pipeline import RagPipeline
from src.core.rag.rewriter import QueryRewriter
from src.core.rag.assembler import ContextAssembler
from src.core.rag.rerankers import LLMReranker
from src.core.llm import OllamaLLMClient, LLMClient


@lru_cache(maxsize=1)
def get_embedding_client() -> OllamaEmbeddingClient:
    """Singleton embedding client."""
    try:
        return OllamaEmbeddingClient()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to init embedding client: {exc}") from exc


@lru_cache(maxsize=1)
def get_indexer() -> TenderMilvusIndexer:
    """Singleton Milvus indexer for tender chunks."""
    embedding_client = get_embedding_client()
    try:
        embedding_dim = len(embedding_client.embed("dimension_probe"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to probe embedding dimension: {exc}") from exc

    cfg = MilvusConfig(
        uri=os.getenv("MILVUS_URI", "http://localhost:19530"),
        alias=os.getenv("MILVUS_ALIAS", "default"),
        user=os.getenv("MILVUS_USER"),
        password=os.getenv("MILVUS_PASSWORD"),
        db_name=os.getenv("MILVUS_DB_NAME", "default"),
        secure=os.getenv("MILVUS_SECURE", "false").lower() == "true",
    )

    try:
        service = MilvusService(cfg)
        return TenderMilvusIndexer(
            service=service,
            embedding_dim=embedding_dim,
            embed_fn=embedding_client.embed_batch,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to initialize indexer: {exc}") from exc


@lru_cache(maxsize=1)
def get_searcher() -> TenderSearcher:
    """Singleton tender searcher orchestrator."""
    embedding_client = get_embedding_client()
    indexer = get_indexer()
    return TenderSearcher(indexer=indexer, embed_client=embedding_client)


@lru_cache(maxsize=1)
def get_llm() -> LLMClient:
    """Singleton LLM client for RAG generation/rewriting."""
    try:
        return OllamaLLMClient()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to init LLM client: {exc}") from exc


@lru_cache(maxsize=1)
def get_rag_pipeline() -> RagPipeline:
    """Singleton RAG pipeline (vector-only for now)."""
    embedding_client = get_embedding_client()
    indexer = get_indexer()
    llm = get_llm()
    vector_searcher = VectorSearcher(indexer=indexer, embed_client=embedding_client)
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


__all__ = ["get_embedding_client", "get_indexer"]
