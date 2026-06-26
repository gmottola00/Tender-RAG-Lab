# LLM API

Language model client interfaces and implementations.

## LLMClient Protocol

```python
from typing import Protocol, List, Dict, Any

class LLMClient(Protocol):
    """Protocol for language model clients."""
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Generate response from chat messages."""
        ...

## Usage Examples

### Basic Chat

```python
from quaerum.infra.llm import OllamaLLMClient

llm = OllamaLLMClient(model="llama3")

response = llm.chat(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is RAG?"}
    ]
)

print(response)
```

### With RAG Pipeline

```python
from quaerum.rag import RagPipeline
from quaerum.infra.llm import OllamaLLMClient

llm = OllamaLLMClient()

pipeline = RagPipeline(
    retriever=indexer,
    llm_client=llm,
)

result = await pipeline.query("What are the requirements?")
```

## Supported Models

- **llama3** (8B, fast, recommended)
- **llama3:70b** (70B, accurate, slow)
- **mistral** (7B, balanced)
- **codellama** (Code-specialized)

## Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | str | "llama3" | Ollama model name |
| `base_url` | str | "http://localhost:11434" | Server URL |
| `temperature` | float | 0.7 | Sampling temperature |
| `top_p` | float | 0.9 | Nucleus sampling |
| `max_tokens` | int | 2048 | Max generation length |

## See Also

- [Embedding API](embedding.md) - Text vectorization
- [RAG Pipeline](../../quaerum/pipeline.md) - Complete RAG flow
