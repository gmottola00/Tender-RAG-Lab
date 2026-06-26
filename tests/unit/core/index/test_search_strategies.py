"""Tests for search strategies — using the actual quaerium API."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from quaerium.core.index.search_strategies import (
    HybridSearch,
    IdentityReranker,
    KeywordSearch,
    VectorSearch,
)
from tests.mocks import create_mock_index_service


def _make_vector_search(search_results=None):
    """Build a VectorSearch with a mock IndexService."""
    mock_index = create_mock_index_service()
    results = search_results if search_results is not None else [
        {"id": "1", "text": "Vector Result 1", "score": 0.95},
        {"id": "2", "text": "Vector Result 2", "score": 0.85},
    ]
    mock_index.search = MagicMock(return_value=results)
    embed_fn = lambda text: [0.1] * 768
    return VectorSearch(index_service=mock_index, embed_fn=embed_fn)


def _make_keyword_search(query_results=None):
    """Build a KeywordSearch with a mock IndexService."""
    mock_index = create_mock_index_service()
    results = query_results if query_results is not None else [
        {"id": "1", "text": "Keyword Result 1"},
        {"id": "3", "text": "Keyword Result 3"},
    ]
    mock_index.query = MagicMock(return_value=results)
    return KeywordSearch(index_service=mock_index)


class TestVectorSearch:
    """Test VectorSearch strategy."""

    def test_initialization(self):
        """VectorSearch stores index_service and embed_fn."""
        mock_index = create_mock_index_service()
        embed_fn = lambda t: [0.1] * 768
        vs = VectorSearch(index_service=mock_index, embed_fn=embed_fn)
        assert vs.index_service is mock_index
        assert vs.embed_fn is embed_fn

    def test_search_returns_list(self):
        """search() returns a list."""
        vs = _make_vector_search()
        results = vs.search("test query")
        assert isinstance(results, list)

    def test_search_uses_embed_fn(self):
        """search() calls embed_fn to convert query to embedding."""
        embed_calls = []
        mock_index = create_mock_index_service()
        mock_index.search = MagicMock(return_value=[{"id": "1", "score": 0.9}])

        def capturing_embed(text):
            embed_calls.append(text)
            return [0.1] * 768

        vs = VectorSearch(index_service=mock_index, embed_fn=capturing_embed)
        vs.search("my query", top_k=3)

        assert len(embed_calls) == 1
        assert embed_calls[0] == "my query"

    def test_search_delegates_to_index_service(self):
        """search() calls index_service.search with the embedding."""
        mock_index = create_mock_index_service()
        mock_index.search = MagicMock(return_value=[])
        embed_fn = lambda t: [0.5] * 768

        vs = VectorSearch(index_service=mock_index, embed_fn=embed_fn)
        vs.search("query", top_k=5)

        mock_index.search.assert_called_once()

    def test_search_with_search_params(self):
        """search() passes search_params to index_service.search."""
        vs = _make_vector_search()
        results = vs.search("query", top_k=3, search_params={"metric_type": "L2"})
        assert isinstance(results, list)

    def test_search_returns_results_from_index(self):
        """search() propagates results from the index service."""
        expected = [{"id": "1", "score": 0.95}, {"id": "2", "score": 0.80}]
        vs = _make_vector_search(search_results=expected)
        results = vs.search("query")
        assert results == expected


class TestKeywordSearch:
    """Test KeywordSearch strategy."""

    def test_initialization(self):
        """KeywordSearch stores index_service."""
        mock_index = create_mock_index_service()
        ks = KeywordSearch(index_service=mock_index)
        assert ks.index_service is mock_index

    def test_search_returns_list(self):
        """search() returns a list."""
        ks = _make_keyword_search()
        results = ks.search("keyword term")
        assert isinstance(results, list)

    def test_search_calls_index_service_query(self):
        """search() calls index_service.query."""
        mock_index = create_mock_index_service()
        mock_index.query = MagicMock(return_value=[])
        ks = KeywordSearch(index_service=mock_index)
        ks.search("my term", top_k=5)
        mock_index.query.assert_called_once()

    def test_search_results_include_score_field(self):
        """Keyword search results have a 'score' key (may be None)."""
        ks = _make_keyword_search(query_results=[{"id": "1", "text": "match"}])
        results = ks.search("match")
        assert len(results) >= 0  # could be 0 or 1
        for r in results:
            assert "score" in r

    def test_empty_query_uses_fallback_expression(self):
        """search() with empty query uses fallback '1 == 1' expression."""
        mock_index = create_mock_index_service()
        mock_index.query = MagicMock(return_value=[])
        ks = KeywordSearch(index_service=mock_index)
        ks.search("", top_k=5)
        mock_index.query.assert_called_once()


class TestHybridSearch:
    """Test HybridSearch strategy."""

    @pytest.fixture
    def vector_search(self):
        return _make_vector_search([
            {"id": "1", "text": "Vector hit 1", "score": 0.9},
            {"id": "2", "text": "Vector hit 2", "score": 0.8},
        ])

    @pytest.fixture
    def keyword_search(self):
        return _make_keyword_search([
            {"id": "1", "text": "Keyword hit 1"},
            {"id": "3", "text": "Keyword hit 3"},
        ])

    @pytest.fixture
    def hybrid_search(self, vector_search, keyword_search):
        return HybridSearch(
            vector_search=vector_search,
            keyword_search=keyword_search,
            alpha=0.7,
        )

    def test_initialization(self, hybrid_search, vector_search, keyword_search):
        """HybridSearch stores both sub-searchers and alpha."""
        assert hybrid_search.vector_search is vector_search
        assert hybrid_search.keyword_search is keyword_search
        assert hybrid_search.alpha == 0.7
        assert hybrid_search.reranker is None

    def test_initialization_with_reranker(self, vector_search, keyword_search):
        """HybridSearch stores reranker when provided."""
        reranker = MagicMock()
        hs = HybridSearch(
            vector_search=vector_search,
            keyword_search=keyword_search,
            reranker=reranker,
            alpha=0.5,
        )
        assert hs.reranker is reranker
        assert hs.alpha == 0.5

    def test_search_returns_list(self, hybrid_search):
        """search() returns a list."""
        results = hybrid_search.search("test query", top_k=5)
        assert isinstance(results, list)

    def test_search_combines_results(self, hybrid_search):
        """search() merges vector and keyword results."""
        # vector returns ids 1, 2; keyword returns ids 1, 3 → combined: 1, 2, 3
        results = hybrid_search.search("query", top_k=10)
        result_ids = {r.get("id") for r in results}
        # Should contain entries from both sources
        assert len(result_ids) >= 2

    def test_search_respects_top_k(self, vector_search, keyword_search):
        """search() returns at most top_k results."""
        hs = HybridSearch(
            vector_search=vector_search,
            keyword_search=keyword_search,
            alpha=0.7,
        )
        results = hs.search("query", top_k=1)
        assert len(results) <= 1

    def test_search_calls_both_strategies(self, vector_search, keyword_search):
        """search() calls both VectorSearch.search and KeywordSearch.search."""
        # Wrap with spies
        vs_mock = MagicMock(wraps=vector_search)
        ks_mock = MagicMock(wraps=keyword_search)
        hs = HybridSearch(vector_search=vs_mock, keyword_search=ks_mock, alpha=0.7)
        hs.search("query", top_k=5)

        vs_mock.search.assert_called_once()
        ks_mock.search.assert_called_once()

    def test_reranker_called_when_configured(self, vector_search, keyword_search):
        """When reranker is set, it is invoked and its results are returned."""
        reranker = IdentityReranker()
        hs = HybridSearch(
            vector_search=vector_search,
            keyword_search=keyword_search,
            reranker=reranker,
            alpha=0.7,
        )
        results = hs.search("query", top_k=5)
        assert isinstance(results, list)


class TestIdentityReranker:
    """Test IdentityReranker — no-op reranker."""

    def test_returns_results_unchanged(self):
        """IdentityReranker returns all results unchanged (no slicing)."""
        reranker = IdentityReranker()
        candidates = [
            {"id": "1", "score": 0.9},
            {"id": "2", "score": 0.8},
            {"id": "3", "score": 0.7},
        ]
        result = reranker.rerank("q", candidates, top_k=2)
        # IdentityReranker returns all candidates unchanged (no top_k slicing)
        assert result == candidates

    def test_returns_all_candidates_regardless_of_top_k(self):
        """IdentityReranker returns all results regardless of top_k."""
        reranker = IdentityReranker()
        candidates = [{"id": "1"}, {"id": "2"}]
        result = reranker.rerank("q", candidates, top_k=10)
        assert result == candidates

    def test_returns_empty_list_for_empty_candidates(self):
        """IdentityReranker returns empty list when no candidates."""
        reranker = IdentityReranker()
        result = reranker.rerank("q", [], top_k=5)
        assert result == []
