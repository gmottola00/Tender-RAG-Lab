"""
Tender-specific Neo4j schema and operations.

This module contains domain-specific logic for the Tender Knowledge Graph:
- Schema constraints and indexes
- Domain-specific queries
- Business logic methods
"""
import logging
from typing import Any, Dict, List, Optional

from quaerium.infra.graphstores.neo4j import Neo4jClient
from quaerium.infra.graphstores.neo4j import convert_neo4j_types

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
            ("org_name_unique", "Organization", "name"),  # Changed from cf to name
            ("chunk_id_unique", "Chunk", "id"),
        ]
        
        for name, label, prop in constraints:
            await self.create_constraint(name, label, prop, "UNIQUE")
        
        # Indexes for common queries
        indexes = [
            ("tender_cpv", "Tender", "cpv_code"),
            ("tender_buyer", "Tender", "buyer_name"),
            ("tender_publication_date", "Tender", "publication_date"),
            ("requirement_mandatory", "Requirement", "mandatory"),
            ("requirement_type", "Requirement", "type"),
            ("deadline_date", "Deadline", "date_text"),
            ("deadline_type", "Deadline", "type"),
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

    async def add_requirement(
        self,
        requirement_id: str,
        requirement_type: str,
        description: str,
        mandatory: bool,
        tender_code: str,
        lot_id: Optional[str] = None,
        chunk_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Add a requirement to a tender (and optionally to a lot).

        Args:
            requirement_id: Unique requirement identifier
            requirement_type: Type (e.g., "tecnico", "economico", "amministrativo")
            description: Requirement description/text
            mandatory: Whether the requirement is mandatory
            tender_code: Parent tender code
            lot_id: Optional lot ID to link to
            chunk_id: Optional chunk ID where requirement is mentioned
            **kwargs: Additional requirement properties

        Returns:
            Summary statistics
        """
        # Build query dynamically based on what's linked
        query = """
        MATCH (t:Tender {code: $tender_code})
        """

        if lot_id:
            query += """
            MATCH (t)-[:HAS_LOT]->(l:Lot {id: $lot_id})
            """

        if chunk_id:
            query += """
            MATCH (c:Chunk {id: $chunk_id})
            """

        query += """
        MERGE (r:Requirement {id: $requirement_id})
        ON CREATE SET
            r.type = $requirement_type,
            r.description = $description,
            r.mandatory = $mandatory
        """

        # Create relationships
        if lot_id:
            query += """
            MERGE (l)-[:HAS_REQUIREMENT]->(r)
            """
        else:
            query += """
            MERGE (t)-[:HAS_REQUIREMENT]->(r)
            """

        if chunk_id:
            query += """
            MERGE (r)-[:MENTIONED_IN]->(c)
            """

        query += """
        RETURN r
        """

        params = {
            "tender_code": tender_code,
            "requirement_id": requirement_id,
            "requirement_type": requirement_type,
            "description": description,
            "mandatory": mandatory,
        }

        if lot_id:
            params["lot_id"] = lot_id
        if chunk_id:
            params["chunk_id"] = chunk_id

        params.update(kwargs)

        return await self.execute_write(query, params)

    async def add_deadline(
        self,
        deadline_id: str,
        deadline_type: str,
        date_text: str,
        tender_code: str,
        chunk_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Add a deadline to a tender.

        Args:
            deadline_id: Unique deadline identifier
            deadline_type: Type (e.g., "scadenza_offerta", "sopralluogo", "qna")
            date_text: Date as extracted text (e.g., "31 marzo 2025")
            tender_code: Parent tender code
            chunk_id: Optional chunk ID where deadline is mentioned
            **kwargs: Additional deadline properties

        Returns:
            Summary statistics
        """
        query = """
        MATCH (t:Tender {code: $tender_code})
        """

        if chunk_id:
            query += """
            MATCH (c:Chunk {id: $chunk_id})
            """

        query += """
        MERGE (d:Deadline {id: $deadline_id})
        ON CREATE SET
            d.type = $deadline_type,
            d.date_text = $date_text
        MERGE (t)-[:HAS_DEADLINE]->(d)
        """

        if chunk_id:
            query += """
            MERGE (d)-[:MENTIONED_IN]->(c)
            """

        query += """
        RETURN d
        """

        params = {
            "tender_code": tender_code,
            "deadline_id": deadline_id,
            "deadline_type": deadline_type,
            "date_text": date_text,
        }

        if chunk_id:
            params["chunk_id"] = chunk_id

        params.update(kwargs)

        return await self.execute_write(query, params)

    async def add_lot_from_structure(
        self,
        tender_code: str,
        lot_id: str,
        lot_name: str,
        section_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Add a Lot node extracted from document structure (section_path).
        
        Args:
            tender_code: Parent tender code
            lot_id: Lot identifier (e.g., "LOT-0001")
            lot_name: Lot description
            section_path: Original section path from chunk
            **kwargs: Additional properties (page_numbers, etc.)
            
        Returns:
            Created lot node summary
        """
        query = """
        MATCH (t:Tender {code: $tender_code})
        MERGE (l:Lot {id: $lot_id, tender_code: $tender_code})
        ON CREATE SET
            l.name = $lot_name,
            l.section_path = $section_path,
            l.source = 'structure',
            l.created_at = datetime()
        ON MATCH SET
            l.updated_at = datetime()
        MERGE (t)-[:HAS_LOT]->(l)
        RETURN l
        """
        
        params = {
            "tender_code": tender_code,
            "lot_id": lot_id,
            "lot_name": lot_name,
            "section_path": section_path,
        }
        params.update(kwargs)
        
        return await self.execute_write(query, params)

    async def add_section_from_structure(
        self,
        tender_code: str,
        section_number: str,
        section_type: str,
        section_name: str,
        full_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Add a Section node extracted from document structure.
        
        Args:
            tender_code: Parent tender code
            section_number: Section number (e.g., "2.1")
            section_type: Section type (procedure, requirement, criteria, etc.)
            section_name: Section full name
            full_path: Full hierarchical path
            **kwargs: Additional properties
            
        Returns:
            Created section node summary
        """
        query = """
        MATCH (t:Tender {code: $tender_code})
        MERGE (s:Section {
            number: $section_number,
            tender_code: $tender_code
        })
        ON CREATE SET
            s.type = $section_type,
            s.name = $section_name,
            s.full_path = $full_path,
            s.source = 'structure',
            s.created_at = datetime()
        ON MATCH SET
            s.updated_at = datetime()
        MERGE (t)-[:HAS_SECTION]->(s)
        RETURN s
        """
        
        params = {
            "tender_code": tender_code,
            "section_number": section_number,
            "section_type": section_type,
            "section_name": section_name,
            "full_path": full_path,
        }
        params.update(kwargs)
        
        return await self.execute_write(query, params)

    async def add_code_from_structure(
        self,
        tender_code: str,
        code_type: str,
        code_value: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Add a Code node (CIG, CUP, CPV) extracted from structure.
        
        Args:
            tender_code: Parent tender code
            code_type: Type of code (CIG, CUP, CPV)
            code_value: Code value
            **kwargs: Additional properties
            
        Returns:
            Created code node summary
        """
        query = """
        MATCH (t:Tender {code: $tender_code})
        MERGE (c:Code {type: $code_type, value: $code_value})
        ON CREATE SET
            c.source = 'structure',
            c.created_at = datetime()
        MERGE (t)-[:HAS_CODE]->(c)
        RETURN c
        """
        
        params = {
            "tender_code": tender_code,
            "code_type": code_type,
            "code_value": code_value,
        }
        params.update(kwargs)
        
        return await self.execute_write(query, params)

    async def add_buyer_from_structure(
        self,
        tender_code: str,
        buyer_name: str,
        section_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Add buyer/contracting authority from structure extraction.
        
        Args:
            tender_code: Parent tender code
            buyer_name: Organization name
            section_path: Source section path
            **kwargs: Additional properties
            
        Returns:
            Created organization node summary
        """
        query = """
        MATCH (t:Tender {code: $tender_code})
        MERGE (o:Organization {name: $buyer_name})
        ON CREATE SET
            o.role = 'buyer',
            o.section_path = $section_path,
            o.source = 'structure',
            o.created_at = datetime()
        ON MATCH SET
            o.updated_at = datetime()
        MERGE (t)-[:PUBLISHED_BY]->(o)
        RETURN o
        """
        
        params = {
            "tender_code": tender_code,
            "buyer_name": buyer_name,
            "section_path": section_path,
        }
        params.update(kwargs)
        
        return await self.execute_write(query, params)

    async def add_organization(
        self,
        name: str,
        role: str,
        tender_code: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Add an organization and optionally link to a tender.

        Args:
            name: Organization name
            role: Role (e.g., "ente_appaltante", "concorrente", "mentioned")
            tender_code: Optional tender to link to
            **kwargs: Additional organization properties

        Returns:
            Summary statistics
        """
        query = """
        MERGE (o:Organization {name: $name})
        ON CREATE SET o.role = $role
        """

        if tender_code:
            query += """
            WITH o
            MATCH (t:Tender {code: $tender_code})
            MERGE (t)-[:ISSUED_BY]->(o)
            """

        query += """
        RETURN o
        """

        params = {
            "name": name,
            "role": role,
        }

        if tender_code:
            params["tender_code"] = tender_code

        params.update(kwargs)

        return await self.execute_write(query, params)

    async def get_requirements_for_tender(
        self,
        tender_code: str,
        lot_id: Optional[str] = None,
        mandatory_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get all requirements for a tender (optionally filtered by lot).

        Args:
            tender_code: Tender code
            lot_id: Optional lot ID to filter
            mandatory_only: If True, return only mandatory requirements

        Returns:
            List of requirements with chunk references
        """
        query = """
        MATCH (t:Tender {code: $tender_code})
        """

        if lot_id:
            query += """
            MATCH (t)-[:HAS_LOT]->(l:Lot {id: $lot_id})
            MATCH (l)-[:HAS_REQUIREMENT]->(r:Requirement)
            """
        else:
            query += """
            MATCH (t)-[:HAS_REQUIREMENT]->(r:Requirement)
            """

        if mandatory_only:
            query += """
            WHERE r.mandatory = true
            """

        query += """
        OPTIONAL MATCH (r)-[:MENTIONED_IN]->(c:Chunk)
        RETURN r.id as requirement_id,
               r.type as type,
               r.description as description,
               r.mandatory as mandatory,
               collect(DISTINCT c.id) as chunk_ids
        ORDER BY r.mandatory DESC, r.id
        """

        params = {"tender_code": tender_code}
        if lot_id:
            params["lot_id"] = lot_id

        return await self.execute_query(query, params)

    async def get_deadlines_for_tender(
        self,
        tender_code: str,
    ) -> List[Dict[str, Any]]:
        """
        Get all deadlines for a tender.

        Args:
            tender_code: Tender code

        Returns:
            List of deadlines with chunk references
        """
        query = """
        MATCH (t:Tender {code: $tender_code})-[:HAS_DEADLINE]->(d:Deadline)
        OPTIONAL MATCH (d)-[:MENTIONED_IN]->(c:Chunk)
        RETURN d.id as deadline_id,
               d.type as type,
               d.date_text as date_text,
               collect(DISTINCT c.id) as chunk_ids
        ORDER BY d.date_text
        """

        return await self.execute_query(query, {"tender_code": tender_code})

    async def get_tender_with_all_entities(
        self,
        tender_code: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get tender with all extracted entities from the knowledge graph.

        This retrieves the complete tender graph including:
        - Tender basic information
        - Organizations (buyers, issuers)
        - Requirements (technical, economic, administrative)
        - Deadlines (submission, Q&A, site visits)
        - Lots (if any)
        - CPV codes
        - Locations
        - Amounts/Values

        Args:
            tender_code: Unique tender code (CIG)

        Returns:
            Dictionary with tender data and all entities grouped by type,
            or None if tender not found
        """
        query = """
        MATCH (t:Tender {code: $tender_code})

        // Get organizations
        OPTIONAL MATCH (t)-[:ISSUED_BY]->(org:Organization)
        WITH t, collect(DISTINCT {
            name: org.name,
            role: org.role,
            properties: properties(org)
        }) as organizations

        // Get requirements
        OPTIONAL MATCH (t)-[:HAS_REQUIREMENT]->(req:Requirement)
        WITH t, organizations, collect(DISTINCT {
            id: req.id,
            type: req.type,
            description: req.description,
            mandatory: req.mandatory,
            properties: properties(req)
        }) as requirements

        // Get deadlines
        OPTIONAL MATCH (t)-[:HAS_DEADLINE]->(deadline:Deadline)
        WITH t, organizations, requirements, collect(DISTINCT {
            id: deadline.id,
            type: deadline.type,
            date_text: deadline.date_text,
            properties: properties(deadline)
        }) as deadlines

        // Get lots
        OPTIONAL MATCH (t)-[:HAS_LOT]->(lot:Lot)
        WITH t, organizations, requirements, deadlines, collect(DISTINCT {
            id: lot.id,
            name: lot.name,
            cpv_code: lot.cpv_code,
            base_amount: lot.base_amount,
            properties: properties(lot)
        }) as lots

        // Get locations (if any entity has location)
        OPTIONAL MATCH (t)-[:HAS_LOCATION]->(loc:Location)
        WITH t, organizations, requirements, deadlines, lots, collect(DISTINCT {
            name: loc.name,
            address: loc.address,
            properties: properties(loc)
        }) as locations

        // Get persons mentioned
        OPTIONAL MATCH (t)-[:MENTIONS_PERSON]->(person:Person)
        WITH t, organizations, requirements, deadlines, lots, locations, collect(DISTINCT {
            name: person.name,
            role: person.role,
            properties: properties(person)
        }) as persons

        // Get CPV codes (additional ones beyond main)
        OPTIONAL MATCH (t)-[:HAS_CPV]->(cpv:CPVCode)
        WITH t, organizations, requirements, deadlines, lots, locations, persons, collect(DISTINCT {
            code: cpv.code,
            description: cpv.description,
            properties: properties(cpv)
        }) as cpv_codes

        // Get amounts/values
        OPTIONAL MATCH (t)-[:HAS_AMOUNT]->(amount:Amount)
        WITH t, organizations, requirements, deadlines, lots, locations, persons, cpv_codes, collect(DISTINCT {
            value: amount.value,
            type: amount.type,
            currency: amount.currency,
            properties: properties(amount)
        }) as amounts

        RETURN {
            tender: {
                code: t.code,
                title: t.title,
                cpv_code: t.cpv_code,
                base_amount: t.base_amount,
                buyer_name: t.buyer_name,
                publication_date: toString(t.publication_date)
            },
            entities: {
                organization: organizations,
                requirement: requirements,
                date: deadlines,
                lot: lots,
                location: locations,
                person: persons,
                cpv_code: cpv_codes,
                amount: amounts
            }
        } as result
        """

        results = await self.execute_query(query, {"tender_code": tender_code})

        if not results or not results[0]:
            return None

        data = results[0].get("result", {})

        # Convert Neo4j types (DateTime, Date, Time) to JSON-serializable types
        data = convert_neo4j_types(data)

        # Filter out empty entity arrays
        if "entities" in data:
            data["entities"] = {
                k: v for k, v in data["entities"].items()
                if v and len(v) > 0 and any(
                    item for item in v
                    if item and any(val for val in item.values() if val not in (None, "", []))
                )
            }

        return data

    async def delete_tender(self, tender_code: str) -> bool:
        """
        Delete a tender and ALL related entities from Neo4j (cascade delete).
        
        Deletes:
        - Tender node
        - All Lots (HAS_LOT)
        - All Sections (HAS_SECTION)
        - All Requirements (HAS_REQUIREMENT)
        - All Deadlines (HAS_DEADLINE)
        - All Codes (HAS_CODE)
        - All Chunks (MENTIONED_IN from requirements/deadlines)
        
        Args:
            tender_code: The tender code to delete
            
        Returns:
            True if tender was deleted, False if not found
        """
        query = """
        MATCH (t:Tender {code: $tender_code})
        
        // Collect all related entities into lists (so we can delete them even if some are empty)
        OPTIONAL MATCH (t)-[:HAS_LOT]->(lot:Lot)
        WITH t, collect(DISTINCT lot) as lots
        
        OPTIONAL MATCH (t)-[:HAS_SECTION]->(section:Section)
        WITH t, lots, collect(DISTINCT section) as sections
        
        OPTIONAL MATCH (t)-[:HAS_REQUIREMENT]->(req:Requirement)
        WITH t, lots, sections, collect(DISTINCT req) as requirements
        
        OPTIONAL MATCH (t)-[:HAS_DEADLINE]->(deadline:Deadline)
        WITH t, lots, sections, requirements, collect(DISTINCT deadline) as deadlines
        
        OPTIONAL MATCH (t)-[:HAS_CODE]->(code:Code)
        WITH t, lots, sections, requirements, deadlines, collect(DISTINCT code) as codes
        
        // Collect chunks from requirements and deadlines
        OPTIONAL MATCH (req)-[:MENTIONED_IN]->(chunk:Chunk)
        WHERE req IN requirements
        WITH t, lots, sections, requirements, deadlines, codes, collect(DISTINCT chunk) as req_chunks
        
        OPTIONAL MATCH (dl)-[:MENTIONED_IN]->(chunk:Chunk)
        WHERE dl IN deadlines
        WITH t, lots, sections, requirements, deadlines, codes, req_chunks, collect(DISTINCT chunk) as deadline_chunks
        
        // Combine all chunks
        WITH t, lots, sections, requirements, deadlines, codes, req_chunks + deadline_chunks as all_chunks
        
        // Delete all collected entities using FOREACH
        FOREACH (lot IN lots | DETACH DELETE lot)
        FOREACH (section IN sections | DETACH DELETE section)
        FOREACH (req IN requirements | DETACH DELETE req)
        FOREACH (deadline IN deadlines | DETACH DELETE deadline)
        FOREACH (code IN codes | DETACH DELETE code)
        FOREACH (chunk IN all_chunks | DETACH DELETE chunk)
        
        // Finally delete the tender
        DETACH DELETE t
        
        RETURN count(t) as deleted_count
        """
        
        result = await self.execute_write(query, {"tender_code": tender_code})
        if result and len(result) > 0:
            deleted_count = result[0].get("deleted_count", 0)
            if deleted_count > 0:
                logger.info(f"Cascade deleted tender {tender_code} and all related entities from Neo4j")
                return True
        
        logger.warning(f"Tender {tender_code} not found in Neo4j")
        return False

    async def delete_all_tenders(self) -> int:
        """
        Delete all tenders and ALL their related entities from Neo4j (cascade delete).
        
        Deletes:
        - All Tender nodes
        - All Lots, Sections, Requirements, Deadlines, Codes
        - All Chunks connected to requirements/deadlines
        
        Returns:
            Number of tenders deleted
        """
        query = """
        MATCH (t:Tender)
        
        // Collect all tenders first
        WITH collect(t) as tenders
        
        // For each tender, find and collect all related entities
        UNWIND tenders as tender
        
        OPTIONAL MATCH (tender)-[:HAS_LOT]->(lot:Lot)
        WITH tenders, tender, collect(DISTINCT lot) as lots
        
        OPTIONAL MATCH (tender)-[:HAS_SECTION]->(section:Section)
        WITH tenders, tender, lots, collect(DISTINCT section) as sections
        
        OPTIONAL MATCH (tender)-[:HAS_REQUIREMENT]->(req:Requirement)
        WITH tenders, tender, lots, sections, collect(DISTINCT req) as requirements
        
        OPTIONAL MATCH (tender)-[:HAS_DEADLINE]->(deadline:Deadline)
        WITH tenders, tender, lots, sections, requirements, collect(DISTINCT deadline) as deadlines
        
        OPTIONAL MATCH (tender)-[:HAS_CODE]->(code:Code)
        WITH tenders, tender, lots, sections, requirements, deadlines, collect(DISTINCT code) as codes
        
        // Collect chunks from requirements and deadlines
        OPTIONAL MATCH (req)-[:MENTIONED_IN]->(chunk:Chunk)
        WHERE req IN requirements
        WITH tenders, tender, lots, sections, requirements, deadlines, codes, collect(DISTINCT chunk) as req_chunks
        
        OPTIONAL MATCH (dl)-[:MENTIONED_IN]->(chunk:Chunk)
        WHERE dl IN deadlines
        WITH tenders, tender, lots, sections, requirements, deadlines, codes, req_chunks, collect(DISTINCT chunk) as deadline_chunks
        
        // Combine all chunks
        WITH tenders, tender, lots, sections, requirements, deadlines, codes, req_chunks + deadline_chunks as all_chunks
        
        // Delete all collected entities for this tender
        FOREACH (lot IN lots | DETACH DELETE lot)
        FOREACH (section IN sections | DETACH DELETE section)
        FOREACH (req IN requirements | DETACH DELETE req)
        FOREACH (deadline IN deadlines | DETACH DELETE deadline)
        FOREACH (code IN codes | DETACH DELETE code)
        FOREACH (chunk IN all_chunks | DETACH DELETE chunk)
        
        // Collect the tender for final deletion
        WITH tenders, tender
        
        // After processing all tenders, delete them
        WITH tenders
        FOREACH (t IN tenders | DETACH DELETE t)
        
        RETURN size(tenders) as deleted_count
        """
        
        result = await self.execute_write(query, {})
        if result and len(result) > 0:
            deleted_count = result[0].get("deleted_count", 0)
            logger.info(f"Cascade deleted {deleted_count} tender(s) and all related entities from Neo4j")
            return deleted_count
        
        return 0


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
