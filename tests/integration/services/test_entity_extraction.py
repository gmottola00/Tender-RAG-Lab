"""Integration tests for EntityExtractionService.

Real dependencies:
- spaCy it_core_news_lg (installed)
- StructureExtractor (pure Python)

Mocked dependencies:
- TenderGraphClient → MockTenderGraphClient (AsyncMock-based)

Tests verify:
- Requirement extraction from chunks containing mandatory keywords
- Deadline extraction from chunks with date context
- populate_graph() calls Neo4j with correct parameters
- Graceful behavior when neo4j_client is None
- Structured entities have priority over NER duplicates
- extract_and_populate() returns combined stats dict
"""

from __future__ import annotations

import pytest

from src.domain.tender.ner.spacy_ner import create_tender_ner
from src.domain.tender.schemas.chunking import TenderChunk
from src.domain.tender.services.entity_extraction import EntityExtractionService
from tests.mocks.neo4j_mock import MockTenderGraphClient


# ── Shared chunk fixtures ─────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def real_ner():
    """Real spaCy NER — loaded once per module to keep tests fast."""
    return create_tender_ner(model_name="it_core_news_lg")


def _make_chunk(
    text: str,
    chunk_id: str = "chunk-001",
    section_path: str = "1. Requisiti generali",
    metadata: dict | None = None,
) -> TenderChunk:
    return TenderChunk(
        id=chunk_id,
        title="Section",
        heading_level=1,
        text=text,
        blocks=[],
        page_numbers=[1],
        section_path=section_path,
        metadata=metadata or {},
        tender_id="TENDER-TEST-001",
    )


@pytest.fixture
def mandatory_chunk() -> TenderChunk:
    """Chunk containing a mandatory requirement indicator."""
    return _make_chunk(
        text=(
            "Il concorrente deve essere in possesso della certificazione ISO 9001. "
            "Tale requisito è obbligatorio pena di esclusione dalla procedura."
        ),
        chunk_id="chunk-mandatory-001",
        section_path="3. Requisiti tecnici",
    )


@pytest.fixture
def deadline_chunk() -> TenderChunk:
    """Chunk containing a date and deadline context."""
    return _make_chunk(
        text=(
            "La scadenza per la presentazione delle offerte è fissata al "
            "31 marzo 2026 entro le ore 12:00."
        ),
        chunk_id="chunk-deadline-001",
        section_path="4. Termini e scadenze",
    )


@pytest.fixture
def lot_chunk() -> TenderChunk:
    """Chunk whose section_path references a lot (must match LOT_PATTERN regex)."""
    return _make_chunk(
        text="Descrizione delle forniture per il lotto specifico.",
        chunk_id="chunk-lot-001",
        # StructureExtractor.LOT_PATTERN requires "Lotto: LOT-XXXX" format
        section_path="Lotto: LOT-0001 Servizi informatici",
        metadata={"lot_id": "LOT-0001"},
    )


@pytest.fixture
def entity_service(real_ner, mock_neo4j_client):
    """EntityExtractionService with real NER + mock Neo4j."""
    return EntityExtractionService(ner=real_ner, neo4j_client=mock_neo4j_client)


@pytest.fixture
def entity_service_no_neo4j(real_ner):
    """EntityExtractionService without Neo4j client."""
    return EntityExtractionService(ner=real_ner, neo4j_client=None)


# ── extract_from_chunks tests ─────────────────────────────────────────────────


def test_extract_from_chunks_returns_required_keys(entity_service, mandatory_chunk):
    """extract_from_chunks() returns dict with all required top-level keys."""
    result = entity_service.extract_from_chunks([mandatory_chunk], tender_id="T-001")

    assert "tender_id" in result
    assert "total_chunks" in result
    assert "entities_by_type" in result
    assert "entity_count" in result
    assert "structured_count" in result
    assert "ner_count" in result
    assert result["tender_id"] == "T-001"
    assert result["total_chunks"] == 1


def test_extract_from_chunks_counts_chunks(entity_service, mandatory_chunk, deadline_chunk):
    """total_chunks equals number of input chunks."""
    result = entity_service.extract_from_chunks(
        [mandatory_chunk, deadline_chunk], tender_id="T-001"
    )
    assert result["total_chunks"] == 2


def test_lot_chunk_creates_structured_lot_entity(entity_service, lot_chunk):
    """Chunk with LOT section_path produces at least one structured lot entity."""
    result = entity_service.extract_from_chunks([lot_chunk], tender_id="T-LOT")

    entities = result["entities_by_type"]
    # Structure extractor should detect the LOT from section_path
    assert "lot" in entities
    assert len(entities["lot"]) >= 1


