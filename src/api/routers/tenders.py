from __future__ import annotations

from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db_session
from src.domain.tender.schemas.tenders import TenderCreate, TenderOut, TenderUpdate
from src.domain.tender.services.tenders import TenderService
from src.infra.graph.tender_client import get_tender_graph_client


router = APIRouter(prefix="/tenders", tags=["tenders"])


@router.post("", response_model=TenderOut, status_code=status.HTTP_201_CREATED)
async def create_tender(payload: TenderCreate, db: AsyncSession = Depends(get_db_session)) -> TenderOut:
    obj = await TenderService.create(db, payload)
    return obj


@router.get("/{tender_id}", response_model=TenderOut)
async def get_tender(tender_id: UUID, db: AsyncSession = Depends(get_db_session)) -> TenderOut:
    obj = await TenderService.get(db, tender_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Tender not found")
    return obj


@router.get("", response_model=List[TenderOut])
async def list_tenders(limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db_session)) -> List[TenderOut]:
    return await TenderService.list(db, limit=limit, offset=offset)


@router.put("/{tender_id}", response_model=TenderOut)
async def update_tender(tender_id: UUID, payload: TenderUpdate, db: AsyncSession = Depends(get_db_session)) -> TenderOut:
    obj = await TenderService.update(db, tender_id, payload)
    if obj is None:
        raise HTTPException(status_code=404, detail="Tender not found")
    return obj


@router.delete("/{tender_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tender(tender_id: UUID, db: AsyncSession = Depends(get_db_session)) -> None:
    ok = await TenderService.delete(db, tender_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Tender not found")
    return None


@router.get("/{tender_id}/entities", response_model=Dict[str, Any])
async def get_tender_entities(tender_id: UUID, db: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    """
    Get tender with all extracted entities from Neo4j knowledge graph.

    This endpoint retrieves the tender's code from the relational DB,
    then queries Neo4j for all extracted entities including:
    - Organizations (buyers, issuers)
    - Requirements (technical, economic, administrative)
    - Deadlines (submission dates, Q&A deadlines, site visits)
    - Lots
    - Locations
    - Persons mentioned
    - CPV codes
    - Amounts/Values

    Returns:
        Dictionary with tender data and entities grouped by type
    """
    # First get tender from relational DB to get the code
    tender = await TenderService.get(db, tender_id)
    if tender is None:
        raise HTTPException(status_code=404, detail="Tender not found")

    # Get tender code
    tender_code = tender.code
    if not tender_code:
        # If no code, return empty entities
        return {"entities": {}}

    # Query Neo4j for entities
    graph_client = get_tender_graph_client()
    try:
        result = await graph_client.get_tender_with_all_entities(tender_code)

        if result is None:
            # Tender exists in relational DB but not in Neo4j yet
            return {"entities": {}}

        # Return only the entities part
        return result.get("entities", {})

    except Exception as e:
        # Log error but don't fail - just return empty entities
        import logging
        logging.error(f"Error fetching entities from Neo4j for tender {tender_code}: {e}")
        return {"entities": {}}
    finally:
        await graph_client.close()


__all__ = ["router"]
