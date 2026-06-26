"""Tests for domain services."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.tender.entities.documents import Document, DocumentType
from src.domain.tender.entities.lots import Lot
from src.domain.tender.entities.tenders import Tender, TenderStatus
from src.domain.tender.schemas.documents import DocumentCreate, DocumentUpdate
from src.domain.tender.schemas.lots import LotCreate, LotUpdate
from src.domain.tender.schemas.tenders import TenderCreate, TenderUpdate
from src.domain.tender.services.documents import DocumentService
from src.domain.tender.services.lots import LotService
from src.domain.tender.services.tenders import TenderService


def _make_mock_storage_client(bucket_name="test-bucket"):
    """Create a mock storage client compatible with DocumentService.create."""
    mock = MagicMock()
    mock.bucket_name = bucket_name
    mock.ensure_bucket = MagicMock(return_value=None)
    mock.build_path = MagicMock(side_effect=lambda tender_id, lot_id, filename: f"{tender_id}/{filename}")
    return mock


@pytest.mark.asyncio
class TestDocumentService:
    """Test DocumentService business logic."""

    @pytest_asyncio.fixture
    async def tender(self, db_session: AsyncSession):
        """Create a parent tender for document FK."""
        t = Tender(code=f"TND-{uuid4().hex[:8]}", title="Parent Tender")
        db_session.add(t)
        await db_session.flush()
        return t

    @pytest_asyncio.fixture
    async def document_data(self, tender):
        """Sample document creation data."""
        return DocumentCreate(
            tender_id=tender.id,
            filename="test_document.pdf",
            document_type=DocumentType.bando,
        )

    async def test_create_document(self, db_session: AsyncSession, document_data):
        """Create a document via mocked storage client."""
        mock_storage = _make_mock_storage_client()
        with patch("src.domain.tender.services.documents.get_storage_client", return_value=mock_storage):
            document = await DocumentService.create(db_session, document_data)

        assert document.id is not None
        assert document.filename == document_data.filename
        assert document.document_type == DocumentType.bando

    async def test_get_document_by_id(self, db_session: AsyncSession, document_data):
        """get() retrieves a document by primary key."""
        mock_storage = _make_mock_storage_client()
        with patch("src.domain.tender.services.documents.get_storage_client", return_value=mock_storage):
            created = await DocumentService.create(db_session, document_data)

        retrieved = await DocumentService.get(db_session, created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.filename == created.filename

    async def test_get_nonexistent_document_returns_none(self, db_session: AsyncSession):
        """get() returns None for a non-existent ID."""
        result = await DocumentService.get(db_session, uuid4())
        assert result is None

    async def test_update_document(self, db_session: AsyncSession, document_data):
        """update() modifies a document field."""
        mock_storage = _make_mock_storage_client()
        with patch("src.domain.tender.services.documents.get_storage_client", return_value=mock_storage):
            document = await DocumentService.create(db_session, document_data)

        new_lot_id = uuid4()
        update_data = DocumentUpdate(lot_id=new_lot_id)
        updated = await DocumentService.update(db_session, document.id, update_data)
        assert updated is not None
        assert updated.lot_id == new_lot_id

    async def test_delete_document(self, db_session: AsyncSession, document_data):
        """delete() removes a document and returns True."""
        mock_storage = _make_mock_storage_client()
        with patch("src.domain.tender.services.documents.get_storage_client", return_value=mock_storage):
            document = await DocumentService.create(db_session, document_data)
        doc_id = document.id

        result = await DocumentService.delete(db_session, doc_id)
        assert result is True

        retrieved = await DocumentService.get(db_session, doc_id)
        assert retrieved is None

    async def test_delete_nonexistent_document_returns_false(self, db_session: AsyncSession):
        """delete() returns False for a non-existent document."""
        result = await DocumentService.delete(db_session, uuid4())
        assert result is False

    async def test_list_documents_by_tender(self, db_session: AsyncSession):
        """list() filters documents by tender_id."""
        tender = Tender(code=f"TND-{uuid4().hex[:8]}", title="List Tender")
        db_session.add(tender)
        await db_session.flush()
        tender_id = tender.id

        mock_storage = _make_mock_storage_client()
        with patch("src.domain.tender.services.documents.get_storage_client", return_value=mock_storage):
            for i in range(3):
                doc_data = DocumentCreate(
                    tender_id=tender_id,
                    filename=f"doc_{i}.pdf",
                )
                await DocumentService.create(db_session, doc_data)

        documents = await DocumentService.list(db_session, tender_id=tender_id)
        assert len(documents) == 3


@pytest.mark.asyncio
class TestTenderService:
    """Test TenderService business logic."""

    @pytest_asyncio.fixture
    async def tender_data(self):
        """Sample tender creation data."""
        return TenderCreate(
            code=f"TENDER-{uuid4().hex[:8]}",
            title="Test Tender",
            description="A tender for testing",
            status=TenderStatus.draft,
            buyer="Test Organization",
        )

    async def test_create_tender(self, db_session: AsyncSession, tender_data):
        """create() persists a new tender."""
        tender = await TenderService.create(db_session, tender_data)
        assert tender.id is not None
        assert tender.code == tender_data.code
        assert tender.status == TenderStatus.draft

    async def test_get_tender_by_id(self, db_session: AsyncSession, tender_data):
        """get() retrieves tender by primary key."""
        created = await TenderService.create(db_session, tender_data)
        retrieved = await TenderService.get(db_session, created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.code == tender_data.code

    async def test_get_nonexistent_tender_returns_none(self, db_session: AsyncSession):
        """get() returns None for unknown ID."""
        result = await TenderService.get(db_session, uuid4())
        assert result is None

    async def test_update_tender(self, db_session: AsyncSession, tender_data):
        """update() modifies tender fields."""
        tender = await TenderService.create(db_session, tender_data)
        update_data = TenderUpdate(title="Updated Title", status=TenderStatus.published)
        updated = await TenderService.update(db_session, tender.id, update_data)
        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.status == TenderStatus.published

    async def test_update_nonexistent_tender_returns_none(self, db_session: AsyncSession):
        """update() returns None for unknown tender ID."""
        result = await TenderService.update(db_session, uuid4(), TenderUpdate(title="X"))
        assert result is None

    async def test_delete_tender(self, db_session: AsyncSession, tender_data):
        """delete() removes a tender and returns True."""
        tender = await TenderService.create(db_session, tender_data)
        tid = tender.id

        result = await TenderService.delete(db_session, tid)
        assert result is True

        retrieved = await TenderService.get(db_session, tid)
        assert retrieved is None

    async def test_delete_nonexistent_tender_returns_false(self, db_session: AsyncSession):
        """delete() returns False for unknown tender ID."""
        result = await TenderService.delete(db_session, uuid4())
        assert result is False

    async def test_list_tenders(self, db_session: AsyncSession):
        """list() returns all created tenders."""
        for i in range(3):
            await TenderService.create(
                db_session,
                TenderCreate(code=f"LIST-{uuid4().hex[:6]}", title=f"Tender {i}"),
            )
        tenders = await TenderService.list(db_session)
        assert len(tenders) >= 3


@pytest.mark.asyncio
class TestLotService:
    """Test LotService business logic."""

    @pytest_asyncio.fixture
    async def tender(self, db_session: AsyncSession):
        """Create a parent tender for lot FK."""
        t = Tender(code=f"TND-{uuid4().hex[:8]}", title="Parent Tender")
        db_session.add(t)
        await db_session.flush()
        return t

    @pytest_asyncio.fixture
    async def lot_data(self, tender):
        """Sample lot creation data."""
        return LotCreate(
            tender_id=tender.id,
            code="LOT-001",
            title="Test Lot",
            description="A test lot",
            value_estimated=100000.0,
            currency="EUR",
        )

    async def test_create_lot(self, db_session: AsyncSession, lot_data):
        """create() persists a new lot."""
        lot = await LotService.create(db_session, lot_data)
        assert lot.id is not None
        assert lot.code == lot_data.code

    async def test_get_lot_by_id(self, db_session: AsyncSession, lot_data):
        """get() retrieves lot by primary key."""
        created = await LotService.create(db_session, lot_data)
        retrieved = await LotService.get(db_session, created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    async def test_get_nonexistent_lot_returns_none(self, db_session: AsyncSession):
        """get() returns None for unknown lot ID."""
        result = await LotService.get(db_session, uuid4())
        assert result is None

    async def test_update_lot(self, db_session: AsyncSession, lot_data):
        """update() modifies lot fields."""
        lot = await LotService.create(db_session, lot_data)
        update_data = LotUpdate(title="Updated Lot Title", value_estimated=150000.0)
        updated = await LotService.update(db_session, lot.id, update_data)
        assert updated is not None
        assert updated.title == "Updated Lot Title"
        assert float(updated.value_estimated) == 150000.0

    async def test_delete_lot(self, db_session: AsyncSession, lot_data):
        """delete() removes a lot and returns True."""
        lot = await LotService.create(db_session, lot_data)
        lid = lot.id

        result = await LotService.delete(db_session, lid)
        assert result is True

        retrieved = await LotService.get(db_session, lid)
        assert retrieved is None

    async def test_delete_nonexistent_lot_returns_false(self, db_session: AsyncSession):
        """delete() returns False for unknown lot ID."""
        result = await LotService.delete(db_session, uuid4())
        assert result is False

    async def test_list_lots_by_tender(self, db_session: AsyncSession, tender):
        """list() filters lots by tender_id."""
        tender_id = tender.id
        for i in range(3):
            await LotService.create(
                db_session,
                LotCreate(tender_id=tender_id, code=f"LOT-{i}", title=f"Lot {i}"),
            )
        lots = await LotService.list(db_session, tender_id=tender_id)
        assert len(lots) == 3

    async def test_list_lots_returns_all_when_no_filter(self, db_session: AsyncSession, tender):
        """list() returns all lots when no tender_id filter applied."""
        tender_id = tender.id
        for i in range(2):
            await LotService.create(
                db_session,
                LotCreate(tender_id=tender_id, code=f"LOTALL-{i}", title=f"Lot All {i}"),
            )
        lots = await LotService.list(db_session)
        assert len(lots) >= 2
