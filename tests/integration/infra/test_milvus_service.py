"""Integration tests for Milvus vector store.

These tests require a running Milvus instance (via docker-compose).
Run with: pytest -m integration
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

from src.infra.vectorstores.milvus.service import MilvusService
from src.infra.vectorstores.milvus.config import MilvusConfig


@pytest.mark.integration
@pytest.mark.milvus
class TestMilvusService:
    """Integration tests for MilvusService."""
    
    @pytest.fixture(scope="class")
    def milvus_config(self):
        """Milvus configuration for tests."""
        return MilvusConfig(
            uri=os.getenv("MILVUS_URI", "http://localhost:19530"),
            user=os.getenv("MILVUS_USER", ""),
            password=os.getenv("MILVUS_PASSWORD", ""),
            db_name="test_db",
            secure=False,
            timeout=30.0
        )
    
    @pytest.fixture(scope="class")
    def milvus_service(self, milvus_config):
        """Create MilvusService instance."""
        service = MilvusService(milvus_config)
        yield service
        # Cleanup happens per test
    
    @pytest.fixture
    def collection_name(self):
        """Generate unique collection name for each test."""
        return f"test_col_{uuid4().hex[:8]}"
    
    @pytest.fixture(autouse=True)
    def cleanup_collection(self, milvus_service, collection_name):
        """Cleanup collection after each test."""
        yield
        # Cleanup
        try:
            if milvus_service.collection.has_collection(collection_name):
                milvus_service.collection.drop(collection_name)
        except Exception:
            pass
    
    def test_service_connection(self, milvus_service):
        """Test connection to Milvus."""
        milvus_service.connection.ensure()
        assert milvus_service.connection.is_connected()
    
    def test_create_collection(self, milvus_service, collection_name):
        """Test creating a collection."""
        milvus_service.collection.create(
            name=collection_name,
            dimension=768,
            metric_type="IP",
            index_type="HNSW"
        )
        
        assert milvus_service.collection.has_collection(collection_name)
    
    def test_insert_and_search(self, milvus_service, collection_name):
        """Test inserting data and searching."""
        # Create collection
        milvus_service.collection.create(
            name=collection_name,
            dimension=128,
            metric_type="IP"
        )
        
        # Insert data
        data = [
            {
                "id": "1",
                "vector": [0.1] * 128,
                "text": "Test document 1",
                "metadata": {"source": "test"}
            },
            {
                "id": "2",
                "vector": [0.2] * 128,
                "text": "Test document 2",
                "metadata": {"source": "test"}
            }
        ]
        
        ids = milvus_service.data.insert(collection_name, data)
        assert len(ids) == 2
        
        # Search
        query_vector = [[0.15] * 128]
        results = milvus_service.data.search(
            collection_name=collection_name,
            query_vectors=query_vector,
            limit=2
        )
        
        assert len(results) > 0
        assert len(results[0]) > 0
    
    def test_query_by_expression(self, milvus_service, collection_name):
        """Test querying with filter expression."""
        # Create collection
        milvus_service.collection.create(
            name=collection_name,
            dimension=128
        )
        
        # Insert data
        data = [
            {
                "id": "1",
                "vector": [0.1] * 128,
                "text": "Document about AI",
                "metadata": {"category": "tech"}
            },
            {
                "id": "2",
                "vector": [0.2] * 128,
                "text": "Document about finance",
                "metadata": {"category": "finance"}
            }
        ]
        
        milvus_service.data.insert(collection_name, data)
        
        # Query with expression
        results = milvus_service.data.query(
            collection_name=collection_name,
            expr='metadata["category"] == "tech"',
            output_fields=["text", "metadata"]
        )
        
        assert len(results) > 0
    
    def test_delete_by_ids(self, milvus_service, collection_name):
        """Test deleting entities by IDs."""
        # Create and populate collection
        milvus_service.collection.create(
            name=collection_name,
            dimension=128
        )
        
        data = [
            {"id": "1", "vector": [0.1] * 128, "text": "Doc 1"},
            {"id": "2", "vector": [0.2] * 128, "text": "Doc 2"},
        ]
        
        milvus_service.data.insert(collection_name, data)
        
        # Delete one
        milvus_service.data.delete(collection_name, ids=["1"])
        
        # Verify deletion
        results = milvus_service.data.query(
            collection_name=collection_name,
            expr="id in ['1']",
            output_fields=["id"]
        )
        
        assert len(results) == 0
    
    def test_collection_stats(self, milvus_service, collection_name):
        """Test getting collection statistics."""
        milvus_service.collection.create(
            name=collection_name,
            dimension=128
        )
        
        # Insert some data
        data = [{"id": str(i), "vector": [0.1] * 128, "text": f"Doc {i}"} for i in range(10)]
        milvus_service.data.insert(collection_name, data)
        
        # Get stats
        stats = milvus_service.collection.get_stats(collection_name)
        
        assert stats is not None
        assert "row_count" in stats
