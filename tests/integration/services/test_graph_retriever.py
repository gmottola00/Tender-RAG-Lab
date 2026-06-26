"""Integration tests for GraphEnrichedRetriever.

All dependencies are mocked (Neo4j + vector searcher).

Tests verify:
- ValueError raised when vector_searcher is None
- use_graph_enrichment=False → Neo4j not called
- Each result has 'graph_context' with three lists (requirements, deadlines, orgs)
- Empty chunk IDs return empty context dict
- Neo4j failure causes graceful degradation (empty context, no exception)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.tender.services.graph_retriever import GraphEnrichedRetriever
from tests.mocks.neo4j_mock import MockTenderGraphClient


# ── Shared fixtures ───────────────────────────────────────────────────────────


def _make_mock_vector_searcher(results: list | None = None):
    """Create a mock async vector searcher."""
    mock = MagicMock()
    mock.search = AsyncMock(return_value=results or [])
    return mock


def _make_vector_results(n: int = 3) -> list[dict]:
    """Generate n mock vector search result dicts."""
    return [
        {
            "id": f"chunk-{i:03d}",
            "chunk_id": f"chunk-{i:03d}",
            "text": f"Chunk text {i}",
            "score": 0.9 - i * 0.05,
            "metadata": {"page": i},
        }
        for i in range(n)
    ]


@pytest.fixture
def neo4j_client() -> MockTenderGraphClient:
    """Fresh MockTenderGraphClient for each test."""
    return MockTenderGraphClient()


@pytest.fixture
def retriever(neo4j_client) -> GraphEnrichedRetriever:
    """GraphEnrichedRetriever with mock Neo4j but no vector searcher."""
    return GraphEnrichedRetriever(vector_searcher=None, neo4j_client=neo4j_client)


# ── search_with_graph_context ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_without_vector_searcher_raises_value_error(retriever):
    """search_with_graph_context() without vector_searcher → ValueError."""
    with pytest.raises(ValueError, match="Vector searcher not configured"):
        await retriever.search_with_graph_context(
            query="test", tender_code="CODE-001"
        )


@pytest.mark.asyncio
async def test_search_with_graph_enrichment_disabled_skips_neo4j(neo4j_client):
    """use_graph_enrichment=False → Neo4j execute_query is never called."""
    vector_results = _make_vector_results(2)
    searcher = _make_mock_vector_searcher(results=vector_results)

    retriever = GraphEnrichedRetriever(
        vector_searcher=searcher,
        neo4j_client=neo4j_client,
    )
    results = await retriever.search_with_graph_context(
        query="test",
        tender_code="CODE-001",
        use_graph_enrichment=False,
    )

    # Should return raw vector results unchanged
    assert results == vector_results
    neo4j_client.execute_query.assert_not_called()


@pytest.mark.asyncio
async def test_search_enriched_results_have_graph_context(neo4j_client):
    """Enriched results contain 'graph_context' key with three lists."""
    vector_results = _make_vector_results(3)
    searcher = _make_mock_vector_searcher(results=vector_results)

    # Neo4j returns empty records (OPTIONAL MATCH → nulls)
    neo4j_client.execute_query = AsyncMock(
        return_value=[
            {
                "chunk_id": f"chunk-{i:03d}",
                "requirements": [],
                "deadlines": [],
                "organizations": [],
            }
            for i in range(3)
        ]
    )

    retriever = GraphEnrichedRetriever(
        vector_searcher=searcher,
        neo4j_client=neo4j_client,
    )
    results = await retriever.search_with_graph_context(
        query="requisiti obbligatori",
        tender_code="CODE-001",
        use_graph_enrichment=True,
    )

    assert len(results) == 3
    for r in results:
        assert "graph_context" in r
        ctx = r["graph_context"]
        assert "requirements" in ctx
        assert "deadlines" in ctx
        assert "organizations" in ctx
        assert isinstance(ctx["requirements"], list)
        assert isinstance(ctx["deadlines"], list)
        assert isinstance(ctx["organizations"], list)


@pytest.mark.asyncio
async def test_search_enriched_results_contain_graph_entities(neo4j_client):
    """Requirements/deadlines from Neo4j appear in matching chunk's graph_context."""
    vector_results = [
        {"id": "chunk-A", "chunk_id": "chunk-A", "text": "ISO cert required", "score": 0.9}
    ]
    searcher = _make_mock_vector_searcher(results=vector_results)

    neo4j_client.execute_query = AsyncMock(
        return_value=[
            {
                "chunk_id": "chunk-A",
                "requirements": [
                    {"id": "req-1", "description": "ISO 9001 obbligatoria", "mandatory": True, "type": "extracted"}
                ],
                "deadlines": [],
                "organizations": [{"name": "Comune di Milano", "role": "buyer"}],
            }
        ]
    )

    retriever = GraphEnrichedRetriever(
        vector_searcher=searcher,
        neo4j_client=neo4j_client,
    )
    results = await retriever.search_with_graph_context(
        query="certificazioni", tender_code="CODE-001"
    )

    assert len(results) == 1
    ctx = results[0]["graph_context"]
    assert len(ctx["requirements"]) == 1
    assert ctx["requirements"][0]["mandatory"] is True
    assert len(ctx["organizations"]) == 1


@pytest.mark.asyncio
async def test_neo4j_failure_causes_graceful_degradation(neo4j_client):
    """If Neo4j raises an exception, results still return with empty graph_context."""
    vector_results = _make_vector_results(2)
    searcher = _make_mock_vector_searcher(results=vector_results)

    neo4j_client.execute_query = AsyncMock(side_effect=ConnectionError("Neo4j down"))

    retriever = GraphEnrichedRetriever(
        vector_searcher=searcher,
        neo4j_client=neo4j_client,
    )
    # Should NOT raise even though Neo4j fails
    results = await retriever.search_with_graph_context(
        query="test", tender_code="CODE-001"
    )

    assert len(results) == 2
    for r in results:
        ctx = r["graph_context"]
        assert ctx == {"requirements": [], "deadlines": [], "organizations": []}


# ── _get_graph_context_for_chunks ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_graph_context_for_empty_chunk_list(retriever):
    """_get_graph_context_for_chunks([]) → empty dict without calling Neo4j."""
    result = await retriever._get_graph_context_for_chunks([], "CODE-001")
    assert result == {}
    retriever.neo4j_client.execute_query.assert_not_called()


# ── search_requirements (graph-first) ────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_requirements_returns_list(neo4j_client):
    """search_requirements() returns the Neo4j response list."""
    neo4j_client.get_requirements_for_tender = AsyncMock(
        return_value=[
            {
                "requirement_id": "req-1",
                "type": "extracted",
                "description": "ISO 9001",
                "mandatory": True,
                "chunk_ids": ["c-1"],
            }
        ]
    )
    retriever = GraphEnrichedRetriever(neo4j_client=neo4j_client)
    results = await retriever.search_requirements("CODE-001", mandatory_only=True)

    assert len(results) == 1
    assert results[0]["mandatory"] is True


@pytest.mark.asyncio
async def test_search_requirements_neo4j_failure_returns_empty(neo4j_client):
    """search_requirements() returns [] on Neo4j failure (graceful degradation)."""
    neo4j_client.get_requirements_for_tender = AsyncMock(
        side_effect=ConnectionError("Neo4j down")
    )
    retriever = GraphEnrichedRetriever(neo4j_client=neo4j_client)
    results = await retriever.search_requirements("CODE-001")

    assert results == []
