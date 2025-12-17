"""Ingestion-related Pydantic models."""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Block(BaseModel):
    """Represents a text or table block within a page."""

    model_config = ConfigDict(extra="allow")

    type: str
    text: Optional[str] = None
    level: Optional[int] = None
    bbox: Optional[List[float]] = None
    raw_cells: Optional[List[List[Any]]] = None
    font_size: Optional[float] = None
    font_name: Optional[str] = None


class Page(BaseModel):
    """Represents a parsed page."""

    page_number: int = Field(..., ge=1)
    blocks: List[Block]


class ParsedDocument(BaseModel):
    """Structured document returned by the ingestion API."""

    doc_id: str
    filename: str
    language: str
    pages: List[Page]


__all__ = ["Block", "Page", "ParsedDocument"]
