#!/usr/bin/env bash
# Setup script for NER dependencies

set -e

echo "🔧 Setting up NER dependencies..."

# Install spaCy if not already installed
echo "📦 Installing spaCy..."
uv pip install spacy

# Download Italian model (large - best accuracy)
echo "📥 Downloading spaCy Italian model (it_core_news_lg - 550MB)..."
echo "   This may take a few minutes..."
uv run python -m spacy download it_core_news_lg

# Also download smaller model for faster testing
echo "📥 Downloading smaller model for testing (it_core_news_sm - 35MB)..."
uv run python -m spacy download it_core_news_sm

echo ""
echo "✅ NER setup complete!"
echo ""
echo "Available models:"
echo "  - it_core_news_lg  (550MB, best accuracy, recommended for production)"
echo "  - it_core_news_sm  (35MB, faster, good for testing)"
echo ""
echo "Test with:"
echo "  python tests/test_ner.py"
echo "  pytest tests/test_ner.py -v"
