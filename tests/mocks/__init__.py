"""Mock implementations for testing.

This module provides reusable mock classes that implement
core protocols for use in unit tests.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

from src.core.embedding.base import EmbeddingClient
from src.core.llm.base import LLMClient


class MockEmbeddingClient(EmbeddingClient):
    """Mock embedding client that returns deterministic vectors."""
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.call_count = 0
        self.last_input: Optional[str | List[str]] = None
    
    def embed(self, text: str) -> List[float]:
        """Return deterministic embedding based on text hash."""
        self.call_count += 1
        self.last_input = text
        # Create deterministic vector based on text length
        base_value = len(text) / 1000.0
        return [base_value + (i / self.dimension) for i in range(self.dimension)]
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Return batch of embeddings."""
        self.call_count += 1
        self.last_input = texts
        return [self.embed(text) for text in texts]


class MockLLMClient(LLMClient):
    """Mock LLM client that returns canned responses."""
    
    def __init__(self, canned_response: str = "This is a mock response."):
        self.canned_response = canned_response
        self.call_count = 0
        self.last_prompt: Optional[str] = None
        self.history: List[Dict[str, str]] = []
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Return canned response."""
        self.call_count += 1
        self.last_prompt = prompt
        self.history.append({"prompt": prompt, "response": self.canned_response})
        return self.canned_response
    
    def set_response(self, response: str) -> None:
        """Set the response to return."""
        self.canned_response = response


class MockVectorStore:
    """Mock vector store for testing IndexService."""
    
    def __init__(self):
        self.collections: Dict[str, Dict[str, Any]] = {}
        self.data: Dict[str, List[Dict[str, Any]]] = {}
    
    def create_collection(self, name: str, dimension: int, **kwargs) -> None:
        """Create collection."""
        self.collections[name] = {"dimension": dimension, **kwargs}
        self.data[name] = []
    
    def has_collection(self, name: str) -> bool:
        """Check if collection exists."""
        return name in self.collections
    
    def drop_collection(self, name: str) -> None:
        """Drop collection."""
        if name in self.collections:
            del self.collections[name]
            del self.data[name]
    
    def insert(self, collection_name: str, data: List[Dict[str, Any]]) -> List[str]:
        """Insert data."""
        if collection_name not in self.data:
            self.data[collection_name] = []
        
        ids = []
        for item in data:
            item_id = item.get("id", f"mock_id_{len(self.data[collection_name])}")
            self.data[collection_name].append(item)
            ids.append(item_id)
        
        return ids
    
    def search(
        self,
        collection_name: str,
        query_vectors: List[List[float]],
        limit: int = 10,
        **kwargs
    ) -> List[List[Dict[str, Any]]]:
        """Mock search - returns first N items."""
        if collection_name not in self.data:
            return [[]]
        
        results = []
        for _ in query_vectors:
            # Return first 'limit' items with mock scores
            items = self.data[collection_name][:limit]
            scored_items = [
                {**item, "score": 0.9 - (i * 0.05)}
                for i, item in enumerate(items)
            ]
            results.append(scored_items)
        
        return results
    
    def query(
        self,
        collection_name: str,
        expr: str,
        output_fields: Optional[List[str]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Mock query."""
        if collection_name not in self.data:
            return []
        
        # Simple mock: return all data
        return self.data[collection_name].copy()


class MockSearchStrategy:
    """Mock search strategy for testing RAG pipeline."""
    
    def __init__(self, results: Optional[List[Dict[str, Any]]] = None):
        self.results = results or []
        self.call_count = 0
        self.last_query: Optional[str] = None
    
    def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Return mock results."""
        self.call_count += 1
        self.last_query = query
        return self.results


class MockReranker:
    """Mock reranker for testing."""
    
    def __init__(self):
        self.call_count = 0
    
    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Return first top_k candidates."""
        self.call_count += 1
        return candidates[:top_k]


def create_mock_index_service(**kwargs) -> MagicMock:
    """Create mock IndexService with common methods."""
    mock = MagicMock()
    mock.create_collection = MagicMock()
    mock.upsert = MagicMock(return_value=["id1", "id2", "id3"])
    mock.search = MagicMock(return_value=[])
    mock.delete = MagicMock()
    
    # Apply any custom behavior
    for key, value in kwargs.items():
        setattr(mock, key, value)
    
    return mock


__all__ = [
    "MockEmbeddingClient",
    "MockLLMClient",
    "MockVectorStore",
    "MockSearchStrategy",
    "MockReranker",
    "create_mock_index_service",
]
