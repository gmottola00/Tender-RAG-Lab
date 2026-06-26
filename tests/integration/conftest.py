"""Integration test fixtures.

Provides a TestClient with:
- Real SQLite in-memory database (reuses test_db_engine from root conftest)
- Mocked external services (Milvus indexer, searcher, RAG pipeline)

External-service dependencies are mocked so integration tests run without
Milvus, Neo4j, or Ollama running.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker

from main import app
from src.api.deps import (
    get_db_session,
    get_embedding_client,
    get_indexer,
    get_llm_client,
    get_rag_pipeline,
    get_searcher,
)
from tests.mocks import MockEmbeddingClient, MockLLMClient
from tests.mocks.neo4j_mock import MockTenderGraphClient


# ── Shared mock fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def mock_neo4j_client() -> MockTenderGraphClient:
    """AsyncMock-based Neo4j client for all integration tests."""
    return MockTenderGraphClient()


@pytest.fixture
def mock_indexer():
    """Mock TenderMilvusIndexer (sync methods that return dicts)."""
    mock = MagicMock()
    mock.index_chunks = MagicMock(return_value={"indexed": 0, "collection": "test"})
    mock.delete_by_tender_id = MagicMock(return_value={"delete_count": 0})
    mock.delete_all = MagicMock(return_value={"delete_count": 0})
    return mock


@pytest.fixture
def mock_searcher():
    """Mock TenderSearcher (async search method)."""
    mock = MagicMock()
    mock.search = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_rag_pipeline():
    """Mock RagPipeline returning a canned answer."""
    from quaerium.rag.models import RagResponse

    mock = MagicMock()
    mock.run = MagicMock(return_value=RagResponse(answer="Mock LLM answer.", citations=[]))
    return mock


# ── Primary TestClient fixture ────────────────────────────────────────────────


@pytest_asyncio.fixture
async def api_client(
    test_db_engine: AsyncEngine,
    mock_indexer,
    mock_searcher,
    mock_rag_pipeline,
):
    """FastAPI TestClient with real SQLite DB and mocked external services.

    The DB dependency is satisfied by a real async session backed by the
    SQLite in-memory engine provided by ``test_db_engine`` from the root
    conftest. All vector/graph/LLM dependencies are mocked so the tests
    run without any external services.
    """
    session_factory = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_db():
        async with session_factory() as session:
            yield session

    embedding = MockEmbeddingClient(dimension=768)
    llm = MockLLMClient(canned_response="Mock LLM response.")

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_embedding_client] = lambda: embedding
    app.dependency_overrides[get_llm_client] = lambda: llm
    app.dependency_overrides[get_indexer] = lambda: mock_indexer
    app.dependency_overrides[get_searcher] = lambda: mock_searcher
    app.dependency_overrides[get_rag_pipeline] = lambda: mock_rag_pipeline

    yield TestClient(app)

    app.dependency_overrides.clear()
