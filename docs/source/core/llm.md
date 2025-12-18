# 🧩 Core Layer: LLM

> **Language model abstractions for text generation and reasoning**

The LLM module provides vendor-agnostic interfaces for interacting with large language models.

---

## 📍 Location

**Directory:** `src/core/llm/`

**Files:**
- `base.py` - `LLMClient` Protocol
- (Implementations in `src/infra/`)

---

## 🎯 Purpose

**What LLMs do in this system:**
- Answer generation (RAG responses)
- Query rewriting (improve search quality)
- Summarization (tender summaries, lot summaries)
- Text classification (optional)

**Core abstraction:** Generate text from prompts, vendor-agnostic.

---

## 🏗️ Architecture

### Protocol Definition

```python
class LLMClient(Protocol):
    """Abstract LLM interface"""
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> str:
        """Synchronous generation"""
        ...
    
    async def agenerate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> str:
        """Async generation (preferred)"""
        ...
    
    def stream(
        self,
        prompt: str,
        temperature: float = 0.7,
        **kwargs
    ) -> Iterator[str]:
        """Streaming tokens"""
        ...
    
    @property
    def model_name(self) -> str:
        """Model identifier"""
        ...
```

**Layer:** Core (pure abstraction)

**Implementations:**
- `OllamaLLM` (in `src/infra/llm/`)
- `OpenAILLM` (in `src/infra/llm/`)

**See:** [Infra: LLM](../infra/llm.md) for implementations.

---

## 🔧 Usage Patterns

### Basic Generation

```python
from src.infra.factories import get_llm_client

llm = get_llm_client()

# Simple generation
response = await llm.agenerate(
    prompt="Summarize this tender: ...",
    temperature=0.3,  # Lower = more deterministic
    max_tokens=200
)

print(response)
```

### Streaming Responses

```python
# Stream tokens as they're generated
async for token in llm.stream(
    prompt="Answer the question: ...",
    temperature=0.7
):
    print(token, end="", flush=True)
```

**Use case:** Real-time UI updates.

---

### Temperature Control

| Temperature | Behavior | Use Case |
|-------------|----------|----------|
| 0.0 - 0.3 | Deterministic, focused | Factual QA, summaries |
| 0.4 - 0.7 | Balanced | General RAG responses |
| 0.8 - 1.0 | Creative, diverse | Brainstorming, rewrites |
| > 1.0 | Very random | Experimental |

**Example:**
```python
# Factual answer (deterministic)
answer = await llm.agenerate(prompt, temperature=0.1)

# Creative rewrite (diverse)
rewrite = await llm.agenerate(prompt, temperature=0.9)
```

---

## 🎯 Common Use Cases

### 1. RAG Answer Generation

**Goal:** Generate answer from retrieved context.

```python
# src/core/rag/pipeline.py
async def generate_answer(
    self,
    question: str,
    context: str
) -> str:
    prompt = f"""You are a helpful assistant answering questions about Italian public procurement tenders.

Context:
{context}

Question: {question}

Provide a clear, accurate answer based ONLY on the context above. If the context doesn't contain the answer, say so.

Answer:"""
    
    return await self._llm.agenerate(
        prompt=prompt,
        temperature=0.2,  # Factual, low creativity
        max_tokens=500
    )
```

---

### 2. Query Rewriting

**Goal:** Expand/improve query for better retrieval.

```python
# src/core/rag/rewriter.py
class QueryRewriter:
    def __init__(self, llm_client: LLMClient):
        self._llm = llm_client
    
    async def rewrite(self, query: str) -> str:
        prompt = f"""Rephrase this search query to be more specific and detailed, preserving the original intent:

Original: {query}

Improved query:"""
        
        return await self._llm.agenerate(
            prompt=prompt,
            temperature=0.5,
            max_tokens=100
        )
```

**Example:**
- Input: "tender requirements"
- Output: "detailed technical and administrative requirements for public procurement tender participation"

---

### 3. Summarization

**Goal:** Summarize long tender documents.

```python
# src/domain/services/tender_service.py
async def summarize_tender(self, tender: Tender) -> str:
    prompt = f"""Summarize this Italian public procurement tender in 3-4 sentences:

Title: {tender.title}
Description: {tender.description}
Budget: {tender.budget} EUR

Focus on: purpose, main requirements, budget, and deadline.

Summary:"""
    
    return await self._llm.agenerate(
        prompt=prompt,
        temperature=0.3,
        max_tokens=200
    )
```

---

## 📊 Model Selection

### Ollama Models

| Model | Params | Speed | Quality | Use Case |
|-------|--------|-------|---------|----------|
| `llama3.2` | 3B | ⚡⚡⚡ Fast | ⭐⭐ Good | Quick answers, testing |
| `llama3.1` | 8B | ⚡⚡ Medium | ⭐⭐⭐ Great | Production RAG |
| `qwen2.5` | 7B | ⚡⚡ Medium | ⭐⭐⭐ Great | Multilingual, Italian |
| `mistral` | 7B | ⚡⚡ Medium | ⭐⭐⭐ Great | General purpose |

**Installation:**
```bash
ollama pull llama3.2
ollama pull qwen2.5
```

---

### OpenAI Models

| Model | Speed | Quality | Cost | Use Case |
|-------|-------|---------|------|----------|
| `gpt-4o-mini` | ⚡⚡⚡ Fast | ⭐⭐⭐ Great | $ Cheap | Production RAG |
| `gpt-4o` | ⚡⚡ Medium | ⭐⭐⭐⭐ Excellent | $$$ Expensive | Complex reasoning |
| `gpt-4-turbo` | ⚡⚡ Medium | ⭐⭐⭐⭐ Excellent | $$ Moderate | Balanced quality/cost |

