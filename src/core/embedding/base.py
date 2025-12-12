"""Base interfaces for embedding clients."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, List, Sequence


class EmbeddingClient(ABC):
    """Abstract interface for embedding providers."""

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Embed a single text."""
        raise NotImplementedError

    def embed_batch(self, texts: Sequence[str]) -> List[List[float]]:
        """Embed a batch of texts; default iterates embed."""
        return [self.embed(t) for t in texts]

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the underlying embedding model name."""
        raise NotImplementedError

    @property
    def dimension(self) -> int | None:
        """Optionally return embedding dimension if known."""
        return None


__all__ = ["EmbeddingClient"]
