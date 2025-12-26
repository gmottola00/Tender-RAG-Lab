# Sphinx Documentation Guide

> **Internal developer guide for managing Tender-RAG-Lab documentation**

This file is NOT included in the compiled documentation. It's a reference for developers working on the docs.

---

## Overview

The documentation uses **Sphinx** with **MyST-Parser** to support both reStructuredText (`.rst`) and Markdown (`.md`) files.

**Stack:**
- **Sphinx 8.2.3** - Documentation generator
- **MyST-Parser 4.0.1** - Markdown support for Sphinx
- **Furo theme** - Clean, modern documentation theme
- **sphinx-copybutton** - Copy code blocks easily
- **autodoc** - Auto-generate API docs from Python docstrings

---

## Quick Commands

```bash
# Navigate to docs directory
cd docs/

# Clean build artifacts
make clean

# Build HTML documentation
make html

# Build and serve locally
make serve  # Opens at http://localhost:8000

# Check for broken links
make linkcheck

# Auto-rebuild on changes (watch mode)
make watch

# Full rebuild (clean + build + linkcheck)
make all
```

---

## File Structure

```
docs/
├── source/                    # Source files
│   ├── conf.py               # Sphinx configuration
│   ├── index.rst             # Main entry point (reStructuredText)
│   ├── architecture/         # Architecture docs (.md)
│   ├── domain/               # Domain layer docs (.md)
│   ├── apps/                 # Apps layer docs (.md)
│   ├── guides/               # User guides (.md)
│   ├── rag_toolkit/          # rag_toolkit integration (.rst)
│   └── api/                  # Auto-generated API docs
├── build/                    # Generated HTML (gitignored)
│   └── html/
├── Makefile                  # Build commands
└── README_SPHINX.md          # This file (not in docs)
```

---

## Sphinx Configuration

**Key settings in `conf.py`:**

```python
# Project info
project = 'Tender-RAG-Lab'
author = 'Gianmarco Mottola'
release = '1.0.0'

# Theme
html_theme = 'furo'

# Extensions
extensions = [
    'sphinx.ext.autodoc',      # Auto API docs
    'sphinx.ext.napoleon',     # Google/NumPy docstrings
    'myst_parser',             # Markdown support
    'sphinx_copybutton',       # Copy button on code blocks
]

# MyST extensions
myst_enable_extensions = [
    'colon_fence',    # ::: syntax
    'deflist',        # Definition lists
    'html_image',     # HTML img tags
    'linkify',        # Auto-link URLs
    'substitution',   # Variable substitution
    'tasklist',       # - [ ] checkboxes
]
```

---

## Writing Documentation

### When to use .rst vs .md

**Use reStructuredText (.rst) for:**
- Main index pages with complex TOC trees
- Files with Sphinx directives (toctree, automodule, etc.)
- API reference pages

**Use Markdown (.md) for:**
- Content-heavy documentation
- Guides and tutorials
- Architecture explanations
- Most new documentation

### Markdown Syntax (MyST)

**Headings:**
```markdown
# H1
## H2
### H3
```

**Links:**
```markdown
[Link text](relative/path.md)
[External link](https://example.com)
{doc}`other-file`  # Sphinx cross-reference
```

**Code blocks:**
````markdown
```python
def example():
    pass
```
````

**Admonitions:**
```markdown
:::{note}
This is a note.
:::

:::{warning}
This is a warning.
:::
```

**Tables:**
```markdown
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
```

---

### reStructuredText Syntax

**TOC Tree (for index pages):**
```rst
.. toctree::
   :maxdepth: 2
   :caption: Section Name

   file1
   file2
   folder/file3
```

**Cross-references:**
```rst
:doc:`path/to/file`         # Link to document
:ref:`label-name`           # Link to label
```

**Directives:**
```rst
.. note::
   This is a note.

.. code-block:: python

   def example():
       pass
```

---

## Adding New Documentation

### 1. Create the file

```bash
# For content pages (prefer Markdown)
touch docs/source/guides/new-guide.md

# For index pages with TOC (use reStructuredText)
touch docs/source/section/index.rst
```

### 2. Add to TOC tree

Edit `docs/source/index.rst`:

```rst
.. toctree::
   :maxdepth: 2
   :caption: Section Name

   guides/new-guide
```

### 3. Write content

Follow existing patterns in similar documents.

### 4. Build and verify

```bash
make clean && make html
open build/html/index.html
```

---

## Sphinx Autodoc (API Reference)

Generate API docs from Python docstrings:

**In `.rst` file:**
```rst
.. automodule:: src.domain.tender.services.tenders
   :members:
   :undoc-members:
   :show-inheritance:
```

**Docstring format (Google style):**
```python
def process_document(doc_id: str, options: dict) -> Document:
    """Process a tender document.
    
    Args:
        doc_id: Unique document identifier
        options: Processing options dict
        
    Returns:
        Processed Document object
        
    Raises:
        DocumentNotFound: If document doesn't exist
    """
```

---

## Troubleshooting

### "WARNING: document isn't included in any toctree"

Add the file to a `toctree` directive in `index.rst` or parent file.

### "WARNING: 'myst' cross-reference target not found"

The linked file doesn't exist. Either create it or remove the link.

### Autodoc import errors

The code imports `rag_toolkit` which isn't in the docs environment. This is expected - autodoc warnings can be ignored for external dependencies.

### Mermaid diagrams not rendering

Convert to ASCII art instead - more reliable across Sphinx versions:

```
┌────────────┐
│   Box 1    │
└─────┬──────┘
      ↓
┌─────▼──────┐
│   Box 2    │
└────────────┘
```

---

## Build Output

**Generated files:**
- `build/html/index.html` - Main entry point
- `build/html/**/*.html` - All documentation pages
- `build/html/_static/` - CSS, JS, fonts
- `build/html/_sources/` - Original source files

**Deploy:**
```bash
# Build for production
make clean && make html

# Deploy to GitHub Pages (if configured)
cp -r build/html/* /path/to/gh-pages/

# Or use Sphinx deployment
make github
```

---

## Best Practices

1. **Exclude development docs** - Files like this aren't in `index.rst`
2. **Use Markdown for content** - Easier to write and maintain
3. **Use .rst for structure** - Better TOC tree control
4. **Remove emoji from titles** - Professional documentation style
5. **Fix broken links immediately** - Run `make linkcheck` regularly
6. **Update last modified date** - At bottom of major pages
7. **Test locally before committing** - `make html` should build cleanly

---

## Useful Resources

- **Sphinx docs:** https://www.sphinx-doc.org/
- **MyST-Parser:** https://myst-parser.readthedocs.io/
- **Furo theme:** https://pradyunsg.me/furo/
- **reStructuredText:** https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html

---

**Last updated:** 2025-12-25
