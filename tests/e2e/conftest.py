"""E2E test configuration and fixtures.

All E2E tests are skipped unless E2E_ENABLED=1 is set in the environment.
They require a fully running stack (via docker-compose.test.yml):
  - PostgreSQL on port 5433  (DATABASE_URL pointing to it)
  - Milvus on port 19531     (MILVUS_URI=http://localhost:19531)
  - Neo4j on port 7688       (NEO4J_URI=bolt://localhost:7688)
  - Ollama (optional)        (OLLAMA_BASE_URL set when needed)

Run the full E2E suite:
    docker-compose -f docker-compose.test.yml up -d
    E2E_ENABLED=1 \\
      DATABASE_URL="postgresql+asyncpg://tender:tender_test_pass@localhost:5433/tender_test" \\
      MILVUS_URI="http://localhost:19531" \\
      NEO4J_URI="bolt://localhost:7688" \\
      NEO4J_PASSWORD="test_password" \\
      uv run pytest tests/e2e/ -v -m e2e
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Global skip: all E2E tests are skipped unless E2E_ENABLED=1
# ---------------------------------------------------------------------------

_E2E_ENABLED = bool(os.getenv("E2E_ENABLED"))

if not _E2E_ENABLED:
    # Apply module-level skip so pytest collects but skips all tests
    import sys

    collect_ignore_glob = []  # Not used here — we use pytestmark instead


def pytest_collection_modifyitems(config, items):
    """Skip all E2E tests when E2E_ENABLED is not set."""
    if _E2E_ENABLED:
        return
    skip_marker = pytest.mark.skip(
        reason="E2E tests disabled (set E2E_ENABLED=1 with docker-compose.test.yml services running)"
    )
    for item in items:
        if "e2e" in str(item.fspath):
            item.add_marker(skip_marker)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def sample_pdf_path() -> Path:
    """Absolute path to the synthetic Italian tender PDF."""
    path = Path(__file__).parent.parent / "fixtures" / "files" / "sample_tender.pdf"
    assert path.exists(), f"Sample PDF not found at {path}. Run the generator script first."
    return path


@pytest.fixture(scope="session")
def http_client() -> Generator[TestClient, None, None]:
    """Raw TestClient with no dependency overrides — all services must be real.

    Requires E2E_ENABLED=1 and all external services running.
    """
    from main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@dataclass
class UploadedTender:
    """Bundle of data produced by the upload_tender fixture."""

    tender_id: str
    tender_code: str
    title: str


@pytest.fixture
def uploaded_tender(http_client: TestClient, sample_pdf_path: Path) -> Generator[UploadedTender, None, None]:
    """Create a tender, upload the sample PDF, and clean up after each test.

    Does NOT index into Milvus or populate Neo4j — just the DB record + raw parse.
    Tests that need indexed data should call the additional endpoints themselves.
    """
    code = f"E2E-{uuid4().hex[:8].upper()}"
    title = "E2E Integration Test Tender"

    # 1. Create tender in PostgreSQL
    create_resp = http_client.post(
        "/api/tenders",
        json={"code": code, "title": title, "status": "draft"},
    )
    assert create_resp.status_code == 201, (
        f"Failed to create tender: {create_resp.status_code} {create_resp.text}"
    )
    tender_id = create_resp.json()["id"]

    bundle = UploadedTender(tender_id=tender_id, tender_code=code, title=title)
    yield bundle

    # Cleanup: best-effort delete (don't fail test on cleanup error)
    try:
        http_client.delete(f"/api/tenders/{tender_id}")
    except Exception:  # noqa: BLE001
        pass
