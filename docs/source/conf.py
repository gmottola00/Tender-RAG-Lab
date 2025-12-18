"""
Sphinx configuration for Tender-RAG-Lab documentation.
"""
import os
import sys
from pathlib import Path

# -- Path setup --------------------------------------------------------------
# Add project root to sys.path for autodoc
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# -- Project information -----------------------------------------------------
project = "Tender-RAG-Lab"
copyright = "2025, Gianmarco Mottola"
author = "Gianmarco Mottola"
release = "0.1.0"
version = "0.1"

# -- General configuration ---------------------------------------------------
extensions = [
    # Core Sphinx extensions
    "sphinx.ext.autodoc",           # Auto-generate docs from docstrings
    "sphinx.ext.napoleon",          # Google/NumPy docstring support
    "sphinx.ext.viewcode",          # Add links to source code
    "sphinx.ext.intersphinx",       # Link to other project docs
    "sphinx.ext.todo",              # Support for TODOs
    "sphinx.ext.coverage",          # Coverage checker
    "sphinx.ext.autosummary",       # Generate autodoc summaries
    
    # Third-party extensions
    "myst_parser",                  # Markdown support
    "sphinx_autodoc_typehints",     # Type hints in docs
    "sphinx_copybutton",            # Copy button for code blocks
    "sphinxcontrib.mermaid",        # Mermaid diagram support
]

# -- MyST Parser Configuration -----------------------------------------------
myst_enable_extensions = [
    "colon_fence",      # ::: for admonitions
    "deflist",          # Definition lists
    "html_image",       # HTML images
    "linkify",          # Auto-detect URLs
    "replacements",     # Text replacements
    "smartquotes",      # Smart quotes
    "substitution",     # Variable substitutions
    "tasklist",         # GitHub-style task lists
]

myst_heading_anchors = 3  # Auto-generate anchors for h1-h3

# -- Autodoc Configuration ---------------------------------------------------
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
    "show-inheritance": True,
}

autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

# -- Napoleon Configuration --------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True

# -- Intersphinx Configuration -----------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "fastapi": ("https://fastapi.tiangolo.com", None),
    "pydantic": ("https://docs.pydantic.dev/latest", None),
    "sqlalchemy": ("https://docs.sqlalchemy.org/en/20/", None),
}

# -- Mermaid Configuration ---------------------------------------------------
mermaid_version = "10.6.0"
mermaid_init_js = """
mermaid.initialize({
    startOnLoad: true,
    theme: 'default',
    securityLevel: 'loose',
    logLevel: 'error',
});
"""

# -- General Settings --------------------------------------------------------
templates_path = ["_templates"]
exclude_patterns = []
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# The master document
master_doc = "index"

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

html_theme_options = {
    "logo_only": False,
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": True,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

html_context = {
    "display_github": True,
    "github_user": "gmottola00",
    "github_repo": "Tender-RAG-Lab",
    "github_version": "main",
    "conf_py_path": "/docs/source/",
}

html_title = f"{project} v{release}"
html_short_title = project
html_favicon = None  # Add favicon.ico to _static/ if you have one
html_logo = None     # Add logo.png to _static/ if you have one

# Show "Edit on GitHub" links
html_show_sourcelink = True

# -- Options for manual page output ------------------------------------------
man_pages = [
    (master_doc, "tender-rag-lab", "Tender-RAG-Lab Documentation", [author], 1)
]

# -- Options for Texinfo output ----------------------------------------------
texinfo_documents = [
    (
        master_doc,
        "Tender-RAG-Lab",
        "Tender-RAG-Lab Documentation",
        author,
        "Tender-RAG-Lab",
        "Production-grade RAG system for Italian procurement documents.",
        "Miscellaneous",
    ),
]

# -- Extension configuration -------------------------------------------------

# sphinx-copybutton
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_remove_prompts = True

# TODO extension
todo_include_todos = True

# Autosummary
autosummary_generate = True
autosummary_imported_members = False

# -- Custom CSS/JS (optional) ------------------------------------------------
def setup(app):
    """Custom Sphinx setup."""
    # Add custom CSS if needed
    # app.add_css_file("custom.css")
    pass
