# Guida Installazione Modello spaCy

## ⚠️ Problema Certificato SSL

Hai un proxy/firewall (TIM) che blocca i certificati GitHub. 

## 🔧 Soluzioni

### Opzione 1: Download Manuale (Consigliato)

1. **Scarica il modello dal browser**:
   - Small (35MB, veloce, test): https://github.com/explosion/spacy-models/releases/download/it_core_news_sm-3.8.0/it_core_news_sm-3.8.0-py3-none-any.whl
   - Large (550MB, accurato, produzione): https://github.com/explosion/spacy-models/releases/download/it_core_news_lg-3.8.0/it_core_news_lg-3.8.0-py3-none-any.whl

2. **Installa da file locale**:
```bash
cd /Users/gianmarcomottola/Desktop/projects/Tender-RAG-Lab
uv run pip install ~/Downloads/it_core_news_sm-3.8.0-py3-none-any.whl
# oppure per large:
# uv run pip install ~/Downloads/it_core_news_lg-3.8.0-py3-none-any.whl
```

### Opzione 2: Disabilita Verifica SSL (Temporaneo)

⚠️ **SOLO per testing, NON per produzione**

```bash
cd /Users/gianmarcomottola/Desktop/projects/Tender-RAG-Lab
uv run pip install --trusted-host github.com --trusted-host objects.githubusercontent.com it-core-news-sm
```

### Opzione 3: Usa VPN/Hotspot Mobile

Se hai problemi persistenti con il proxy TIM, connettiti a:
- Hotspot mobile del telefono
- VPN personale
- Rete diversa

---

## ✅ Test Dopo Installazione

```bash
cd /Users/gianmarcomottola/Desktop/projects/Tender-RAG-Lab
uv run python tests/test_ner.py
```

Dovrebbe stampare:
```
✓ Initialized: TenderNER(model='it_core_news_sm')
✓ Extracted N entity types:
  ORGANIZATION: [...]
  DATE: [...]
  MONEY: [...]
✅ All tests passed!
```

---

## 📦 Modelli Disponibili

| Modello | Dimensione | Accuratezza | Velocità | Uso |
|---------|------------|-------------|----------|-----|
| `it_core_news_sm` | 35MB | Bassa | Veloce | Test, sviluppo |
| `it_core_news_md` | 90MB | Media | Media | Bilanciato |
| `it_core_news_lg` | 550MB | Alta | Lenta | **Produzione** |

**Consiglio**: Inizia con `sm` per testare, poi usa `lg` per produzione.
