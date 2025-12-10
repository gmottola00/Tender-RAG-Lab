"""Rule-based heading detection for PDF blocks."""

from __future__ import annotations

import re
from statistics import median
from typing import Dict, List

BlockDict = Dict[str, object]

ART_PATTERN = re.compile(r"^Art\.?\s+\d+.*", re.IGNORECASE)
CAPO_PATTERN = re.compile(r"^CAPO\s+[IVXLC]+.*", re.IGNORECASE)
CAPITOLO_PATTERN = re.compile(r"^Capitolo\s+\d+.*", re.IGNORECASE)
TITLE_PATTERN = re.compile(r"^Titolo\s+\d+.*", re.IGNORECASE)


def _font_threshold(blocks: List[BlockDict], boost: float) -> float:
    """Compute a heuristic threshold for heading font sizes."""
    sizes = [b.get("font_size") for b in blocks if isinstance(b.get("font_size"), (int, float))]
    if not sizes:
        return 0.0
    return median(sizes) + boost


def _classify_block(text: str, font_size: float, size_threshold: float) -> tuple[str, int | None]:
    """Classify a single block returning (type, level)."""
    block_type = "paragraph"
    level = None

    if font_size is not None and font_size >= size_threshold > 0:
        block_type = "heading"
        level = 1

    if ART_PATTERN.match(text):
        block_type = "heading"
        level = 2
    elif CAPO_PATTERN.match(text) or CAPITOLO_PATTERN.match(text) or TITLE_PATTERN.match(text):
        block_type = "heading"
        level = 1

    return block_type, level


def tag_headings(page_blocks: List[BlockDict], font_boost: float = 1.5) -> List[BlockDict]:
    """Assign heading tags to a list of page blocks.

    Args:
        page_blocks: Blocks extracted from a PDF page.
        font_boost: Additional size added to the median to mark headings.

    Returns:
        The same list of blocks with ``type`` and optional ``level`` keys added.
    """
    size_threshold = _font_threshold(page_blocks, boost=font_boost)

    for block in page_blocks:
        text = str(block.get("text", "")).strip()
        font_size = block.get("font_size")
        block_type, level = _classify_block(
            text,
            font_size if isinstance(font_size, (int, float)) else 0,
            size_threshold,
        )

        block["type"] = block_type
        if level is not None:
            block["level"] = level

    return page_blocks


__all__ = ["tag_headings"]
