"""Tests for generic IndexService — using the actual quaerium API."""

from __future__ import annotations

from typing import List
from unittest.mock import MagicMock

import pytest

from quaerium.core.index.service import IndexService


def _make_mock_vector_store(search_return=None, query_return=None):
    """Build a MagicMock that mimics VectorStoreService interface."""
    mock = MagicMock()

    # connection.ensure() should do nothing
    mock.connection.ensure = MagicMock(return_value=None)

    # ensure_collection should succeed
    mock.ensure_collection = MagicMock(return_value=None)

    # data.upsert / flush
    mock.data.upsert = MagicMock(return_value=None)
    mock.data.flush = MagicMock(return_value=None)

    # data.search — default returns one result set with no hits
    mock.data.search = MagicMock(return_value=search_return if search_return is not None else [[]])

    # data.query — default returns empty list
    mock.data.query = MagicMock(return_value=query_return if query_return is not None else [])

    # drop_collection
    mock.drop_collection = MagicMock(return_value=None)

    return mock


def _make_embed_fn(dim: int = 768):
    """Create a simple embedding function returning constant vectors."""
    def embed_fn(texts: List[str]) -> List[List[float]]:
        return [[0.1] * dim for _ in texts]
    return embed_fn


class TestIndexServiceInitialization:
    """Test IndexService constructor validation."""

    def test_valid_initialization(self):
        """Service initialises with valid params."""
        vector_store = _make_mock_vector_store()
        svc = IndexService(
            vector_store=vector_store,
            embedding_dim=768,
            embed_fn=_make_embed_fn(768),
            collection_name="test_col",
        )
        assert svc.collection_name == "test_col"
        assert svc.embedding_dim == 768
        assert svc.embed_fn is not None
        assert svc.metric_type == "IP"
        assert svc.index_type == "HNSW"

    def test_invalid_embedding_dim_raises(self):
        """Constructor raises ValueError when embedding_dim <= 0."""
        vector_store = _make_mock_vector_store()
        with pytest.raises(ValueError, match="embedding_dim must be positive"):
            IndexService(
                vector_store=vector_store,
                embedding_dim=0,
                embed_fn=_make_embed_fn(768),
                collection_name="test_col",
            )

    def test_negative_embedding_dim_raises(self):
        """Constructor raises ValueError for negative embedding_dim."""
        vector_store = _make_mock_vector_store()
        with pytest.raises(ValueError, match="embedding_dim must be positive"):
            IndexService(
                vector_store=vector_store,
                embedding_dim=-1,
                embed_fn=_make_embed_fn(768),
                collection_name="test_col",
            )

    def test_custom_metric_and_index_type(self):
        """Service accepts custom metric_type and index_type."""
        vector_store = _make_mock_vector_store()
        svc = IndexService(
            vector_store=vector_store,
            embedding_dim=128,
            embed_fn=_make_embed_fn(128),
            collection_name="col",
            metric_type="L2",
            index_type="IVF_FLAT",
        )
        assert svc.metric_type == "L2"
        assert svc.index_type == "IVF_FLAT"


class TestEnsureCollection:
    """Test ensure_collection method."""

    def test_ensure_collection_calls_connection_and_store(self):
        """ensure_collection calls connection.ensure and vector_store.ensure_collection."""
        vector_store = _make_mock_vector_store()
        svc = IndexService(
            vector_store=vector_store,
            embedding_dim=768,
            embed_fn=_make_embed_fn(),
            collection_name="my_col",
        )
        schema = MagicMock()
        svc.ensure_collection(schema)

        vector_store.connection.ensure.assert_called_once()
        vector_store.ensure_collection.assert_called_once()
        call_kwargs = vector_store.ensure_collection.call_args
        assert call_kwargs.kwargs.get("name") == "my_col" or call_kwargs.args[0] == "my_col" or "my_col" in str(call_kwargs)


