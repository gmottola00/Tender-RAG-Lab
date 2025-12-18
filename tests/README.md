# Test Structure Documentation

## Overview

This directory contains comprehensive tests for the Tender-RAG-Lab project, organized according to clean architecture principles.

## Directory Structure

```
tests/
├── conftest.py              # Root fixtures available to all tests
├── mocks/                   # Reusable mock implementations
│   └── __init__.py         # MockEmbeddingClient, MockLLMClient, etc.
├── fixtures/                # Test data and sample files
│   ├── files/              # Sample PDFs, DOCX for parser tests
│   └── __init__.py
├── unit/                    # Fast tests, no external dependencies
│   ├── core/               # Test generic RAG components
│   │   ├── chunking/       # Chunk types, DynamicChunker
│   │   ├── index/          # IndexService, search strategies
│   │   ├── rag/            # RAG pipeline, rerankers
│   │   ├── embedding/      # Embedding protocols
│   │   └── llm/            # LLM protocols
│   └── domain/             # Test business logic
│       └── tender/
│           ├── test_entities.py
│           ├── test_schemas.py
│           └── test_services.py
├── integration/            # Tests requiring external services
│   ├── infra/
│   │   └── test_milvus_service.py  # Real Milvus operations
│   └── apps/
│       └── test_api_routers.py     # FastAPI endpoint tests
└── e2e/                    # Full workflow tests
    └── test_workflows.py   # Complete ingestion & RAG flows
```

## Test Categories (Markers)

Tests are categorized using pytest markers:

### `@pytest.mark.unit`
- **Fast tests** (< 1 second each)
- **No external dependencies** (no database, Milvus, APIs)
- Use mocks for all I/O operations
- Run by default in CI/CD

**Example:**
```python
@pytest.mark.unit
def test_chunk_creation():
    chunk = Chunk(text="test", metadata={})
    assert chunk.text == "test"
```

### `@pytest.mark.integration`
- Require **real services** (Milvus, Postgres, etc.)
- Test interactions between components
- May require docker-compose services running

**Example:**
```python
@pytest.mark.integration
@pytest.mark.milvus
def test_milvus_search(milvus_service):
    results = milvus_service.search(...)
    assert len(results) > 0
```

### `@pytest.mark.e2e`
- **End-to-end workflows**
- Test complete user scenarios
- Require full infrastructure stack
- Slowest tests

**Example:**
```python
@pytest.mark.e2e
@pytest.mark.slow
def test_document_ingestion_workflow():
    # parse → chunk → embed → index → search
    pass
```

## Running Tests

### Run All Unit Tests (Fast, Default)
```bash
pytest tests/unit/
# or
pytest -m unit
```

### Run Integration Tests (Requires Services)
```bash
# Start services first
docker-compose up -d

# Run tests
pytest -m integration
```

### Run E2E Tests
```bash
pytest -m e2e
```

### Run Tests for Specific Layer
```bash
# Core layer only
pytest tests/unit/core/

# Domain layer only
pytest tests/unit/domain/

# Infrastructure tests
pytest tests/integration/infra/
```

### Run with Coverage
```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html
```

### Run Specific Test File
```bash
pytest tests/unit/core/chunking/test_types.py -v
```

### Run Tests Matching Pattern
```bash
pytest -k "test_chunk" -v
```

## Fixtures

### Database Fixtures (conftest.py)

- `test_db_engine`: In-memory SQLite for tests
- `db_session`: Auto-rollback session for isolation
- Sample data: `sample_text`, `sample_chunks`, `sample_embedding`

**Usage:**
```python
@pytest.mark.asyncio
async def test_create_document(db_session):
    doc = await DocumentService.create(db_session, data)
    assert doc.id is not None
```

### Mock Fixtures (tests/mocks/)

- `MockEmbeddingClient`: Returns deterministic embeddings
- `MockLLMClient`: Returns canned responses
- `MockVectorStore`: In-memory vector store
- `MockSearchStrategy`: Controlled search results

**Usage:**
```python
def test_rag_pipeline():
    mock_llm = MockLLMClient(canned_response="Answer")
    mock_searcher = MockSearchStrategy(results=[...])
    pipeline = RagPipeline(...)
    response = pipeline.run("question")
    assert response.answer == "Answer"
```

## Writing New Tests

### 1. Unit Test Template
```python
"""Tests for MyComponent."""

import pytest
from src.core.mymodule import MyComponent
from tests.mocks import MockDependency

class TestMyComponent:
    """Test MyComponent functionality."""
    
    @pytest.fixture
    def component(self):
        """Create component instance."""
        return MyComponent(dep=MockDependency())
    
    def test_basic_functionality(self, component):
        """Test that component works."""
        result = component.do_something()
        assert result == expected_value
```

### 2. Integration Test Template
```python
"""Integration tests for MyService."""

import pytest
from src.infra.myservice import MyService

@pytest.mark.integration
class TestMyServiceIntegration:
    """Test MyService with real dependencies."""
    
    @pytest.fixture(scope="class")
    def service(self):
        """Create service instance."""
        return MyService(real_config)
    
    def test_service_operation(self, service):
        """Test real service operation."""
        result = service.perform_action()
        assert result.success
```

### 3. Async Test Template
```python
import pytest_asyncio

@pytest.mark.asyncio
class TestAsyncService:
    """Test async operations."""
    
    @pytest_asyncio.fixture
    async def resource(self):
        """Setup async resource."""
        r = await create_resource()
        yield r
        await r.cleanup()
    
    async def test_async_operation(self, resource):
        """Test async function."""
        result = await resource.fetch_data()
        assert result is not None
```

## Best Practices

### ✅ DO

1. **Use descriptive test names**
   ```python
   def test_document_service_creates_document_with_valid_data():
   ```

2. **Follow AAA pattern** (Arrange, Act, Assert)
   ```python
   def test_example():
       # Arrange
       data = {"key": "value"}
       
       # Act
       result = process(data)
       
       # Assert
       assert result == expected
   ```

3. **Use fixtures for setup/teardown**
4. **Mock external dependencies in unit tests**
5. **Test edge cases and error conditions**
6. **Keep tests independent** (no shared state)

### ❌ DON'T

1. Don't test implementation details
2. Don't use real services in unit tests
3. Don't share state between tests
4. Don't write tests that depend on execution order
5. Don't skip cleanup (use fixtures with yield)

## Coverage Goals

| Layer      | Target Coverage |
|------------|----------------|
| `core/`    | 80%+           |
| `domain/`  | 75%+           |
| `infra/`   | 60%+           |
| `apps/`    | 70%+           |

## CI/CD Integration

In CI pipeline:

```yaml
# Run fast tests on every commit
- pytest -m unit --cov=src --cov-fail-under=70

# Run integration tests on merge requests
- docker-compose up -d
- pytest -m integration

# Run E2E tests nightly
- pytest -m e2e
```

## Troubleshooting

### Tests Can't Import src Module
```bash
# Install in editable mode
pip install -e .
```

### Async Tests Not Running
```bash
# Install pytest-asyncio
pip install pytest-asyncio
```

### Milvus Tests Failing
```bash
# Check Milvus is running
docker-compose ps
docker-compose logs milvus

# Check connection
export MILVUS_URI=http://localhost:19530
pytest tests/integration/infra/test_milvus_service.py -v
```

### Database Tests Failing
```bash
# Tests use in-memory SQLite by default
# Check SQLAlchemy models are imported in conftest.py
```

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Clean Architecture Testing](https://blog.cleancoder.com/uncle-bob/2017/03/03/TDD-Harms-Architecture.html)
