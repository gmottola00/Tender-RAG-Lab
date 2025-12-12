"""Specialized Milvus indexer for token chunks produced by the ingestion pipeline."""

from __future__ import annotations

import json
import os
from typing import Callable, Dict, Iterable, List, Optional, Sequence

from src.core.index.vector.connection import MilvusConnectionManager
from src.core.index.vector.exceptions import CollectionError, DataOperationError
from src.core.index.vector.service import MilvusService
from src.schemas.chunking import TokenChunk

try:
    from pymilvus import (
        Collection,
        CollectionSchema,
        DataType,
        FieldSchema,
        MilvusException,
    )
except ImportError as exc:  # pragma: no cover - optional dependency
    Collection = None  # type: ignore
    CollectionSchema = None  # type: ignore
    DataType = None  # type: ignore
    FieldSchema = None  # type: ignore
    MilvusException = None  # type: ignore
    _pymilvus_import_error = exc


DEFAULT_COLLECTION = os.getenv("MILVUS_COLLECTION", "tender_chunks")
DEFAULT_METRIC = os.getenv("MILVUS_METRIC", "IP")
DEFAULT_INDEX_TYPE = os.getenv("MILVUS_INDEX_TYPE", "HNSW")
DEFAULT_HNSW_M = int(os.getenv("MILVUS_HNSW_M", "24"))
DEFAULT_HNSW_EF = int(os.getenv("MILVUS_HNSW_EF", "200"))


class TenderMilvusIndexer:
    """Indexer tailored to ingest token chunks with metadata into Milvus."""

    def __init__(
        self,
        service: MilvusService,
        embedding_dim: int,
        embed_fn: Callable[[List[str]], List[List[float]]],
        *,
        collection_name: str = DEFAULT_COLLECTION,
        metric_type: str = DEFAULT_METRIC,
        index_type: str = DEFAULT_INDEX_TYPE,
    ) -> None:
        if Collection is None or CollectionSchema is None:
            raise ImportError("pymilvus is required for Milvus operations") from _pymilvus_import_error
        if embedding_dim <= 0:
            raise ValueError("embedding_dim must be positive")
        self.service = service
        self.embedding_dim = embedding_dim
        self.embed_fn = embed_fn
        self.collection_name = collection_name
        self.metric_type = metric_type
        self.index_type = index_type
        self.connection: MilvusConnectionManager = service.connection
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create collection and index if missing."""
        self.connection.ensure()
        if self._has_collection():
            return

        schema = self._build_schema()
        self.service.collections.ensure_collection(
            self.collection_name,
            schema=schema,
            consistency_level="Bounded",
            shards_num=2,
        )
        index_params = self._build_index_params()
        self._create_index(index_params)

    def _has_collection(self) -> bool:
        try:
            from pymilvus import utility

            return utility.has_collection(self.collection_name, using=self.connection.get_alias())
        except Exception as exc:  # pragma: no cover - passthrough
            raise CollectionError("Failed to check collection existence") from exc

    def _build_schema(self) -> CollectionSchema:
        try:
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="section_path", dtype=DataType.VARCHAR, max_length=2048),
                FieldSchema(name="metadata", dtype=DataType.JSON),
                FieldSchema(name="page_numbers", dtype=DataType.JSON),
                FieldSchema(name="source_chunk_id", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim),
            ]
            return CollectionSchema(fields=fields, description="Tender token chunks")
        except MilvusException as exc:  # pragma: no cover - passthrough
            raise CollectionError("Failed to build schema") from exc

    def _build_index_params(self) -> Dict[str, object]:
        if self.index_type.upper() == "HNSW":
            return {"index_type": "HNSW", "metric_type": self.metric_type, "params": {"M": DEFAULT_HNSW_M, "efConstruction": DEFAULT_HNSW_EF}}
        return {"index_type": self.index_type, "metric_type": self.metric_type, "params": {}}

    def _create_index(self, index_params: Dict[str, object]) -> None:
        try:
            col = Collection(name=self.collection_name, using=self.connection.get_alias())
            col.create_index(field_name="embedding", index_params=index_params)
            col.load()
        except Exception as exc:  # pragma: no cover - passthrough
            raise CollectionError("Failed to create/load index") from exc

    def upsert_token_chunks(self, chunks: Sequence[TokenChunk]) -> None:
        """Embed and insert token chunks into Milvus."""
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
            rows.append(
                {
                    "id": chunk.id,
                    "text": chunk.text,
                    "section_path": chunk.section_path,
                    "metadata": chunk.metadata,
                    "page_numbers": chunk.page_numbers,
                    "source_chunk_id": chunk.source_chunk_id,
                    "embedding": emb,
                }
            )
        try:
            col = Collection(name=self.collection_name, using=self.connection.get_alias())
            col.insert(rows)
            col.flush()
        except Exception as exc:  # pragma: no cover - passthrough
            raise DataOperationError("Insert/upsert failed") from exc

    def search(
        self,
        query_embedding: List[float],
        *,
        top_k: int = 5,
        output_fields: Optional[List[str]] = None,
        search_params: Optional[Dict[str, object]] = None,
    ) -> List[Dict[str, object]]:
        """Search similar chunks by embedding."""
        if len(query_embedding) != self.embedding_dim:
            raise ValueError(f"Query embedding dim mismatch: expected {self.embedding_dim}")

        params = search_params or {"metric_type": self.metric_type, "params": {"ef": DEFAULT_HNSW_EF if self.index_type.upper() == "HNSW" else 64}}
        try:
            col = Collection(name=self.collection_name, using=self.connection.get_alias())
            col.load()
            results = col.search(
                data=[query_embedding],
                anns_field="embedding",
                param=params,
                limit=top_k,
                output_fields=output_fields or ["text", "section_path", "metadata", "page_numbers", "source_chunk_id"],
            )
        except Exception as exc:  # pragma: no cover - passthrough
            raise DataOperationError("Search failed") from exc

        hits: List[Dict[str, object]] = []
        for hit in results[0]:
            hits.append(
                {
                    "score": hit.distance,
                    "text": hit.entity.get("text"),
                    "section_path": hit.entity.get("section_path"),
                    "metadata": hit.entity.get("metadata"),
                    "page_numbers": hit.entity.get("page_numbers"),
                    "source_chunk_id": hit.entity.get("source_chunk_id"),
                    "id": hit.id,
                }
            )
        return hits


__all__ = ["TenderMilvusIndexer"]
