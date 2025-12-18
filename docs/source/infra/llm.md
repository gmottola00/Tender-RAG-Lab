# 🤖 Infrastructure: LLM Implementations

> **Concrete implementations of the LLMClient Protocol**

This module contains vendor-specific implementations for Large Language Model clients.

---

## 📍 Location

**Directory:** `src/infra/llm/`

**Files:**
- `ollama.py` - Ollama implementation
- `openai.py` - OpenAI implementation

---

## 🔌 Available Implementations

### Ollama LLM Client

**Location:** `src/infra/llm/ollama.py`

Local LLM via Ollama API.

```python
from src.infra.llm import OllamaLLMClient

# Initialize
client = OllamaLLMClient(
    model="phi3:mini",
    base_url="http://localhost:11434",
    timeout=120
)

# Generate
response = client.generate(
    "Explain RAG in one sentence",
    temperature=0.7,
    max_tokens=100
)
```

**Configuration:**
- `model`: Ollama model name (default: `phi3:mini`)
- `base_url`: Ollama server URL (default: `http://localhost:11434`)
- `timeout`: Request timeout in seconds (default: 120)

---

### OpenAI LLM Client

**Location:** `src/infra/llm/openai.py`

OpenAI API (GPT models).

```python
from src.infra.llm import OpenAILLMClient

# Initialize
client = OpenAILLMClient(
    model="gpt-4-turbo-preview",
    api_key="sk-...",
    base_url=None  # Optional: custom endpoint
)

# Generate
response = client.generate(
    "Summarize this tender document",
    temperature=0.3,
    max_tokens=500
)
```

**Configuration:**
- `model`: OpenAI model name (default: from `OPENAI_LLM_MODEL` env)
- `api_key`: OpenAI API key (required, from `OPENAI_API_KEY` env)
- `base_url`: Custom endpoint (optional)

---

## 🎯 Protocol Compliance

Both implementations satisfy the `LLMClient` Protocol from `src.core.llm.base`:

```python
from typing import Protocol, Any, Iterable

class LLMClient(Protocol):
    def generate(self, prompt: str, **kwargs: Any) -> str: ...
    def generate_batch(self, prompts: Iterable[str], **kwargs: Any) -> Iterable[str]: ...
    
    @property
    def model_name(self) -> str: ...
```

---

## 🔄 Dependency Injection

Use with factory pattern for swappable implementations:

```python
from src.core.llm import LLMClient
from src.infra.llm import OllamaLLMClient, OpenAILLMClient

def create_llm_client(provider: str) -> LLMClient:
    """Factory for LLM clients."""
    if provider == "ollama":
        return OllamaLLMClient()
    elif provider == "openai":
        return OpenAILLMClient()
    else:
        raise ValueError(f"Unknown provider: {provider}")

# Usage
llm = create_llm_client("ollama")  # Type: LLMClient
response = llm.generate("What is RAG?")
```

---

## 📚 See Also

- [Core LLM Documentation](../core/llm.md) - Protocol definition
- [RAG Pipeline](../core/rag.md) - LLM usage in RAG
- [Adding Integrations](adding-integrations.md) - Add new LLM providers
