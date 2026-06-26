"""Integration tests for TenderGraphClient against a real Neo4j instance.

Skipped automatically when NEO4J_URI is not set in the environment.
Run with: NEO4J_URI=bolt://localhost:7687 uv run pytest tests/integration/infra/test_neo4j_client.py

Tests verify:
- Schema creation (constraints and indexes)
- Tender CRUD round-trip (create → get → delete)
- Requirement creation and retrieval
- Cascade delete (no orphan nodes remain)
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("NEO4J_TEST_ENABLED"),
    reason=(
        "Neo4j integration tests disabled "
        "(set NEO4J_TEST_ENABLED=1 with a running Neo4j instance)"
    ),
)


@pytest.fixture(scope="module")
async def graph_client():
    """Create a real TenderGraphClient connected to test Neo4j."""
    from src.infra.graph.tender_client import TenderGraphClient

    uri = os.environ["NEO4J_URI"]
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    database = os.getenv("NEO4J_DATABASE", "neo4j")

    client = TenderGraphClient(uri=uri, user=user, password=password, database=database)
    yield client
    await client.close()


@pytest.fixture
def tender_code() -> str:
    """Unique tender code for each test to avoid conflicts."""
    return f"TEST-{uuid4().hex[:8].upper()}"


@pytest.mark.neo4j
@pytest.mark.asyncio
async def test_verify_connectivity(graph_client):
    """Client can connect and ping the Neo4j instance."""
    result = await graph_client.verify_connectivity()
    assert result is True


@pytest.mark.neo4j
@pytest.mark.asyncio
async def test_create_tender_schema(graph_client):
    """create_tender_schema() runs without error on a live Neo4j instance."""
    # Should not raise even if constraints already exist
    await graph_client.create_tender_schema()


@pytest.mark.neo4j
@pytest.mark.asyncio
async def test_create_and_get_tender_round_trip(graph_client, tender_code):
    """create_tender() → get_tender_by_code() round-trip returns correct data."""
    await graph_client.create_tender(
        code=tender_code,
        title="Integration Test Tender",
        cpv_code="72000000",
        base_amount=100000.0,
        buyer_name="Comune di Test",
        publication_date="2026-01-01",
    )

    result = await graph_client.get_tender_by_code(tender_code)

    assert result is not None
    assert result["code"] == tender_code
    assert result["buyer_name"] == "Comune di Test"

    # Cleanup
    await graph_client.delete_tender(tender_code)


@pytest.mark.neo4j
@pytest.mark.asyncio
async def test_add_requirement_and_retrieve(graph_client, tender_code):
    """add_requirement() → get_requirements_for_tender() returns correct data."""
    # Create tender first
    await graph_client.create_tender(
        code=tender_code,
        title="Requirement Test",
        cpv_code="72000000",
        base_amount=50000.0,
        buyer_name="Ente Test",
        publication_date="2026-01-01",
    )

    # Add a mandatory requirement
    req_id = f"req-{uuid4().hex[:8]}"
    await graph_client.add_requirement(
        requirement_id=req_id,
        requirement_type="tecnico",
        description="Certificazione ISO 9001 obbligatoria pena esclusione",
        mandatory=True,
        tender_code=tender_code,
    )

    # Retrieve
    requirements = await graph_client.get_requirements_for_tender(
        tender_code=tender_code,
        mandatory_only=True,
    )

    assert len(requirements) >= 1
    req = next(r for r in requirements if r["requirement_id"] == req_id)
    assert req["mandatory"] is True
    assert req["type"] == "tecnico"

    # Cleanup
    await graph_client.delete_tender(tender_code)


@pytest.mark.neo4j
@pytest.mark.asyncio
async def test_delete_tender_removes_all_nodes(graph_client, tender_code):
    """delete_tender() removes tender and all related nodes (no orphans)."""
    # Create tender with related entities
    await graph_client.create_tender(
        code=tender_code,
        title="Delete Test",
        cpv_code="72000000",
        base_amount=10000.0,
        buyer_name="Test Buyer",
        publication_date="2026-01-01",
    )
    await graph_client.add_requirement(
        requirement_id=f"req-{uuid4().hex[:8]}",
        requirement_type="admin",
        description="Requisito di test",
        mandatory=False,
        tender_code=tender_code,
    )

    # Delete
    deleted = await graph_client.delete_tender(tender_code)
    assert deleted is True

    # Verify tender is gone
    result = await graph_client.get_tender_by_code(tender_code)
    assert result is None

    # Verify no orphan requirements remain
    orphan_query = """
    MATCH (r:Requirement)
    WHERE NOT EXISTS { MATCH ()-[:HAS_REQUIREMENT]->(r) }
    RETURN count(r) as orphan_count
    """
    results = await graph_client.execute_query(orphan_query, {})
    orphan_count = results[0]["orphan_count"] if results else 0
    assert orphan_count == 0, f"Found {orphan_count} orphan Requirement nodes"
