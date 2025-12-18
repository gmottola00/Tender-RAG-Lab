# 🔄 Migration Guide: Ingestion Refactor

## Overview

The ingestion system has been refactored following clean architecture principles:
- **Core abstractions** moved to `src/core/ingestion/`
- **Concrete implementations** moved to `src/infra/parsers/`
- **Dependency injection** pattern for maximum flexibility

---

## What Changed

### Before (Old Code)
```python
from src.core.ingestion.ingestion_service import IngestionService

service = IngestionService.singleton()
result = service.parse_document("file.pdf")
```

### After (New Code)
```python
from src.infra.parsers import create_ingestion_service

service = create_ingestion_service()
result = service.parse_document("file.pdf")
```

---

## Directory Structure

### Old Structure ❌
```
src/core/ingestion/
├── ingestion_service.py          # Monolithic service
└── core/
    ├── parser_pdf.py             # Concrete PDF parser
    ├── parser_docx.py            # Concrete DOCX parser
    ├── ocr.py                    # Concrete OCR
    ├── lang_detect.py            # Concrete language detection
    └── file_utils.py             # Utils
```

### New Structure ✅
```
src/
├── core/
│   ├── ingestion/
│   │   ├── base.py               # 🟢 Abstract protocols
│   │   └── service.py            # 🟢 Generic orchestrator
│   └── utils/
│       └── file_utils.py         # 🟢 Generic utilities
│
└── infra/
    └── parsers/
        ├── factory.py            # 🔴 Production factory
        ├── pdf/
        │   ├── parser.py         # 🔴 PyMuPDF wrapper
        │   ├── pdfplumber_parser.py  # Original functions
        │   ├── ocr.py            # 🔴 Tesseract wrapper
        │   └── tesseract_ocr.py  # Original functions
        ├── docx/
        │   ├── parser.py         # 🔴 python-docx wrapper
        │   └── python_docx_parser.py  # Original functions
        └── text/
            ├── detector.py       # 🔴 fastText wrapper
            └── fasttext_detector.py  # Original functions
```

---

## Migration Steps

### Step 1: Update Imports

**Old:**
```python
from src.core.ingestion.ingestion_service import IngestionService
from src.core.ingestion.core.file_utils import temporary_directory
```

**New:**
```python
from src.infra.parsers import create_ingestion_service
from src.core.utils.file_utils import temporary_directory
```

### Step 2: Replace Singleton Pattern

**Old:**
```python
service = IngestionService.singleton()
```

**New:**
```python
service = create_ingestion_service()
```

### Step 3: Update Configuration

**Old:**
```python
service = IngestionService(
    enable_ocr=True,
    detect_headings=True,
)
```

**New:**
```python
service = create_ingestion_service(
    enable_ocr=True,
    detect_headings=True,
    detect_tables=True,
)
```

---

## Benefits of New Architecture

### ✅ **Testability**
```python
# Easy to mock dependencies
class MockPDFParser:
    def parse(self, path): return [...]

service = IngestionService(
    pdf_parser=MockPDFParser(),
    docx_parser=...,
)
```

### ✅ **Pluggability**
```python
# Want to use PyPDF2 instead of PyMuPDF?
class PyPDF2Parser:
    def parse(self, path): ...

service = IngestionService(
    pdf_parser=PyPDF2Parser(),  # Just swap it!
    ...
)
```

### ✅ **Library Extraction**
```python
# In future rag-lab library
from rag_lab.ingestion import IngestionService

# In tender-lab (this project)
from infra.parsers.factory import create_ingestion_service
```

### ✅ **Zero Breaking Changes for API**
The FastAPI endpoints remain unchanged - only internal implementation changed.

---

## Common Patterns

### Pattern 1: Production Usage
```python
from src.infra.parsers import create_ingestion_service

service = create_ingestion_service()
result = service.parse_document("document.pdf")
```

### Pattern 2: Testing
```python
from src.core.ingestion import IngestionService

service = IngestionService(
    pdf_parser=mock_pdf_parser,
    docx_parser=mock_docx_parser,
    ocr_engine=None,
    lang_detector=None,
)
```

### Pattern 3: Custom Configuration
```python
from src.infra.parsers.factory import create_ingestion_service

service = create_ingestion_service(
    enable_ocr=False,
    detect_headings=True,
    lang_model_path="/custom/path/lid.176.bin",
)
```

---

## Files to Update

Search your codebase for these patterns and update them:

```bash
# Find old imports
grep -r "from src.core.ingestion.ingestion_service import" .
grep -r "from src.core.ingestion.core" .

# Find singleton usage
grep -r "IngestionService.singleton()" .
```

**Files updated in this refactor:**
- ✅ `src/api/routers/ingestion.py` - Updated to use factory
- ✅ `README_chunking.md` - Updated examples

---

## Breaking Changes

### None for API consumers!

The HTTP API endpoints (`/parse`, `/parse-and-chunk`) work exactly the same.

### Internal code changes:
- `IngestionService.singleton()` → `create_ingestion_service()`
- `src.core.ingestion.core.*` → `src.infra.parsers.*` or `src.core.utils.*`

---

## Rollback Plan

If you need to rollback temporarily:

1. The old `src/core/ingestion/core/` files still exist (not deleted)
2. You can import from them directly if needed
3. But they are deprecated and will be removed in future

---

## Questions?

- Check `examples/ingestion_usage.py` for complete examples
- See `src/core/ingestion/base.py` for protocol definitions
- See `src/infra/parsers/factory.py` for configuration options

**Architecture document:** `architecture.md`
