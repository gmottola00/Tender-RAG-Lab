"""Ollama embedding client."""

from __future__ import annotations

import os
from typing import Any, Dict, List

from src.core.embedding.base import EmbeddingClient

try:
    import requests
except ImportError as exc:  # pragma: no cover - optional dependency
    requests = None  # type: ignore
    _import_error = exc
else:
    _import_error = None

DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")


class OllamaEmbeddingClient(EmbeddingClient):
    """Client for Ollama's /api/embeddings endpoint."""

    def __init__(
        self,
        *,
        model: str = DEFAULT_OLLAMA_EMBED_MODEL,
        base_url: str = DEFAULT_OLLAMA_URL,
        timeout: int = 120,
    ) -> None:
        if _import_error:
            raise ImportError("requests is required for OllamaEmbeddingClient") from _import_error
        self._model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @property
    def model_name(self) -> str:
        return self._model

    def embed(self, text: str) -> List[float]:
        payload: Dict[str, Any] = {"model": self._model, "input": text}
        resp = requests.post(
            f"{self.base_url}/api/embeddings",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        vector = data.get("embedding") or data.get("vector")
        if not isinstance(vector, list):
            raise ValueError("Invalid embedding response from Ollama")
        return vector


__all__ = ["OllamaEmbeddingClient"]
