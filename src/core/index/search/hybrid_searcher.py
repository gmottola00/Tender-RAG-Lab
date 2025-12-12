"""Hybrid search combining vector and keyword signals with optional reranking."""

from __future__ import annotations

from typing import Dict, List, Optional

from .vector_searcher import VectorSearcher
from .keyword_searcher import KeywordSearcher
from .reranker import Reranker, IdentityReranker


class HybridSearcher:
    """Combine vector and keyword search and optionally rerank results."""

    def __init__(
        self,
        vector_searcher: VectorSearcher,
        keyword_searcher: KeywordSearcher,
        reranker: Optional[Reranker] = None,
        *,
        alpha: float = 0.7,
    ) -> None:
        """Initialize hybrid searcher.

        Args:
            vector_searcher: Semantic search component.
            keyword_searcher: Keyword search component.
            reranker: Optional reranker (cross-encoder). Defaults to IdentityReranker.
            alpha: Weight for vector score vs keyword presence (0..1).
        """
        self.vector_searcher = vector_searcher
        self.keyword_searcher = keyword_searcher
        self.reranker = reranker or IdentityReranker()
        self.alpha = alpha

    def search(self, query: str, *, top_k: int = 5) -> List[Dict[str, object]]:
        vec_results = self.vector_searcher.search(query, top_k=top_k)
        kw_results = self.keyword_searcher.search(query, top_k=top_k)

        combined = _merge_results(vec_results, kw_results, alpha=self.alpha)
        reranked = self.reranker.rerank(query, combined, top_k)
        return reranked[:top_k]


def _merge_results(
    vec_results: List[Dict[str, object]],
    kw_results: List[Dict[str, object]],
    *,
    alpha: float,
) -> List[Dict[str, object]]:
    """Merge vector and keyword results with a simple weighted score."""
    merged: Dict[str, Dict[str, object]] = {}

    def add_or_update(hit: Dict[str, object], score: float) -> None:
        hit_id = hit.get("id") or hit.get("source_chunk_id")
        if hit_id is None:
            return
        existing = merged.get(hit_id)
        if existing is None or score > existing.get("score", float("-inf")):
            updated = dict(hit)
            updated["score"] = score
            merged[hit_id] = updated

    # Normalize vector scores (assuming distance: higher means closer in Milvus IP)
    vec_scores = [h.get("score", 0.0) for h in vec_results if isinstance(h.get("score"), (int, float))]
    max_vec = max(vec_scores) if vec_scores else 1.0

    for hit in vec_results:
        raw_score = hit.get("score", 0.0)
        norm_score = float(raw_score) / max_vec if max_vec else 0.0
        add_or_update(hit, alpha * norm_score)

    for hit in kw_results:
        add_or_update(hit, (1 - alpha))

    return sorted(merged.values(), key=lambda h: h.get("score", 0.0), reverse=True)


__all__ = ["HybridSearcher"]
