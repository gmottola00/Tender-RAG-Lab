from __future__ import annotations

from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db_session, get_indexer
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
    # Get tender to retrieve code before deletion
    tender = await TenderService.get(db, tender_id)
    if tender is None:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    tender_code = tender.code
    tender_id_str = str(tender_id)
    
    # Delete from PostgreSQL
    ok = await TenderService.delete(db, tender_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    # Delete from Neo4j if code exists (tender_code = code in Neo4j)
    if tender_code:
        graph_client = get_tender_graph_client()
        try:
            await graph_client.delete_tender(tender_code)
        except Exception as e:
            # Log error but don't fail - PostgreSQL deletion already happened
            import logging
            logging.warning(f"Failed to delete tender {tender_code} from Neo4j: {e}")
        finally:
            await graph_client.close()
    
    # Delete from Milvus (id in PostgreSQL = tender_id in Milvus)
    try:
        indexer = get_indexer()
        milvus_result = indexer.delete_by_tender_id(tender_id_str)
        import logging
        logging.info(f"Deleted {milvus_result.get('delete_count', 0)} chunks from Milvus for tender {tender_id_str}")
    except Exception as e:
        # Log error but don't fail
        import logging
        logging.warning(f"Failed to delete tender {tender_id_str} chunks from Milvus: {e}")
    
    return None


@router.delete("", status_code=status.HTTP_200_OK)
async def delete_all_tenders(db: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    """Delete all tenders from PostgreSQL, Neo4j, and Milvus.
    
    Returns:
        Dictionary with count of deleted items from all databases
    """
    # Delete from PostgreSQL
    pg_count = await TenderService.delete_all(db)
    
    # Delete from Neo4j
    graph_client = get_tender_graph_client()
    neo4j_count = 0
    try:
        neo4j_count = await graph_client.delete_all_tenders()
    except Exception as e:
        # Log error but don't fail
        import logging
        logging.warning(f"Failed to delete tenders from Neo4j: {e}")
    finally:
        await graph_client.close()
    
    # Delete from Milvus (all chunks)
    milvus_count = 0
    try:
        indexer = get_indexer()
        milvus_result = indexer.delete_all()
        milvus_count = milvus_result.get('delete_count', 0)
    except Exception as e:
        # Log error but don't fail
        import logging
        logging.warning(f"Failed to delete chunks from Milvus: {e}")
    
    return {
        "deleted_count": pg_count,
        "neo4j_deleted_count": neo4j_count,
        "milvus_deleted_count": milvus_count,
        "message": f"Deleted {pg_count} tender(s) from PostgreSQL, {neo4j_count} from Neo4j, and {milvus_count} chunks from Milvus"
    }



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
