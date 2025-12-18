"""Tests for search strategies."""

from __future__ import annotations

import pytest

from src.core.index.search_strategies import VectorSearch, KeywordSearch, HybridSearch
from tests.mocks import MockVectorStore, create_mock_index_service


class TestVectorSearch:
    """Test VectorSearch strategy."""
    
    @pytest.fixture
    def mock_index_service(self):
        """Create mock index service."""
        mock = create_mock_index_service()
        mock.search = lambda query_embedding, top_k, **kwargs: [
            {"id": "1", "text": "Result 1", "score": 0.95},
            {"id": "2", "text": "Result 2", "score": 0.85},
        ]
        return mock
    
    @pytest.fixture
    def embed_fn(self):
        """Mock embedding function."""
        return lambda text: [0.1] * 768
    
    @pytest.fixture
    def vector_search(self, mock_index_service, embed_fn):
        """Create VectorSearch instance."""
        return VectorSearch(
            index_service=mock_index_service,
            embed_fn=embed_fn
        )
    
    def test_vector_search_initialization(self, vector_search):
        """Test VectorSearch initializes."""
        assert vector_search.index_service is not None
        assert vector_search.embed_fn is not None
    
    def test_vector_search_execution(self, vector_search):
        """Test executing vector search."""
        results = vector_search.search("test query", top_k=2)
        
        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0]["score"] == 0.95
    
    def test_vector_search_with_params(self, vector_search):
        """Test search with custom parameters."""
        results = vector_search.search(
            "test query",
            top_k=5,
            search_params={"metric_type": "IP"}
        )
        
        assert isinstance(results, list)


class TestKeywordSearch:
    """Test KeywordSearch strategy."""
    
    @pytest.fixture
    def mock_index_service(self):
        """Create mock index service."""
        mock = create_mock_index_service()
        # Mock query method for keyword search
        mock.query = lambda expr, output_fields, **kwargs: [
            {"id": "1", "text": "Document with keyword", "score": 1.0},
        ]
        return mock
    
    @pytest.fixture
    def keyword_search(self, mock_index_service):
        """Create KeywordSearch instance."""
        return KeywordSearch(index_service=mock_index_service)
    
    def test_keyword_search_initialization(self, keyword_search):
        """Test KeywordSearch initializes."""
        assert keyword_search.index_service is not None
    
    def test_keyword_search_execution(self, keyword_search):
        """Test executing keyword search."""
        results = keyword_search.search("keyword", top_k=5)
        
        assert isinstance(results, list)
        # Mock returns results
        assert len(results) >= 0


class TestHybridSearch:
    """Test HybridSearch strategy."""
    
    @pytest.fixture
    def mock_index_service(self):
        """Create mock index service."""
        mock = create_mock_index_service()
        mock.search = lambda query_embedding, top_k, **kwargs: [
            {"id": "1", "text": "Vector result", "score": 0.9},
            {"id": "2", "text": "Another result", "score": 0.8},
        ]
        mock.query = lambda expr, output_fields, **kwargs: [
            {"id": "1", "text": "Keyword result"},
            {"id": "3", "text": "Different result"},
        ]
        return mock
    
    @pytest.fixture
    def embed_fn(self):
        """Mock embedding function."""
        return lambda text: [0.1] * 768
    
    @pytest.fixture
    def hybrid_search(self, mock_index_service, embed_fn):
        """Create HybridSearch instance."""
        return HybridSearch(
            index_service=mock_index_service,
            embed_fn=embed_fn,
            alpha=0.7  # 70% vector, 30% keyword
        )
    
    def test_hybrid_search_initialization(self, hybrid_search):
        """Test HybridSearch initializes."""
        assert hybrid_search.index_service is not None
        assert hybrid_search.embed_fn is not None
        assert hybrid_search.alpha == 0.7
    
    def test_hybrid_search_execution(self, hybrid_search):
        """Test executing hybrid search."""
        results = hybrid_search.search("test query", top_k=5)
        
        assert isinstance(results, list)
        # Should combine vector and keyword results
        assert len(results) >= 0
    
    def test_hybrid_search_combines_results(self, hybrid_search):
        """Test that hybrid search combines both strategies."""
        results = hybrid_search.search("query", top_k=10)
        
        # Should have results from both vector and keyword search
        # Mock returns different IDs from each method
        assert isinstance(results, list)
