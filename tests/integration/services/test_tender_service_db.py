"""Integration tests for TenderService with real SQLite in-memory database.

Uses the ``db_session`` fixture from the root conftest (real AsyncSession
backed by SQLite). All external services are irrelevant here.

Tests cover:
- generate_next_code with empty DB (first tender → FY26-0001)
- generate_next_code with existing tender (increments correctly)
- generate_next_code with corrupted code format (fallback to -0001)
- CRUD lifecycle: create → get → update status → delete
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.tender.entities.tenders import Tender, TenderStatus
from src.domain.tender.schemas.tenders import TenderCreate, TenderUpdate
from src.domain.tender.services.tenders import TenderService


# ── generate_next_code ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_next_code_empty_db_returns_fy26_0001(
    db_session: AsyncSession,
):
    """With no tenders in DB, generate_next_code() returns FY26-0001."""
    code = await TenderService.generate_next_code(db_session, fiscal_year="FY26")
    assert code == "FY26-0001"


@pytest.mark.asyncio
async def test_generate_next_code_increments_last_code(db_session: AsyncSession):
    """With FY26-0003 existing, next code is FY26-0004."""
    existing = Tender(code="FY26-0003", title="Existing Tender")
    db_session.add(existing)
    await db_session.commit()

    code = await TenderService.generate_next_code(db_session, fiscal_year="FY26")
    assert code == "FY26-0004"


@pytest.mark.asyncio
async def test_generate_next_code_uses_current_fiscal_year_by_default(
    db_session: AsyncSession,
):
    """Without explicit fiscal_year, code uses current year (FY{YY})."""
    from datetime import datetime

    current_year = datetime.now().year
    expected_prefix = f"FY{str(current_year)[2:]}"

    code = await TenderService.generate_next_code(db_session)
    assert code.startswith(expected_prefix)
    assert code.endswith("-0001")  # No tenders for current year in test DB


@pytest.mark.asyncio
async def test_generate_next_code_with_corrupted_format_falls_back(
    db_session: AsyncSession,
):
    """Tender with non-numeric sequence (FY26-XXXX) falls back to FY26-0001."""
    bad = Tender(code="FY26-XXXX", title="Corrupted Code")
    db_session.add(bad)
    await db_session.commit()

    code = await TenderService.generate_next_code(db_session, fiscal_year="FY26")
    # The code "FY26-XXXX" sorts higher than "FY26-0001", so it will be last.
    # split("-")[1] = "XXXX" → ValueError → fallback to next_num=1
    assert code == "FY26-0001"


# ── CRUD lifecycle ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_tender_persists_to_db(db_session: AsyncSession):
    """TenderService.create() persists tender and returns it with an id."""
    data = TenderCreate(code="FY26-CRUD-01", title="CRUD Test Tender")
    tender = await TenderService.create(db_session, data)

    assert tender.id is not None
    assert tender.code == "FY26-CRUD-01"
    assert tender.title == "CRUD Test Tender"


@pytest.mark.asyncio
async def test_get_tender_after_create(db_session: AsyncSession):
    """TenderService.get() retrieves the tender created in the same session."""
    data = TenderCreate(code="FY26-CRUD-02", title="Get Test")
    created = await TenderService.create(db_session, data)

    retrieved = await TenderService.get(db_session, created.id)
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.code == created.code


@pytest.mark.asyncio
async def test_update_tender_status(db_session: AsyncSession):
    """TenderService.update() changes status from draft to published."""
    data = TenderCreate(code="FY26-CRUD-03", title="Update Status Test", status=TenderStatus.draft)
    tender = await TenderService.create(db_session, data)

    updated = await TenderService.update(
        db_session, tender.id, TenderUpdate(status=TenderStatus.published)
    )
    assert updated is not None
    assert updated.status == TenderStatus.published
    assert updated.title == tender.title  # Other fields unchanged


@pytest.mark.asyncio
async def test_delete_tender(db_session: AsyncSession):
    """TenderService.delete() removes the tender; subsequent get() returns None."""
    data = TenderCreate(code="FY26-CRUD-04", title="Delete Test")
    tender = await TenderService.create(db_session, data)
    tid = tender.id

    result = await TenderService.delete(db_session, tid)
    assert result is True

    gone = await TenderService.get(db_session, tid)
    assert gone is None


@pytest.mark.asyncio
async def test_delete_nonexistent_tender_returns_false(db_session: AsyncSession):
    """TenderService.delete() returns False for an unknown UUID."""
    from uuid import uuid4

    result = await TenderService.delete(db_session, uuid4())
    assert result is False


@pytest.mark.asyncio
async def test_list_tenders_returns_all(db_session: AsyncSession):
    """TenderService.list() returns all tenders created in this test."""
    codes = [f"LIST-{i:03d}" for i in range(3)]
    for code in codes:
        await TenderService.create(db_session, TenderCreate(code=code, title=f"T {code}"))

    tenders = await TenderService.list(db_session)
    listed_codes = [t.code for t in tenders]
    for code in codes:
        assert code in listed_codes
