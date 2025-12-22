"""Ollama embedding client."""

from __future__ import annotations

import os
from typing import Any, Dict, List

from rag_toolkit.core.embedding import EmbeddingClient

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
        # Ollama embeddings API expects "prompt"; support "input" for backward compatibility.
        payload: Dict[str, Any] = {"model": self._model, "prompt": text}
        resp = requests.post(
            f"{self.base_url}/api/embeddings",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        # Handle different shapes: {"embedding": [...]}, {"data": [{"embedding": [...]}]}, {"embeddings": [...]}
        vector = data.get("embedding") or data.get("vector")
        if vector is None and isinstance(data.get("data"), list) and data["data"]:
            vector = data["data"][0].get("embedding")
        if vector is None and isinstance(data.get("embeddings"), list) and data["embeddings"]:
            vector = data["embeddings"][0]

        normalized = _normalize_embedding(vector)
        if normalized is None:
            raise ValueError(f"Invalid embedding response from Ollama: keys={list(data.keys())}")
        return normalized


def _normalize_embedding(raw: Any) -> List[float] | None:
    """Normalize embedding payload into a flat list of floats."""
    if raw is None:
        return None
    if isinstance(raw, list):
        if raw and isinstance(raw[0], list):
            raw = raw[0]
        else:
            # allow empty list or flat list
            pass
    if isinstance(raw, (list, tuple)):
        try:
            return [float(x) for x in raw]
        except (TypeError, ValueError):
            return None
    return None


__all__ = ["OllamaEmbeddingClient"]