**Configuration:**
```bash
# .env
OPENAI_API_KEY=sk-proj-...
OPENAI_LLM_MODEL=gpt-4o-mini
```

---

## 🚀 Performance Best Practices

### 1. Token Limits

**Avoid hitting max tokens:**
```python
# Bad: Generate until max_tokens
response = await llm.agenerate(prompt, max_tokens=4000)

# Good: Reasonable limit
response = await llm.agenerate(prompt, max_tokens=500)
```

**Why?**
- Faster generation
- Lower cost (OpenAI)
- More focused answers

---

### 2. Prompt Engineering

**Structure prompts clearly:**

**❌ Bad (vague):**
```python
prompt = f"Answer: {question}"
```

**✅ Good (structured):**
```python
prompt = f"""You are an expert on Italian procurement tenders.

Context:
{context}

Question: {question}

Instructions:
- Base answer ONLY on context
- Be concise (2-3 sentences)
- If unsure, say "Information not available"

Answer:"""
```

**Benefits:**
- Better quality
- Consistent format
- Reduces hallucinations

---

### 3. Caching (for Repeated Prompts)

**For frequently used prompts:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
async def cached_generate(prompt: str) -> str:
    return await llm.agenerate(prompt)
```

**Use case:** Summarizing the same tenders multiple times.

---

## 🐛 Common Issues

### Issue: Slow Generation

**Symptom:** Takes >10s to generate response

**Solutions:**
1. **Reduce max_tokens:**
   ```python
   max_tokens=200  # Instead of 1000
   ```

2. **Use faster model:**
   - Ollama: `llama3.2` instead of `llama3.1`
   - OpenAI: `gpt-4o-mini` instead of `gpt-4o`

3. **Use streaming:**
   ```python
   async for token in llm.stream(prompt):
       # Display tokens as they arrive
   ```

---

### Issue: Hallucinations

**Symptom:** LLM invents facts not in context

**Solutions:**
1. **Lower temperature:**
   ```python
   temperature=0.1  # More deterministic
   ```

2. **Explicit instructions:**
   ```python
   prompt = """...
   IMPORTANT: Only use information from the context above.
   If you don't know, say "I don't have that information."
   ..."""
   ```

3. **Add citation requirement:**
   ```python
   prompt = """...
   Include citations: [1], [2], etc.
   ..."""
   ```

---

### Issue: Inconsistent Formatting

**Symptom:** Responses have random formatting

**Solutions:**
1. **Specify format in prompt:**
   ```python
   prompt = """...
   Format your answer as:
   Summary: [one sentence]
   Details: [bullet points]
   ..."""
   ```

2. **Use structured output (JSON):**
   ```python
   prompt = """...
   Respond in JSON:
   {"summary": "...", "confidence": 0.9}
   ..."""
   ```

---

## 🌍 Multi-Language Support

### Italian Tender Documents

**Recommended models:**
- **Ollama:** `qwen2.5` (excellent for non-English)
- **OpenAI:** `gpt-4o-mini` (multilingual)

**Example:**
```python
prompt = f"""Rispondi in italiano.

Contesto:
{italian_context}

Domanda: {italian_question}

Risposta:"""
```

**Tip:** Specify language in prompt for better results.

---

## 🛠️ Implementation Details

### Error Handling

**Common errors:**

1. **API rate limits (OpenAI):**
   ```python
   from openai import RateLimitError
   
   try:
       response = await llm.agenerate(prompt)
   except RateLimitError:
       # Wait and retry
       await asyncio.sleep(5)
       response = await llm.agenerate(prompt)
   ```

2. **Model not found (Ollama):**
   ```bash
   ollama pull llama3.2
   ```

3. **Timeout:**
   ```python
   response = await asyncio.wait_for(
       llm.agenerate(prompt),
       timeout=30  # 30 seconds
   )
   ```

---

### Logging

```python
# configs/logger.py logs LLM calls
logger.info(
    "LLM generation",
    extra={
        "model": llm.model_name,
        "prompt_length": len(prompt),
        "temperature": temperature,
        "max_tokens": max_tokens
    }
)
```

---

## 🚀 Adding a New LLM Provider

**Example:** Add Anthropic Claude support.

### 1. Create Implementation (Infra Layer)

```python
# src/infra/llm/anthropic_llm.py
import anthropic

class AnthropicLLM:
    """Anthropic Claude implementation"""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet"):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
    
    async def agenerate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> str:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    @property
    def model_name(self) -> str:
        return f"anthropic/{self._model}"
```

### 2. Add to Factory

```python
# src/infra/factories/llm_factory.py
from src.infra.llm.anthropic_llm import AnthropicLLM

def get_llm_client() -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "ollama")
    
    if provider == "anthropic":
        return AnthropicLLM(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet")
        )
    # ... existing providers
```

### 3. Environment Config

```bash
# .env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-sonnet
```

**See:** [Adding Integrations](../infra/adding-integrations.md)

---

## 📚 Related Documentation

- [Core Layer Overview](README.md)
- [Embedding Module](embedding.md) - Vector generation
- [RAG Pipeline](rag.md) - Uses LLM for answers
- [Infra: LLM](../infra/llm.md) - Concrete implementations

---

**[⬅️ Embedding](embedding.md) | [⬆️ Documentation Home](../README.md) | [Indexing ➡️](indexing.md)**

*Last updated: 2025-12-18*
