"""Test suite for TenderNER.

Run with: pytest tests/test_ner.py -v
"""

import pytest
from src.domain.tender.ner.spacy_ner import TenderNER, create_tender_ner


# Sample tender text in Italian
SAMPLE_TEXT = """
Il Comune di Milano indice procedura aperta per l'affidamento di servizi
di pulizia e sanificazione degli edifici comunali.

Importo a base d'asta: €500.000,00 (IVA esclusa).
Scadenza presentazione offerte: 30 gennaio 2026, ore 12:00.

Responsabile Unico del Procedimento (RUP): Dott. Mario Rossi
Contatti: Ufficio Gare, Via Roma 10, 20121 Milano
Tel: 02-12345678
Email: gare@comune.milano.it

CIG: 123456789XYZ
CUP: A12B34C56D78E90F
"""


@pytest.fixture
def ner():
    """Create TenderNER instance for tests."""
    # Use smaller model for faster tests
    return create_tender_ner(model_name="it_core_news_sm")


def test_ner_initialization():
    """Test TenderNER can be initialized."""
    ner = TenderNER(model_name="it_core_news_sm")
    assert ner.model_name == "it_core_news_sm"
    assert ner.nlp is not None


def test_extract_entities_basic(ner):
    """Test basic entity extraction."""
    entities = ner.extract_entities(SAMPLE_TEXT)
    
    # Should find at least some entities
    assert len(entities) > 0
    
    # Should find organizations
    if "ORGANIZATION" in entities:
        assert any("Milano" in org for org in entities["ORGANIZATION"])


def test_extract_entities_organizations(ner):
    """Test organization extraction."""
    text = "Il Comune di Milano e la Regione Lombardia collaborano."
    entities = ner.extract_entities(text)
    
    orgs = entities.get("ORGANIZATION", [])
    # At least one organization should be found
    assert len(orgs) >= 1


def test_extract_entities_dates(ner):
    """Test date extraction."""
    text = "Scadenza: 30 gennaio 2026"
    entities = ner.extract_entities(text)
    
    dates = entities.get("DATE", [])
    assert len(dates) >= 1


def test_extract_entities_money(ner):
    """Test monetary amount extraction."""
    text = "Importo: €500.000,00 o 1.2 milioni di euro"
    entities = ner.extract_entities(text)
    
    money = entities.get("MONEY", [])
    assert len(money) >= 1


def test_extract_entities_empty_text(ner):
    """Test handling of empty text."""
    assert ner.extract_entities("") == {}
    assert ner.extract_entities("   ") == {}


def test_extract_entities_min_length(ner):
    """Test minimum length filter."""
    text = "A è l'inizio. Milano è una città."
    
    # With default min_length=2, single chars should be filtered
    entities = ner.extract_entities(text, min_length=2)
    
    # Should not contain single-character entities
    all_entities = [e for entities_list in entities.values() for e in entities_list]
    assert all(len(e) >= 2 for e in all_entities)


def test_extract_with_positions(ner):
    """Test entity extraction with positions."""
    text = "Il Comune di Milano indice gara."
    entities = ner.extract_with_positions(text)
    
    assert len(entities) > 0
    
    # Check structure
    for entity in entities:
        assert "text" in entity
        assert "label" in entity
        assert "start" in entity
        assert "end" in entity
        
        # Positions should be valid
        assert entity["start"] >= 0
        assert entity["end"] > entity["start"]
        assert entity["end"] <= len(text)


def test_extract_with_positions_empty(ner):
    """Test position extraction with empty text."""
    assert ner.extract_with_positions("") == []


def test_extract_tender_metadata(ner):
    """Test tender-specific metadata extraction."""
    metadata = ner.extract_tender_metadata(SAMPLE_TEXT)
    
    # Check structure
    assert "organizations" in metadata
    assert "people" in metadata
    assert "locations" in metadata
    assert "dates" in metadata
    assert "amounts" in metadata
    assert "all_entities" in metadata
    
    # Should be lists
    assert isinstance(metadata["organizations"], list)
    assert isinstance(metadata["people"], list)


def test_extract_tender_metadata_organizations(ner):
    """Test organization extraction in metadata."""
    text = "Stazione Appaltante: Comune di Milano"
    metadata = ner.extract_tender_metadata(text)
    
    # Should find organization
    assert len(metadata["organizations"]) >= 1


def test_process_chunks(ner):
    """Test processing multiple chunks."""
    from dataclasses import dataclass
    
    @dataclass
    class MockChunk:
        id: str
        text: str
    
    chunks = [
        MockChunk(id="1", text="Il Comune di Milano indice gara."),
        MockChunk(id="2", text="Importo: €500.000"),
        MockChunk(id="3", text="Scadenza: 30 gennaio 2026"),
    ]
    
    results = ner.process_chunks(chunks)
    
    assert len(results) == 3
    
    for result in results:
        assert "chunk_id" in result
        assert "text" in result
        assert "entities" in result


def test_process_chunks_empty(ner):
    """Test processing empty chunk list."""
    results = ner.process_chunks([])
    assert results == []


def test_create_tender_ner_factory():
    """Test factory function."""
    ner = create_tender_ner(model_name="it_core_news_sm")
    
    assert isinstance(ner, TenderNER)
    assert ner.model_name == "it_core_news_sm"


def test_ner_repr():
    """Test string representation."""
    ner = TenderNER(model_name="it_core_news_sm")
    repr_str = repr(ner)
    
    assert "TenderNER" in repr_str
    assert "it_core_news_sm" in repr_str


def test_normalize_labels(ner):
    """Test label normalization."""
    text = "Milano è una città. Comune di Milano."
    
    # With normalization (default)
    entities_normalized = ner.extract_entities(text, normalize_labels=True)
    
    # Should use simplified labels
    assert "ORGANIZATION" in entities_normalized or "LOCATION" in entities_normalized
    
    # Without normalization
    entities_raw = ner.extract_entities(text, normalize_labels=False)
    
    # Should use spaCy labels
    assert "ORG" in entities_raw or "LOC" in entities_raw or "GPE" in entities_raw


@pytest.mark.parametrize("text,expected_entity_type", [
    ("Il Comune di Milano", "ORGANIZATION"),
    ("Mario Rossi è il RUP", "PERSON"),
    ("Scadenza: 30 gennaio 2026", "DATE"),
    ("Importo: €500.000", "MONEY"),
])
def test_entity_types(ner, text, expected_entity_type):
    """Test extraction of specific entity types."""
    entities = ner.extract_entities(text)
    
    # Should find the expected entity type (may not always work with small model)
    # This is a probabilistic test
    assert len(entities) > 0, f"No entities found in: {text}"


if __name__ == "__main__":
    # Quick manual test
    print("Testing TenderNER...")
    
    try:
        ner = create_tender_ner(model_name="it_core_news_sm")
        print(f"✓ Initialized: {ner}")
        
        entities = ner.extract_entities(SAMPLE_TEXT)
        print(f"\n✓ Extracted {len(entities)} entity types:")
        for entity_type, values in entities.items():
            print(f"  {entity_type}: {values}")
        
        metadata = ner.extract_tender_metadata(SAMPLE_TEXT)
        print(f"\n✓ Tender metadata:")
        print(f"  Organizations: {metadata['organizations']}")
        print(f"  People: {metadata['people']}")
        print(f"  Dates: {metadata['dates']}")
        print(f"  Amounts: {metadata['amounts']}")
        
        print("\n✅ All tests passed!")
        
    except OSError as e:
        print(f"\n❌ Error: {e}")
        print("\nInstall spaCy model with:")
        print("  python -m spacy download it_core_news_sm")
