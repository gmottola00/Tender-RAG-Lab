"""Graph-enriched hybrid retrieval strategy.

This module provides hybrid search capabilities that combine:
1. Vector search (Milvus) for semantic similarity
2. Knowledge graph (Neo4j) for structured entity context

Use cases:
- Enrich vector search results with graph context (requirements, deadlines, orgs)
- Graph-first queries for structured data (all deadlines, mandatory requirements)
- Hybrid orchestration for optimal retrieval strategy
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.infra.graph import get_tender_graph_client

logger = logging.getLogger(__name__)


class GraphEnrichedRetriever:
    """Hybrid retriever that enriches vector search with graph context.

    This retriever implements multiple strategies:
    1. Vector-first + graph enrichment: Standard semantic search enhanced with entities
    2. Graph-first: Direct queries to knowledge graph for structured data
    3. Hybrid orchestration: Automatically choose best strategy based on query type

    Example:
        >>> retriever = GraphEnrichedRetriever(vector_searcher=milvus_search)
        >>> results = await retriever.search_with_graph_context(
        ...     query="Quali sono i requisiti obbligatori?",
        ...     tender_code="CIG-2025-001",
        ...     top_k=5
        ... )
        >>> for r in results:
        ...     print(r["graph_context"]["requirements"])
    """

    def __init__(self, vector_searcher=None, neo4j_client=None):
        """Initialize graph-enriched retriever.

        Args:
            vector_searcher: Vector search service (Milvus/Qdrant)
                Must implement async search(query, filters, top_k) -> List[Dict]
            neo4j_client: Neo4j client for graph queries
                If None, creates new client from settings
        """
        self.vector_searcher = vector_searcher
        self.neo4j_client = neo4j_client or get_tender_graph_client()

    async def search_with_graph_context(
        self,
        query: str,
        tender_code: str,
        top_k: int = 5,
        use_graph_enrichment: bool = True,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search with graph enrichment (vector-first strategy).

        Pipeline:
        1. Vector search on Milvus (semantic similarity)
        2. For each chunk, retrieve connected entities from graph
        3. Enrich results with graph context

        Args:
            query: User query
            tender_code: Tender code to filter
            top_k: Number of results to return
            use_graph_enrichment: Whether to add graph context
            filters: Additional filters for vector search

        Returns:
            List of enriched search results:
            [
                {
                    "chunk_id": "uuid-123",
                    "text": "Chunk text...",
                    "score": 0.85,
                    "metadata": {...},
                    "graph_context": {
                        "requirements": [
                            {
                                "id": "req-001",
                                "description": "ISO 27001 obbligatoria",
                                "mandatory": true,
                                "type": "extracted"
                            }
                        ],
                        "deadlines": [...],
                        "organizations": [...]
                    }
                }
            ]

        Example:
            >>> results = await retriever.search_with_graph_context(
            ...     query="certificazioni richieste",
            ...     tender_code="CIG-2025-001"
            ... )
            >>> print(results[0]["graph_context"]["requirements"])
        """
        if not self.vector_searcher:
            raise ValueError("Vector searcher not configured")

        # 1. Vector search
        search_filters = filters or {}
        search_filters["tender_code"] = tender_code

        logger.info(f"Vector search: query='{query}', tender={tender_code}, top_k={top_k}")

        vector_results = await self.vector_searcher.search(
            query=query,
            filters=search_filters,
            top_k=top_k,
        )

        if not use_graph_enrichment:
            logger.debug("Graph enrichment disabled, returning vector results only")
            return vector_results

        # 2. Enrich with graph
        chunk_ids = [r.get("chunk_id") or r.get("id") for r in vector_results]

        logger.debug(f"Enriching {len(chunk_ids)} chunks with graph context")

        graph_context = await self._get_graph_context_for_chunks(chunk_ids, tender_code)

        # 3. Merge contexts
        enriched = []
        for result in vector_results:
            chunk_id = result.get("chunk_id") or result.get("id")
            result["graph_context"] = graph_context.get(chunk_id, {
                "requirements": [],
                "deadlines": [],
                "organizations": [],
            })
            enriched.append(result)

        logger.info(f"Returned {len(enriched)} enriched results")
        return enriched

    async def _get_graph_context_for_chunks(
        self,
        chunk_ids: List[str],
        tender_code: str,
    ) -> Dict[str, Dict[str, Any]]:
        """Get entities connected to chunks via graph.

        Args:
            chunk_ids: List of chunk IDs to get context for
            tender_code: Tender code for scoping

        Returns:
            Dictionary mapping chunk_id -> graph_context:
            {
                "chunk-123": {
                    "requirements": [...],
                    "deadlines": [...],
                    "organizations": [...]
                }
            }
        """
        if not chunk_ids:
            return {}

        query = """
        UNWIND $chunk_ids as chunk_id
        MATCH (c:Chunk {id: chunk_id})

        // Get requirements mentioning this chunk
        OPTIONAL MATCH (r:Requirement)-[:MENTIONED_IN]->(c)

        // Get deadlines mentioning this chunk
        OPTIONAL MATCH (d:Deadline)-[:MENTIONED_IN]->(c)

        // Get organizations related to the tender
        OPTIONAL MATCH (t:Tender {code: $tender_code})-[:ISSUED_BY]->(o:Organization)

        RETURN c.id as chunk_id,
               collect(DISTINCT {
                   id: r.id,
                   description: r.description,
                   mandatory: r.mandatory,
                   type: r.type
               }) as requirements,
               collect(DISTINCT {
                   id: d.id,
                   date_text: d.date_text,
                   type: d.type
               }) as deadlines,
               collect(DISTINCT {
                   name: o.name,
                   role: o.role
               }) as organizations
        """

        try:
            results = await self.neo4j_client.execute_query(
                query,
                {"chunk_ids": chunk_ids, "tender_code": tender_code}
            )

            # Build mapping
            context_map = {}
            for record in results:
                # Filter out null entities (from OPTIONAL MATCH)
                context_map[record["chunk_id"]] = {
                    "requirements": [r for r in record["requirements"] if r.get("id")],
                    "deadlines": [d for d in record["deadlines"] if d.get("id")],
                    "organizations": [o for o in record["organizations"] if o.get("name")],
                }

            return context_map

        except Exception as e:
            logger.error(f"Failed to get graph context: {e}")
            # Return empty context on error (graceful degradation)
            return {chunk_id: {"requirements": [], "deadlines": [], "organizations": []}
                    for chunk_id in chunk_ids}

    async def search_requirements(
        self,
        tender_code: str,
        lot_id: Optional[str] = None,
        mandatory_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """Graph-first search: Get all requirements for tender/lot.

        This bypasses vector search and queries the graph directly.
        Use case: UC1 from roadmap - "Lista tutti i requisiti obbligatori"

        Args:
            tender_code: Tender code
            lot_id: Optional lot ID to filter
            mandatory_only: If True, return only mandatory requirements

        Returns:
            List of requirements with chunk references:
            [
                {
                    "requirement_id": "req-001",
                    "description": "Certificazione ISO 27001 obbligatoria",
                    "type": "extracted",
                    "mandatory": true,
                    "chunk_ids": ["chunk-abc", "chunk-def"]
                }
            ]

        Example:
            >>> reqs = await retriever.search_requirements(
            ...     tender_code="CIG-2025-001",
            ...     mandatory_only=True
            ... )
            >>> print(f"Found {len(reqs)} mandatory requirements")
        """
        logger.info(f"Graph-first search: requirements for {tender_code}, lot={lot_id}, mandatory={mandatory_only}")

        try:
            results = await self.neo4j_client.get_requirements_for_tender(
                tender_code=tender_code,
                lot_id=lot_id,
                mandatory_only=mandatory_only,
            )

            logger.info(f"Found {len(results)} requirements")
            return results

        except Exception as e:
            logger.error(f"Failed to search requirements: {e}")
            return []

    async def search_deadlines(
        self,
        tender_code: str,
    ) -> List[Dict[str, Any]]:
        """Graph-first search: Get all deadlines for tender.

        This bypasses vector search and queries the graph directly.
        Use case: UC4 from roadmap - "Elenca tutte le scadenze"

        Args:
            tender_code: Tender code

        Returns:
            List of deadlines with chunk references:
            [
                {
                    "deadline_id": "deadline-001",
                    "type": "scadenza_offerta",
                    "date_text": "31 marzo 2025",
                    "chunk_ids": ["chunk-xyz"]
                }
            ]

        Example:
            >>> deadlines = await retriever.search_deadlines("CIG-2025-001")
            >>> for d in deadlines:
            ...     print(f"{d['type']}: {d['date_text']}")
        """
        logger.info(f"Graph-first search: deadlines for {tender_code}")

        try:
            results = await self.neo4j_client.get_deadlines_for_tender(
                tender_code=tender_code
            )

            logger.info(f"Found {len(results)} deadlines")
            return results

        except Exception as e:
            logger.error(f"Failed to search deadlines: {e}")
            return []

    async def close(self):
        """Close Neo4j connection."""
        if self.neo4j_client:
            await self.neo4j_client.close()


def create_graph_enriched_retriever(
    vector_searcher=None,
    neo4j_client=None,
) -> GraphEnrichedRetriever:
    """Factory function to create GraphEnrichedRetriever.

    Args:
        vector_searcher: Vector search service
        neo4j_client: Neo4j client (creates default if None)

    Returns:
        Configured GraphEnrichedRetriever

    Example:
        >>> from src.infra.vector.milvus import get_milvus_searcher
        >>> retriever = create_graph_enriched_retriever(
        ...     vector_searcher=get_milvus_searcher()
        ... )
        >>> results = await retriever.search_with_graph_context(...)
    """
    return GraphEnrichedRetriever(
        vector_searcher=vector_searcher,
        neo4j_client=neo4j_client,
    )
