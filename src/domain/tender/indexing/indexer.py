"""Tender-specific indexer wrapper using generic IndexService.

This module provides backward compatibility while using the new
generic IndexService underneath. It handles TokenChunk serialization.
"""

from __future__ import annotations

import os
from typing import Callable, Dict, List, Optional, Sequence

from src.core.index.service import IndexService
from rag_toolkit.core.chunking.types import TokenChunkLike

try:
    from pymilvus import DataType
except ImportError as exc:
    DataType = None
    _pymilvus_import_error = exc


DEFAULT_COLLECTION = os.getenv("MILVUS_COLLECTION", "tender_chunks")
DEFAULT_METRIC = os.getenv("MILVUS_METRIC", "IP")
DEFAULT_INDEX_TYPE = os.getenv("MILVUS_INDEX_TYPE", "HNSW")
DEFAULT_HNSW_M = int(os.getenv("MILVUS_HNSW_M", "24"))
DEFAULT_HNSW_EF = int(os.getenv("MILVUS_HNSW_EF", "200"))


class TenderMilvusIndexer:
    """Indexer for token chunks using generic IndexService underneath.
    
    This class maintains backward compatibility with existing code while
    delegating to the generic IndexService for actual operations.
    """

    def __init__(
        self,
        index_service: IndexService,
        embedding_dim: int,
        embed_fn: Callable[[List[str]], List[List[float]]],
        *,
        collection_name: str = DEFAULT_COLLECTION,
        metric_type: str = DEFAULT_METRIC,
        index_type: str = DEFAULT_INDEX_TYPE,
    ) -> None:
        """Initialize with generic IndexService.
        
        Args:
            index_service: Generic index service (configured with vector store).
            embedding_dim: Dimensionality of embeddings.
            embed_fn: Function to generate embeddings.
            collection_name: Collection name.
            metric_type: Distance metric.
            index_type: Index type.
        """
        if DataType is None:
            raise ImportError("pymilvus is required for Milvus operations") from _pymilvus_import_error
        if embedding_dim <= 0:
            raise ValueError("embedding_dim must be positive")
        
        self.index_service = index_service
        self.embedding_dim = embedding_dim
        self.embed_fn = embed_fn
        self.collection_name = collection_name
        self.metric_type = metric_type
        self.index_type = index_type
        
        # Expose legacy attributes for backward compatibility
        self.service = index_service.vector_store
        self.connection = index_service.vector_store.connection
        
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create collection and index if missing."""
        schema = self._build_schema()
        index_params = self._build_index_params()
        
        self.index_service.ensure_collection(
            schema=schema,
            index_params={"field_name": "embedding", **index_params},
        )

    def _build_schema(self):
        """Build Milvus schema for token chunks."""
        client = self.connection.client
        schema = client.create_schema(auto_id=False, enable_dynamic_field=False)
        schema.add_field(field_name="id", datatype=DataType.VARCHAR, is_primary=True, max_length=64)
        schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=65535)
        schema.add_field(field_name="section_path", datatype=DataType.VARCHAR, max_length=2048)
        schema.add_field(field_name="tender_id", datatype=DataType.VARCHAR, max_length=2048)
        schema.add_field(field_name="metadata", datatype=DataType.JSON)
        schema.add_field(field_name="page_numbers", datatype=DataType.JSON)
        schema.add_field(field_name="source_chunk_id", datatype=DataType.VARCHAR, max_length=64)
        schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=self.embedding_dim)
        return schema

    def _build_index_params(self) -> Dict[str, object]:
        """Build index parameters."""
        if self.index_type.upper() == "HNSW":
            return {
                "index_type": "HNSW",
                "metric_type": self.metric_type,
                "M": DEFAULT_HNSW_M,
                "efConstruction": DEFAULT_HNSW_EF,
            }
        return {"index_type": self.index_type, "metric_type": self.metric_type}

    def upsert_token_chunks(self, chunks: Sequence[TokenChunkLike]) -> None:
        """Embed and insert token chunks into Milvus.
        
        Args:
            chunks: Sequence of TokenChunkLike objects to index.
        """
        if not chunks:
            return

        texts = [chunk.text for chunk in chunks]
        embeddings = self.embed_fn(texts)
        
        if len(embeddings) != len(chunks):
            raise ValueError("Embedding count does not match chunks length")

        rows = []
        for chunk, emb in zip(chunks, embeddings):
            if len(emb) != self.embedding_dim:
                raise ValueError(f"Embedding dim mismatch: expected {self.embedding_dim}, got {len(emb)}")
            rows.append({
                "id": chunk.id,
                "text": chunk.text,
                "section_path": chunk.section_path,
                "metadata": chunk.metadata,
                "page_numbers": chunk.page_numbers,
                "source_chunk_id": chunk.source_chunk_id,
                "embedding": emb,
            })
        
        self.index_service.upsert(rows)

    def search(
        self,
        query_embedding: List[float],
        *,
        top_k: int = 5,
        output_fields: Optional[List[str]] = None,
        search_params: Optional[Dict[str, object]] = None,
    ) -> List[Dict[str, object]]:
        """Search similar chunks by embedding.
        
        Args:
            query_embedding: Query vector.
            top_k: Number of results.
            output_fields: Fields to return.
            search_params: Search parameters.
            
        Returns:
            List of result dictionaries.
        """
        if len(query_embedding) != self.embedding_dim:
            raise ValueError(f"Query embedding dim mismatch: expected {self.embedding_dim}")

        params = search_params or {
            "metric_type": self.metric_type,
            "params": {"ef": DEFAULT_HNSW_EF if self.index_type.upper() == "HNSW" else 64},
        }
        
        default_fields = ["text", "section_path", "metadata", "page_numbers", "source_chunk_id"]
        
        return self.index_service.search(
            query_embedding=query_embedding,
            top_k=top_k,
            output_fields=output_fields or default_fields,
            search_params=params,
        )


__all__ = ["TenderMilvusIndexer"]
