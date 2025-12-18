"""Tests for domain services."""

from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.tender.entities.documents import Document, DocumentType
from src.domain.tender.entities.tenders import Tender, TenderStatus
from src.domain.tender.entities.lots import Lot
from src.domain.tender.schemas.documents import DocumentCreate, DocumentUpdate
from src.domain.tender.schemas.tenders import TenderCreate, TenderUpdate
from src.domain.tender.schemas.lots import LotCreate, LotUpdate
from src.domain.tender.services.documents import DocumentService
from src.domain.tender.services.tenders import TenderService
from src.domain.tender.services.lots import LotService


@pytest.mark.asyncio
class TestDocumentService:
    """Test DocumentService business logic."""
    
    @pytest_asyncio.fixture
    async def document_data(self):
        """Sample document creation data."""
        return DocumentCreate(
            tender_id=uuid4(),
            filename="test_document.pdf",
            storage_bucket="test-bucket",
            storage_path="tests/test_document.pdf",
            document_type=DocumentType.TECHNICAL
        )
    
    async def test_create_document(self, db_session: AsyncSession, document_data):
        """Test creating a document."""
        document = await DocumentService.create(db_session, document_data)
        
        assert document.id is not None
        assert document.filename == document_data.filename
        assert document.document_type == DocumentType.TECHNICAL
    
    async def test_get_document_by_id(self, db_session: AsyncSession, document_data):
        """Test retrieving document by ID."""
        # Create document
        created = await DocumentService.create(db_session, document_data)
        
        # Retrieve it
        retrieved = await DocumentService.get_by_id(db_session, created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.filename == created.filename
    
    async def test_update_document(self, db_session: AsyncSession, document_data):
        """Test updating a document."""
        # Create document
        document = await DocumentService.create(db_session, document_data)
        
        # Update it
        new_lot_id = uuid4()
        update_data = DocumentUpdate(lot_id=new_lot_id)
        updated = await DocumentService.update(db_session, document.id, update_data)
        
        assert updated.lot_id == new_lot_id
    
    async def test_delete_document(self, db_session: AsyncSession, document_data):
        """Test deleting a document."""
        # Create document
        document = await DocumentService.create(db_session, document_data)
        doc_id = document.id
        
        # Delete it
        result = await DocumentService.delete(db_session, doc_id)
        assert result is True
        
        # Verify it's gone
        retrieved = await DocumentService.get_by_id(db_session, doc_id)
        assert retrieved is None
    
    async def test_list_documents_by_tender(self, db_session: AsyncSession):
        """Test listing documents by tender ID."""
        tender_id = uuid4()
        
        # Create multiple documents for same tender
        for i in range(3):
            doc_data = DocumentCreate(
                tender_id=tender_id,
                filename=f"doc_{i}.pdf",
                storage_bucket="test",
                storage_path=f"path/doc_{i}.pdf"
            )
            await DocumentService.create(db_session, doc_data)
        
        # List documents
        documents = await DocumentService.list_by_tender(db_session, tender_id)
        
        assert len(documents) == 3


@pytest.mark.asyncio
class TestTenderService:
    """Test TenderService business logic."""
    
    @pytest_asyncio.fixture
    async def tender_data(self):
        """Sample tender creation data."""
        return TenderCreate(
            code="TENDER-TEST-001",
            title="Test Tender",
            description="A tender for testing",
            status=TenderStatus.DRAFT,
            buyer="Test Organization"
        )
    
    async def test_create_tender(self, db_session: AsyncSession, tender_data):
        """Test creating a tender."""
        tender = await TenderService.create(db_session, tender_data)
        
        assert tender.id is not None
        assert tender.code == tender_data.code
        assert tender.status == TenderStatus.DRAFT
    
    async def test_get_tender_by_id(self, db_session: AsyncSession, tender_data):
        """Test retrieving tender by ID."""
        created = await TenderService.create(db_session, tender_data)
        retrieved = await TenderService.get_by_id(db_session, created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
    
    async def test_update_tender(self, db_session: AsyncSession, tender_data):
        """Test updating a tender."""
        tender = await TenderService.create(db_session, tender_data)
        
        update_data = TenderUpdate(
            title="Updated Title",
            status=TenderStatus.PUBLISHED
        )
        updated = await TenderService.update(db_session, tender.id, update_data)
        
        assert updated.title == "Updated Title"
        assert updated.status == TenderStatus.PUBLISHED
    
    async def test_list_all_tenders(self, db_session: AsyncSession):
        """Test listing all tenders."""
        # Create multiple tenders
        for i in range(3):
            data = TenderCreate(
                code=f"TENDER-{i}",
                title=f"Tender {i}"
            )
            await TenderService.create(db_session, data)
        
        tenders = await TenderService.list_all(db_session)
        assert len(tenders) >= 3


@pytest.mark.asyncio
class TestLotService:
    """Test LotService business logic."""
    
    @pytest_asyncio.fixture
    async def lot_data(self):
        """Sample lot creation data."""
        return LotCreate(
            tender_id=uuid4(),
            code="LOT-001",
            title="Test Lot",
            description="A test lot",
            value_estimated=100000.0,
            currency="EUR"
        )
    
    async def test_create_lot(self, db_session: AsyncSession, lot_data):
        """Test creating a lot."""
        lot = await LotService.create(db_session, lot_data)
        
        assert lot.id is not None
        assert lot.code == lot_data.code
        assert lot.value_estimated == 100000.0
    
    async def test_get_lot_by_id(self, db_session: AsyncSession, lot_data):
        """Test retrieving lot by ID."""
        created = await LotService.create(db_session, lot_data)
        retrieved = await LotService.get_by_id(db_session, created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
    
    async def test_update_lot(self, db_session: AsyncSession, lot_data):
        """Test updating a lot."""
        lot = await LotService.create(db_session, lot_data)
        
        update_data = LotUpdate(
            title="Updated Lot Title",
            value_estimated=150000.0
        )
        updated = await LotService.update(db_session, lot.id, update_data)
        
        assert updated.title == "Updated Lot Title"
        assert updated.value_estimated == 150000.0
    
    async def test_list_lots_by_tender(self, db_session: AsyncSession):
        """Test listing lots by tender ID."""
        tender_id = uuid4()
        
        # Create multiple lots for same tender
        for i in range(3):
            data = LotCreate(
                tender_id=tender_id,
                code=f"LOT-{i}",
                title=f"Lot {i}"
            )
            await LotService.create(db_session, data)
        
        lots = await LotService.list_by_tender(db_session, tender_id)
        assert len(lots) == 3
