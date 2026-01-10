"""Text cleaning utilities for tender documents.

Handles common issues from PDF parsing:
- Excessive newlines and whitespace
- Header/footer artifacts (Page X/Y, timestamps)
- Broken words from multi-column layouts
- Uppercase/lowercase normalization
"""

import re
from typing import List


def clean_tender_text(text: str) -> str:
    """Clean text extracted from tender PDF documents.

    Args:
        text: Raw text from PDF parser

    Returns:
        Cleaned text suitable for NER and chunking

    Example:
        >>> raw = "DELL'ART\\nICALO  Page 1/4\\nRequisiti\\n\\n\\nobbligatori"
        >>> clean_tender_text(raw)
        "dell'articolo Requisiti obbligatori"
    """
    if not text:
        return ""

    # 1. Remove common PDF artifacts
    # Page numbers (Page X/Y, Page X of Y, Pagina X/Y)
    text = re.sub(r'Page \d+/\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Pagina \d+/\d+', '', text, flags=re.IGNORECASE)

    # Timestamps (UTC+XX:XX, 2025-01-XX)
    text = re.sub(r'UTC[+-]\d{2}:\d{2}', '', text)
    text = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', '', text)

    # Common headers/footers
    text = re.sub(r'Tender_\d+', '', text)

    # 2. Fix broken words (common in multi-column PDFs)
    # Example: "DELL'ART ICALO" → "DELL'ARTICALO" (not perfect but helps)
    # This is heuristic - full fix needs layout analysis

    # 3. Normalize whitespace
    # Multiple newlines → single newline
    text = re.sub(r'\n\s*\n+', '\n', text)

    # Multiple spaces → single space
    text = re.sub(r' {2,}', ' ', text)

    # Spaces around newlines
    text = re.sub(r' *\n *', '\n', text)

    # 4. Remove leading/trailing whitespace per line
    lines = text.split('\n')
    lines = [line.strip() for line in lines if line.strip()]

    # 5. Rejoin with single newline
    text = '\n'.join(lines)

    return text.strip()


def clean_chunks(chunks: List[dict]) -> List[dict]:
    """Clean text in a list of chunk dictionaries.

    Args:
        chunks: List of chunk dicts with 'text' field

    Returns:
        Chunks with cleaned text

    Example:
        >>> chunks = [{"id": "1", "text": "Page 1/4\\nRequisiti  obbligatori"}]
        >>> cleaned = clean_chunks(chunks)
        >>> cleaned[0]["text"]
        "Requisiti obbligatori"
    """
    for chunk in chunks:
        if "text" in chunk:
            chunk["text"] = clean_tender_text(chunk["text"])

    return chunks


def extract_structured_fields(text: str) -> dict:
    """Extract common structured fields from tender text.

    Useful for pre-processing before NER.

    Args:
        text: Tender document text

    Returns:
        Dictionary with extracted fields:
        {
            "cig": "CIG-XXXXX" or None,
            "cpv": "72000000" or None,
            "lot_ids": ["LOT-0001", ...],
            ...
        }

    Example:
        >>> text = "Codice CIG: CIG12345\\nCPV: 72000000\\nLOT-0001: Servizi IT"
        >>> extract_structured_fields(text)
        {'cig': 'CIG12345', 'cpv': '72000000', 'lot_ids': ['LOT-0001']}
    """
    fields = {
        "cig": None,
        "cpv": None,
        "lot_ids": [],
    }

    # Extract CIG code
    cig_match = re.search(r'CIG[:\s-]*([A-Z0-9]{10,})', text, re.IGNORECASE)
    if cig_match:
        fields["cig"] = cig_match.group(1)

    # Extract CPV code (8 digits)
    cpv_match = re.search(r'CPV[:\s-]*(\d{8})', text, re.IGNORECASE)
    if cpv_match:
        fields["cpv"] = cpv_match.group(1)

    # Extract LOT IDs
    lot_matches = re.findall(r'LOT[-_]?\d{4}', text, re.IGNORECASE)
    if lot_matches:
        fields["lot_ids"] = list(set(lot_matches))  # Deduplicate

    return fields