class TestUpsert:
    """Test upsert method."""

    def test_upsert_calls_data_upsert_and_flush(self):
        """upsert() calls vector_store.data.upsert and flush."""
        vector_store = _make_mock_vector_store()
        svc = IndexService(
            vector_store=vector_store,
            embedding_dim=768,
            embed_fn=_make_embed_fn(),
            collection_name="col",
        )
        data = [{"id": "1", "text": "doc1"}, {"id": "2", "text": "doc2"}]
        svc.upsert(data)

        vector_store.data.upsert.assert_called_once_with("col", data)
        vector_store.data.flush.assert_called_once_with("col")

    def test_upsert_empty_data_does_nothing(self):
        """upsert() with empty list does not call data.upsert."""
        vector_store = _make_mock_vector_store()
        svc = IndexService(
            vector_store=vector_store,
            embedding_dim=768,
            embed_fn=_make_embed_fn(),
            collection_name="col",
        )
        svc.upsert([])
        vector_store.data.upsert.assert_not_called()


class TestSearch:
    """Test search method."""

    def test_search_returns_list(self):
        """search() returns a list."""
        vector_store = _make_mock_vector_store(search_return=[[]])
        svc = IndexService(
            vector_store=vector_store,
            embedding_dim=768,
            embed_fn=_make_embed_fn(),
            collection_name="col",
        )
        results = svc.search(query_embedding=[0.1] * 768, top_k=5)
        assert isinstance(results, list)

    def test_search_calls_data_search(self):
        """search() delegates to vector_store.data.search."""
        vector_store = _make_mock_vector_store(search_return=[[]])
        svc = IndexService(
            vector_store=vector_store,
            embedding_dim=768,
            embed_fn=_make_embed_fn(),
            collection_name="col",
        )
        svc.search(query_embedding=[0.5] * 768, top_k=3)
        vector_store.data.search.assert_called_once()

    def test_search_wrong_dim_raises(self):
        """search() raises ValueError when embedding dimension is wrong."""
        vector_store = _make_mock_vector_store()
        svc = IndexService(
            vector_store=vector_store,
            embedding_dim=768,
            embed_fn=_make_embed_fn(),
            collection_name="col",
        )
        with pytest.raises(ValueError, match="dim mismatch"):
            svc.search(query_embedding=[0.1] * 128, top_k=5)

    def test_search_with_results(self):
        """search() parses and returns results from vector store."""
        hit = {"entity": {"id": "1", "text": "found doc"}, "distance": 0.95}
        vector_store = _make_mock_vector_store(search_return=[[hit]])
        svc = IndexService(
            vector_store=vector_store,
            embedding_dim=768,
            embed_fn=_make_embed_fn(),
            collection_name="col",
        )
        results = svc.search(query_embedding=[0.1] * 768)
        assert len(results) == 1
        assert results[0]["score"] == 0.95


class TestQuery:
    """Test query method."""

    def test_query_delegates_to_vector_store(self):
        """query() delegates to vector_store.data.query."""
        rows = [{"id": "1", "text": "match"}]
        vector_store = _make_mock_vector_store(query_return=rows)
        svc = IndexService(
            vector_store=vector_store,
            embedding_dim=768,
            embed_fn=_make_embed_fn(),
            collection_name="col",
        )
        result = svc.query(expr='text like "%match%"', limit=5)
        assert result == rows
        vector_store.data.query.assert_called_once()

    def test_query_returns_list(self):
        """query() always returns a list."""
        vector_store = _make_mock_vector_store(query_return=[])
        svc = IndexService(
            vector_store=vector_store,
            embedding_dim=768,
            embed_fn=_make_embed_fn(),
            collection_name="col",
        )
        result = svc.query(expr="1 == 1")
        assert isinstance(result, list)


class TestDropCollection:
    """Test drop_collection method."""

    def test_drop_collection_calls_vector_store(self):
        """drop_collection() calls vector_store.drop_collection."""
        vector_store = _make_mock_vector_store()
        svc = IndexService(
            vector_store=vector_store,
            embedding_dim=768,
            embed_fn=_make_embed_fn(),
            collection_name="col_to_drop",
        )
        svc.drop_collection()
        vector_store.drop_collection.assert_called_once_with("col_to_drop")
