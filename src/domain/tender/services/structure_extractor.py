"""
Structure-based Entity Extraction for Tender Documents.

This module extracts structured entities from document metadata (section_path, 
page numbers, headings) to complement NER-based extraction. It provides higher
confidence for structured information like lot IDs, section types, and codes.

Architecture:
    - Regex patterns for common tender structures (LOT-XXXX, CIG, CUP)
    - Hierarchical section parsing from section_path
    - Deduplication and confidence scoring
    - Integration with NER entities via merge logic

Usage:
    extractor = StructureExtractor()
    entities = extractor.extract_from_chunks(chunks)
    # Returns: {'lot': [...], 'section': [...], 'code': [...]}
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class StructuredEntity:
    """Entity extracted from document structure.
    
    Attributes:
        type: Entity type (lot, section, code, buyer, etc.)
        id: Unique identifier (LOT-0001, CIG123, etc.)
        name: Human-readable name
        properties: Additional metadata
        source_chunk_id: Originating chunk ID for traceability
        confidence: Extraction confidence (0.0-1.0)
    """
    type: str
    id: Optional[str]
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    source_chunk_id: str = ""
    confidence: float = 1.0  # Structure-based = high confidence


class StructureExtractor:
    """Extract entities from document structure (section_path, metadata).
    
    This extractor uses regex patterns and hierarchical parsing to identify:
    - Lots (LOT-0001, Lotto 1, etc.)
    - Sections (Procedura, Requisiti, Criteri)
    - Codes (CIG, CUP, CPV)
    - Buyers (from "Committente" sections)
    
    Strategy:
        1. Parse section_path for hierarchical structure
        2. Apply regex patterns for known entities
        3. Extract metadata from chunk properties
        4. Deduplicate by (type, id) tuple
    """
    
    # Regex patterns for common tender structures
    LOT_PATTERN = re.compile(
        r'(?:lotto|lot)[:\s-]+(LOT-[A-Z0-9-]+|[A-Z]{2,}[0-9-]+)(?![a-zA-Z0-9-])',
        re.IGNORECASE
    )
    CIG_PATTERN = re.compile(
        r'CIG.*?([A-Z0-9]{10,})\b',
        re.IGNORECASE
    )
    CUP_PATTERN = re.compile(
        r'CUP[:\s]*([A-Z0-9]{15})',
        re.IGNORECASE
    )
    CPV_PATTERN = re.compile(
        r'CPV[:\s]*(\d{8}(?:-\d)?)',
        re.IGNORECASE
    )
    AMOUNT_PATTERN = re.compile(
        r"(?:importo|valore|base d['']asta)[:\s]*€?\s*([\d\.,]+)\s*(?:EUR|€)?",
        re.IGNORECASE
    )
    
    # Section type mappings (keyword → entity type)
    SECTION_TYPES = {
        'procedura': 'procedure',
        'requisiti': 'requirement',
        'criteri': 'criteria',
        'modalità': 'modality',
        'informazioni': 'information',
        'valore': 'value',
        'durata': 'duration',
        'finalità': 'purpose',
        'committente': 'buyer',
        'stazione appaltante': 'buyer',
        'aggiudicazione': 'award',
        'valutazione': 'evaluation',
    }
    
    def extract_from_chunk(self, chunk: Dict[str, Any]) -> List[StructuredEntity]:
        """Extract structured entities from a single chunk.
        
        Args:
            chunk: Dict with keys:
                - section_path: Hierarchical path (e.g., "5. Lotto > 5.1. LOT-0001")
                - metadata: Additional chunk metadata
                - text: Chunk text content
                - source_chunk_id: Chunk identifier
                
        Returns:
            List of StructuredEntity objects with high confidence scores
        """
        entities = []
        section_path = chunk.get('section_path', '')
        metadata = chunk.get('metadata', {})
        text = chunk.get('text', '')
        chunk_id = chunk.get('source_chunk_id', chunk.get('id', ''))
        
        if not section_path and not text:
            return entities
        
        # 1. Extract Lot entities from section_path
        lot_entities = self._extract_lots(section_path, text, chunk_id, metadata)
        entities.extend(lot_entities)
        
        # 2. Extract Section entities from hierarchical path
        section_entities = self._extract_sections(section_path, chunk_id, metadata)
        entities.extend(section_entities)
        
        # 3. Extract Code entities (CIG, CUP, CPV)
        code_entities = self._extract_codes(section_path, text, chunk_id)
        entities.extend(code_entities)
        
        # 4. Extract Buyer information
        buyer_entities = self._extract_buyer(section_path, text, chunk_id)
        entities.extend(buyer_entities)
        
        # 5. Extract monetary amounts
        amount_entities = self._extract_amounts(section_path, text, chunk_id)
        entities.extend(amount_entities)
        
        logger.debug(f"Extracted {len(entities)} structured entities from chunk {chunk_id}")
        return entities
    
    def _extract_lots(
        self, 
        section_path: str, 
        text: str, 
        chunk_id: str,
        metadata: Dict[str, Any]
    ) -> List[StructuredEntity]:
        """Extract lot entities from section path and text.
        
        Patterns matched:
        - "5. Lotto > 5.1. Lotto: LOT-0001"
        - "Lotto 1"
        - "LOT-0001"
        """
        entities = []
        
        # Search in section_path first (higher confidence)
        if 'lotto' in section_path.lower() or 'lot' in section_path.lower():
            lot_match = self.LOT_PATTERN.search(section_path)
            if lot_match:
                lot_id = lot_match.group(1).upper()
                entities.append(StructuredEntity(
                    type='lot',
                    id=lot_id,
                    name=f"Lotto {lot_id}",
                    properties={
                        'lot_id': lot_id,
                        'section_path': section_path,
                        'tender_id': metadata.get('tender_id', ''),
                        'page_numbers': metadata.get('page_numbers', []),
                    },
                    source_chunk_id=chunk_id,
                    confidence=0.95,  # High confidence from section_path
                ))
                logger.debug(f"Extracted lot: {lot_id} from section_path")
        
        # Fallback: search in text (medium confidence)
        if not entities:
            lot_match = self.LOT_PATTERN.search(text[:500])  # First 500 chars
            if lot_match:
                lot_id = lot_match.group(1).upper()
                entities.append(StructuredEntity(
                    type='lot',
                    id=lot_id,
                    name=f"Lotto {lot_id}",
                    properties={
                        'lot_id': lot_id,
                        'tender_id': metadata.get('tender_id', ''),
                    },
                    source_chunk_id=chunk_id,
                    confidence=0.75,  # Medium confidence from text
                ))
                logger.debug(f"Extracted lot: {lot_id} from text")
        
        return entities
    
    def _extract_sections(
        self, 
        section_path: str, 
        chunk_id: str,
        metadata: Dict[str, Any]
    ) -> List[StructuredEntity]:
        """Extract section entities from hierarchical section path.
        
        Example:
            Input: "2. Procedura > 2.1. Modalità di presentazione"
            Output: Section(type="procedure", number="2.1", ...)
        """
        entities = []
        
        if not section_path:
            return entities
        
        # Parse hierarchical sections: "2. Procedura > 2.1. Procedura Titolo"
        parts = [p.strip() for p in section_path.split('>')]
        
        for part in parts:
            # Check if part matches known section types
            for keyword, section_type in self.SECTION_TYPES.items():
                if keyword in part.lower():
                    # Extract section number (e.g., "2.1" from "2.1. Procedura Titolo")
                    number_match = re.match(r'(\d+(?:\.\d+)*)', part)
                    section_number = number_match.group(1) if number_match else None
                    
                    entities.append(StructuredEntity(
                        type='section',
                        id=section_number,
                        name=part,
                        properties={
                            'section_type': section_type,
                            'section_number': section_number,
                            'full_path': section_path,
                            'tender_id': metadata.get('tender_id', ''),
                            'keyword': keyword,
                        },
                        source_chunk_id=chunk_id,
                        confidence=0.9,
                    ))
                    logger.debug(f"Extracted section: {section_type} - {part}")
                    break  # One entity per part
        
        return entities
    
    def _extract_codes(
        self, 
        section_path: str, 
        text: str, 
        chunk_id: str
    ) -> List[StructuredEntity]:
        """Extract CIG, CUP, CPV codes from section path or text.
        
        Codes:
        - CIG: Codice Identificativo Gara (10+ alphanumeric)
        - CUP: Codice Unico Progetto (15 alphanumeric)
        - CPV: Common Procurement Vocabulary (8 digits)
        """
        entities = []
        combined = section_path + ' ' + text[:1000]  # Check first 1000 chars
        
        # Extract CIG
        cig_match = self.CIG_PATTERN.search(combined)
        if cig_match:
            cig_code = cig_match.group(1).upper()
            entities.append(StructuredEntity(
                type='code',
                id=f"CIG-{cig_code}",
                name=f"CIG {cig_code}",
                properties={
                    'code_type': 'CIG',
                    'code_value': cig_code,
                },
                source_chunk_id=chunk_id,
                confidence=0.95,
            ))
            logger.debug(f"Extracted CIG: {cig_code}")
        
        # Extract CUP
        cup_match = self.CUP_PATTERN.search(combined)
        if cup_match:
            cup_code = cup_match.group(1).upper()
            entities.append(StructuredEntity(
                type='code',
                id=f"CUP-{cup_code}",
                name=f"CUP {cup_code}",
                properties={
                    'code_type': 'CUP',
                    'code_value': cup_code,
                },
                source_chunk_id=chunk_id,
                confidence=0.95,
            ))
            logger.debug(f"Extracted CUP: {cup_code}")
        
        # Extract CPV
        cpv_match = self.CPV_PATTERN.search(combined)
        if cpv_match:
            cpv_code = cpv_match.group(1)
            entities.append(StructuredEntity(
                type='code',
                id=f"CPV-{cpv_code}",
                name=f"CPV {cpv_code}",
                properties={
                    'code_type': 'CPV',
                    'code_value': cpv_code,
                },
                source_chunk_id=chunk_id,
                confidence=0.9,
            ))
            logger.debug(f"Extracted CPV: {cpv_code}")
        
        return entities
    
    def _extract_buyer(
        self,
        section_path: str,
        text: str,
        chunk_id: str
    ) -> List[StructuredEntity]:
        """Extract buyer/contracting authority from section.
        
        Looks for sections containing:
        - "Committente"
        - "Stazione appaltante"
        - "Organizzazione"
        """
        entities = []
        
        # Check if this is a buyer section
        if any(kw in section_path.lower() for kw in ['committente', 'stazione appaltante']):
            # Extract organization name from text (first line or after colon)
            lines = text.strip().split('\n')
            buyer_name = None
            
            for line in lines[:5]:  # Check first 5 lines
                line = line.strip()
                if len(line) > 5 and not line.startswith(('Page', 'Pagina', '5.')):
                    buyer_name = line
                    break
            
            if buyer_name:
                entities.append(StructuredEntity(
                    type='buyer',
                    id=None,  # No unique ID for buyer
                    name=buyer_name,
                    properties={
                        'organization_name': buyer_name,
                        'section_path': section_path,
                    },
                    source_chunk_id=chunk_id,
                    confidence=0.85,
                ))
                logger.debug(f"Extracted buyer: {buyer_name}")
        
        return entities
    
    def _extract_amounts(
        self,
        section_path: str,
        text: str,
        chunk_id: str
    ) -> List[StructuredEntity]:
        """Extract monetary amounts from text.
        
        Patterns:
        - "Importo: € 1.000.000"
        - "Base d'asta: 500.000,00 EUR"
        - "Valore: € 250.000"
        """
        entities = []
        
        # Look for amount patterns in text
        amount_match = self.AMOUNT_PATTERN.search(text[:1000])
        if amount_match:
            amount_str = amount_match.group(1)
            # Parse amount (handle Italian number format: 1.000.000,00)
            amount_str = amount_str.replace('.', '').replace(',', '.')
            try:
                amount_value = float(amount_str)
                entities.append(StructuredEntity(
                    type='amount',
                    id=None,
                    name=f"€ {amount_value:,.2f}",
                    properties={
                        'amount': amount_value,
                        'currency': 'EUR',
                        'section_path': section_path,
                    },
                    source_chunk_id=chunk_id,
                    confidence=0.8,
                ))
                logger.debug(f"Extracted amount: € {amount_value:,.2f}")
            except ValueError:
                logger.warning(f"Failed to parse amount: {amount_str}")
        
        return entities
    
    def extract_from_chunks(
        self, 
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, List[StructuredEntity]]:
        """Extract entities from multiple chunks, grouped by type.
        
        Args:
            chunks: List of chunk dicts with section_path, metadata, text
            
        Returns:
            Dict mapping entity type to list of entities:
            {
                'lot': [StructuredEntity(type='lot', ...), ...],
                'section': [...],
                'code': [...],
                'buyer': [...],
                'amount': [...]
            }
        """
        all_entities: Dict[str, List[StructuredEntity]] = {}
        
        for chunk in chunks:
            entities = self.extract_from_chunk(chunk)
            for entity in entities:
                if entity.type not in all_entities:
                    all_entities[entity.type] = []
                all_entities[entity.type].append(entity)
        
        # Deduplicate entities by (type, id) tuple
        deduplicated = {}
        for entity_type, entities in all_entities.items():
            seen_keys = set()
            unique_entities = []
            for entity in entities:
                # For entities with no ID (buyer, amount), use name as key
                key = (entity.type, entity.id or entity.name)
                if key not in seen_keys:
                    seen_keys.add(key)
                    unique_entities.append(entity)
                else:
                    # Entity exists - keep higher confidence version
                    existing_idx = next(
                        i for i, e in enumerate(unique_entities)
                        if (e.type, e.id or e.name) == key
                    )
                    if entity.confidence > unique_entities[existing_idx].confidence:
                        unique_entities[existing_idx] = entity
            
            deduplicated[entity_type] = unique_entities
        
        total_count = sum(len(v) for v in deduplicated.values())
        logger.info(f"Extracted {total_count} unique structured entities across {len(deduplicated)} types")
        
        return deduplicated
