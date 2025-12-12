# Ingestion Pipeline (PDF/DOCX → blocchi strutturati)

Questo modulo fornisce la pipeline di ingestione testuale (PDF e DOCX) per estrarre contenuti strutturati pronti per chunking e indicizzazione.

## Architettura

- `ingestion_service.py`: orchestratore high-level, coordina parsing, OCR, tagging heading e detection tabelle.
- `core/normalizer.py`: normalizzazione encoding e fix dei caratteri con `charset-normalizer` + `ftfy`.
- `core/lang_detect.py`: rilevazione lingua con fastText (fallback lingua-py).
- `core/parser_pdf.py`: parsing PDF con PyMuPDF, merge span/line/paragraph, ordinamento per bbox, rimozione header/footer ripetuti, label/value merge.
- `core/parser_docx.py`: parsing DOCX con python-docx, heading per stile, tabelle estratte come blocchi.
- `core/heading_detection.py`: euristiche heading (font-size/bold + numerazione tipo `1.` `1.1.` + regex Art./Capo).
- `core/table_detection.py`: detection tabelle con pdfplumber + euristiche testuali.
- `core/ocr.py`: wrapper ocrmypdf, detect PDF “image-heavy”, esegue OCR on demand.
- `core/file_utils.py`: helper per temp file/dir.

## Flusso di parsing

1. **Dispatch per estensione** (`IngestionService.parse_document`):
   - `.pdf`: `parse_pdf` (OCR opzionale se il PDF ha poco testo).
   - `.docx`: `parse_docx`.
2. **PDF**:
   - PyMuPDF → estrazione span → merge linee e paragrafi (bbox/font/size/page_number).
   - Ordinamento per y/x; merge label/valore; rimozione header/footer ripetuti; dedup globale testo+font.
   - Heading tagging (`heading_detection`), table detection (`table_detection`).
3. **DOCX**:
   - Heading da stile (“Heading 1/2/…”), paragrafi, tabelle come blocchi; `page_number=1`.
4. **Lingua**:
   - Concatenazione testo dei blocchi → `lang_detect.detect_language` (fastText se modello disponibile, fallback lingua-py).

Output: lista di pagine con blocchi arricchiti (`type`, `level`, `bbox`, `font_size`, `font_name`, `raw_cells`, `page_number`), più metadati base (`doc_id`, `filename`, `language`).

## Regole chiave

- **Heading**: bold+font-size relativa, numerazione gerarchica (`1.` `1.1.` `1.1.1`), regex per Art./Capo/Titolo; livelli assegnati per rango dimensione e pattern numerici.
- **Tabelle**: pdfplumber + euristiche (pipe, tab, colonne allineate); conversione a `table_block` con `raw_cells`.
- **Pulizia**: rimozione marker pagina (“Page X/Y”), header/footer ripetuti su più pagine; merge label/valore (righe che terminano con “:” unite alla successiva).
- **Ordine**: ordinamento per bbox (y poi x) per mantenere la prossimità visiva; merge blocchi adiacenti con stesso font/size e gap ridotto.

## Tecnologie

- PyMuPDF (`fitz`) per layout PDF.
- pdfplumber per tabelle PDF (opzionale).
- python-docx per DOCX.
- ocrmypdf + tesseract per OCR (opzionale).
- charset-normalizer, ftfy per testo.
- fastText o lingua-py per language detection.

## Configurazione e variabili ambiente

- Percorso modello fastText (se usato): passare a `IngestionService(lang_model_path=...)` o definire un path noto (default: `models/lid.176.bin`).
- OCR: richiede binari `ocrmypdf`/`tesseract` installati nel sistema.
- Parametri parsing (es. soglia OCR, heading/table detection) configurabili via init `IngestionService`; estrarre da env se necessario.

## Estensioni suggerite

- Esposizione di configurazioni via env/dataclass settings per library-level reuse.
- Migliorare heading detection con modelli ML o dizionari dominio-specifici.
- Rilevare e rimuovere header/footer con pattern personalizzabili.
- Estrarre metadati dominio (tender_code, lot_id, ecc.) da heading/paragrafi e propagarli ai chunk.

