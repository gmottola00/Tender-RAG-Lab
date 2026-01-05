# Testing Guide

Comprehensive testing strategy for Tender-RAG-Lab.

## Test Structure

```
tests/
├── test_ner.py                # NER unit tests
├── test_chunking.py           # Chunking tests
├── test_services.py           # Domain service tests
├── test_api.py                # API integration tests
└── conftest.py                # Pytest fixtures
```

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific marker
pytest -m "not slow"

# Verbose output
pytest -v tests/test_ner.py
```

## Test Categories

### Unit Tests

Fast, isolated tests:

```python
def test_tender_chunk_creation():
    chunk = TenderChunk(
        id="1",
        text="sample",
        tender_id="T001"
    )
    assert chunk.to_dict()["tender_id"] == "T001"
```

### Integration Tests

Tests with real services:

```python
@pytest.mark.integration
async def test_document_upload(client: TestClient):
    response = client.post("/documents/upload", files=...)
    assert response.status_code == 200
```

### Slow Tests

Mark expensive tests:

```python
@pytest.mark.slow
async def test_full_rag_pipeline():
    # End-to-end test
    ...
```

## Fixtures

Common fixtures in `conftest.py`:

```python
@pytest.fixture
def embed_client():
    return Mock(spec=EmbeddingClient)

@pytest.fixture
def test_db():
    # Setup test database
    yield db
    # Cleanup
```

## Coverage Goals

- **Overall**: >80%
- **Domain Layer**: >90%
- **API Layer**: >70%
- **Infrastructure**: >60%

## See Also

- [Contributing](contributing.md) - Development workflow
- [CI/CD](../about/changelog.md) - Automated testing
