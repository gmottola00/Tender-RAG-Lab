"""Service layer orchestrating ingestion steps for PDFs and DOCX files."""

from __future__ import annotations

import uuid
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Sequence, Union

from src.core.ingestion.core import heading_detection, lang_detect, ocr, parser_docx, parser_pdf
from src.core.ingestion.core.file_utils import temporary_directory

PageDict = Dict[str, Any]


class IngestionService:
    """High-level orchestrator for document ingestion.

    This service compone pure functions from ``core`` to:
    - optionally run OCR on mostly-image PDFs
    - parse PDF/DOCX into structured pages/blocks
    - detect language on aggregated text

    Args:
        lang_model_path: Optional path to a fastText model; if omitted, defaults
            to the path used in ``lang_detect``.
        enable_ocr: Whether OCR is allowed on PDFs detected as scanned.
        ocr_text_threshold: Minimum pre-existing text length before skipping OCR.
        detect_headings: Whether to classify heading-like blocks on PDFs.
        detect_tables: Whether to detect tables via pdfplumber/heuristics.
    """

    def __init__(
        self,
        *,
        lang_model_path: Optional[str] = None,
        enable_ocr: bool = True,
        ocr_text_threshold: int = 200,
        detect_headings: bool = True,
        detect_tables: bool = True,
    ) -> None:
        self.lang_model_path = lang_model_path
        self.enable_ocr = enable_ocr
        self.ocr_text_threshold = ocr_text_threshold
        self.detect_headings = detect_headings
        self.detect_tables = detect_tables

    # --- Singleton support ---
    _singleton: Optional["IngestionService"] = None
    _singleton_config: Optional[Dict[str, Any]] = None
    _singleton_lock: Lock = Lock()

    @classmethod
    def singleton(
        cls,
        *,
        lang_model_path: Optional[str] = None,
        enable_ocr: bool = True,
        ocr_text_threshold: int = 200,
        detect_headings: bool = True,
        detect_tables: bool = True,
    ) -> "IngestionService":
        """Return a process-wide singleton instance with the given configuration.

        If called multiple times with different parameters, a ValueError is raised
        to avoid silently reconfiguring the shared instance.
        """
        with cls._singleton_lock:
            config = {
                "lang_model_path": lang_model_path,
                "enable_ocr": enable_ocr,
                "ocr_text_threshold": ocr_text_threshold,
                "detect_headings": detect_headings,
                "detect_tables": detect_tables,
            }
            if cls._singleton is not None:
                if config != cls._singleton_config:
                    raise ValueError(
                        "IngestionService singleton already initialized with different configuration"
                    )
                return cls._singleton

            cls._singleton = cls(**config)
            cls._singleton_config = config
            return cls._singleton

    @classmethod
    def reset_singleton(cls) -> None:
        """Reset the singleton instance (intended for tests)."""
        with cls._singleton_lock:
            cls._singleton = None
            cls._singleton_config = None

    def parse_document(self, path: Union[str, Path], doc_id: Optional[str] = None) -> Dict[str, Any]:
        """Parse a PDF or DOCX and return a structured representation."""
        source_path = Path(path)
        if not source_path.exists():
            raise FileNotFoundError(f"File not found at {source_path}")

        ext = source_path.suffix.lower()
        if ext == ".pdf":
            pages = self._parse_pdf_with_optional_ocr(source_path)
        elif ext == ".docx":
            pages = self._parse_docx(source_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        language = self.detect_language_from_pages(pages)

        return {
            "doc_id": doc_id or str(uuid.uuid4()),
            "filename": source_path.name,
            "language": language,
            "pages": pages,
        }

    def _parse_pdf_with_optional_ocr(self, pdf_path: Path) -> List[PageDict]:
        """Parse a PDF, running OCR first if the document is mostly images."""
        if not self.enable_ocr:
            return parser_pdf.parse_pdf(
                pdf_path,
                detect_headings=self.detect_headings,
                detect_tables=self.detect_tables,
            )

        with temporary_directory() as tmp_dir:
            ocr_output = tmp_dir / f"ocr_{pdf_path.name}"
            needs_ocr = ocr.ocr_if_needed(
                pdf_path,
                ocr_output,
                text_threshold=self.ocr_text_threshold,
                force=False,
            )
            target_path = ocr_output if needs_ocr else pdf_path

            return parser_pdf.parse_pdf(
                target_path,
                detect_headings=self.detect_headings,
                detect_tables=self.detect_tables,
            )

    def _parse_docx(self, docx_path: Path) -> List[PageDict]:
        """Parse DOCX into a single-page layout with blocks and tables."""
        parsed = parser_docx.parse_docx(docx_path)
        blocks = list(parsed.get("blocks", [])) + list(parsed.get("tables", []))
        return [{"page_number": 1, "blocks": blocks}]

    def detect_language_from_pages(self, pages: Sequence[PageDict]) -> str:
        """Run language detection over aggregated page text."""
        texts: List[str] = []
        for page in pages:
            for block in page.get("blocks", []):
                text = block.get("text")
                if isinstance(text, str):
                    texts.append(text)
        combined = "\n".join(texts)
        return lang_detect.detect_language(combined, model_path=self.lang_model_path)


__all__ = ["IngestionService"]
