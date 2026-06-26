"""Mock implementation of TenderGraphClient for testing.

Provides a complete AsyncMock-based replacement for TenderGraphClient
that tracks all method calls without requiring a real Neo4j connection.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock


class MockTenderGraphClient:
    """Mock TenderGraphClient with AsyncMock for every domain method.

    Usage::

        mock = MockTenderGraphClient()
        service = EntityExtractionService(ner=real_ner, neo4j_client=mock)
        await service.populate_graph(extraction_result, tender_code="TEST-001")

        mock.add_requirement.assert_called_once()
        call_kwargs = mock.add_requirement.call_args.kwargs
        assert call_kwargs["mandatory"] is True
    """

    def __init__(self) -> None:
        # ── Low-level graph operations ────────────────────────────────────────
        self.execute_write = AsyncMock(return_value=[{"result": "ok"}])
        self.execute_query = AsyncMock(return_value=[])

        # ── Schema ────────────────────────────────────────────────────────────
        self.create_tender_schema = AsyncMock(return_value=None)
        self.create_constraint = AsyncMock(return_value=None)
        self.create_index = AsyncMock(return_value=None)

        # ── Tender CRUD ───────────────────────────────────────────────────────
        self.create_tender = AsyncMock(return_value=[{"code": "test"}])
        self.get_tender_by_code = AsyncMock(return_value=None)
        self.get_tender_with_lots = AsyncMock(return_value=None)
        self.get_tender_with_all_entities = AsyncMock(return_value=None)
        self.delete_tender = AsyncMock(return_value=True)
        self.delete_all_tenders = AsyncMock(return_value=0)

        # ── Lot operations ────────────────────────────────────────────────────
        self.add_lot_to_tender = AsyncMock(return_value=[{"lot_id": "test"}])
        self.add_lot_from_structure = AsyncMock(return_value=[{"id": "lot-test"}])

        # ── Section operations ────────────────────────────────────────────────
        self.add_section_from_structure = AsyncMock(return_value=[{"id": "sec-test"}])

        # ── Code operations (CIG, CUP, CPV) ──────────────────────────────────
        self.add_code_from_structure = AsyncMock(return_value=[{"id": "code-test"}])

        # ── Buyer / Organization operations ───────────────────────────────────
        self.add_buyer_from_structure = AsyncMock(return_value=[{"id": "buyer-test"}])
        self.add_organization = AsyncMock(return_value=[{"name": "org-test"}])

        # ── Requirement / Deadline operations ─────────────────────────────────
        self.add_requirement = AsyncMock(return_value=[{"id": "req-test"}])
        self.add_deadline = AsyncMock(return_value=[{"id": "deadline-test"}])

        # ── Query operations ──────────────────────────────────────────────────
        self.get_requirements_for_tender = AsyncMock(return_value=[])
        self.get_deadlines_for_tender = AsyncMock(return_value=[])
        self.find_tenders_by_cpv = AsyncMock(return_value=[])
        self.find_tenders_by_buyer = AsyncMock(return_value=[])

        # ── Lifecycle ─────────────────────────────────────────────────────────
        self.close = AsyncMock(return_value=None)
        self.verify_connectivity = AsyncMock(return_value=True)

    def reset_mocks(self) -> None:
        """Reset call history on all mocks (useful between subtests)."""
        for name in dir(self):
            val = getattr(self, name)
            if isinstance(val, AsyncMock):
                val.reset_mock()
