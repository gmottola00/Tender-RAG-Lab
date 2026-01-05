# Contributing Guide

Thank you for considering contributing to Tender-RAG-Lab!

## Development Setup

1. Fork and clone:
```bash
git clone https://github.com/YOUR_USERNAME/Tender-RAG-Lab.git
cd Tender-RAG-Lab
```

2. Install dependencies:
```bash
uv sync --group dev
```

3. Install pre-commit hooks:
```bash
uv run pre-commit install
```

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src tests/

# Specific test file
pytest tests/test_ner.py -v
```

## Code Style

We use:
- **Black** for formatting
- **isort** for import sorting
- **pylint** for linting
- **mypy** for type checking

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Run linters
pylint src/
mypy src/
```

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/amazing-feature`
2. Make changes and commit: `git commit -m "Add amazing feature"`
3. Push: `git push origin feature/amazing-feature`
4. Open a Pull Request

## Documentation

Build docs locally:
```bash
mkdocs serve
```

Visit: http://127.0.0.1:8000

## Questions?

Open an [issue](https://github.com/gmottola00/Tender-RAG-Lab/issues) or [discussion](https://github.com/gmottola00/Tender-RAG-Lab/discussions).
