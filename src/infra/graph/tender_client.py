"""
Tender-specific Neo4j schema and operations.

This module contains domain-specific logic for the Tender Knowledge Graph:
- Schema constraints and indexes
- Domain-specific queries
- Business logic methods
"""
import logging
from typing import Any, Dict, List, Optional

from src.infra.graph.base_client import Neo4jClient

logger = logging.getLogger(__name__)


class TenderGraphClient(Neo4jClient):
    """
    Tender-specific Neo4j client with domain logic.
    
    Extends the generic Neo4jClient with Tender-specific methods:
    - Schema setup (constraints/indexes for Tender, Lot, etc.)
    - Business queries (find tenders by CPV, get tender with lots, etc.)
    - Domain validations
    """
    
    async def create_tender_schema(self):
        """
        Create constraints and indexes for tender domain model.
        
        Schema includes:
        - Tender: code (unique), cpv_code, buyer_name, publication_date
        - Lot: id (unique), cpv_code
        - Requirement: id (unique), mandatory
        - Deadline: id (unique), date
        - Organization: cf (unique - codice fiscale)
        
        Call this once during initial setup.
        """
        logger.info("Creating Tender domain schema...")
        
        # Uniqueness constraints
        constraints = [
            ("tender_code_unique", "Tender", "code"),
            ("lot_id_unique", "Lot", "id"),
            ("requirement_id_unique", "Requirement", "id"),
            ("deadline_id_unique", "Deadline", "id"),
            ("org_cf_unique", "Organization", "cf"),
        ]
        
        for name, label, prop in constraints:
            await self.create_constraint(name, label, prop, "UNIQUE")
        
        # Indexes for common queries
        indexes = [
            ("tender_cpv", "Tender", "cpv_code"),
            ("tender_buyer", "Tender", "buyer_name"),
            ("tender_publication_date", "Tender", "publication_date"),
            ("requirement_mandatory", "Requirement", "mandatory"),
            ("deadline_date", "Deadline", "date"),
            ("lot_cpv", "Lot", "cpv_code"),
        ]
        
        for name, label, prop in indexes:
            await self.create_index(name, label, prop, "RANGE")
        
        logger.info("✅ Tender schema created successfully")
    
    async def create_tender(
        self,
        code: str,
        title: str,
        cpv_code: str,
        base_amount: float,
        buyer_name: str,
        publication_date: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new Tender node.
        
        Args:
            code: Unique tender code (CIG)
            title: Tender title/description
            cpv_code: CPV classification code
            base_amount: Base auction amount (€)
            buyer_name: Buyer/contracting authority name
            publication_date: Publication date (ISO format: YYYY-MM-DD)
            **kwargs: Additional tender properties
        
        Returns:
            Summary statistics
        """
        query = """
        CREATE (t:Tender {
            code: $code,
            title: $title,
            cpv_code: $cpv_code,
            base_amount: $base_amount,
            buyer_name: $buyer_name,
            publication_date: date($publication_date)
        })
        RETURN t
        """
        
        params = {
            "code": code,
            "title": title,
            "cpv_code": cpv_code,
            "base_amount": base_amount,
            "buyer_name": buyer_name,
            "publication_date": publication_date,
        }
        params.update(kwargs)
        
        return await self.execute_write(query, params)
    
    async def get_tender_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Get tender by unique code (CIG).
        
        Args:
            code: Tender code
        
        Returns:
            Tender data or None if not found
        """
        query = """
        MATCH (t:Tender {code: $code})
        RETURN t.code as code, 
               t.title as title, 
               t.cpv_code as cpv_code,
               t.base_amount as base_amount,
               t.buyer_name as buyer_name,
               t.publication_date as publication_date
        """
        
        results = await self.execute_query(query, {"code": code})
        return results[0] if results else None
    
    async def get_tender_with_lots(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Get tender with all its lots.
        
        Args:
            code: Tender code
        
        Returns:
            Tender data with lots array
        """
        query = """
        MATCH (t:Tender {code: $code})
        OPTIONAL MATCH (t)-[:HAS_LOT]->(l:Lot)
        RETURN t.code as code,
               t.title as title,
               t.base_amount as base_amount,
               collect({
                   id: l.id,
                   name: l.name,
                   cpv_code: l.cpv_code,
                   base_amount: l.base_amount
               }) as lots,
               count(l) as lot_count,
               sum(l.base_amount) as total_lots_amount
        """
        
        results = await self.execute_query(query, {"code": code})
        return results[0] if results else None
    
    async def find_tenders_by_cpv(
        self,
        cpv_code: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find tenders by CPV code.
        
        Args:
            cpv_code: CPV classification code (can be partial, e.g., "72" for IT)
            limit: Maximum results to return
        
        Returns:
            List of matching tenders
        """
        query = """
        MATCH (t:Tender)
        WHERE t.cpv_code STARTS WITH $cpv_code
        RETURN t.code as code,
               t.title as title,
               t.cpv_code as cpv_code,
               t.base_amount as base_amount,
               t.buyer_name as buyer_name,
               t.publication_date as publication_date
        ORDER BY t.publication_date DESC
        LIMIT $limit
        """
        
        return await self.execute_query(
            query,
            {"cpv_code": cpv_code, "limit": limit}
        )
    
    async def find_tenders_by_buyer(
        self,
        buyer_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find tenders by buyer name (case-insensitive partial match).
        
        Args:
            buyer_name: Buyer name or partial name
            limit: Maximum results to return
        
        Returns:
            List of matching tenders
        """
        query = """
        MATCH (t:Tender)
        WHERE toLower(t.buyer_name) CONTAINS toLower($buyer_name)
        RETURN t.code as code,
               t.title as title,
               t.buyer_name as buyer_name,
               t.base_amount as base_amount,
               t.publication_date as publication_date
        ORDER BY t.publication_date DESC
        LIMIT $limit
        """
        
        return await self.execute_query(
            query,
            {"buyer_name": buyer_name, "limit": limit}
        )
    
    async def add_lot_to_tender(
        self,
        tender_code: str,
        lot_id: str,
        lot_name: str,
        cpv_code: str,
        base_amount: float,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Add a lot to an existing tender.
        
        Args:
            tender_code: Parent tender code
            lot_id: Unique lot identifier
            lot_name: Lot name/description
            cpv_code: CPV code for the lot
            base_amount: Lot base amount (€)
            **kwargs: Additional lot properties
        
        Returns:
            Summary statistics
        """
        query = """
        MATCH (t:Tender {code: $tender_code})
        CREATE (l:Lot {
            id: $lot_id,
            name: $lot_name,
            cpv_code: $cpv_code,
            base_amount: $base_amount
        })
        CREATE (t)-[:HAS_LOT]->(l)
        RETURN l
        """
        
        params = {
            "tender_code": tender_code,
            "lot_id": lot_id,
            "lot_name": lot_name,
            "cpv_code": cpv_code,
            "base_amount": base_amount,
        }
        params.update(kwargs)
        
        return await self.execute_write(query, params)


def get_tender_graph_client() -> TenderGraphClient:
    """
    Factory function to create TenderGraphClient from settings.
    
    Returns:
        Configured TenderGraphClient instance
    
    Usage:
        client = get_tender_graph_client()
        await client.verify_connectivity()
        await client.create_tender_schema()
        tender = await client.get_tender_by_code("TENDER-2025-001")
    """
    from configs.config import get_settings
    
    settings = get_settings()
    
    return TenderGraphClient(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD,
        database=settings.NEO4J_DATABASE,
    )
