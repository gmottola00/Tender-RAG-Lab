"""Tender-specific chunk implementations.

This module provides domain-specific implementations of the core chunking
protocols, adding tender-related metadata while maintaining compatibility
with the generic chunking interfaces defined in rag_toolkit.core.chunking.types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from rag_toolkit.core.chunking.types import ChunkLike, TokenChunkLike


@dataclass
class TenderChunk:
    """Tender-specific implementation of ChunkLike Protocol.

    Extends the core chunk interface with tender-specific metadata,
    allowing tracking of which tender, lot, and section type each chunk belongs to.

    This implementation conforms to the ChunkLike Protocol from rag_toolkit.core.chunking.types
    and can be used anywhere a ChunkLike is expected.

    Attributes:
        id: Unique identifier for the chunk
        title: Section title or heading
        heading_level: Hierarchical level of the heading (e.g., h1=1, h2=2)
        text: The actual text content of the chunk
        blocks: List of structured text blocks within this chunk
        page_numbers: List of page numbers where this chunk appears
        tender_id: ID of the tender this chunk belongs to
        lot_id: Optional ID of the specific lot within the tender
        section_type: Classification of the section (e.g., "requirements", "evaluation_criteria")
    """

    id: str
    title: str
    heading_level: int
    text: str
    blocks: List[Dict[str, Any]] = field(default_factory=list)
    page_numbers: List[int] = field(default_factory=list)
    
    # Tender-specific fields
    tender_id: str = ""
    lot_id: Optional[str] = None
    section_type: str = ""

    def to_dict(self, *, include_blocks: bool = True) -> Dict[str, Any]:
        """Convert chunk to dictionary representation.

        Args:
            include_blocks: Whether to include the blocks field in the output

        Returns:
            Dictionary containing all chunk data including tender-specific metadata
        """
        data = {
            "id": self.id,
            "title": self.title,
            "heading_level": self.heading_level,
            "text": self.text,
            "page_numbers": self.page_numbers,
            "tender_id": self.tender_id,
            "lot_id": self.lot_id,
            "section_type": self.section_type,
        }
        if include_blocks:
            data["blocks"] = self.blocks
        return data


@dataclass
class TenderTokenChunk:
    """Tender-specific implementation of TokenChunkLike Protocol.

    Extends the core token chunk interface with tender-specific metadata,
    optimized for embedding and retrieval operations with tender context.

    This implementation conforms to the TokenChunkLike Protocol from rag_toolkit.core.chunking.types
    and can be used anywhere a TokenChunkLike is expected.

    Attributes:
        id: Unique identifier for the token chunk
        text: The token-optimized text content
        section_path: Hierarchical path to the section (e.g., "Section 1 > Subsection A")
        metadata: Additional metadata as key-value pairs
        page_numbers: List of page numbers where this chunk appears
        source_chunk_id: Reference to the original Chunk this was derived from
        tender_id: ID of the tender this chunk belongs to
        lot_id: Optional ID of the specific lot within the tender
        section_type: Classification of the section (e.g., "requirements", "evaluation_criteria")
    """

    id: str
    text: str
    section_path: str
    metadata: Dict[str, str] = field(default_factory=dict)
    page_numbers: List[int] = field(default_factory=list)
    source_chunk_id: str = ""
    
    # Tender-specific fields
    tender_id: str = ""
    lot_id: Optional[str] = None
    section_type: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert token chunk to dictionary representation.

        Returns:
            Dictionary containing all token chunk data including tender-specific metadata
        """
        return {
            "id": self.id,
            "text": self.text,
            "section_path": self.section_path,
            "metadata": self.metadata,
            "page_numbers": self.page_numbers,
            "source_chunk_id": self.source_chunk_id,
            "tender_id": self.tender_id,
            "lot_id": self.lot_id,
            "section_type": self.section_type,
        }


# Legacy compatibility - maintain backward compatibility if needed
Chunk = TenderChunk
TokenChunk = TenderTokenChunk

__all__ = ["TenderChunk", "TenderTokenChunk", "Chunk", "TokenChunk"]
