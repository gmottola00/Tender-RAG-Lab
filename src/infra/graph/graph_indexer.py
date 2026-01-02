"""
Graph-enhanced ingestion pipeline.

Extends standard ingestion to build Knowledge Graph during indexing.
"""
import logging
from typing import List, Dict, Any
from pathlib import Path

from src.infra.graph import get_tender_graph_client

logger = logging.getLogger(__name__)


async def index_tender_to_graph(
    tender_code: str,
    tender_metadata: Dict[str, Any],
    chunks: List[Dict[str, Any]],  # Generic dict, not domain model
) -> None:
    """
    Index tender and its chunks to Knowledge Graph.
    
    Args:
        tender_code: Unique tender code (CIG)
        tender_metadata: Tender information (title, buyer, amount, etc.)
        chunks: List of chunk dictionaries with keys: id, text, metadata
    
    Example:
        chunks = await chunk_document(file_path)
        await index_to_milvus(chunks)  # Standard flow
        
        # NEW: Also index to graph
        await index_tender_to_graph(
            tender_code="2025-001",
            tender_metadata={
                "title": "IT Services",
                "cpv_code": "72000000",
                "base_amount": 500000.0,
                "buyer_name": "Ministero",
                "publication_date": "2025-01-15"
            },
            chunks=chunks
        )
    """
    graph = get_tender_graph_client()
    
    try:
        # 1. Create tender node
        logger.info(f"Creating tender node: {tender_code}")
        await graph.create_tender(
            code=tender_code,
            title=tender_metadata["title"],
            cpv_code=tender_metadata["cpv_code"],
            base_amount=tender_metadata["base_amount"],
            buyer_name=tender_metadata["buyer_name"],
            publication_date=tender_metadata["publication_date"],
        )
        
        # 2. Create chunk nodes and link to tender
        logger.info(f"Linking {len(chunks)} chunks to tender {tender_code}")
        for chunk in chunks:
            # Handle both dict and object chunks
            chunk_id = chunk.get("id") if isinstance(chunk, dict) else chunk.id
            chunk_text = chunk.get("text") if isinstance(chunk, dict) else chunk.text
            chunk_meta = chunk.get("metadata", {}) if isinstance(chunk, dict) else getattr(chunk, "metadata", {})
            
            await graph.execute_write(
                """
                MATCH (t:Tender {code: $tender_code})
                CREATE (c:Chunk {
                    id: $chunk_id,
                    text_preview: $preview,
                    page_number: $page,
                    chunk_index: $index
                })
                CREATE (t)-[:HAS_CHUNK]->(c)
                """,
                {
                    "tender_code": tender_code,
                    "chunk_id": chunk_id,
                    "preview": chunk_text[:200] if chunk_text else "",
                    "page": chunk_meta.get("page_number", 0),
                    "index": chunk_meta.get("chunk_index", 0),
                }
            )
        
        logger.info(f"✅ Indexed tender {tender_code} to Knowledge Graph")
        
    except Exception as e:
        logger.error(f"Failed to index tender {tender_code} to graph: {e}")
        raise
    finally:
        await graph.close()


async def get_tender_context_for_chunks(
    chunk_ids: List[str]
) -> Dict[str, Dict[str, Any]]:
    """
    Get tender context for a list of chunks.
    
    Args:
        chunk_ids: List of chunk IDs
    
    Returns:
        Dictionary mapping chunk_id → tender_context
    
    Example:
        # After vector search
        search_results = await milvus_search("requisiti tecnici", top_k=5)
        chunk_ids = [r.id for r in search_results]
        
        # Get graph context
        contexts = await get_tender_context_for_chunks(chunk_ids)
        
        for result in search_results:
            tender_info = contexts.get(result.id)
            print(f"Chunk from tender: {tender_info['tender_title']}")
    """
    graph = get_tender_graph_client()
    
    try:
        # Query graph for all chunks at once
        results = await graph.execute_query(
            """
            UNWIND $chunk_ids as chunk_id
            MATCH (c:Chunk {id: chunk_id})<-[:HAS_CHUNK]-(t:Tender)
            RETURN c.id as chunk_id,
                   t.code as tender_code,
                   t.title as tender_title,
                   t.buyer_name as buyer_name,
                   t.cpv_code as cpv_code,
                   t.base_amount as base_amount,
                   t.publication_date as publication_date
            """,
            {"chunk_ids": chunk_ids}
        )
        
        # Build mapping
        context_map = {}
        for record in results:
            context_map[record["chunk_id"]] = {
                "tender_code": record["tender_code"],
                "tender_title": record["tender_title"],
                "buyer_name": record["buyer_name"],
                "cpv_code": record["cpv_code"],
                "base_amount": record["base_amount"],
                "publication_date": str(record["publication_date"]),
            }
        
        return context_map
        
    finally:
        await graph.close()


async def find_related_tenders(
    tender_code: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Find tenders related by CPV code or buyer.
    
    Args:
        tender_code: Reference tender code
        limit: Maximum related tenders to return
    
    Returns:
        List of related tenders with similarity score
    
    Example:
        # User is viewing tender "2025-001"
        related = await find_related_tenders("2025-001", limit=3)
        
        for tender in related:
            print(f"Similar: {tender['title']} (score: {tender['similarity']})")
    """
    graph = get_tender_graph_client()
    
    try:
        results = await graph.execute_query(
            """
            MATCH (t1:Tender {code: $tender_code})
            MATCH (t2:Tender)
            WHERE t2.code <> t1.code
            WITH t1, t2,
                 CASE 
                   WHEN t2.cpv_code STARTS WITH substring(t1.cpv_code, 0, 2) THEN 2
                   WHEN t2.buyer_name = t1.buyer_name THEN 1
                   ELSE 0
                 END as similarity_score
            WHERE similarity_score > 0
            RETURN t2.code as code,
                   t2.title as title,
                   t2.buyer_name as buyer_name,
                   t2.cpv_code as cpv_code,
                   t2.base_amount as base_amount,
                   similarity_score
            ORDER BY similarity_score DESC, t2.publication_date DESC
            LIMIT $limit
            """,
            {"tender_code": tender_code, "limit": limit}
        )
        
        return results
        
    finally:
        await graph.close()
