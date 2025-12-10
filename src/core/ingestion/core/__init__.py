"""Convenience exports for ingestion core utilities."""

from .normalizer import normalize_bytes, normalize_text
from .lang_detect import detect_language
from .parser_pdf import extract_pdf_layout, parse_pdf
from .parser_docx import parse_docx
from .ocr import is_mostly_image_pdf, ocr_if_needed, run_ocrmypdf
from .heading_detection import tag_headings
from .table_detection import (
    extract_pdf_tables,
    flag_table_like_blocks,
    integrate_tables,
    table_to_block,
)
from .file_utils import copy_to_temporary_file, temporary_directory, write_bytes_to_file

__all__ = [
    "normalize_bytes",
    "normalize_text",
    "detect_language",
    "extract_pdf_layout",
    "parse_pdf",
    "parse_docx",
    "is_mostly_image_pdf",
    "ocr_if_needed",
    "run_ocrmypdf",
    "tag_headings",
    "extract_pdf_tables",
    "flag_table_like_blocks",
    "integrate_tables",
    "table_to_block",
    "copy_to_temporary_file",
    "temporary_directory",
    "write_bytes_to_file",
]
