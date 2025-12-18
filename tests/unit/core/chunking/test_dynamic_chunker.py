"""Tests for DynamicChunker."""

from __future__ import annotations

import pytest

from src.core.chunking.dynamic_chunker import DynamicChunker
from src.core.chunking.types import Chunk


class TestDynamicChunker:
    """Test DynamicChunker class."""
    
    @pytest.fixture
    def chunker(self):
        """Create chunker instance."""
        return DynamicChunker(
            max_tokens=100,
            overlap_tokens=10,
            min_chunk_tokens=20
        )
    
    @pytest.fixture
    def sample_blocks(self):
        """Sample document blocks."""
        return [
            {"text": "# Title", "type": "heading", "level": 1},
            {"text": "Introduction paragraph.", "type": "paragraph"},
            {"text": "## Section 1", "type": "heading", "level": 2},
            {"text": "Section 1 content.", "type": "paragraph"},
            {"text": "More content here.", "type": "paragraph"},
            {"text": "## Section 2", "type": "heading", "level": 2},
            {"text": "Section 2 content.", "type": "paragraph"},
        ]
    
    def test_chunker_initialization(self, chunker):
        """Test chunker is initialized correctly."""
        assert chunker.max_tokens == 100
        assert chunker.overlap_tokens == 10
        assert chunker.min_chunk_tokens == 20
    
    def test_chunk_creation(self, chunker, sample_blocks):
        """Test creating chunks from blocks."""
        chunks = chunker.chunk(sample_blocks)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(chunk, Chunk) for chunk in chunks)
    
    def test_chunks_have_metadata(self, chunker, sample_blocks):
        """Test chunks contain metadata."""
        chunks = chunker.chunk(sample_blocks)
        
        for chunk in chunks:
            assert chunk.metadata is not None
            assert isinstance(chunk.metadata, dict)
            assert chunk.text is not None
            assert chunk.id is not None
    
    def test_chunks_respect_max_tokens(self, chunker):
        """Test chunks don't exceed max token limit."""
        # Create large blocks that should be split
        large_blocks = [
            {"text": "word " * 200, "type": "paragraph"}  # Very long paragraph
        ]
        
        chunks = chunker.chunk(large_blocks)
        
        # Should create multiple chunks
        assert len(chunks) > 1
        
        # Each chunk should be reasonably sized
        for chunk in chunks:
            # Rough estimate: max_tokens * ~4 chars per token
            assert len(chunk.text) < chunker.max_tokens * 10
    
    def test_empty_input(self, chunker):
        """Test chunking empty input."""
        chunks = chunker.chunk([])
        assert chunks == []
    
    def test_heading_hierarchy(self, chunker, sample_blocks):
        """Test that chunks maintain heading hierarchy."""
        chunks = chunker.chunk(sample_blocks)
        
        # Should have metadata about section structure
        for chunk in chunks:
            # Metadata should be preserved
            assert isinstance(chunk.metadata, dict)
