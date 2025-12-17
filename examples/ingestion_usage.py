"""Example: Using the refactored ingestion system.

This example demonstrates how to use the new dependency-injected
ingestion architecture for maximum flexibility and testability.
"""

from pathlib import Path

# === PRODUCTION USAGE ===
# Use the factory for fully configured service
from src.infra.parsers import create_ingestion_service

# Create service with all features enabled
service = create_ingestion_service(
    enable_ocr=True,
    detect_headings=True,
    detect_tables=True,
)

# Parse a document
result = service.parse_document("example.pdf")
print(f"Language: {result['language']}")
print(f"Pages: {result['total_pages']}")

# === LIGHTWEIGHT USAGE ===
# For testing or simple parsing without OCR
from src.infra.parsers import create_lightweight_ingestion_service

light_service = create_lightweight_ingestion_service()
result = light_service.parse_document("simple.pdf")

# === CUSTOM CONFIGURATION ===
# Build your own service with custom implementations
from src.core.ingestion import IngestionService
from src.infra.parsers.pdf.parser import PyMuPDFParser
from src.infra.parsers.docx.parser import PythonDocxParser
from src.infra.parsers.pdf.ocr import TesseractOCREngine
from src.infra.parsers.text.detector import FastTextLanguageDetector

custom_service = IngestionService(
    pdf_parser=PyMuPDFParser(detect_headings=False),
    docx_parser=PythonDocxParser(),
    ocr_engine=TesseractOCREngine(),
    lang_detector=FastTextLanguageDetector(max_chars=10000),
    ocr_text_threshold=500,
)

# === TESTING WITH MOCKS ===
# Easy to inject mocks for testing
class MockPDFParser:
    def parse(self, path: Path):
        return [{"page_number": 1, "blocks": [{"text": "Mock content"}]}]

class MockLanguageDetector:
    def detect(self, text: str) -> str:
        return "en"

test_service = IngestionService(
    pdf_parser=MockPDFParser(),  # type: ignore
    docx_parser=PythonDocxParser(),
    ocr_engine=None,
    lang_detector=MockLanguageDetector(),  # type: ignore
)

test_result = test_service.parse_document("test.pdf")
assert test_result["language"] == "en"

# === PLUGGABLE ARCHITECTURE ===
# Want to use a different PDF parser? Just implement DocumentParser protocol!
from src.core.ingestion.base import DocumentParser
from typing import List

class CustomPDFParser:
    """Example: Use PyPDF2 instead of PyMuPDF."""
    
    def parse(self, path: Path) -> List[dict]:
        # Your implementation here
        # import PyPDF2
        # ...
        return []

# Replace PyMuPDF with your custom parser
custom_pdf_service = IngestionService(
    pdf_parser=CustomPDFParser(),  # type: ignore
    docx_parser=PythonDocxParser(),
)

print("✅ All examples completed successfully!")
