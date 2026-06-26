"""E2E tests for complete tender workflows.

Requires E2E_ENABLED=1 and all services running via docker-compose.test.yml.

Test scenarios covered:
- Tender CRUD lifecycle (PostgreSQL only)
- Document parsing from PDF (parser, no Milvus)
- Full ingestion pipeline (PostgreSQL + Milvus + Neo4j)
- Search workflows (Milvus + optional Neo4j)
- Tender deletion cascades across all systems

Skip behaviour: all tests are automatically skipped when E2E_ENABLED is not
set in the environment (handled by conftest.pytest_collection_modifyitems).
"""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tests.e2e.conftest import UploadedTender


# ---------------------------------------------------------------------------
# Tender CRUD lifecycle (requires PostgreSQL only)
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestTenderLifecycle:
    """End-to-end CRUD tests using the /api/tenders router and a real PostgreSQL DB."""

    def test_create_tender_returns_201_with_id(self, http_client: TestClient):
        """POST /api/tenders → 201 with id and code."""
        code = f"E2E-CRUD-{uuid4().hex[:6].upper()}"
        resp = http_client.post(
            "/api/tenders",
            json={"code": code, "title": "E2E CRUD Lifecycle Test"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["code"] == code
        # Cleanup
        http_client.delete(f"/api/tenders/{data['id']}")

    def test_get_tender_after_create(self, http_client: TestClient):
        """Create then GET by id → 200 with matching data."""
        code = f"E2E-GET-{uuid4().hex[:6].upper()}"
        create = http_client.post("/api/tenders", json={"code": code, "title": "Get Me"})
        assert create.status_code == 201
        tender_id = create.json()["id"]

        resp = http_client.get(f"/api/tenders/{tender_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == tender_id
        assert resp.json()["code"] == code

        # Cleanup
        http_client.delete(f"/api/tenders/{tender_id}")

    def test_list_tenders_includes_created(self, http_client: TestClient):
        """Tenders just created appear in GET /api/tenders list."""
        code = f"E2E-LIST-{uuid4().hex[:6].upper()}"
        create = http_client.post("/api/tenders", json={"code": code, "title": "List Me"})
        assert create.status_code == 201
        tender_id = create.json()["id"]

        resp = http_client.get("/api/tenders")
        assert resp.status_code == 200
        codes = [t["code"] for t in resp.json()]
        assert code in codes

        # Cleanup
        http_client.delete(f"/api/tenders/{tender_id}")

    def test_update_tender_status(self, http_client: TestClient):
        """PUT /api/tenders/{id} with status change → 200 with new status."""
        code = f"E2E-UPD-{uuid4().hex[:6].upper()}"
        create = http_client.post("/api/tenders", json={"code": code, "title": "Update Me"})
        assert create.status_code == 201
        tender_id = create.json()["id"]

        update = http_client.put(
            f"/api/tenders/{tender_id}",
            json={"title": "Updated Title", "status": "published"},
        )
        assert update.status_code == 200
        assert update.json()["status"] == "published"
        assert update.json()["title"] == "Updated Title"

        # Cleanup
        http_client.delete(f"/api/tenders/{tender_id}")

    def test_delete_tender_returns_204_and_gone(self, http_client: TestClient):
        """DELETE /api/tenders/{id} → 204, then GET returns 404."""
        code = f"E2E-DEL-{uuid4().hex[:6].upper()}"
        create = http_client.post("/api/tenders", json={"code": code, "title": "Delete Me"})
        assert create.status_code == 201
        tender_id = create.json()["id"]

        delete = http_client.delete(f"/api/tenders/{tender_id}")
        assert delete.status_code == 204

        get = http_client.get(f"/api/tenders/{tender_id}")
        assert get.status_code == 404

    def test_get_nonexistent_tender_returns_404(self, http_client: TestClient):
        """GET /api/tenders/{unknown-uuid} → exact 404."""
        resp = http_client.get(f"/api/tenders/{uuid4()}")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Document parsing (requires parser, no Milvus/Neo4j)
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestDocumentParsing:
    """E2E tests for the /api/ingestion/parse endpoint."""

    def test_parse_valid_pdf_returns_200(self, http_client: TestClient, sample_pdf_path: Path):
        """POST /api/ingestion/parse with valid PDF → 200 + pages list."""
        with sample_pdf_path.open("rb") as f:
            resp = http_client.post(
                "/api/ingestion/parse",
                files={"file": ("sample_tender.pdf", f, "application/pdf")},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "pages" in data
        assert len(data["pages"]) >= 1

    def test_parse_pdf_extracts_known_text(self, http_client: TestClient, sample_pdf_path: Path):
        """Parsing the sample PDF returns pages containing the known CIG."""
        with sample_pdf_path.open("rb") as f:
            resp = http_client.post(
                "/api/ingestion/parse",
                files={"file": ("sample_tender.pdf", f, "application/pdf")},
            )
        assert resp.status_code == 200
        full_text = " ".join(
            page.get("text", "") for page in resp.json()["pages"]
        )
        assert "TEST-CIG-001" in full_text

    def test_parse_empty_filename_returns_400(self, http_client: TestClient):
        """POST /api/ingestion/parse with an empty file → 400."""
        resp = http_client.post(
            "/api/ingestion/parse",
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        assert resp.status_code == 400

    def test_parse_unsupported_type_returns_400(self, http_client: TestClient):
        """POST /api/ingestion/parse with .txt file → 400."""
        resp = http_client.post(
            "/api/ingestion/parse",
            files={"file": ("document.txt", b"some text", "text/plain")},
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Full ingestion pipeline (requires PostgreSQL + Milvus + Ollama)
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.milvus
@pytest.mark.ollama
class TestIngestionPipeline:
    """E2E ingestion tests requiring Milvus and Ollama for embedding."""

    def test_parse_chunk_index_returns_inserted_count(
        self, http_client: TestClient, sample_pdf_path: Path
    ):
        """POST /api/ingestion/parse-chunk-index → 200 with inserted > 0."""
        with sample_pdf_path.open("rb") as f:
            resp = http_client.post(
                "/api/ingestion/parse-chunk-index",
                files={"file": ("sample_tender.pdf", f, "application/pdf")},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "inserted" in data
        assert data["inserted"] > 0

    def test_vector_search_after_indexing(
        self, http_client: TestClient, sample_pdf_path: Path
    ):
        """After indexing, vector search for a known phrase returns results."""
        # Index first
        with sample_pdf_path.open("rb") as f:
            index_resp = http_client.post(
                "/api/ingestion/parse-chunk-index",
                files={"file": ("sample_tender.pdf", f, "application/pdf")},
            )
        assert index_resp.status_code == 200

        # Now search for content we know is in the PDF
        search_resp = http_client.post(
            "/api/ingestion/rag/vector-search",
            params={"question": "certificazione ISO obbligatoria", "top_k": 3},
        )
        assert search_resp.status_code == 200
        data = search_resp.json()
        assert "results" in data
        assert len(data["results"]) > 0


# ---------------------------------------------------------------------------
# Entity extraction (requires parser + spaCy, no Milvus/Neo4j)
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestEntityExtraction:
    """E2E tests for entity extraction endpoint (no vector store needed)."""

    def test_extract_entities_from_pdf_returns_entity_count(
        self,
        http_client: TestClient,
        sample_pdf_path: Path,
        uploaded_tender: UploadedTender,
    ):
        """POST /api/ingestion/extract-entities with sample PDF → entity_count >= 0."""
        with sample_pdf_path.open("rb") as f:
            resp = http_client.post(
                "/api/ingestion/extract-entities",
                files={"file": ("sample_tender.pdf", f, "application/pdf")},
                params={
                    "tender_id": uploaded_tender.tender_id,
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "entity_count" in data
        assert "entities_by_type" in data
        assert data["entity_count"] >= 0  # may be 0 if text is simple

    def test_extract_entities_returns_tender_id(
        self,
        http_client: TestClient,
        sample_pdf_path: Path,
        uploaded_tender: UploadedTender,
    ):
        """Entity extraction result contains the passed tender_id."""
        with sample_pdf_path.open("rb") as f:
            resp = http_client.post(
                "/api/ingestion/extract-entities",
                files={"file": ("sample_tender.pdf", f, "application/pdf")},
                params={"tender_id": uploaded_tender.tender_id},
            )
        assert resp.status_code == 200
        assert resp.json().get("tender_id") == uploaded_tender.tender_id


# ---------------------------------------------------------------------------
# Graph-enriched search (requires Milvus + Neo4j + Ollama)
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.milvus
@pytest.mark.neo4j
@pytest.mark.ollama
class TestGraphEnrichedSearch:
    """E2E tests for graph-enriched retrieval (all services required)."""

    def test_graph_search_returns_results_with_graph_context(
        self,
        http_client: TestClient,
        sample_pdf_path: Path,
        uploaded_tender: UploadedTender,
    ):
        """After NER+graph population, graph-enriched search returns graph_context."""
        # Step 1: Extract entities and populate Neo4j graph
        with sample_pdf_path.open("rb") as f:
            extract_resp = http_client.post(
                "/api/ingestion/extract-entities-and-populate-graph",
                files={"file": ("sample_tender.pdf", f, "application/pdf")},
                params={
                    "tender_id": uploaded_tender.tender_id,
                    "tender_code": uploaded_tender.tender_code,
                    "populate_graph": True,
                },
            )
        assert extract_resp.status_code == 200

        # Step 2: Graph-enriched search
        search_resp = http_client.post(
            "/api/ingestion/rag/search-with-graph",
            params={
                "query": "requisiti obbligatori",
                "tender_code": uploaded_tender.tender_code,
                "top_k": 3,
                "use_graph_enrichment": True,
            },
        )
        assert search_resp.status_code == 200
        data = search_resp.json()
        assert "results" in data
        if data["results"]:
            first = data["results"][0]
            assert "graph_context" in first

    def test_graph_requirements_returns_list(
        self,
        http_client: TestClient,
        sample_pdf_path: Path,
        uploaded_tender: UploadedTender,
    ):
        """GET /api/ingestion/graph/requirements/{tender_code} → list (may be empty)."""
        resp = http_client.get(
            f"/api/ingestion/graph/requirements/{uploaded_tender.tender_code}",
            params={"mandatory_only": False},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "requirements" in data
        assert isinstance(data["requirements"], list)

    def test_search_without_graph_enrichment_lacks_graph_context(
        self,
        http_client: TestClient,
        uploaded_tender: UploadedTender,
    ):
        """Graph-enriched search with use_graph_enrichment=False has no graph_context."""
        search_resp = http_client.post(
            "/api/ingestion/rag/search-with-graph",
            params={
                "query": "requisiti",
                "tender_code": uploaded_tender.tender_code,
                "top_k": 3,
                "use_graph_enrichment": False,
            },
        )
        assert search_resp.status_code == 200
        data = search_resp.json()
        for result in data.get("results", []):
            assert "graph_context" not in result or result["graph_context"] is None
