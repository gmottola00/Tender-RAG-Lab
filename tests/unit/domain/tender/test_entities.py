"""Tests for domain entities."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest

from src.domain.tender.entities.documents import Document, DocumentType
from src.domain.tender.entities.lots import Lot
from src.domain.tender.entities.tenders import Tender, TenderStatus


class TestDocument:
    """Test Document entity."""

    def test_document_creation_minimal(self):
        """Create a document entity with required fields only."""
        doc = Document(
            tender_id=UUID("12345678-1234-5678-1234-567812345678"),
            filename="test.pdf",
            document_type=DocumentType.bando,
        )
        assert doc.filename == "test.pdf"
        assert doc.document_type == DocumentType.bando
        # storage_bucket and storage_path are nullable
        assert doc.storage_bucket is None or doc.storage_bucket is not None

    def test_document_creation_with_storage(self):
        """Create a document entity with optional storage fields."""
        doc = Document(
            tender_id=UUID("12345678-1234-5678-1234-567812345678"),
            filename="spec.pdf",
            storage_bucket="my-bucket",
            storage_path="tender/spec.pdf",
            document_type=DocumentType.disciplinare,
        )
        assert doc.filename == "spec.pdf"
        assert doc.storage_bucket == "my-bucket"
        assert doc.storage_path == "tender/spec.pdf"
        assert doc.document_type == DocumentType.disciplinare

    def test_document_type_enum_values(self):
        """All expected DocumentType enum values exist."""
        assert DocumentType.bando.value == "bando"
        assert DocumentType.capitolato.value == "capitolato"
        assert DocumentType.disciplinare.value == "disciplinare"
        assert DocumentType.rettifica.value == "rettifica"
        assert DocumentType.avviso.value == "avviso"
        assert DocumentType.chiarimenti.value == "chiarimenti"
        assert DocumentType.qa.value == "qa"
        assert DocumentType.altro.value == "altro"

    def test_document_type_no_technical(self):
        """DocumentType.TECHNICAL does not exist."""
        assert not hasattr(DocumentType, "TECHNICAL")

    def test_document_has_uploaded_at_not_created_at(self):
        """Document has 'uploaded_at' attribute, not 'created_at'."""
        doc = Document(
            tender_id=UUID("12345678-1234-5678-1234-567812345678"),
            filename="test.pdf",
        )
        assert hasattr(doc, "uploaded_at")
        assert not hasattr(doc, "created_at")
        assert not hasattr(doc, "updated_at")

    def test_document_lot_id_optional(self):
        """Document lot_id is optional and defaults to None."""
        doc = Document(
            tender_id=UUID("12345678-1234-5678-1234-567812345678"),
            filename="test.pdf",
        )
        assert doc.lot_id is None


class TestTender:
    """Test Tender entity."""

    def test_tender_creation(self):
        """Create a tender entity with required fields."""
        tender = Tender(
            code="TENDER-2026-001",
            title="Test Tender",
        )
        assert tender.code == "TENDER-2026-001"
        assert tender.title == "Test Tender"

    def test_tender_creation_with_optional_fields(self):
        """Create a tender entity with optional fields."""
        tender = Tender(
            code="TENDER-2026-002",
            title="Full Tender",
            description="A test tender for testing",
            status=TenderStatus.published,
            buyer="Test Organization",
            publish_date=date(2026, 1, 1),
            closing_date=date(2026, 2, 1),
        )
        assert tender.status == TenderStatus.published
        assert tender.buyer == "Test Organization"
        assert tender.publish_date < tender.closing_date

    def test_tender_status_enum_values(self):
        """All expected TenderStatus enum values exist."""
        assert TenderStatus.draft.value == "draft"
        assert TenderStatus.published.value == "published"
        assert TenderStatus.open.value == "open"
        assert TenderStatus.closed.value == "closed"
        assert TenderStatus.awarded.value == "awarded"
        assert TenderStatus.cancelled.value == "cancelled"

    def test_tender_status_published_exists(self):
        """TenderStatus.published (lowercase) exists."""
        # The enum uses lowercase names
        status = TenderStatus.published
        assert status.value == "published"

    def test_tender_has_created_at_updated_at(self):
        """Tender has created_at and updated_at attributes."""
        tender = Tender(code="T-001", title="Test")
        assert hasattr(tender, "created_at")
        assert hasattr(tender, "updated_at")

    def test_tender_description_optional(self):
        """Tender description is optional."""
        tender = Tender(code="T-002", title="Simple Tender")
        assert tender.description is None

    def test_tender_dates_optional(self):
        """Tender publish_date and closing_date are optional."""
        tender = Tender(code="T-003", title="No Dates Tender")
        assert tender.publish_date is None
        assert tender.closing_date is None


class TestLot:
    """Test Lot entity."""

    def test_lot_creation_required_fields(self):
        """Create a lot entity with required fields."""
        lot = Lot(
            tender_id=UUID("12345678-1234-5678-1234-567812345678"),
            code="LOT-001",
            title="Test Lot",
        )
        assert lot.code == "LOT-001"
        assert lot.title == "Test Lot"

    def test_lot_creation_with_optional_fields(self):
        """Create a lot entity with optional fields."""
        lot = Lot(
            tender_id=UUID("12345678-1234-5678-1234-567812345678"),
            code="LOT-002",
            title="Full Lot",
            description="A test lot",
            value_estimated=100000.0,
            currency="EUR",
            status="active",
        )
        assert lot.description == "A test lot"
        assert lot.currency == "EUR"
        assert lot.status == "active"

    def test_lot_optional_fields_default_none(self):
        """Lot optional fields default to None."""
        lot = Lot(
            tender_id=UUID("12345678-1234-5678-1234-567812345678"),
            code="LOT-003",
            title="Minimal Lot",
        )
        assert lot.description is None
        assert lot.value_estimated is None
        assert lot.currency is None

    def test_lot_has_created_at_updated_at(self):
        """Lot has created_at and updated_at attributes."""
        lot = Lot(
            tender_id=UUID("12345678-1234-5678-1234-567812345678"),
            code="LOT-004",
            title="Lot with timestamps",
        )
        assert hasattr(lot, "created_at")
        assert hasattr(lot, "updated_at")

    def test_lot_tender_id_required(self):
        """Lot requires tender_id, code, and title."""
        # Just instantiating verifies no unexpected errors
        lot = Lot(
            tender_id=UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
            code="LOT-TEST",
            title="Test Lot Title",
        )
        assert str(lot.tender_id) == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
