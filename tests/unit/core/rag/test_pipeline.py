"""Tests for RAG pipeline."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.core.rag.pipeline import RagPipeline
from src.core.rag.assembler import ContextAssembler
from src.core.rag.rewriter import QueryRewriter
from tests.mocks import MockSearchStrategy, MockLLMClient, MockReranker


class TestRagPipeline:
    """Test RAG pipeline orchestration."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM client."""
        return MockLLMClient(canned_response="This is the answer.")
    
    @pytest.fixture
    def mock_search_results(self):
        """Mock search results."""
        return [
            {"text": "Context 1 about AI", "score": 0.9, "id": "1"},
            {"text": "Context 2 about ML", "score": 0.8, "id": "2"},
            {"text": "Context 3 about data", "score": 0.7, "id": "3"},
        ]
    
    @pytest.fixture
    def mock_searcher(self, mock_search_results):
        """Create mock search strategy."""
        return MockSearchStrategy(results=mock_search_results)
    
    @pytest.fixture
    def mock_reranker(self):
        """Create mock reranker."""
        return MockReranker()
    
    @pytest.fixture
    def mock_rewriter(self, mock_llm):
        """Create query rewriter."""
        return QueryRewriter(mock_llm)
    
    @pytest.fixture
    def mock_assembler(self):
        """Create context assembler."""
        return ContextAssembler(max_tokens=2000)
    
    @pytest.fixture
    def rag_pipeline(
        self,
        mock_searcher,
        mock_rewriter,
        mock_reranker,
        mock_assembler,
        mock_llm
    ):
        """Create RAG pipeline instance."""
        return RagPipeline(
            vector_searcher=mock_searcher,
            rewriter=mock_rewriter,
            reranker=mock_reranker,
            assembler=mock_assembler,
            generator_llm=mock_llm
        )
    
    def test_pipeline_initialization(self, rag_pipeline):
        """Test pipeline initializes with all components."""
        assert rag_pipeline.vector_searcher is not None
        assert rag_pipeline.rewriter is not None
        assert rag_pipeline.reranker is not None
        assert rag_pipeline.assembler is not None
        assert rag_pipeline.generator_llm is not None
    
    def test_pipeline_execution(self, rag_pipeline, mock_searcher, mock_llm):
        """Test full pipeline execution."""
        response = rag_pipeline.run("What is AI?", top_k=3)
        
        # Check response structure
        assert hasattr(response, 'answer')
        assert hasattr(response, 'chunks')
        
        # Verify answer was generated
        assert response.answer == "This is the answer."
        
        # Verify search was called
        assert mock_searcher.call_count > 0
        assert mock_llm.call_count > 0
    
    def test_pipeline_with_metadata_hint(self, rag_pipeline):
        """Test pipeline with metadata filtering hint."""
        response = rag_pipeline.run(
            "What is AI?",
            metadata_hint={"source": "academic"},
            top_k=5
        )
        
        assert response is not None
        assert hasattr(response, 'answer')
    
    def test_pipeline_retrieves_chunks(self, rag_pipeline, mock_search_results):
        """Test that pipeline retrieves and returns chunks."""
        response = rag_pipeline.run("test question", top_k=3)
        
        # Should have retrieved chunks
        assert response.chunks is not None
        assert len(response.chunks) > 0
    
    def test_pipeline_reranks_results(self, rag_pipeline, mock_reranker):
        """Test that reranker is called."""
        rag_pipeline.run("test question", top_k=3)
        
        # Reranker should be invoked
        assert mock_reranker.call_count > 0
    
    def test_pipeline_query_rewriting(self, rag_pipeline, mock_llm):
        """Test query rewriting step."""
        original_call_count = mock_llm.call_count
        
        rag_pipeline.run("What is machine learning?", top_k=3)
        
        # LLM should be called for rewriting and generation
        assert mock_llm.call_count > original_call_count
    
    def test_pipeline_handles_no_results(self, mock_llm):
        """Test pipeline behavior when no search results."""
        empty_searcher = MockSearchStrategy(results=[])
        rewriter = QueryRewriter(mock_llm)
        reranker = MockReranker()
        assembler = ContextAssembler()
        
        pipeline = RagPipeline(
            vector_searcher=empty_searcher,
            rewriter=rewriter,
            reranker=reranker,
            assembler=assembler,
            generator_llm=mock_llm
        )
        
        response = pipeline.run("question", top_k=5)
        
        # Should still return a response (may indicate no context)
        assert response is not None
