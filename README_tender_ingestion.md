# Tender Ingestion & Preprocessing Service

Pipeline Python per l’ingestione e la normalizzazione di documenti di gara (bandi, disciplinari, capitolati, allegati) da PDF/Word verso un formato JSON strutturato, pronto per RAG classico e Graph RAG.

---

## Obiettivi

- Estrarre **testo strutturato** da PDF e Word.
- Mantenere la struttura logica:
  - pagine
  - heading (Capitolo, Articolo, Titolo, ecc.)
  - blocchi di testo normali
  - tabelle (anche solo come blocchi di testo / celle).
- Normalizzare:
  - encoding → UTF-8 pulito
  - lingua del documento (language detection).
- Esporre il tutto tramite un servizio (es. FastAPI) o come libreria interna.

---

## Stack Tecnologico (open source)

**Parsing PDF**
- [`pymupdf`](https://pymupdf.readthedocs.io/) (`fitz`): estrazione testo + layout (bbox, font, size, ecc.)
- [`pdfplumber`](https://github.com/jsvine/pdfplumber) *(opzionale)*: supporto tabella base.

**OCR per PDF scanner**
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [`ocrmypdf`](https://github.com/ocrmypdf/OCRmyPDF)

**Parsing Word**
- [`python-docx`](https://python-docx.readthedocs.io/)

**Normalizzazione testo**
- [`charset-normalizer`](https://github.com/Ousret/charset_normalizer) o `chardet`
- [`ftfy`](https://ftfy.readthedocs.io/en/latest/)

**Language detection**
- [fastText LID.176](https://fasttext.cc/docs/en/language-identification.html) *(consigliato)*  
  oppure
- [`lingua-py`](https://github.com/pemistahl/lingua-py) / `langid` / `langdetect`.

**API (facoltativo ma consigliato)**
- [`fastapi`](https://fastapi.tiangolo.com/)
- [`uvicorn`](https://www.uvicorn.org/)

---

## Requisiti di Sistema

Dipendenze di sistema minime (esempi generici):

```bash
# Ubuntu / Debian (esempio)
sudo apt-get update
sudo apt-get install -y   tesseract-ocr   ocrmypdf   ghostscript   poppler-utils   python3-dev   build-essential
```

Su macOS:
- Installare Homebrew.
- Installare tesseract + ocrmypdf via `brew`.

```bash
brew install tesseract ocrmypdf ghostscript
```

---

## Installazione Python

Creazione ambiente (esempio con `venv`):

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

Installazione dipendenze minime:

```bash
pip install \
  pymupdf \
  pdfplumber \
  python-docx \
  charset-normalizer \
  ftfy \
  fastapi uvicorn[standard]
```

Per fastText:

```bash
pip install fasttext
# oppure
pip install lingua-language-detector
```

Scaricare il modello pre-addestrato LID.176 (se usi fastText):

```bash
wget https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin
# spostalo in una cartella nota, es: models/lid.176.bin
```

---

## Struttura del Progetto (proposta)

```bash
tender-ingestion/
├─ ingestion/
│  ├─ __init__.py
│  ├─ main.py                 # FastAPI app (endpoint /parse)
│  ├─ config.py
│  ├─ models/
│  │  ├─ schemas.py           # Pydantic models per input/output
│  ├─ core/
│  │  ├─ normalizer.py        # encoding + ftfy
│  │  ├─ lang_detect.py       # fastText / lingua
│  │  ├─ parser_pdf.py        # logica parsing PDF
│  │  ├─ parser_docx.py       # logica parsing DOCX
│  │  ├─ ocr.py               # gestione OCR / OCRmyPDF
│  │  ├─ heading_detection.py # euristiche per heading
│  │  ├─ table_detection.py   # tabella come blocco
│  └─ utils/
│     ├─ file_utils.py        # helper gestione file temporanei
└─ tests/
   ├─ test_pdf_parsing.py
   ├─ test_docx_parsing.py
   ├─ test_lang_detect.py
```

---

## Checklist di Implementazione (dettaglio)

### 1. Normalizzazione encoding

Obiettivo: partire da `bytes` e ottenere `str` UTF-8 pulita.

File: `core/normalizer.py`

Esempio:

```python
from charset_normalizer import from_bytes
import ftfy

def normalize_bytes(raw_bytes: bytes) -> str:
    # 1) rileva encoding e decodifica
    result = from_bytes(raw_bytes).best()
    if result is None:
        text = raw_bytes.decode("utf-8", errors="replace")
    else:
        text = str(result)

    # 2) fix caratteri strani (Ã¨ -> è, ecc.)
    text = ftfy.fix_text(text)

    return text
```

Nel caso PDF/Word:
- spesso le librerie ti danno già `str`.
- Usa `ftfy.fix_text()` come step finale per sistemare anomalie.

---

### 2. Language detection

Obiettivo: determinare la lingua principale del documento (es. `it`, `en`).

File: `core/lang_detect.py`

Con fastText:

```python
import fasttext
from functools import lru_cache

@lru_cache(maxsize=1)
def load_lang_model(model_path: str = "models/lid.176.bin"):
    return fasttext.load_model(model_path)

def detect_language(text: str, max_chars: int = 5000) -> str:
    if not text:
        return "unknown"

    snippet = text[:max_chars]
    model = load_lang_model()
    labels, probabilities = model.predict(snippet.replace("\n", " "))
    label = labels[0]  # es. "__label__it"
    lang = label.replace("__label__", "")
    return lang
```

Uso tipico:
- concatenare una parte del testo estratto (ad es. primi N caratteri).
- chiamare `detect_language()` una sola volta per documento.

---

### 3. Parsing PDF (digitale)

File: `core/parser_pdf.py`

Obiettivi:
- Caricare PDF con PyMuPDF.
- Estrarre blocchi di testo per pagina.
- Raccogliere info su font / size / bbox.
- Passare i blocchi a:
  - `heading_detection.py` per classificare heading.
  - `table_detection.py` per marcare tabelle.

Esempio base di estrazione:

```python
import fitz  # pymupdf
from typing import List, Dict, Any

def extract_pdf_layout(path: str) -> List[Dict[str, Any]]:
    """
    Ritorna una lista di pagine, ognuna con lista di blocchi:
    [
      {
        "page_number": 1,
        "blocks": [
          {"text": "...", "bbox": [...], "font_size": 11.0, "font_name": "..."},
          ...
        ]
      },
      ...
    ]
    """
    doc = fitz.open(path)
    pages = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        blocks = []

        for b in page.get_text("dict")["blocks"]:
            if "lines" not in b:
                continue
            for line in b["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    blocks.append({
                        "text": text,
                        "bbox": span["bbox"],
                        "font_size": span["size"],
                        "font_name": span["font"],
                    })

        pages.append({
            "page_number": page_index + 1,
            "blocks": blocks,
        })

    doc.close()
    return pages
```

Questi `blocks` saranno poi arricchiti con `type` (`heading`, `paragraph`, `table_block`, ecc.).

---

### 4. Riconoscimento heading (Capitolo, Articolo, ecc.)

File: `core/heading_detection.py`

Logica base (euristiche):

- heading candidate se:
  - font più grande della mediana (sulla stessa pagina)
  - oppure regex su pattern tipo:
    - `r"^Art\.?\s+\d+"`
    - `r"^CAPO\s+[IVXLC]+"`
    - `r"^Capitolo\s+\d+"`
- Assegnare `level` in base al pattern o dimensione font.

Esempio:

```python
import re
from statistics import median
from typing import List, Dict

ART_PATTERN = re.compile(r"^Art\.?\s+\d+.*", re.IGNORECASE)
CAPO_PATTERN = re.compile(r"^CAPO\s+[IVXLC]+.*", re.IGNORECASE)

def tag_headings(page_blocks: List[Dict]) -> List[Dict]:
    sizes = [b["font_size"] for b in page_blocks if b.get("font_size")]
    if not sizes:
        return page_blocks

    size_med = median(sizes)
    size_threshold = size_med + 1.5  # euristica

    for block in page_blocks:
        text = block["text"]
        size = block["font_size"]

        block_type = "paragraph"
        level = None

        if size >= size_threshold:
            block_type = "heading"
            level = 1
        if ART_PATTERN.match(text):
            block_type = "heading"
            level = 2
        if CAPO_PATTERN.match(text):
            block_type = "heading"
            level = 1

        block["type"] = block_type
        if level is not None:
            block["level"] = level

    return page_blocks
```

---

### 5. Tabelle base (PDF → blocchi di testo)

File: `core/table_detection.py`

Due approcci:

1. Usare `pdfplumber` per tentare `extract_tables()`.
2. Applicare un’etichetta `table_block` in base a euristiche (es. molte colonne allineate).

Esempio semplice con pdfplumber:

```python
import pdfplumber
from typing import List, Dict, Any

def extract_pdf_tables(path: str) -> List[Dict[str, Any]]:
    tables_per_page = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            page_tables = []
            for t in tables:
                page_tables.append({
                    "page_number": i,
                    "cells": t,  # lista di righe, ciascuna lista di celle
                })
            tables_per_page.append(page_tables)
    return tables_per_page
```

In seguito:
- puoi mappare ogni tabella in un blocco logico:

```python
def table_to_block(table_cells):
    # Linearizza oppure mantieni la struttura
    text_rows = [" | ".join(cell or "" for cell in row) for row in table_cells]
    text = "\n".join(text_rows)
    return {
        "type": "table_block",
        "text": text,
        "raw_cells": table_cells,
    }
```

---

### 6. PDF scanner → OCR

File: `core/ocr.py`

Strategia:

1. Apri il PDF con PyMuPDF e controlla se c’è quasi zero testo:
   - se sì → considera il documento come “scanner”.
2. Usa `ocrmypdf` per creare un nuovo PDF con layer di testo.
3. Ripassa quel PDF “OCR-izzato” nella pipeline standard.

Esempio wrapper `ocrmypdf`:

```python
import subprocess

def run_ocrmypdf(input_path: str, output_path: str):
    cmd = [
        "ocrmypdf",
        "--deskew",
        "--optimize", "3",
        "--output-type", "pdf",
        input_path,
        output_path,
    ]
    subprocess.run(cmd, check=True)

def is_mostly_image_pdf(path: str, text_threshold: int = 200) -> bool:
    import fitz
    doc = fitz.open(path)
    total_text_len = 0
    for page in doc:
        total_text_len += len(page.get_text())
    doc.close()
    return total_text_len < text_threshold
```

---

### 7. Parsing Word (DOCX)

File: `core/parser_docx.py`

Obiettivi:
- Estrarre paragrafi con stile (Heading 1, Heading 2, Body, ecc.).
- Estrarre tabelle come blocchi strutturati.

Esempio:

```python
from docx import Document
from typing import List, Dict, Any

def parse_docx(path: str) -> Dict[str, Any]:
    doc = Document(path)

    blocks = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        style_name = para.style.name if para.style else ""
        block_type = "paragraph"
        level = None

        if style_name.startswith("Heading"):
            block_type = "heading"
            try:
                level = int(style_name.replace("Heading", "").strip())
            except Exception:
                level = 1

        blocks.append({
            "type": block_type,
            "level": level,
            "text": text,
            "style": style_name,
        })

    tables = []
    for t in doc.tables:
        rows = []
        for row in t.rows:
            cells = [c.text.strip() for c in row.cells]
            rows.append(cells)
        tables.append({
            "type": "table_block",
            "raw_cells": rows,
        })

    return {
        "blocks": blocks,
        "tables": tables,
    }
```

---

### 8. Schema JSON di output

File: `models/schemas.py` (esempio Pydantic)

```python
from typing import List, Optional
from pydantic import BaseModel

class Block(BaseModel):
    type: str                 # "heading", "paragraph", "table_block"
    text: str
    level: Optional[int] = None
    bbox: Optional[list] = None
    raw_cells: Optional[list] = None
    font_size: Optional[float] = None
    font_name: Optional[str] = None

class Page(BaseModel):
    page_number: int
    blocks: List[Block]

class ParsedDocument(BaseModel):
    doc_id: str
    filename: str
    language: str
    pages: List[Page]
```

Output atteso (esempio):

```json
{
  "doc_id": "bando-123",
  "filename": "bando.pdf",
  "language": "it",
  "pages": [
    {
      "page_number": 1,
      "blocks": [
        {
          "type": "heading",
          "level": 1,
          "text": "CAPO I – DISPOSIZIONI GENERALI",
          "bbox": [50.0, 80.0, 560.0, 110.0]
        },
        {
          "type": "paragraph",
          "text": "L'appalto ha per oggetto...",
          "bbox": [50.0, 120.0, 560.0, 200.0]
        },
        {
          "type": "table_block",
          "text": "Lotto 1 | Importo a base d'asta ...",
          "raw_cells": [["Lotto 1", "Importo ..."], ["Lotto 2", "Importo ..."]]
        }
      ]
    }
  ]
}
```

---

### 9. API FastAPI di alto livello

File: `ingestion/main.py`

Esempio endpoint `/parse`:

```python
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import uuid
import os
from .models.schemas import ParsedDocument
from .core import parser_pdf, parser_docx, lang_detect

app = FastAPI(title="Tender Ingestion Service")

@app.post("/parse", response_model=ParsedDocument)
async def parse_document(file: UploadFile = File(...)):
    # Salva su disco temporaneamente
    tmp_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    # Dispatch per estensione
    ext = os.path.splitext(file.filename)[1].lower()
    if ext == ".pdf":
        # gestire OCR + parsing layout
        # (es: detect scanner -> run ocrmypdf -> parser_pdf.extract_pdf_layout)
        pages_raw = parser_pdf.extract_pdf_layout(tmp_path)
        # arricchire con tag_headings, table_detection, ecc.
    elif ext in [".docx"]:
        # parse_docx e poi adattare al modello Page/Block
        ...
    else:
        os.remove(tmp_path)
        return JSONResponse(
            status_code=400,
            content={"detail": f"Unsupported file type: {ext}"}
        )

    # concatenare testo per detection lingua
    all_text = []
    for p in pages_raw:
        for b in p["blocks"]:
            all_text.append(b.get("text", ""))
    language = lang_detect.detect_language("\n".join(all_text))

    # mappare pages_raw -> ParsedDocument
    parsed_doc = ParsedDocument(
        doc_id=str(uuid.uuid4()),
        filename=file.filename,
        language=language,
        pages=pages_raw,  # adattare/serializzare verso Page/Block
    )

    os.remove(tmp_path)
    return parsed_doc
```

Avvio del servizio:

```bash
uvicorn ingestion.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Test Locali Rapidi

1. Mettere alcuni PDF e DOCX di prova in `tests/data/`.
2. Scrivere test di base:

```python
# tests/test_pdf_parsing.py
from ingestion.core.parser_pdf import extract_pdf_layout

def test_pdf_parsing_basic():
    pages = extract_pdf_layout("tests/data/bando_sample.pdf")
    assert len(pages) > 0
    assert len(pages[0]["blocks"]) > 0
```

3. Eseguire:

```bash
pytest -q
```

---

## Estensioni Future

- Migliorare il riconoscimento heading con modelli ML leggeri.
- Usare `layoutparser` per una segmentation più avanzata (tabelle, header, footer).
- Aggiungere normalizzazione semantica (es. riconoscere esplicitamente “Articolo X”, “Lotto Y” e creare campi dedicati).
- Gestire multi-lingua all’interno dello stesso documento (es. capitolati bilingue).

Questo README definisce tutti i passi necessari per implementare in Python la pipeline di ingestion & preprocessing per il progetto Tender, basata sulla checklist secca ma arricchita con il dettaglio operativo.
