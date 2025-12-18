"""Tests for core chunking types and utilities."""

from __future__ import annotations

import pytest

from src.domain.tender.schemas.chunking import TenderChunk, TenderTokenChunk


class TestChunk:
    """Test TenderChunk implementation of ChunkLike Protocol."""
    
    def test_chunk_creation(self):
        """Test creating a basic chunk."""
        chunk = TenderChunk(
            id="chunk_1",
            title="Test Section",
            heading_level=2,
            text="This is a test chunk.",
            blocks=[],
            page_numbers=[1]
        )
        
        assert chunk.text == "This is a test chunk."
        assert chunk.title == "Test Section"
        assert chunk.id == "chunk_1"
        assert chunk.heading_level == 2
    
    def test_chunk_to_dict(self):
        """Test chunk serialization to dict."""
        chunk = TenderChunk(
            id="chunk_1",
            title="Test",
            heading_level=1,
            text="Content",
            blocks=[{"type": "paragraph", "text": "Content"}],
            page_numbers=[1, 2]
        )
        
        chunk_dict = chunk.to_dict()
        assert chunk_dict["id"] == "chunk_1"
        assert chunk_dict["text"] == "Content"
        assert "blocks" in chunk_dict
    
    def test_chunk_to_dict_without_blocks(self):
        """Test chunk serialization without blocks."""
        chunk = TenderChunk(
            id="chunk_1",
            title="Test",
            heading_level=1,
            text="Content",
            blocks=[{"type": "para"}],
            page_numbers=[1]
        )
        
        chunk_dict = chunk.to_dict(include_blocks=False)
        assert "blocks" not in chunk_dict
        assert chunk_dict["text"] == "Content"


class TestTokenChunk:
    """Test TenderTokenChunk implementation of TokenChunkLike Protocol."""
    
    def test_token_chunk_creation(self):
        """Test creating a token chunk."""
        chunk = TenderTokenChunk(
            id="token_1",
            text="This is a test token chunk.",
            section_path="doc/section1",
            page_numbers=[1, 2],
            metadata={},
            source_chunk_id="chunk_1"
        )
        
        assert chunk.text == "This is a test token chunk."
        assert chunk.id == "token_1"
        assert chunk.section_path == "doc/section1"
        assert chunk.page_numbers == [1, 2]
    
    def test_token_chunk_fields(self):
        """Test token chunk has correct fields."""
        chunk = TenderTokenChunk(
            id="token_1",
            text="Test",
            section_path="root",
            page_numbers=[1],
            metadata={"key": "value"},
            source_chunk_id="src_1"
        )
        
        assert chunk.id == "token_1"
        assert chunk.text == "Test"
        assert chunk.metadata == {"key": "value"}
        assert chunk.source_chunk_id == "src_1"
    
    def test_token_chunk_with_empty_metadata(self):
        """Test token chunk with empty metadata."""
        chunk = TenderTokenChunk(
            id="token_1",
            text="Test",
            section_path="",
            page_numbers=[],
            metadata={},
            source_chunk_id=""
        )
        
        assert chunk.metadata == {}
        assert chunk.section_path == ""
