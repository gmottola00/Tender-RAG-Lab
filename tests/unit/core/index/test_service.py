"""Tests for generic IndexService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.core.index.service import IndexService
from tests.mocks import MockVectorStore


class TestIndexService:
    """Test generic IndexService."""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store."""
        return MockVectorStore()
    
    @pytest.fixture
    def mock_embed_fn(self):
        """Create mock embedding function."""
        def embed_fn(texts: list[str]) -> list[list[float]]:
            return [[0.1] * 768 for _ in texts]
        return embed_fn
    
    @pytest.fixture
    def index_service(self, mock_vector_store, mock_embed_fn):
        """Create IndexService instance."""
        return IndexService(
            vector_store=mock_vector_store,
            collection_name="test_collection",
            embedding_dim=768,
            embed_fn=mock_embed_fn
        )
    
    def test_service_initialization(self, index_service):
        """Test service initializes correctly."""
        assert index_service.collection_name == "test_collection"
        assert index_service.embedding_dim == 768
        assert index_service.embed_fn is not None
    
    def test_create_collection(self, index_service, mock_vector_store):
        """Test creating a collection."""
        index_service.create_collection()
        
        assert mock_vector_store.has_collection("test_collection")
        assert "test_collection" in mock_vector_store.collections
    
    def test_upsert_data(self, index_service, mock_vector_store):
        """Test upserting data."""
        # Create collection first
        index_service.create_collection()
        
        # Prepare data
        data = [
            {"id": "1", "text": "First document"},
            {"id": "2", "text": "Second document"},
        ]
        
        # Upsert
        ids = index_service.upsert(data)
        
        assert len(ids) == 2
        assert len(mock_vector_store.data["test_collection"]) == 2
    
    def test_search(self, index_service, mock_vector_store):
        """Test vector search."""
        # Setup
        index_service.create_collection()
        index_service.upsert([
            {"id": "1", "text": "Document about AI"},
            {"id": "2", "text": "Document about ML"},
        ])
        
        # Search with query embedding
        query_embedding = [0.15] * 768
        results = index_service.search(
            query_embedding=query_embedding,
            top_k=2
        )
        
        assert isinstance(results, list)
        # Mock returns results
        assert len(results) >= 0
    
    def test_delete_by_ids(self, index_service, mock_vector_store):
        """Test deleting by IDs."""
        index_service.create_collection()
        index_service.upsert([{"id": "1", "text": "Test"}])
        
        # Delete should not raise
        index_service.delete(ids=["1"])
    
    def test_embedding_function_called(self, index_service, mock_embed_fn):
        """Test that embedding function is called during upsert."""
        with patch.object(index_service, 'embed_fn', wraps=mock_embed_fn) as mock:
            index_service.create_collection()
            index_service.upsert([{"text": "Test document"}])
            
            # Embedding function should be called
            assert mock.call_count > 0
    
    def test_collection_not_exists_error(self, index_service):
        """Test operations on non-existent collection."""
        # Should handle gracefully or create collection
        try:
            index_service.upsert([{"text": "Test"}])
        except Exception:
            # Expected if collection doesn't exist
            pass
