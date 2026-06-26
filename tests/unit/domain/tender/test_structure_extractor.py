"""
Tests for Structure-Based Entity Extraction.

Tests the StructureExtractor component for extracting structured entities
from tender document metadata (section_path, headings, etc.).
"""
import pytest

from src.domain.tender.services.structure_extractor import (
    StructureExtractor,
    StructuredEntity,
)


@pytest.fixture
def extractor():
    """Create StructureExtractor instance."""
    return StructureExtractor()


class TestLotExtraction:
    """Test lot identifier extraction from section_path."""
    
    def test_extract_lot_from_section_path_standard(self, extractor):
        """Test standard lot format: '5. Lotto > 5.1. Lotto: LOT-0001'"""
        chunk = {
            'section_path': '5. Lotto > 5.1. Lotto: LOT-0001',
            'metadata': {'tender_id': 'test-uuid'},
            'text': 'Some text',
            'source_chunk_id': 'chunk-001'
        }
        
        entities = extractor.extract_from_chunk(chunk)
        
        assert len(entities) > 0
        lot_entities = [e for e in entities if e.type == 'lot']
        assert len(lot_entities) == 1
        
        lot = lot_entities[0]
        assert lot.id == 'LOT-0001'
        assert lot.name == 'Lotto LOT-0001'
        assert lot.confidence == 0.95  # High confidence from section_path
        assert lot.properties['tender_id'] == 'test-uuid'
    
    def test_extract_lot_from_text_fallback(self, extractor):
        """Test lot extraction from text when section_path doesn't contain it."""
        chunk = {
            'section_path': '5. Informazioni generali',
            'metadata': {},
            'text': 'Il presente lotto LOT-ABC-123 riguarda...',
            'source_chunk_id': 'chunk-002'
        }
        
        entities = extractor.extract_from_chunk(chunk)
        
        lot_entities = [e for e in entities if e.type == 'lot']
        assert len(lot_entities) == 1
        
        lot = lot_entities[0]
        assert lot.id == 'LOT-ABC-123'
        assert lot.confidence == 0.75  # Lower confidence from text
    
    def test_no_lot_when_not_present(self, extractor):
        """Test that no lot is extracted when none present."""
        chunk = {
            'section_path': '2. Procedura > 2.1. Modalità',
            'metadata': {},
            'text': 'Generic tender information without lot reference',
            'source_chunk_id': 'chunk-003'
        }
        
        entities = extractor.extract_from_chunk(chunk)
        
        lot_entities = [e for e in entities if e.type == 'lot']
        assert len(lot_entities) == 0


class TestSectionExtraction:
    """Test section entity extraction from hierarchical paths."""
    
    def test_extract_procedure_section(self, extractor):
        """Test extraction of procedure section."""
        chunk = {
            'section_path': '2. Procedura > 2.1. Modalità di presentazione',
            'metadata': {'tender_id': 'test-uuid'},
            'text': '',
            'source_chunk_id': 'chunk-004'
        }
        
        entities = extractor.extract_from_chunk(chunk)
        
        section_entities = [e for e in entities if e.type == 'section']
        assert len(section_entities) > 0
        
        # Should extract "2. Procedura" section
        procedure_section = next(
            (e for e in section_entities if e.properties['section_type'] == 'procedure'),
            None
        )
        assert procedure_section is not None
        assert procedure_section.confidence == 0.9
    
    def test_extract_requirement_section(self, extractor):
        """Test extraction of requirement section."""
        chunk = {
            'section_path': '3. Requisiti > 3.1. Requisiti tecnici',
            'metadata': {},
            'text': '',
            'source_chunk_id': 'chunk-005'
        }
        
        entities = extractor.extract_from_chunk(chunk)
        
        section_entities = [e for e in entities if e.type == 'section']
        requirement_sections = [
            e for e in section_entities
            if e.properties['section_type'] == 'requirement'
        ]
        
        assert len(requirement_sections) > 0
        assert any('3.1' in e.id or '3.1' in e.name for e in requirement_sections)
    
    def test_extract_multiple_sections_from_hierarchy(self, extractor):
        """Test that hierarchical path creates multiple section entities."""
        chunk = {
            'section_path': '2. Procedura > 2.1. Modalità > 2.1.1. Termini',
            'metadata': {},
            'text': '',
            'source_chunk_id': 'chunk-006'
        }
        
        entities = extractor.extract_from_chunk(chunk)
        
        section_entities = [e for e in entities if e.type == 'section']
        # Should create entities for each level that matches known types
        assert len(section_entities) >= 1


