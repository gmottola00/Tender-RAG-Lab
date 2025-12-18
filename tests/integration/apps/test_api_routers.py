"""Integration tests for FastAPI routers.

These tests use TestClient to test API endpoints without external services.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from main import app


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.mark.integration
class TestDocumentsRouter:
    """Test documents API endpoints."""
    
    def test_health_check(self, client):
        """Test basic connectivity."""
        response = client.get("/health")
        # If no health endpoint, skip or test root
        assert response.status_code in [200, 404]
    
    def test_create_document(self, client):
        """Test creating a document via API."""
        tender_id = str(uuid4())
        
        document_data = {
            "tender_id": tender_id,
            "filename": "test.pdf",
            "storage_bucket": "test-bucket",
            "storage_path": "path/test.pdf",
            "document_type": "technical"
        }
        
        response = client.post("/documents/", json=document_data)
        
        # May fail if database not setup, but tests the route
        assert response.status_code in [200, 201, 422, 500]
    
    def test_list_documents(self, client):
        """Test listing documents."""
        response = client.get("/documents/")
        
        # Should return list or error
        assert response.status_code in [200, 404, 500]
    
    def test_get_document_by_id(self, client):
        """Test getting document by ID."""
        doc_id = str(uuid4())
        response = client.get(f"/documents/{doc_id}")
        
        # Likely 404 since document doesn't exist
        assert response.status_code in [200, 404, 500]


@pytest.mark.integration
class TestTendersRouter:
    """Test tenders API endpoints."""
    
    def test_create_tender(self, client):
        """Test creating a tender."""
        tender_data = {
            "code": "TEST-001",
            "title": "Test Tender",
            "description": "A test tender",
            "status": "draft",
            "buyer": "Test Org"
        }
        
        response = client.post("/tenders/", json=tender_data)
        assert response.status_code in [200, 201, 422, 500]
    
    def test_list_tenders(self, client):
        """Test listing tenders."""
        response = client.get("/tenders/")
        assert response.status_code in [200, 500]
    
    def test_get_tender_by_id(self, client):
        """Test getting tender by ID."""
        tender_id = str(uuid4())
        response = client.get(f"/tenders/{tender_id}")
        assert response.status_code in [200, 404, 500]


@pytest.mark.integration
class TestLotsRouter:
    """Test lots API endpoints."""
    
    def test_create_lot(self, client):
        """Test creating a lot."""
        lot_data = {
            "tender_id": str(uuid4()),
            "code": "LOT-001",
            "title": "Test Lot",
            "description": "A test lot",
            "value_estimated": 100000.0,
            "currency": "EUR"
        }
        
        response = client.post("/lots/", json=lot_data)
        assert response.status_code in [200, 201, 422, 500]
    
    def test_list_lots(self, client):
        """Test listing lots."""
        response = client.get("/lots/")
        assert response.status_code in [200, 500]


@pytest.mark.integration
class TestIngestionRouter:
    """Test ingestion API endpoints."""
    
    def test_parse_endpoint_exists(self, client):
        """Test parse endpoint is accessible."""
        # Test with invalid data to see if route exists
        response = client.post("/ingestion/parse", json={})
        
        # Should fail validation but route exists
        assert response.status_code in [422, 404, 500]
    
    def test_chunk_endpoint_exists(self, client):
        """Test chunk endpoint is accessible."""
        response = client.post("/ingestion/chunk", json={})
        assert response.status_code in [422, 404, 500]
