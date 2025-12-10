"""PDF parsing utilities based on PyMuPDF."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Union

import fitz  # type: ignore

from . import heading_detection, table_detection
from .normalizer import normalize_text

PageDict = Dict[str, Any]
BlockDict = Dict[str, Any]


def _validate_pdf_path(path: Union[str, Path]) -> Path:
    """Validate that the PDF path exists and points to a file."""
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found at {pdf_path}")
    if not pdf_path.is_file():
        raise ValueError(f"Path is not a file: {pdf_path}")
    return pdf_path


def extract_pdf_layout(path: Union[str, Path]) -> List[PageDict]:
    """Extract text layout information from a PDF file using PyMuPDF.

    Args:
        path: Path to the PDF file.

    Returns:
        List of pages with extracted blocks (text, bbox, font info).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the path is not a file.
        RuntimeError: If PyMuPDF fails to read the document.
    """
    pdf_path = _validate_pdf_path(path)

    try:
        doc = fitz.open(pdf_path.as_posix())
    except Exception as exc:  # pragma: no cover - passthrough
        raise RuntimeError(f"Failed to open PDF: {pdf_path}") from exc

    pages: List[PageDict] = []
    try:
        for page_index, page in enumerate(doc, start=1):
            blocks: List[BlockDict] = []
            text_dict = page.get_text("dict")
            for block in text_dict.get("blocks", []):
                if "lines" not in block:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = normalize_text(span.get("text", "")).strip()
                        if not text:
                            continue
                        blocks.append(
                            {
                                "text": text,
                                "bbox": span.get("bbox"),
                                "font_size": span.get("size"),
                                "font_name": span.get("font"),
                            }
                        )

            pages.append({"page_number": page_index, "blocks": blocks})
    finally:
        doc.close()

    return pages


def parse_pdf(
    path: Union[str, Path],
    detect_headings: bool = True,
    detect_tables: bool = True,
) -> List[PageDict]:
    """Parse a PDF file and optionally tag headings and tables.

    Args:
        path: Path to the PDF file.
        detect_headings: Whether to classify heading-like blocks. Defaults to True.
        detect_tables: Whether to detect tables via pdfplumber and heuristics. Defaults to True.

    Returns:
        A list of page dictionaries, each containing enriched blocks.
    """
    pages = extract_pdf_layout(path)

    if detect_headings:
        for page in pages:
            page["blocks"] = heading_detection.tag_headings(page.get("blocks", []))

    if detect_tables:
        pages = table_detection.integrate_tables(path, pages)

    return pages


__all__ = ["extract_pdf_layout", "parse_pdf"]
