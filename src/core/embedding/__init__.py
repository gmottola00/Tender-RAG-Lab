"""Embedding clients."""

from .base import EmbeddingClient
from .ollama import OllamaEmbeddingClient
from .openai_embedding import OpenAIEmbeddingClient

__all__ = ["EmbeddingClient", "OllamaEmbeddingClient", "OpenAIEmbeddingClient"]