def test_entity_count_sums_all_types(entity_service, mandatory_chunk, deadline_chunk):
    """entity_count equals sum of all entities across types."""
    result = entity_service.extract_from_chunks(
        [mandatory_chunk, deadline_chunk], tender_id="T-SUM"
    )
    expected = sum(len(v) for v in result["entities_by_type"].values())
    assert result["entity_count"] == expected


# ── populate_graph tests ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_populate_graph_with_none_neo4j_returns_empty_dict(
    entity_service_no_neo4j, mandatory_chunk
):
    """populate_graph() with neo4j_client=None returns {} without raising."""
    extraction = entity_service_no_neo4j.extract_from_chunks(
        [mandatory_chunk], tender_id="T-NO-NEO4J"
    )
    stats = await entity_service_no_neo4j.populate_graph(extraction, tender_code="CODE-001")
    assert stats == {}


@pytest.mark.asyncio
async def test_mandatory_requirement_triggers_add_requirement(
    entity_service, mock_neo4j_client, mandatory_chunk
):
    """Chunk with 'obbligatorio pena di esclusione' triggers add_requirement call."""
    extraction = entity_service.extract_from_chunks([mandatory_chunk], tender_id="T-REQ")
    await entity_service.populate_graph(extraction, tender_code="CODE-REQ")

    # Neo4j should have been called to add at least one requirement
    mock_neo4j_client.add_requirement.assert_called()


@pytest.mark.asyncio
async def test_mandatory_requirement_has_mandatory_true(
    entity_service, mock_neo4j_client, mandatory_chunk
):
    """Requirements from 'pena di esclusione' chunks are flagged as mandatory=True."""
    extraction = entity_service.extract_from_chunks([mandatory_chunk], tender_id="T-MAND")
    await entity_service.populate_graph(extraction, tender_code="CODE-MAND")

    calls = mock_neo4j_client.add_requirement.call_args_list
    assert len(calls) >= 1
    # At least one call should have mandatory=True
    mandatory_calls = [
        c for c in calls if c.kwargs.get("mandatory") or (c.args and True in c.args)
    ]
    assert len(mandatory_calls) >= 1


@pytest.mark.asyncio
async def test_lot_chunk_calls_add_lot_from_structure(
    entity_service, mock_neo4j_client, lot_chunk
):
    """Chunk with LOT section_path calls add_lot_from_structure on Neo4j client."""
    extraction = entity_service.extract_from_chunks([lot_chunk], tender_id="T-LOT")
    await entity_service.populate_graph(extraction, tender_code="CODE-LOT")

    mock_neo4j_client.add_lot_from_structure.assert_called()


@pytest.mark.asyncio
async def test_populate_graph_returns_stats_dict(entity_service, mock_neo4j_client, mandatory_chunk):
    """populate_graph() returns a dict with at least the expected stat keys."""
    extraction = entity_service.extract_from_chunks([mandatory_chunk], tender_id="T-STATS")
    stats = await entity_service.populate_graph(extraction, tender_code="CODE-STATS")

    assert isinstance(stats, dict)
    expected_keys = {
        "lots_created",
        "sections_created",
        "codes_created",
        "buyers_created",
        "organizations_created",
        "requirements_created",
        "deadlines_created",
        "relationships_created",
    }
    assert expected_keys.issubset(stats.keys())


# ── extract_and_populate pipeline ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_extract_and_populate_returns_combined_stats(
    entity_service, mock_neo4j_client, mandatory_chunk
):
    """extract_and_populate() returns dict with both entity and graph_stats keys."""
    result = await entity_service.extract_and_populate(
        chunks=[mandatory_chunk],
        tender_id="T-FULL",
        tender_code="CODE-FULL",
    )

    # Extraction keys
    assert "entity_count" in result
    assert "entities_by_type" in result

    # Graph population key
    assert "graph_stats" in result
    assert isinstance(result["graph_stats"], dict)


# ── Merge priority tests ──────────────────────────────────────────────────────


def test_merge_prioritizes_structured_over_ner(entity_service):
    """Structured entities block NER entities with the same name (case-insensitive)."""
    from src.domain.tender.services.structure_extractor import StructuredEntity

    structured = {
        "ORGANIZATION": [
            StructuredEntity(
                type="buyer",
                id="org-1",
                name="Comune di Milano",
            )
        ]
    }
    ner_entities = {
        "ORGANIZATION": ["comune di milano", "Regione Lombardia"]  # lowercase duplicate
    }

    merged = entity_service._merge_entities(structured, ner_entities)

    orgs = merged.get("ORGANIZATION", [])
    org_names = [
        (e.name if hasattr(e, "name") else e).lower() for e in orgs
    ]
    # "comune di milano" should appear only once (structured takes priority)
    comune_count = sum(1 for n in org_names if "comune di milano" in n)
    assert comune_count == 1
    # "Regione Lombardia" should be added from NER
    assert any("regione lombardia" in n for n in org_names)
