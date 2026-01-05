"""Named Entity Recognition using spaCy for tender documents.

This module provides NER capabilities for extracting structured entities
from tender and procurement documents in Italian language.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import spacy
from spacy.language import Language
from spacy.tokens import Doc

logger = logging.getLogger(__name__)


class TenderNER:
    """Named Entity Recognition for tender documents using spaCy.
    
    Extracts entities like organizations, people, locations, dates, and monetary
    amounts from tender documents to enrich knowledge graph and metadata.
    
    Supported entity types:
        - PER (PERSON): Names of people (e.g., "Mario Rossi", "Dott. Bianchi")
        - ORG (ORGANIZATION): Companies, institutions (e.g., "Comune di Milano")
        - LOC (LOCATION): Places, addresses (e.g., "Milano", "Via Roma 10")
        - GPE (GEO-POLITICAL ENTITY): Cities, countries, states
        - DATE: Temporal expressions (e.g., "30 gennaio 2026")
        - MONEY: Monetary amounts (e.g., "€500.000", "1.2 milioni")
        - PERCENT: Percentages
        - CARDINAL: Numeric values
    
    Example:
        >>> ner = TenderNER()
        >>> text = "Il Comune di Milano indice gara per €500.000"
        >>> entities = ner.extract_entities(text)
        >>> print(entities)
        {'ORG': ['Comune di Milano'], 'MONEY': ['€500.000']}
    """
    
    # Mapping from spaCy Italian labels to simplified labels
    LABEL_MAPPING = {
        "PER": "PERSON",
        "ORG": "ORGANIZATION",
        "LOC": "LOCATION",
        "GPE": "LOCATION",  # Treat GPE as generic location
    }
    
    def __init__(
        self,
        model_name: str = "it_core_news_lg",
        use_gpu: bool = False,
    ):
        """Initialize TenderNER with spaCy Italian model.
        
        Args:
            model_name: spaCy model name. Options:
                - "it_core_news_sm" (35MB, fast, lower accuracy)
                - "it_core_news_md" (90MB, balanced)
                - "it_core_news_lg" (550MB, best accuracy, recommended)
            use_gpu: Whether to use GPU acceleration (requires spacy[cuda])
        
        Raises:
            OSError: If the specified model is not installed.
                     Run: python -m spacy download <model_name>
        """
        self.model_name = model_name
        
        try:
            if use_gpu:
                spacy.prefer_gpu()
                logger.info("GPU acceleration enabled for spaCy")
            
            self.nlp: Language = spacy.load(model_name)
            logger.info(f"Loaded spaCy model: {model_name}")
            
        except OSError as e:
            logger.error(f"Failed to load spaCy model '{model_name}'. "
                        f"Install it with: python -m spacy download {model_name}")
            raise
    
    def extract_entities(
        self,
        text: str,
        normalize_labels: bool = True,
        min_length: int = 2,
    ) -> Dict[str, List[str]]:
        """Extract named entities from text, grouped by type.
        
        Args:
            text: Input text to extract entities from
            normalize_labels: Whether to map spaCy labels to simplified labels
            min_length: Minimum character length for entity (filters noise)
        
        Returns:
            Dictionary mapping entity types to lists of entity texts:
            {
                "PERSON": ["Mario Rossi", "Dott. Bianchi"],
                "ORGANIZATION": ["Comune di Milano"],
                "LOCATION": ["Milano"],
                "DATE": ["30 gennaio 2026"],
                "MONEY": ["€500.000"]
            }
        
        Example:
            >>> ner = TenderNER()
            >>> entities = ner.extract_entities(
            ...     "Il RUP Mario Rossi del Comune di Milano."
            ... )
            >>> entities["PERSON"]
            ['Mario Rossi']
        """
        if not text or not text.strip():
            return {}
        
        doc: Doc = self.nlp(text)
        entities: Dict[str, List[str]] = {}
        
        for ent in doc.ents:
            # Filter short entities (often noise)
            if len(ent.text.strip()) < min_length:
                continue
            
            # Map label if normalization enabled
            label = ent.label_
            if normalize_labels and label in self.LABEL_MAPPING:
                label = self.LABEL_MAPPING[label]
            
            # Add to result
            if label not in entities:
                entities[label] = []
            
            # Avoid duplicates
            entity_text = ent.text.strip()
            if entity_text not in entities[label]:
                entities[label].append(entity_text)
        
        return entities
    
    def extract_with_positions(
        self,
        text: str,
        normalize_labels: bool = True,
    ) -> List[Dict[str, Any]]:
        """Extract entities with their positions in the text.
        
        Useful for highlighting entities in UI or creating precise references.
        
        Args:
            text: Input text to extract entities from
            normalize_labels: Whether to map spaCy labels to simplified labels
        
        Returns:
            List of entity dictionaries with text, label, and positions:
            [
                {
                    "text": "Comune di Milano",
                    "label": "ORGANIZATION",
                    "start": 10,
                    "end": 26,
                    "start_char": 10,
                    "end_char": 26
                },
                ...
            ]
        
        Example:
            >>> ner = TenderNER()
            >>> entities = ner.extract_with_positions(
            ...     "Il Comune di Milano indice gara."
            ... )
            >>> entities[0]
            {'text': 'Comune di Milano', 'label': 'ORGANIZATION', 'start': 3, 'end': 19}
        """
        if not text or not text.strip():
            return []
        
        doc: Doc = self.nlp(text)
        result = []
        
        for ent in doc.ents:
            label = ent.label_
            if normalize_labels and label in self.LABEL_MAPPING:
                label = self.LABEL_MAPPING[label]
            
            result.append({
                "text": ent.text.strip(),
                "label": label,
                "start": ent.start_char,
                "end": ent.end_char,
                "start_char": ent.start_char,  # Alias for compatibility
                "end_char": ent.end_char,
            })
        
        return result
    
    def extract_tender_metadata(self, text: str) -> Dict[str, Any]:
        """Extract tender-specific metadata using NER.
        
        Extracts and categorizes entities most relevant for tender documents:
        - Issuing organizations
        - Key people (RUP, contact persons)
        - Locations
        - Deadlines and dates
        - Monetary amounts
        
        Args:
            text: Tender document text
        
        Returns:
            Structured metadata dictionary:
            {
                "organizations": ["Comune di Milano"],
                "people": ["Mario Rossi"],
                "locations": ["Milano"],
                "dates": ["30 gennaio 2026"],
                "amounts": ["€500.000"],
                "all_entities": {...}  # Full entity extraction
            }
        
        Example:
            >>> ner = TenderNER()
            >>> metadata = ner.extract_tender_metadata(tender_text)
            >>> print(metadata["organizations"])
            ['Comune di Milano', 'Regione Lombardia']
        """
        entities = self.extract_entities(text, normalize_labels=True)
        
        return {
            "organizations": entities.get("ORGANIZATION", []),
            "people": entities.get("PERSON", []),
            "locations": entities.get("LOCATION", []),
            "dates": entities.get("DATE", []),
            "amounts": entities.get("MONEY", []),
            "all_entities": entities,
        }
    
    def process_chunks(
        self,
        chunks: List[Any],
        text_field: str = "text",
    ) -> List[Dict[str, Any]]:
        """Process multiple chunks and extract entities from each.
        
        Efficiently processes a list of chunk objects, extracting entities
        and adding them as metadata.
        
        Args:
            chunks: List of chunk objects (must have text_field attribute)
            text_field: Name of the attribute containing text to process
        
        Returns:
            List of dictionaries with chunk data + entities:
            [
                {
                    "chunk_id": "...",
                    "text": "...",
                    "entities": {"ORGANIZATION": [...], ...}
                },
                ...
            ]
        
        Example:
            >>> ner = TenderNER()
            >>> enriched = ner.process_chunks(tender_chunks)
            >>> enriched[0]["entities"]["ORGANIZATION"]
            ['Comune di Milano']
        """
        results = []
        
        for chunk in chunks:
            text = getattr(chunk, text_field, "")
            if not text:
                continue
            
            entities = self.extract_entities(text)
            
            chunk_data = {
                "chunk_id": getattr(chunk, "id", None),
                "text": text,
                "entities": entities,
            }
            
            # Preserve other chunk attributes
            if hasattr(chunk, "to_dict"):
                chunk_data.update(chunk.to_dict())
            
            results.append(chunk_data)
        
        return results
    
    def __repr__(self) -> str:
        return f"TenderNER(model='{self.model_name}')"


def create_tender_ner(
    model_name: str = "it_core_news_lg",
    use_gpu: bool = False,
) -> TenderNER:
    """Factory function to create TenderNER instance.
    
    Args:
        model_name: spaCy model name
        use_gpu: Whether to use GPU acceleration
    
    Returns:
        Configured TenderNER instance
    
    Example:
        >>> ner = create_tender_ner()
        >>> entities = ner.extract_entities("Il Comune di Milano...")
    """
    return TenderNER(model_name=model_name, use_gpu=use_gpu)