class TestCodeExtraction:
    """Test extraction of CIG, CUP, CPV codes."""
    
    def test_extract_cig_code(self, extractor):
        """Test CIG code extraction."""
        chunk = {
            'section_path': '',
            'metadata': {},
            'text': 'Il CIG del presente appalto è: 1234567890ABC',
            'source_chunk_id': 'chunk-007'
        }
        
        entities = extractor.extract_from_chunk(chunk)
        
        code_entities = [e for e in entities if e.type == 'code']
        cig_codes = [
            e for e in code_entities
            if e.properties.get('code_type') == 'CIG'
        ]
        
        assert len(cig_codes) == 1
        assert cig_codes[0].properties['code_value'] == '1234567890ABC'
        assert cig_codes[0].confidence == 0.95
    
    def test_extract_cup_code(self, extractor):
        """Test CUP code extraction."""
        chunk = {
            'section_path': '',
            'metadata': {},
            'text': 'CUP: A12B34C56D78E90',
            'source_chunk_id': 'chunk-008'
        }
        
        entities = extractor.extract_from_chunk(chunk)
        
        code_entities = [e for e in entities if e.type == 'code']
        cup_codes = [
            e for e in code_entities
            if e.properties.get('code_type') == 'CUP'
        ]
        
        assert len(cup_codes) == 1
        assert cup_codes[0].properties['code_value'] == 'A12B34C56D78E90'
    
    def test_extract_cpv_code(self, extractor):
        """Test CPV code extraction."""
        chunk = {
            'section_path': '1. Classificazione > CPV: 09310000',
            'metadata': {},
            'text': 'Codice CPV principale: 09310000 - Elettricità',
            'source_chunk_id': 'chunk-009'
        }
        
        entities = extractor.extract_from_chunk(chunk)
        
        code_entities = [e for e in entities if e.type == 'code']
        cpv_codes = [
            e for e in code_entities
            if e.properties.get('code_type') == 'CPV'
        ]
        
        assert len(cpv_codes) == 1
        assert cpv_codes[0].properties['code_value'] == '09310000'
    
    def test_extract_multiple_codes(self, extractor):
        """Test extraction when multiple codes present."""
        chunk = {
            'section_path': '',
            'metadata': {},
            'text': 'CIG: 1234567890ABC CUP: A12B34C56D78E90 CPV: 09310000',
            'source_chunk_id': 'chunk-010'
        }
        
        entities = extractor.extract_from_chunk(chunk)
        
        code_entities = [e for e in entities if e.type == 'code']
        assert len(code_entities) == 3
        
        code_types = {e.properties['code_type'] for e in code_entities}
        assert code_types == {'CIG', 'CUP', 'CPV'}


class TestBuyerExtraction:
    """Test buyer/contracting authority extraction."""
    
    def test_extract_buyer_from_committente_section(self, extractor):
        """Test buyer extraction from 'Committente' section."""
        chunk = {
            'section_path': '1. Committente > 1.1. Stazione Appaltante',
            'metadata': {},
            'text': 'Comune di Perugia\nVia Roma 1\n06100 Perugia',
            'source_chunk_id': 'chunk-011'
        }
        
        entities = extractor.extract_from_chunk(chunk)
        
        buyer_entities = [e for e in entities if e.type == 'buyer']
        assert len(buyer_entities) == 1
        
        buyer = buyer_entities[0]
        assert buyer.name == 'Comune di Perugia'
        assert buyer.confidence == 0.85
        assert 'Committente' in buyer.properties['section_path']
    
    def test_extract_buyer_from_stazione_appaltante(self, extractor):
        """Test buyer extraction from 'Stazione appaltante' keyword."""
        chunk = {
            'section_path': 'Stazione appaltante e soggetti competenti',
            'metadata': {},
            'text': 'Umbria Acque Spa\nOrganizzazione che firma il contratto',
            'source_chunk_id': 'chunk-012'
        }
        
        entities = extractor.extract_from_chunk(chunk)
        
        buyer_entities = [e for e in entities if e.type == 'buyer']
        assert len(buyer_entities) == 1
        assert buyer_entities[0].name == 'Umbria Acque Spa'


