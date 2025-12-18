"""Tests for domain entities."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

import pytest

from src.domain.tender.entities.documents import Document, DocumentType
from src.domain.tender.entities.tenders import Tender, TenderStatus
from src.domain.tender.entities.lots import Lot


class TestDocument:
    """Test Document entity."""
    
    def test_document_creation(self):
        """Test creating a document entity."""
        doc = Document(
            tender_id=UUID("12345678-1234-5678-1234-567812345678"),
            filename="test.pdf",
            storage_bucket="test-bucket",
            storage_path="path/to/file",
            document_type=DocumentType.TECHNICAL
        )
        
        assert doc.filename == "test.pdf"
        assert doc.storage_bucket == "test-bucket"
        assert doc.document_type == DocumentType.TECHNICAL
    
    def test_document_type_enum(self):
        """Test DocumentType enum values."""
        assert DocumentType.TECHNICAL.value == "technical"
        assert DocumentType.ADMINISTRATIVE.value == "administrative"
        assert DocumentType.ECONOMIC.value == "economic"


class TestTender:
    """Test Tender entity."""
    
    def test_tender_creation(self):
        """Test creating a tender entity."""
        tender = Tender(
            code="TENDER-2025-001",
            title="Test Tender",
            description="A test tender for testing",
            status=TenderStatus.PUBLISHED,
            buyer="Test Organization",
            publish_date=date(2025, 1, 1),
            closing_date=date(2025, 2, 1)
        )
        
        assert tender.code == "TENDER-2025-001"
        assert tender.title == "Test Tender"
        assert tender.status == TenderStatus.PUBLISHED
        assert tender.buyer == "Test Organization"
    
    def test_tender_status_enum(self):
        """Test TenderStatus enum."""
        assert TenderStatus.DRAFT.value == "draft"
        assert TenderStatus.PUBLISHED.value == "published"
        assert TenderStatus.CLOSED.value == "closed"
    
    def test_tender_dates(self):
        """Test tender date fields."""
        tender = Tender(
            code="TEST-001",
            title="Test",
            publish_date=date(2025, 1, 1),
            closing_date=date(2025, 2, 1)
        )
        
        assert tender.publish_date < tender.closing_date


class TestLot:
    """Test Lot entity."""
    
    def test_lot_creation(self):
        """Test creating a lot entity."""
        lot = Lot(
            tender_id=UUID("12345678-1234-5678-1234-567812345678"),
            code="LOT-001",
            title="Test Lot",
            description="A test lot",
            value_estimated=100000.0,
            currency="EUR",
            status="active"
        )
        
        assert lot.code == "LOT-001"
        assert lot.title == "Test Lot"
        assert lot.value_estimated == 100000.0
        assert lot.currency == "EUR"
    
    def test_lot_optional_fields(self):
        """Test lot with optional fields."""
        lot = Lot(
            tender_id=UUID("12345678-1234-5678-1234-567812345678"),
            code="LOT-001",
            title="Test Lot"
        )
        
        assert lot.description is None
        assert lot.value_estimated is None
        assert lot.currency is None
