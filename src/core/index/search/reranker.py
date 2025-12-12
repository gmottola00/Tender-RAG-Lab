"""Reranker interfaces for hybrid search."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class Reranker(ABC):
    """Abstract reranker interface."""

    @abstractmethod
    def rerank(self, query: str, candidates: List[Dict[str, object]], top_k: int) -> List[Dict[str, object]]:
        """Return reranked candidates."""
        raise NotImplementedError


class IdentityReranker(Reranker):
    """Pass-through reranker."""

    def rerank(self, query: str, candidates: List[Dict[str, object]], top_k: int) -> List[Dict[str, object]]:
        return candidates[:top_k]


__all__ = ["Reranker", "IdentityReranker"]
