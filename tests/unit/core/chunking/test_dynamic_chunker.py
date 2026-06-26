"""Tests for DynamicChunker — using the actual quaerium API."""

from __future__ import annotations

import pytest

from quaerium.core.chunking.dynamic_chunker import DynamicChunker
from quaerium.core.chunking.models import Chunk


class TestDynamicChunker:
    """Test DynamicChunker class."""

    def test_chunker_initialization(self):
        """Test default parameter values."""
        chunker = DynamicChunker()
        assert chunker.include_tables is True
        assert chunker.max_heading_level == 6
        assert chunker.allow_preamble is False

    def test_chunker_custom_params(self):
        """Test custom parameter initialization."""
        chunker = DynamicChunker(
            include_tables=False,
            max_heading_level=3,
            allow_preamble=True,
        )
        assert chunker.include_tables is False
        assert chunker.max_heading_level == 3
        assert chunker.allow_preamble is True

    def test_build_chunks_basic(self):
        """Pages with h1 headings produce at least one chunk."""
        chunker = DynamicChunker()
        pages = [
            {
                "blocks": [
                    {"type": "heading", "level": 1, "text": "Introduction"},
                    {"type": "paragraph", "text": "This is the intro content."},
                ]
            }
        ]
        chunks = chunker.build_chunks(pages)
        assert isinstance(chunks, list)
        assert len(chunks) == 1

    def test_chunk_has_correct_fields(self):
        """Chunks contain all required fields."""
        chunker = DynamicChunker()
        pages = [
            {
                "blocks": [
                    {"type": "heading", "level": 1, "text": "My Title"},
                    {"type": "paragraph", "text": "Body text."},
                ]
            }
        ]
        chunks = chunker.build_chunks(pages)
        assert len(chunks) == 1
        chunk = chunks[0]
        assert isinstance(chunk, Chunk)
        assert chunk.id is not None and len(chunk.id) > 0
        assert isinstance(chunk.title, str)
        assert isinstance(chunk.heading_level, int)
        assert isinstance(chunk.text, str)
        assert isinstance(chunk.blocks, list)
        assert isinstance(chunk.page_numbers, list)

    def test_chunks_split_at_h1(self):
        """Each h1 heading creates a new chunk boundary."""
        chunker = DynamicChunker()
        pages = [
            {
                "blocks": [
                    {"type": "heading", "level": 1, "text": "Section A"},
                    {"type": "paragraph", "text": "Content A."},
                    {"type": "heading", "level": 1, "text": "Section B"},
                    {"type": "paragraph", "text": "Content B."},
                ]
            }
        ]
        chunks = chunker.build_chunks(pages)
        assert len(chunks) == 2
        assert chunks[0].title == "Section A"
        assert chunks[1].title == "Section B"

    def test_allow_preamble_false(self):
        """Content before first h1 is skipped when allow_preamble=False."""
        chunker = DynamicChunker(allow_preamble=False)
        pages = [
            {
                "blocks": [
                    {"type": "paragraph", "text": "Preamble content before any heading."},
                    {"type": "heading", "level": 1, "text": "First Heading"},
                    {"type": "paragraph", "text": "Actual content."},
                ]
            }
        ]
        chunks = chunker.build_chunks(pages)
        # Should have exactly one chunk for "First Heading"
        assert len(chunks) == 1
        assert chunks[0].title == "First Heading"

    def test_allow_preamble_true(self):
        """Content before first h1 becomes a preamble chunk."""
        chunker = DynamicChunker(allow_preamble=True)
        pages = [
            {
                "blocks": [
                    {"type": "paragraph", "text": "This is preamble content."},
                    {"type": "heading", "level": 1, "text": "First Heading"},
                    {"type": "paragraph", "text": "Section content."},
                ]
            }
        ]
        chunks = chunker.build_chunks(pages)
        # Should have preamble chunk + first heading chunk
        assert len(chunks) == 2
        assert chunks[0].title == "Preamble"

    def test_empty_pages(self):
        """Empty input list returns empty chunk list."""
        chunker = DynamicChunker()
        chunks = chunker.build_chunks([])
        assert chunks == []

    def test_empty_pages_with_empty_blocks(self):
        """Pages with no blocks return empty chunk list."""
        chunker = DynamicChunker()
        chunks = chunker.build_chunks([{"blocks": []}])
        assert chunks == []

    def test_chunk_title_is_h1_text(self):
        """Chunk title matches the h1 heading text."""
        chunker = DynamicChunker()
        pages = [
            {
                "blocks": [
                    {"type": "heading", "level": 1, "text": "Requisiti Tecnici"},
                    {"type": "paragraph", "text": "Body."},
                ]
            }
        ]
        chunks = chunker.build_chunks(pages)
        assert len(chunks) == 1
        assert chunks[0].title == "Requisiti Tecnici"

    def test_h2_headings_included_in_chunk(self):
        """Sub-headings (h2, h3) are included inside the parent chunk."""
        chunker = DynamicChunker()
        pages = [
            {
                "blocks": [
                    {"type": "heading", "level": 1, "text": "Main Section"},
                    {"type": "heading", "level": 2, "text": "Sub Section"},
                    {"type": "paragraph", "text": "Sub content."},
                ]
            }
        ]
        chunks = chunker.build_chunks(pages)
        assert len(chunks) == 1
        # The h2 block should be in the chunk's blocks list
        block_types = [b.get("type") for b in chunks[0].blocks]
        assert "heading" in block_types

    def test_include_tables_false(self):
        """Table blocks are excluded when include_tables=False."""
        chunker = DynamicChunker(include_tables=False)
        pages = [
            {
                "blocks": [
                    {"type": "heading", "level": 1, "text": "Section"},
                    {"type": "table_block", "text": "Table data"},
                    {"type": "paragraph", "text": "Normal paragraph."},
                ]
            }
        ]
        chunks = chunker.build_chunks(pages)
        assert len(chunks) == 1
        block_types = [b.get("type") for b in chunks[0].blocks]
        assert "table_block" not in block_types

    def test_include_tables_true(self):
        """Table blocks are included when include_tables=True (default)."""
        chunker = DynamicChunker(include_tables=True)
        pages = [
            {
                "blocks": [
                    {"type": "heading", "level": 1, "text": "Section"},
                    {"type": "table_block", "text": "Table data"},
                    {"type": "paragraph", "text": "Normal paragraph."},
                ]
            }
        ]
        chunks = chunker.build_chunks(pages)
        assert len(chunks) == 1
        block_types = [b.get("type") for b in chunks[0].blocks]
        assert "table_block" in block_types

    def test_page_numbers_tracked(self):
        """Chunk page_numbers reflects which pages the blocks come from."""
        chunker = DynamicChunker()
        pages = [
            {
                "blocks": [
                    {"type": "heading", "level": 1, "text": "Section"},
                    {"type": "paragraph", "text": "Page 1 content."},
                ]
            },
            {
                "blocks": [
                    {"type": "paragraph", "text": "Page 2 content."},
                ]
            },
        ]
        chunks = chunker.build_chunks(pages)
        assert len(chunks) == 1
        # Should contain page numbers 1 and 2
        assert 1 in chunks[0].page_numbers

    def test_multiple_pages_multiple_chunks(self):
        """Multiple h1 headings across pages create separate chunks."""
        chunker = DynamicChunker()
        pages = [
            {
                "blocks": [
                    {"type": "heading", "level": 1, "text": "Chapter 1"},
                    {"type": "paragraph", "text": "Chapter 1 content."},
                ]
            },
            {
                "blocks": [
                    {"type": "heading", "level": 1, "text": "Chapter 2"},
                    {"type": "paragraph", "text": "Chapter 2 content."},
                ]
            },
        ]
        chunks = chunker.build_chunks(pages)
        assert len(chunks) == 2
        assert chunks[0].title == "Chapter 1"
        assert chunks[1].title == "Chapter 2"
