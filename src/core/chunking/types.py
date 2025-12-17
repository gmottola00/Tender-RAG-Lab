"""Chunking types and data structures.

This module defines generic chunk types used across the RAG system.
These are domain-agnostic and can be reused in any project.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Chunk:
    """Structured chunk grouping a heading and its related content.
    
    This is a generic representation suitable for any document type.
    """

    id: str
    title: str
    heading_level: int
    text: str
    blocks: List[Dict[str, Any]]
    page_numbers: List[int]

    def to_dict(self, *, include_blocks: bool = True) -> Dict[str, Any]:
        """Convert chunk to a serializable dict."""
        data = {
            "id": self.id,
            "title": self.title,
            "heading_level": self.heading_level,
            "text": self.text,
            "page_numbers": self.page_numbers,
        }
        if include_blocks:
            data["blocks"] = self.blocks
        return data


@dataclass
class TokenChunk:
    """Represents a token-level chunk with metadata.
    
    Generic token chunk suitable for vector indexing.
    """

    id: str
    text: str
    section_path: str
    metadata: Dict[str, str]
    page_numbers: List[int]
    source_chunk_id: str


__all__ = ["Chunk", "TokenChunk"]
