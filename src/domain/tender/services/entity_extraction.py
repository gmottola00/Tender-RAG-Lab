"""Entity extraction service for tender documents.

Extracts entities using:
1. Structure-based extraction (section_path, metadata) - HIGH CONFIDENCE
2. NER-based extraction (spaCy) - MEDIUM CONFIDENCE

The hybrid approach leverages document structure (lots, sections, codes) 
while complementing with NER for unstructured entities (organizations, people).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.domain.tender.ner.spacy_ner import TenderNER, create_tender_ner
from src.domain.tender.schemas.chunking import TenderChunk
from src.domain.tender.services.structure_extractor import StructureExtractor, StructuredEntity

logger = logging.getLogger(__name__)


class EntityExtractionService:
    """Service for extracting entities from tender documents and populating graph.
    
    Uses hybrid extraction strategy:
    - Structure-based: Lots, sections, codes (CIG/CUP/CPV), buyers from section_path
    - NER-based: Organizations, people, locations, dates, money from text
    
    The structured entities have higher confidence and are prioritized during merge.
    """
    
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
        self.structure_extractor = StructureExtractor()  # ✅ NEW
        logger.debug(f"EntityExtractionService initialized with hybrid extraction")
    
    def extract_from_chunks(
        self,
        chunks: List[TenderChunk],
        tender_id: str,
    ) -> Dict[str, Any]:
        """Extract entities from all chunks using hybrid approach.
        
        Pipeline:
        1. Structure extraction from section_path and metadata (HIGH confidence)
        2. NER extraction from text content (MEDIUM confidence)
        3. Merge and deduplicate entities
        
        Args:
            chunks: List of tender chunks to process
            tender_id: Tender ID for linking entities
        
        Returns:
            Aggregated entity extraction results:
            {
                "tender_id": "...",
                "total_chunks": 10,
                "entities_by_type": {
                    "lot": [StructuredEntity(...)],  # From structure
                    "section": [StructuredEntity(...)],  # From structure
                    "code": [StructuredEntity(...)],  # From structure (CIG, CUP, CPV)
                    "ORGANIZATION": ["Comune di Milano"],  # From NER
                    "PERSON": ["Mario Rossi"],  # From NER
                    ...
                },
                "entity_count": 25,
                "chunks_with_entities": [...],
                "structured_count": 8,  # Number from structure
                "ner_count": 17,  # Number from NER
            }
        """
        logger.info(f"🔍 Extracting entities from {len(chunks)} chunks for tender {tender_id}")
        
        # ===== 1. STRUCTURE-BASED EXTRACTION =====
        chunk_dicts = [
            {
                'section_path': getattr(chunk, 'section_path', ''),
                'metadata': getattr(chunk, 'metadata', {}),
                'text': chunk.text,
                'source_chunk_id': chunk.id,
                'id': chunk.id,
            }
            for chunk in chunks
        ]
        
        structured_entities = self.structure_extractor.extract_from_chunks(chunk_dicts)
        structured_count = sum(len(v) for v in structured_entities.values())
        logger.info(f"📊 Structure extraction: {structured_count} entities")
        
        # ===== 2. NER-BASED EXTRACTION =====
        enriched_chunks = self.ner.process_chunks(chunks, text_field="text")
        
        # Aggregate NER entities (deduplicate across chunks)
        ner_aggregated: Dict[str, List[str]] = {}
        chunks_with_entities = []
        
        for chunk_data in enriched_chunks:
            entities = chunk_data.get("entities", {})

            # Track chunks that have entities
            if entities:
                chunks_with_entities.append({
                    "chunk_id": chunk_data.get("chunk_id"),
                    "text": chunk_data.get("text", ""),
                    "entities": entities,
                })
            
            # Aggregate by type
            for entity_type, entity_list in entities.items():
                if entity_type not in ner_aggregated:
                    ner_aggregated[entity_type] = []
                
                for entity in entity_list:
                    if entity not in ner_aggregated[entity_type]:
                        ner_aggregated[entity_type].append(entity)
        
        ner_count = sum(len(v) for v in ner_aggregated.values())
        logger.info(f"🤖 NER extraction: {ner_count} entities from {len(chunks_with_entities)} chunks")
        
        # ===== 3. MERGE STRUCTURED + NER =====
        merged_entities = self._merge_entities(structured_entities, ner_aggregated)
        total_entities = sum(len(v) for v in merged_entities.values())
        
        result = {
            "tender_id": tender_id,
            "total_chunks": len(chunks),
            "entities_by_type": merged_entities,
            "entity_count": total_entities,
            "structured_count": structured_count,
            "ner_count": ner_count,
            "chunks_with_entities": chunks_with_entities,
        }
        
        logger.info(
            f"✅ Total: {total_entities} entities "
            f"({structured_count} structured + {ner_count} NER)"
        )
        
        return result
    
    def _merge_entities(
        self,
        structured: Dict[str, List[StructuredEntity]],
        ner_entities: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Merge structured and NER entities with priority to structured.
        
        Strategy:
        - Structured entities kept as-is (high confidence)
        - NER entities added if not overlapping with structured
        - For buyers: prefer structured extraction from "Committente" section
        
        Args:
            structured: Dict of structured entities by type
            ner_entities: Dict of NER entities (strings) by type
            
        Returns:
            Merged dict with both structured entities and NER strings
        """
        merged = {}
        
        # Add structured entities first (prioritized)
        for entity_type, entities in structured.items():
            merged[entity_type] = entities
        
        # Add NER entities (check for overlaps)
        for entity_type, entity_names in ner_entities.items():
            if entity_type not in merged:
                merged[entity_type] = []
            
            # Get existing names from structured entities to avoid duplicates
            existing_names_lower = set()
            if entity_type in structured:
                for entity in structured[entity_type]:
                    existing_names_lower.add(entity.name.lower())
            
            # Add NER entities that don't overlap
            for entity_name in entity_names:
                if entity_name.lower() not in existing_names_lower:
                    merged[entity_type].append(entity_name)
        
        logger.debug(f"Merged {len(merged)} entity types")
        return merged
    
    async def populate_graph(
        self,
        extraction_result: Dict[str, Any],
        tender_code: str,
    ) -> Dict[str, int]:
        """Populate Neo4j graph with extracted entities (structured + NER).

        Priority order:
        1. Structured entities (lots, sections, codes, buyers) - HIGH confidence
        2. NER entities (organizations, people, locations) - MEDIUM confidence
        3. Pattern-based entities (requirements, deadlines) - MEDIUM confidence

        Args:
            extraction_result: Result from extract_from_chunks()
            tender_code: Tender CIG/CUP code for graph linking

        Returns:
            Statistics about created nodes/relationships:
            {
                "lots_created": 3,
                "sections_created": 12,
                "codes_created": 3,  # CIG, CUP, CPV
                "buyers_created": 1,
                "organizations_created": 5,
                "people_created": 3,
                "locations_created": 2,
                "requirements_created": 4,
                "deadlines_created": 3,
                "relationships_created": 30
            }
        """
        if not self.neo4j_client:
            logger.warning("Neo4j client not configured, skipping graph population")
            return {}

        entities = extraction_result.get("entities_by_type", {})
        chunks_with_entities = extraction_result.get("chunks_with_entities", [])

        stats = {
            "lots_created": 0,
            "sections_created": 0,
            "codes_created": 0,
            "buyers_created": 0,
            "organizations_created": 0,
            "people_created": 0,
            "locations_created": 0,
            "requirements_created": 0,
            "deadlines_created": 0,
            "relationships_created": 0,
        }

        logger.info(f"📝 Populating graph for tender {tender_code}")

        # ===== 1. STRUCTURED ENTITIES (High Priority) =====
        
        # 1a. Lots from section_path
        for lot_entity in entities.get("lot", []):
            try:
                if isinstance(lot_entity, StructuredEntity):
                    await self.neo4j_client.add_lot_from_structure(
                        tender_code=tender_code,
                        lot_id=lot_entity.id,
                        lot_name=lot_entity.name,
                        section_path=lot_entity.properties.get('section_path', ''),
                        page_numbers=lot_entity.properties.get('page_numbers', []),
                    )
                    stats["lots_created"] += 1
                    stats["relationships_created"] += 1  # HAS_LOT
                    logger.debug(f"Created Lot: {lot_entity.id}")
            except Exception as e:
                logger.warning(f"Failed to create Lot '{lot_entity.id}': {e}")

        # 1b. Sections from hierarchical structure
        for section_entity in entities.get("section", []):
            try:
                if isinstance(section_entity, StructuredEntity):
                    await self.neo4j_client.add_section_from_structure(
                        tender_code=tender_code,
                        section_number=section_entity.id or "unknown",
                        section_type=section_entity.properties.get('section_type', 'unknown'),
                        section_name=section_entity.name,
                        full_path=section_entity.properties.get('full_path', ''),
                    )
                    stats["sections_created"] += 1
                    stats["relationships_created"] += 1  # HAS_SECTION
            except Exception as e:
                logger.warning(f"Failed to create Section '{section_entity.name}': {e}")

        # 1c. Codes (CIG, CUP, CPV)
        for code_entity in entities.get("code", []):
            try:
                if isinstance(code_entity, StructuredEntity):
                    await self.neo4j_client.add_code_from_structure(
                        tender_code=tender_code,
                        code_type=code_entity.properties.get('code_type', 'UNKNOWN'),
                        code_value=code_entity.properties.get('code_value', ''),
                    )
                    stats["codes_created"] += 1
                    stats["relationships_created"] += 1  # HAS_CODE
                    logger.debug(f"Created Code: {code_entity.name}")
            except Exception as e:
                logger.warning(f"Failed to create Code '{code_entity.name}': {e}")

        # 1d. Buyers from "Committente" sections
        for buyer_entity in entities.get("buyer", []):
            try:
                if isinstance(buyer_entity, StructuredEntity):
                    await self.neo4j_client.add_buyer_from_structure(
                        tender_code=tender_code,
                        buyer_name=buyer_entity.name,
                        section_path=buyer_entity.properties.get('section_path', ''),
                    )
                    stats["buyers_created"] += 1
                    stats["relationships_created"] += 1  # PUBLISHED_BY
                    logger.debug(f"Created Buyer: {buyer_entity.name}")
            except Exception as e:
                logger.warning(f"Failed to create Buyer '{buyer_entity.name}': {e}")

        # ===== 2. NER ENTITIES =====
        
        # 2a. Organizations (from NER - avoid duplicates with structured buyers)
        ner_orgs = [e for e in entities.get("ORGANIZATION", []) if isinstance(e, str)]
        for org_name in ner_orgs:
            try:
                await self.neo4j_client.add_organization(
                    name=org_name,
                    role="mentioned",
                    tender_code=tender_code,
                )
                stats["organizations_created"] += 1
                stats["relationships_created"] += 1  # ISSUED_BY relationship
            except Exception as e:
                logger.warning(f"Failed to create Organization '{org_name}': {e}")

        # 2b. Create Chunk nodes first (needed for MENTIONED_IN relationships)
        chunks_created = 0
        for chunk_data in chunks_with_entities:
            chunk_id = chunk_data["chunk_id"]
            chunk_text = chunk_data.get("text", "")

            try:
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

        if chunks_created > 0:
            logger.debug(f"Created {chunks_created} chunk nodes")

        # ===== 3. PATTERN-BASED ENTITIES =====
        
        # 3a. Extract Requirements from patterns
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

        # ===== FINAL STATS =====
        logger.info(
            f"✅ Graph populated for tender {tender_code}:\n"
            f"  📦 Structured: {stats['lots_created']} lots, "
            f"{stats['sections_created']} sections, "
            f"{stats['codes_created']} codes, "
            f"{stats['buyers_created']} buyers\n"
            f"  🤖 NER: {stats['organizations_created']} orgs, "
            f"{stats['requirements_created']} reqs, "
            f"{stats['deadlines_created']} deadlines\n"
            f"  🔗 Total: {stats['relationships_created']} relationships"
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
