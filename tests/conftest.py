"""Root conftest.py for pytest configuration.

This file provides shared fixtures and configuration for all tests.
Fixtures defined here are available to all test modules.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Set test environment
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "test"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Return path to test data directory."""
    return Path(__file__).parent / "fixtures" / "files"


@pytest.fixture
def sample_text() -> str:
    """Sample text for testing chunking and embedding."""
    return """
    # Introduction
    This is a test document for the RAG system.
    
    ## Section 1
    The RAG (Retrieval-Augmented Generation) system combines retrieval
    and generation to answer questions based on a knowledge base.
    
    ## Section 2
    The system uses vector embeddings to find relevant documents,
    then generates answers using a language model.
    
    # Conclusion
    This completes the test document.
    """


@pytest.fixture
def sample_chunks() -> list[dict]:
    """Sample chunks for testing indexing."""
    return [
        {
            "text": "The RAG system combines retrieval and generation.",
            "metadata": {"section": "Introduction", "page": 1},
            "id": "chunk_1",
        },
        {
            "text": "Vector embeddings are used to find relevant documents.",
            "metadata": {"section": "Section 1", "page": 2},
            "id": "chunk_2",
        },
        {
            "text": "Language models generate answers from retrieved context.",
            "metadata": {"section": "Section 2", "page": 3},
            "id": "chunk_3",
        },
    ]


@pytest.fixture
def sample_embedding() -> list[float]:
    """Sample embedding vector for testing."""
    # Return a deterministic 768-dimensional vector
    return [0.1] * 384 + [0.2] * 384


@pytest_asyncio.fixture
async def test_db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create test database engine with transaction rollback."""
    # Use in-memory SQLite for tests
    database_url = "sqlite+aiosqlite:///:memory:"
    
    engine = create_async_engine(
        database_url,
        echo=False,
        poolclass=NullPool,
    )
    
    # Create tables
    from src.infra.database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session with automatic rollback.
    
    Each test gets a fresh session that rolls back at the end,
    ensuring test isolation.
    """
    async_session = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        async with session.begin():
            yield session
            # Rollback happens automatically on exit


@pytest.fixture
def random_collection_name() -> str:
    """Generate random collection name for Milvus tests."""
    return f"test_collection_{uuid4().hex[:8]}"


# Test result collection for debugging
def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test (no external dependencies)"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark tests based on path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
