"""Tests for domain schemas."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from src.domain.tender.entities.documents import DocumentType
from src.domain.tender.entities.tenders import TenderStatus
from src.domain.tender.schemas.documents import DocumentCreate, DocumentOut, DocumentUpdate
from src.domain.tender.schemas.lots import LotCreate, LotOut, LotUpdate
from src.domain.tender.schemas.tenders import TenderCreate, TenderOut, TenderUpdate


class TestDocumentSchemas:
    """Test document Pydantic schemas."""

    def test_document_create_minimal(self):
        """DocumentCreate works with only required fields."""
        doc = DocumentCreate(
            tender_id=uuid4(),
            filename="test.pdf",
        )
        assert doc.filename == "test.pdf"
        # Optional fields default to None
        assert doc.storage_bucket is None
        assert doc.storage_path is None
        assert doc.document_type is None

    def test_document_create_with_document_type(self):
        """DocumentCreate with DocumentType.bando (not TECHNICAL)."""
        doc = DocumentCreate(
            tender_id=uuid4(),
            filename="bando.pdf",
            document_type=DocumentType.bando,
        )
        assert doc.document_type == DocumentType.bando

    def test_document_create_with_all_fields(self):
        """DocumentCreate with all fields set."""
        doc = DocumentCreate(
            tender_id=uuid4(),
            filename="capitolato.pdf",
            storage_bucket="my-bucket",
            storage_path="path/capitolato.pdf",
            document_type=DocumentType.capitolato,
        )
        assert doc.filename == "capitolato.pdf"
        assert doc.storage_bucket == "my-bucket"
        assert doc.document_type == DocumentType.capitolato

    def test_document_create_missing_tender_id(self):
        """DocumentCreate without tender_id raises ValidationError."""
        with pytest.raises(ValidationError):
            DocumentCreate(filename="test.pdf")

    def test_document_create_missing_filename(self):
        """DocumentCreate without filename raises ValidationError."""
        with pytest.raises(ValidationError):
            DocumentCreate(tender_id=uuid4())

    def test_document_create_invalid_document_type(self):
        """DocumentCreate with invalid document_type raises ValidationError."""
        with pytest.raises(ValidationError):
            DocumentCreate(
                tender_id=uuid4(),
                filename="test.pdf",
                document_type="invalid_type",
            )

    def test_document_update(self):
        """DocumentUpdate schema accepts lot_id."""
        update = DocumentUpdate(lot_id=uuid4())
        assert update.lot_id is not None

    def test_document_out_has_uploaded_at(self):
        """DocumentOut has uploaded_at (not created_at or updated_at)."""
        doc_out = DocumentOut(
            id=uuid4(),
            tender_id=uuid4(),
            filename="test.pdf",
            uploaded_at=datetime(2026, 1, 1, 12, 0, 0),
        )
        assert doc_out.filename == "test.pdf"
        assert isinstance(doc_out.uploaded_at, datetime)
        assert not hasattr(doc_out, "created_at")
        assert not hasattr(doc_out, "updated_at")

    def test_document_out_optional_storage_fields(self):
        """DocumentOut storage_bucket and storage_path are optional."""
        doc_out = DocumentOut(
            id=uuid4(),
            tender_id=uuid4(),
            filename="test.pdf",
            uploaded_at=datetime(2026, 1, 1),
        )
        assert doc_out.storage_bucket is None
        assert doc_out.storage_path is None


class TestTenderSchemas:
    """Test tender Pydantic schemas."""

    def test_tender_create_minimal(self):
        """TenderCreate with only required fields."""
        t = TenderCreate(code="TENDER-001", title="Test Tender")
        assert t.code == "TENDER-001"
        assert t.title == "Test Tender"

    def test_tender_create_with_all_fields(self):
        """TenderCreate with all optional fields set."""
        t = TenderCreate(
            code="TENDER-002",
            title="Full Tender",
            description="Description",
            status=TenderStatus.published,
            buyer="Buyer Org",
            publish_date=date(2026, 1, 1),
            closing_date=date(2026, 2, 1),
        )
        assert t.status == TenderStatus.published
        assert t.buyer == "Buyer Org"

    def test_tender_create_missing_code(self):
        """TenderCreate without code raises ValidationError."""
        with pytest.raises(ValidationError):
            TenderCreate(title="No Code Tender")

    def test_tender_create_missing_title(self):
        """TenderCreate without title raises ValidationError."""
        with pytest.raises(ValidationError):
            TenderCreate(code="T-001")

    def test_tender_update_partial(self):
        """TenderUpdate accepts partial updates."""
        update = TenderUpdate(title="Updated Title")
        assert update.title == "Updated Title"
        assert update.code is None
        assert update.status is None

    def test_tender_out_requires_timestamps(self):
        """TenderOut requires both created_at and updated_at."""
        now = datetime(2026, 1, 1)
        t = TenderOut(
            id=uuid4(),
            code="TEST-001",
            title="Test",
            created_at=now,
            updated_at=now,
        )
        assert t.code == "TEST-001"
        assert isinstance(t.created_at, datetime)
        assert isinstance(t.updated_at, datetime)

    def test_tender_out_missing_created_at_raises(self):
        """TenderOut raises ValidationError without created_at."""
        with pytest.raises(ValidationError):
            TenderOut(
                id=uuid4(),
                code="T-001",
                title="Test",
                # missing created_at and updated_at
            )


class TestLotSchemas:
    """Test lot Pydantic schemas."""

    def test_lot_create_minimal(self):
        """LotCreate with only required fields."""
        lot = LotCreate(tender_id=uuid4(), code="LOT-001", title="Test Lot")
        assert lot.code == "LOT-001"
        assert lot.description is None
        assert lot.value_estimated is None

    def test_lot_create_with_all_fields(self):
        """LotCreate with all optional fields."""
        lot = LotCreate(
            tender_id=uuid4(),
            code="LOT-002",
            title="Full Lot",
            description="Lot description",
            value_estimated=50000.0,
            currency="EUR",
        )
        assert lot.code == "LOT-002"
        assert lot.value_estimated == 50000.0
        assert lot.currency == "EUR"

    def test_lot_create_missing_tender_id(self):
        """LotCreate without tender_id raises ValidationError."""
        with pytest.raises(ValidationError):
            LotCreate(code="LOT-001", title="Lot Without Tender")

    def test_lot_create_missing_code(self):
        """LotCreate without code raises ValidationError."""
        with pytest.raises(ValidationError):
            LotCreate(tender_id=uuid4(), title="Lot Without Code")

    def test_lot_create_missing_title(self):
        """LotCreate without title raises ValidationError."""
        with pytest.raises(ValidationError):
            LotCreate(tender_id=uuid4(), code="LOT-001")

    def test_lot_update_partial(self):
        """LotUpdate accepts partial updates."""
        update = LotUpdate(title="Updated", value_estimated=75000.0)
        assert update.title == "Updated"
        assert update.value_estimated == 75000.0
        assert update.currency is None

    def test_lot_out_requires_timestamps(self):
        """LotOut requires both created_at and updated_at."""
        now = datetime(2026, 1, 1)
        lot = LotOut(
            id=uuid4(),
            tender_id=uuid4(),
            code="LOT-001",
            title="Test Lot",
            created_at=now,
            updated_at=now,
        )
        assert lot.code == "LOT-001"
        assert isinstance(lot.created_at, datetime)
        assert isinstance(lot.updated_at, datetime)


class TestSchemaValidation:
    """Test schema validation rules."""

    def test_uuid_validation_valid(self):
        """Valid UUID string is accepted."""
        doc = DocumentCreate(
            tender_id=UUID("12345678-1234-5678-1234-567812345678"),
            filename="test.pdf",
        )
        assert isinstance(doc.tender_id, UUID)

    def test_uuid_validation_invalid_raises(self):
        """Invalid UUID string raises ValidationError."""
        with pytest.raises(ValidationError):
            DocumentCreate(
                tender_id="not-a-uuid",
                filename="test.pdf",
            )

    def test_document_type_enum_validation(self):
        """Valid DocumentType enum passes validation."""
        doc = DocumentCreate(
            tender_id=uuid4(),
            filename="test.pdf",
            document_type=DocumentType.bando,
        )
        assert doc.document_type == DocumentType.bando

    def test_document_type_invalid_raises(self):
        """Invalid document_type string raises ValidationError."""
        with pytest.raises(ValidationError):
            DocumentCreate(
                tender_id=uuid4(),
                filename="test.pdf",
                document_type="invalid_type",
            )

    def test_tender_status_valid(self):
        """Valid TenderStatus passes validation."""
        t = TenderCreate(
            code="T-001",
            title="Test",
            status=TenderStatus.draft,
        )
        assert t.status == TenderStatus.draft

    def test_tender_status_published_valid(self):
        """TenderStatus.published is a valid enum value."""
        t = TenderCreate(
            code="T-002",
            title="Published",
            status=TenderStatus.published,
        )
        assert t.status == TenderStatus.published
