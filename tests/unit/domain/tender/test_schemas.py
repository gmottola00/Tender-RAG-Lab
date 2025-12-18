"""Tests for domain schemas."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from src.domain.tender.schemas.documents import DocumentCreate, DocumentUpdate, DocumentOut
from src.domain.tender.schemas.tenders import TenderCreate, TenderUpdate, TenderOut
from src.domain.tender.schemas.lots import LotCreate, LotUpdate, LotOut
from src.domain.tender.entities.documents import DocumentType
from src.domain.tender.entities.tenders import TenderStatus


class TestDocumentSchemas:
    """Test document Pydantic schemas."""
    
    def test_document_create_valid(self):
        """Test creating valid DocumentCreate."""
        doc_data = DocumentCreate(
            tender_id=uuid4(),
            filename="test.pdf",
            storage_bucket="bucket",
            storage_path="path/test.pdf",
            document_type=DocumentType.TECHNICAL
        )
        
        assert doc_data.filename == "test.pdf"
        assert doc_data.document_type == DocumentType.TECHNICAL
    
    def test_document_create_missing_required(self):
        """Test DocumentCreate with missing required fields."""
        with pytest.raises(ValidationError):
            DocumentCreate(filename="test.pdf")  # Missing tender_id
    
    def test_document_update(self):
        """Test DocumentUpdate schema."""
        update = DocumentUpdate(lot_id=uuid4())
        assert update.lot_id is not None
    
    def test_document_out_serialization(self):
        """Test DocumentOut schema."""
        doc_out = DocumentOut(
            id=uuid4(),
            tender_id=uuid4(),
            filename="test.pdf",
            storage_bucket="bucket",
            storage_path="path",
            document_type=DocumentType.TECHNICAL,
            created_at=None,
            updated_at=None
        )
        
        # Should be serializable
        assert doc_out.filename == "test.pdf"


class TestTenderSchemas:
    """Test tender Pydantic schemas."""
    
    def test_tender_create_valid(self):
        """Test creating valid TenderCreate."""
        tender_data = TenderCreate(
            code="TENDER-001",
            title="Test Tender",
            description="Description",
            status=TenderStatus.PUBLISHED,
            buyer="Buyer Org",
            publish_date=date(2025, 1, 1),
            closing_date=date(2025, 2, 1)
        )
        
        assert tender_data.code == "TENDER-001"
        assert tender_data.status == TenderStatus.PUBLISHED
    
    def test_tender_create_missing_required(self):
        """Test TenderCreate with missing required fields."""
        with pytest.raises(ValidationError):
            TenderCreate(title="Test")  # Missing code
    
    def test_tender_update_partial(self):
        """Test partial TenderUpdate."""
        update = TenderUpdate(title="Updated Title")
        assert update.title == "Updated Title"
        assert update.code is None  # Optional
    
    def test_tender_out(self):
        """Test TenderOut schema."""
        tender_out = TenderOut(
            id=uuid4(),
            code="TEST-001",
            title="Test",
            created_at=None,
            updated_at=None
        )
        
        assert tender_out.code == "TEST-001"


class TestLotSchemas:
    """Test lot Pydantic schemas."""
    
    def test_lot_create_valid(self):
        """Test creating valid LotCreate."""
        lot_data = LotCreate(
            tender_id=uuid4(),
            code="LOT-001",
            title="Test Lot",
            description="Lot description",
            value_estimated=50000.0,
            currency="EUR"
        )
        
        assert lot_data.code == "LOT-001"
        assert lot_data.value_estimated == 50000.0
    
    def test_lot_create_minimal(self):
        """Test LotCreate with minimal fields."""
        lot_data = LotCreate(
            tender_id=uuid4(),
            code="LOT-001",
            title="Test Lot"
        )
        
        assert lot_data.description is None
        assert lot_data.value_estimated is None
    
    def test_lot_update(self):
        """Test LotUpdate schema."""
        update = LotUpdate(
            title="Updated Lot Title",
            value_estimated=75000.0
        )
        
        assert update.title == "Updated Lot Title"
        assert update.value_estimated == 75000.0
    
    def test_lot_out(self):
        """Test LotOut schema."""
        lot_out = LotOut(
            id=uuid4(),
            tender_id=uuid4(),
            code="LOT-001",
            title="Test",
            created_at=None,
            updated_at=None
        )
        
        assert lot_out.code == "LOT-001"


class TestSchemaValidation:
    """Test schema validation rules."""
    
    def test_uuid_validation(self):
        """Test UUID field validation."""
        # Valid UUID
        doc = DocumentCreate(
            tender_id=UUID("12345678-1234-5678-1234-567812345678"),
            filename="test.pdf"
        )
        assert isinstance(doc.tender_id, UUID)
        
        # Invalid UUID string should fail
        with pytest.raises(ValidationError):
            DocumentCreate(
                tender_id="not-a-uuid",  # type: ignore
                filename="test.pdf"
            )
    
    def test_enum_validation(self):
        """Test enum field validation."""
        # Valid enum
        doc = DocumentCreate(
            tender_id=uuid4(),
            filename="test.pdf",
            document_type=DocumentType.TECHNICAL
        )
        assert doc.document_type == DocumentType.TECHNICAL
        
        # Invalid enum should fail
        with pytest.raises(ValidationError):
            DocumentCreate(
                tender_id=uuid4(),
                filename="test.pdf",
                document_type="invalid_type"  # type: ignore
            )