class TestAmountExtraction:
    """Test monetary amount extraction."""
    
    def test_extract_euro_amount(self, extractor):
        """Test extraction of euro amounts."""
        chunk = {
            'section_path': '5.1.4. Valore',
            'metadata': {},
            'text': 'Importo: € 1.000.000,00 EUR',
            'source_chunk_id': 'chunk-013'
        }
        
        entities = extractor.extract_from_chunk(chunk)
        
        amount_entities = [e for e in entities if e.type == 'amount']
        assert len(amount_entities) == 1
        
        amount = amount_entities[0]
        assert amount.properties['amount'] == 1000000.00
        assert amount.properties['currency'] == 'EUR'
        assert amount.confidence == 0.8
    
    def test_extract_base_asta_amount(self, extractor):
        """Test extraction with 'Base d'asta' keyword."""
        chunk = {
            'section_path': '',
            'metadata': {},
            'text': 'Base d\'asta: 500.000,00 EUR',
            'source_chunk_id': 'chunk-014'
        }
        
        entities = extractor.extract_from_chunk(chunk)
        
        amount_entities = [e for e in entities if e.type == 'amount']
        assert len(amount_entities) == 1
        assert amount_entities[0].properties['amount'] == 500000.00


class TestBatchExtraction:
    """Test batch extraction from multiple chunks."""
    
    def test_extract_from_multiple_chunks(self, extractor):
        """Test extraction and deduplication across chunks."""
        chunks = [
            {
                'section_path': '5. Lotto > 5.1. Lotto: LOT-0001',
                'metadata': {},
                'text': '',
                'source_chunk_id': 'chunk-001',
                'id': 'chunk-001'
            },
            {
                'section_path': '5. Lotto > 5.1. Lotto: LOT-0001 > 5.1.1. Finalità',
                'metadata': {},
                'text': 'CIG: 1234567890ABC',
                'source_chunk_id': 'chunk-002',
                'id': 'chunk-002'
            },
            {
                'section_path': '2. Procedura > 2.1. Modalità',
                'metadata': {},
                'text': '',
                'source_chunk_id': 'chunk-003',
                'id': 'chunk-003'
            }
        ]
        
        result = extractor.extract_from_chunks(chunks)
        
        # Should have multiple types
        assert 'lot' in result
        assert 'section' in result
        assert 'code' in result
        
        # Lots should be deduplicated (LOT-0001 appears twice)
        assert len(result['lot']) == 1
        assert result['lot'][0].id == 'LOT-0001'
        
        # Should have CIG code
        assert len(result['code']) >= 1
    
    def test_deduplication_keeps_highest_confidence(self, extractor):
        """Test that deduplication keeps entity with highest confidence."""
        chunks = [
            {
                # High confidence from section_path
                'section_path': 'Lotto: LOT-ABC-001',
                'metadata': {},
                'text': '',
                'source_chunk_id': 'chunk-high',
                'id': 'chunk-high'
            },
            {
                # Lower confidence from text
                'section_path': 'Generic section',
                'metadata': {},
                'text': 'Reference to lot LOT-ABC-001 mentioned here',
                'source_chunk_id': 'chunk-low',
                'id': 'chunk-low'
            }
        ]
        
        result = extractor.extract_from_chunks(chunks)
        
        # Should keep only one LOT-ABC-001 with highest confidence
        lots = result.get('lot', [])
        lot_001 = [l for l in lots if l.id == 'LOT-ABC-001']
        assert len(lot_001) == 1
        assert lot_001[0].confidence == 0.95  # From section_path


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_chunk(self, extractor):
        """Test handling of empty chunk."""
        chunk = {
            'section_path': '',
            'metadata': {},
            'text': '',
            'source_chunk_id': 'chunk-empty'
        }
        
        entities = extractor.extract_from_chunk(chunk)
        
        assert entities == []
    
    def test_missing_keys(self, extractor):
        """Test handling of chunk with missing keys."""
        chunk = {
            'source_chunk_id': 'chunk-minimal'
        }
        
        # Should not raise exception
        entities = extractor.extract_from_chunk(chunk)
        
        assert isinstance(entities, list)
    
    def test_invalid_amount_format(self, extractor):
        """Test that invalid amounts are skipped."""
        chunk = {
            'section_path': '',
            'metadata': {},
            'text': 'Importo: € abc.def,xyz EUR',
            'source_chunk_id': 'chunk-invalid'
        }
        
        entities = extractor.extract_from_chunk(chunk)
        
        amount_entities = [e for e in entities if e.type == 'amount']
        assert len(amount_entities) == 0  # Invalid amount should be skipped
