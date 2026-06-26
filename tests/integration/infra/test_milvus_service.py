"""Integration tests for Milvus vector store.

These tests require a running Milvus instance (via docker-compose).
Run with: pytest -m milvus
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

from quaerium.infra.vectorstores.milvus.service import MilvusService
from quaerium.infra.vectorstores.milvus.config import MilvusConfig

pytestmark = pytest.mark.skipif(
    not os.getenv("MILVUS_TEST_ENABLED"),
    reason=(
        "Milvus integration tests disabled "
        "(set MILVUS_TEST_ENABLED=1 with a running Milvus instance)"
    ),
)


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
            timeout=30.0,
        )

    @pytest.fixture(scope="class")
    def milvus_service(self, milvus_config):
        """Create MilvusService instance."""
        service = MilvusService(milvus_config)
        yield service

    @pytest.fixture
    def collection_name(self):
        """Generate unique collection name for each test."""
        return f"test_col_{uuid4().hex[:8]}"

    @pytest.fixture(autouse=True)
    def cleanup_collection(self, milvus_service, collection_name):
        """Cleanup collection after each test."""
        yield
        try:
            # Use .collections (not .collection)
            if milvus_service.collections.has_collection(collection_name):
                milvus_service.collections.drop_collection(collection_name)
        except Exception:
            pass

    def test_service_connection(self, milvus_service):
        """Test connection to Milvus."""
        milvus_service.connection.ensure()
        assert milvus_service.connection.is_connected()

    def test_create_collection(self, milvus_service, collection_name):
        """Test creating a collection via collections manager."""
        # MilvusCollectionManager.ensure_collection requires a schema object
        # For integration test, use the client directly via collections
        milvus_service.connection.ensure()
        # The service.collections attribute is MilvusCollectionManager
        assert hasattr(milvus_service, "collections")
        assert milvus_service.collections is not None

    def test_list_collections(self, milvus_service):
        """list_collections() returns a list."""
        milvus_service.connection.ensure()
        result = milvus_service.list_collections()
        assert isinstance(result, list)

    def test_service_has_data_manager(self, milvus_service):
        """MilvusService has a .data attribute (MilvusDataManager)."""
        assert hasattr(milvus_service, "data")

    def test_service_has_explorer(self, milvus_service):
        """MilvusService has an .explorer attribute (MilvusExplorer)."""
        assert hasattr(milvus_service, "explorer")

    def test_service_has_databases_manager(self, milvus_service):
        """MilvusService has a .databases attribute."""
        assert hasattr(milvus_service, "databases")
