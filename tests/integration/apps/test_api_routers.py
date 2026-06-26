"""Integration tests for FastAPI routers.

Uses TestClient with real SQLite in-memory DB and mocked external services
(Milvus, Neo4j, Ollama). Every test makes precise assertions on status codes
and response shapes — never "accept any 5xx" patterns.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestTendersRouter:
    """Tests for /api/tenders endpoints."""

    def test_create_tender_valid_returns_201(self, api_client: TestClient):
        """POST /api/tenders with valid payload → 201 + id and code in body."""
        payload = {
            "code": f"INTG-{uuid4().hex[:8]}",
            "title": "Integration Test Tender",
            "description": "Created in integration test",
            "status": "draft",
            "buyer": "Test Organization",
        }
        response = api_client.post("/api/tenders", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["code"] == payload["code"]
        assert data["title"] == payload["title"]

    def test_create_tender_missing_code_returns_422(self, api_client: TestClient):
        """POST /api/tenders missing required 'code' field → 422 with error detail."""
        payload = {"title": "Tender Without Code"}
        response = api_client.post("/api/tenders", json=payload)

        assert response.status_code == 422
        error = response.json()
        assert "detail" in error

    def test_create_tender_empty_body_returns_422(self, api_client: TestClient):
        """POST /api/tenders with empty body → 422."""
        response = api_client.post("/api/tenders", json={})
        assert response.status_code == 422

    def test_get_tender_not_found_returns_exact_404(self, api_client: TestClient):
        """GET /api/tenders/{random-uuid} → exact 404 with 'not found' in detail."""
        response = api_client.get(f"/api/tenders/{uuid4()}")

        assert response.status_code == 404
        body = response.json()
        assert "detail" in body
        assert "not found" in body["detail"].lower()

    def test_get_tender_found_returns_200(self, api_client: TestClient):
        """GET /api/tenders/{id} → 200 with full tender data including id."""
        code = f"INTG-{uuid4().hex[:6]}"
        create = api_client.post("/api/tenders", json={"code": code, "title": "Find Me"})
        assert create.status_code == 201
        tender_id = create.json()["id"]

        response = api_client.get(f"/api/tenders/{tender_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tender_id
        assert data["code"] == code

    def test_list_tenders_returns_200_list(self, api_client: TestClient):
        """GET /api/tenders → 200 + JSON array."""
        response = api_client.get("/api/tenders")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_tenders_includes_created(self, api_client: TestClient):
        """Tenders created during the test appear in list response."""
        codes = [f"LIST-{uuid4().hex[:6]}" for _ in range(2)]
        for code in codes:
            api_client.post("/api/tenders", json={"code": code, "title": f"T {code}"})

        response = api_client.get("/api/tenders")
        listed_codes = [t["code"] for t in response.json()]
        for code in codes:
            assert code in listed_codes

    def test_update_tender_returns_200_with_new_values(self, api_client: TestClient):
        """PUT /api/tenders/{id} → 200 with updated fields."""
        code = f"UPD-{uuid4().hex[:6]}"
        create = api_client.post("/api/tenders", json={"code": code, "title": "Original Title"})
        tender_id = create.json()["id"]

        update = api_client.put(
            f"/api/tenders/{tender_id}",
            json={"title": "Updated Title", "status": "published"},
        )
        assert update.status_code == 200
        data = update.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "published"

    def test_update_nonexistent_tender_returns_404(self, api_client: TestClient):
        """PUT /api/tenders/{unknown-uuid} → 404."""
        response = api_client.put(
            f"/api/tenders/{uuid4()}",
            json={"title": "Ghost Update"},
        )
        assert response.status_code == 404

    def test_delete_tender_calls_neo4j_and_milvus(self, api_client: TestClient):
        """DELETE /api/tenders/{id} → 204, Neo4j and Milvus cleanup called."""
        code = f"DEL-{uuid4().hex[:6]}"
        create = api_client.post("/api/tenders", json={"code": code, "title": "To Delete"})
        assert create.status_code == 201
        tender_id = create.json()["id"]

        mock_graph = MockTenderGraphClientForPatch()
        mock_idx = MagicMock()
        mock_idx.delete_by_tender_id = MagicMock(return_value={"delete_count": 2})

        with (
            patch("src.api.routers.tenders.get_tender_graph_client", return_value=mock_graph),
            patch("src.api.routers.tenders.get_indexer", return_value=mock_idx),
        ):
            response = api_client.delete(f"/api/tenders/{tender_id}")

        assert response.status_code == 204
        mock_graph.delete_tender.assert_called_once_with(code)
        mock_idx.delete_by_tender_id.assert_called_once_with(str(tender_id))

    def test_delete_nonexistent_tender_returns_404(self, api_client: TestClient):
        """DELETE /api/tenders/{unknown-uuid} → 404 (not 204 or 500)."""
        mock_graph = MockTenderGraphClientForPatch()
        mock_idx = MagicMock()
        mock_idx.delete_by_tender_id = MagicMock(return_value={"delete_count": 0})

        with (
            patch("src.api.routers.tenders.get_tender_graph_client", return_value=mock_graph),
            patch("src.api.routers.tenders.get_indexer", return_value=mock_idx),
        ):
            response = api_client.delete(f"/api/tenders/{uuid4()}")

        assert response.status_code == 404


class MockTenderGraphClientForPatch:
    """Minimal sync-compatible mock for patching direct calls in router."""

    def __init__(self):
        self.delete_tender = AsyncMock(return_value=True)
        self.delete_all_tenders = AsyncMock(return_value=0)
        self.close = AsyncMock(return_value=None)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


@pytest.mark.integration
class TestLotsRouter:
    """Tests for /api/lots endpoints."""

    def _create_tender(self, client: TestClient) -> str:
        resp = client.post(
            "/api/tenders",
            json={"code": f"LOT-TND-{uuid4().hex[:6]}", "title": "Parent Tender"},
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_list_lots_returns_200(self, api_client: TestClient):
        """GET /api/lots → 200 + list (possibly empty)."""
        response = api_client.get("/api/lots")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_lots_filtered_by_tender_returns_200(self, api_client: TestClient):
        """GET /api/lots?tender_id=xxx → 200 + list."""
        tender_id = self._create_tender(api_client)
        response = api_client.get(f"/api/lots?tender_id={tender_id}")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_lot_valid_payload(self, api_client: TestClient):
        """POST /api/lots with valid payload → 201."""
        tender_id = self._create_tender(api_client)
        payload = {
            "tender_id": tender_id,
            "code": f"LOT-{uuid4().hex[:6]}",
            "title": "Test Lot",
            "value_estimated": 50000.0,
            "currency": "EUR",
        }
        response = api_client.post("/api/lots", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["tender_id"] == tender_id

    def test_create_lot_missing_tender_id_returns_422(self, api_client: TestClient):
        """POST /api/lots missing required 'tender_id' → 422."""
        payload = {"code": "LOT-X", "title": "Orphan Lot"}
        response = api_client.post("/api/lots", json=payload)
        assert response.status_code == 422

    def test_get_lot_not_found_returns_404(self, api_client: TestClient):
        """GET /api/lots/{unknown-uuid} → 404."""
        response = api_client.get(f"/api/lots/{uuid4()}")
        assert response.status_code == 404


@pytest.mark.integration
class TestDocumentsRouter:
    """Tests for /api/documents endpoints."""

    def _create_tender(self, client: TestClient) -> str:
        resp = client.post(
            "/api/tenders",
            json={"code": f"DOC-TND-{uuid4().hex[:6]}", "title": "Parent Tender"},
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_get_document_not_found_returns_404(self, api_client: TestClient):
        """GET /api/documents/{unknown-uuid} → 404."""
        response = api_client.get(f"/api/documents/{uuid4()}")
        assert response.status_code == 404

    def test_list_documents_returns_200(self, api_client: TestClient):
        """GET /api/documents → 200 + list."""
        response = api_client.get("/api/documents")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_document_valid_payload(self, api_client: TestClient):
        """POST /api/documents (multipart form + file upload) → 201."""
        tender_id = self._create_tender(api_client)

        with patch("src.domain.tender.services.documents.get_storage_client") as mock_storage:
            storage_mock = MagicMock()
            storage_mock.bucket_name = "test-bucket"
            storage_mock.ensure_bucket = MagicMock(return_value=None)
            storage_mock.build_path = MagicMock(return_value="test-bucket/bando.pdf")
            storage_mock.upload_bytes = MagicMock(return_value=None)
            mock_storage.return_value = storage_mock

            response = api_client.post(
                "/api/documents",
                data={"tender_id": tender_id, "document_type": "bando"},
                files={"file": ("bando.pdf", b"%PDF-1.4 test content", "application/pdf")},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["tender_id"] == tender_id
        assert data["filename"] == "bando.pdf"
