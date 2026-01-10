"""Entity extraction service for tender documents.

Extracts entities using NER and populates Neo4j knowledge graph.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.domain.tender.ner.spacy_ner import TenderNER, create_tender_ner
from src.domain.tender.schemas.chunking import TenderChunk

logger = logging.getLogger(__name__)


class EntityExtractionService:
    """Service for extracting entities from tender documents and populating graph."""
    
    def __init__(
        self,
        ner: Optional[TenderNER] = None,
        neo4j_client=None,  # TODO: Add Neo4j client type hint
    ):
        """Initialize entity extraction service.
        
        Args:
            ner: TenderNER instance (creates default if None)
            neo4j_client: Neo4j client for graph operations
        """
        self.ner = ner or create_tender_ner()
        self.neo4j_client = neo4j_client
        logger.info(f"EntityExtractionService initialized with {self.ner}")
    
    def extract_from_chunks(
        self,
        chunks: List[TenderChunk],
        tender_id: str,
    ) -> Dict[str, Any]:
        """Extract entities from all chunks and aggregate results.
        
        Args:
            chunks: List of tender chunks to process
            tender_id: Tender ID for linking entities
        
        Returns:
            Aggregated entity extraction results:
            {
                "tender_id": "...",
                "total_chunks": 10,
                "entities_by_type": {
                    "ORGANIZATION": ["Comune di Milano", ...],
                    "PERSON": ["Mario Rossi", ...],
                    ...
                },
                "entity_count": 25,
                "chunks_with_entities": [...]
            }
        """
        logger.info(f"Extracting entities from {len(chunks)} chunks for tender {tender_id}")
        
        # Process all chunks
        enriched_chunks = self.ner.process_chunks(chunks, text_field="text")
        
        # Aggregate entities (deduplicate across chunks)
        aggregated: Dict[str, List[str]] = {}
        chunks_with_entities = []
        
        for chunk_data in enriched_chunks:
            entities = chunk_data.get("entities", {})

            # Track chunks that have entities
            if entities:
                chunks_with_entities.append({
                    "chunk_id": chunk_data.get("chunk_id"),
                    "text": chunk_data.get("text", ""),  # Include text for pattern matching
                    "entities": entities,
                })
            
            # Aggregate by type
            for entity_type, entity_list in entities.items():
                if entity_type not in aggregated:
                    aggregated[entity_type] = []
                
                for entity in entity_list:
                    if entity not in aggregated[entity_type]:
                        aggregated[entity_type].append(entity)
        
        total_entities = sum(len(v) for v in aggregated.values())
        
        result = {
            "tender_id": tender_id,
            "total_chunks": len(chunks),
            "entities_by_type": aggregated,
            "entity_count": total_entities,
            "chunks_with_entities": chunks_with_entities,
        }
        
        logger.info(
            f"Extracted {total_entities} entities from {len(chunks_with_entities)} chunks",
            extra=result
        )
        
        return result
    
    async def populate_graph(
        self,
        extraction_result: Dict[str, Any],
        tender_code: str,
    ) -> Dict[str, int]:
        """Populate Neo4j graph with extracted entities.

        Creates nodes for entities and relationships to tender.

        Args:
            extraction_result: Result from extract_from_chunks()
            tender_code: Tender CIG/CUP code for graph linking

        Returns:
            Statistics about created nodes/relationships:
            {
                "organizations_created": 5,
                "people_created": 3,
                "locations_created": 2,
                "requirements_created": 4,
                "deadlines_created": 3,
                "relationships_created": 10
            }

        Example Cypher queries generated:
            MERGE (t:Tender {code: 'CIG-12345'})
            MERGE (o:Organization {name: 'Comune di Milano'})
            MERGE (t)-[:ISSUED_BY]->(o)
        """
        if not self.neo4j_client:
            logger.warning("Neo4j client not configured, skipping graph population")
            return {}

        entities = extraction_result.get("entities_by_type", {})
        chunks_with_entities = extraction_result.get("chunks_with_entities", [])

        stats = {
            "organizations_created": 0,
            "people_created": 0,
            "locations_created": 0,
            "requirements_created": 0,
            "deadlines_created": 0,
            "relationships_created": 0,
        }

        # 1. Populate Organizations
        for org_name in entities.get("ORGANIZATION", []):
            try:
                await self.neo4j_client.add_organization(
                    name=org_name,
                    role="mentioned",  # Can be refined with classification
                    tender_code=tender_code,
                )
                stats["organizations_created"] += 1
                stats["relationships_created"] += 1  # ISSUED_BY relationship
                logger.debug(f"Created Organization: {org_name}")
            except Exception as e:
                logger.warning(f"Failed to create Organization '{org_name}': {e}")

        # 2. Create Chunk nodes first (needed for MENTIONED_IN relationships)
        chunks_created = 0
        for chunk_data in chunks_with_entities:
            chunk_id = chunk_data["chunk_id"]
            chunk_text = chunk_data.get("text", "")

            try:
                # Create chunk node if it doesn't exist
                chunk_query = """
                MERGE (c:Chunk {id: $chunk_id})
                ON CREATE SET c.text_preview = substring($text, 0, 200)
                RETURN c
                """
                await self.neo4j_client.execute_write(
                    chunk_query,
                    {"chunk_id": chunk_id, "text": chunk_text}
                )
                chunks_created += 1
            except Exception as e:
                logger.warning(f"Failed to create Chunk '{chunk_id}': {e}")

        logger.debug(f"Created {chunks_created} chunk nodes")

        # 3. Extract Requirements from patterns
        # Pattern matching for mandatory requirements
        requirement_patterns = [
            # Strict mandatory indicators
            "obbligatorio",
            "obbligatoria",
            "pena esclusione",
            "pena di esclusione",
            "pena l'esclusione",
            "comporta l'esclusione",
            "sarà escluso",
            "saranno esclusi",
            # Modal verbs
            "deve",
            "devono",
            "dovrà",
            "dovranno",
            # Requirements indicators
            "è richiesto",
            "è richiesta",
            "sono richiesti",
            "sono richieste",
            "necessario",
            "necessaria",
            "necessari",
            "necessarie",
            "requisito",
            "requisiti",
            # Common phrases in tender documents
            "in possesso di",
            "essere in possesso",
            "possedere",
            "dimostrare",
            "attestare",
            "certificare",
            "documentare",
        ]

        for chunk_data in chunks_with_entities:
            chunk_id = chunk_data["chunk_id"]
            chunk_text = chunk_data.get("text", "")

            # Check if chunk contains requirement indicators
            if any(pattern in chunk_text.lower() for pattern in requirement_patterns):
                req_id = f"req-{tender_code}-{chunk_id[:8]}"

                # Determine if mandatory based on strict keywords
                is_mandatory = any(
                    kw in chunk_text.lower()
                    for kw in ["obbligatorio", "pena esclusione", "pena di esclusione"]
                )

                # Extract relevant sentences (simple approach)
                sentences = chunk_text.split(".")
                for sent in sentences:
                    sent_lower = sent.lower()
                    if any(pattern in sent_lower for pattern in requirement_patterns):
                        try:
                            await self.neo4j_client.add_requirement(
                                requirement_id=req_id,
                                requirement_type="extracted",
                                description=sent.strip()[:500],  # Limit description length
                                mandatory=is_mandatory,
                                tender_code=tender_code,
                                chunk_id=chunk_id,
                            )
                            stats["requirements_created"] += 1
                            stats["relationships_created"] += 2  # HAS_REQUIREMENT + MENTIONED_IN
                            logger.debug(f"Created Requirement: {req_id} (mandatory={is_mandatory})")
                            break  # One requirement per chunk for now
                        except Exception as e:
                            logger.warning(f"Failed to create Requirement: {e}")
                            break

        # 4. Extract Deadlines from DATE entities
        deadline_patterns = [
            # Generic deadline indicators
            "scadenza",
            "entro",
            "entro il",
            "entro la",
            "termine",
            "termine ultimo",
            "termine perentorio",
            "data limite",
            "data di",
            "data prevista",
            "data ultima",
            # Specific deadline types
            "presentazione",
            "presentazione offerta",
            "presentazione delle offerte",
            "presentazione domande",
            "sopralluogo",
            "sopralluoghi",
            "chiarimenti",
            "chiarimento",
            "quesiti",
            "richiesta di chiarimenti",
            # Other common deadline phrases
            "apertura buste",
            "aggiudicazione",
            "pubblicazione",
            "pubblicato",
            "invio",
            "consegna",
            "firma contratto",
        ]

        for chunk_data in chunks_with_entities:
            chunk_id = chunk_data["chunk_id"]
            chunk_text = chunk_data.get("text", "")
            dates = chunk_data.get("entities", {}).get("DATE", [])

            # Check if chunk has deadline context
            chunk_lower = chunk_text.lower()
            has_deadline_context = any(pattern in chunk_lower for pattern in deadline_patterns)

            if dates and has_deadline_context:
                for date_str in dates:
                    # Determine deadline type from context
                    deadline_type = "generic"
                    if "presentazione" in chunk_lower and "offerta" in chunk_lower:
                        deadline_type = "scadenza_offerta"
                    elif "sopralluogo" in chunk_lower:
                        deadline_type = "sopralluogo"
                    elif "chiariment" in chunk_lower or "quesit" in chunk_lower:
                        deadline_type = "qna"
                    elif "scadenza" in chunk_lower:
                        deadline_type = "scadenza_generica"

                    deadline_id = f"deadline-{tender_code}-{hash(date_str) % 100000}"

                    try:
                        await self.neo4j_client.add_deadline(
                            deadline_id=deadline_id,
                            deadline_type=deadline_type,
                            date_text=date_str,
                            tender_code=tender_code,
                            chunk_id=chunk_id,
                        )
                        stats["deadlines_created"] += 1
                        stats["relationships_created"] += 2  # HAS_DEADLINE + MENTIONED_IN
                        logger.debug(f"Created Deadline: {deadline_id} ({deadline_type}: {date_str})")
                    except Exception as e:
                        logger.warning(f"Failed to create Deadline for '{date_str}': {e}")

        logger.info(
            f"Graph populated for tender {tender_code}: "
            f"{stats['organizations_created']} orgs, "
            f"{stats['requirements_created']} reqs, "
            f"{stats['deadlines_created']} deadlines"
        )

        return stats
    
    async def extract_and_populate(
        self,
        chunks: List[TenderChunk],
        tender_id: str,
        tender_code: str,
    ) -> Dict[str, Any]:
        """Complete pipeline: extract entities + populate graph.

        Args:
            chunks: Tender chunks to process
            tender_id: Internal tender ID
            tender_code: Tender CIG/CUP code

        Returns:
            Combined extraction + graph statistics
        """
        # Extract entities
        extraction = self.extract_from_chunks(chunks, tender_id)

        # Populate graph
        graph_stats = await self.populate_graph(extraction, tender_code)

        return {
            **extraction,
            "graph_stats": graph_stats,
        }


def create_entity_extraction_service(
    ner_model: str = "it_core_news_lg",
    neo4j_client=None,
) -> EntityExtractionService:
    """Factory function to create EntityExtractionService.
    
    Args:
        ner_model: spaCy model name
        neo4j_client: Neo4j client instance
    
    Returns:
        Configured EntityExtractionService
    """
    ner = create_tender_ner(model_name=ner_model)
    return EntityExtractionService(ner=ner, neo4j_client=neo4j_client)
