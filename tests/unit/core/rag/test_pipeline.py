"""Tests for RAG pipeline — using the actual quaerium API."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from quaerium.rag import RagPipeline
from quaerium.rag.assembler import ContextAssembler
from quaerium.rag.models import RagResponse, RetrievedChunk
from quaerium.rag.rerankers import LLMReranker
from quaerium.rag.rewriter import QueryRewriter
from tests.mocks import MockLLMClient, MockSearchStrategy


def _make_mock_reranker(llm=None):
    """Create a mock LLMReranker that returns candidates unchanged."""
    mock = MagicMock(spec=LLMReranker)
    mock.rerank = MagicMock(side_effect=lambda q, candidates, top_k: candidates[:top_k])
    return mock


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
    def mock_reranker(self, mock_llm):
        """Create mock reranker (wraps LLMReranker spec)."""
        return _make_mock_reranker(mock_llm)

    @pytest.fixture
    def mock_rewriter(self, mock_llm):
        """Create query rewriter backed by mock LLM."""
        return QueryRewriter(mock_llm)

    @pytest.fixture
    def mock_assembler(self):
        """Create context assembler."""
        return ContextAssembler(max_tokens=2000)

    @pytest.fixture
    def rag_pipeline(self, mock_searcher, mock_rewriter, mock_reranker, mock_assembler, mock_llm):
        """Create RAG pipeline instance."""
        return RagPipeline(
            vector_searcher=mock_searcher,
            rewriter=mock_rewriter,
            reranker=mock_reranker,
            assembler=mock_assembler,
            generator_llm=mock_llm,
        )

    def test_pipeline_initialization(self, rag_pipeline, mock_searcher, mock_rewriter, mock_reranker, mock_assembler, mock_llm):
        """Test pipeline initializes with all components."""
        assert rag_pipeline.vector_searcher is not None
        assert rag_pipeline.rewriter is not None
        assert rag_pipeline.reranker is not None
        assert rag_pipeline.assembler is not None
        assert rag_pipeline.generator_llm is not None

    def test_pipeline_returns_rag_response(self, rag_pipeline):
        """run() returns a RagResponse instance."""
        response = rag_pipeline.run("What is AI?", top_k=3)
        assert isinstance(response, RagResponse)

    def test_pipeline_response_has_answer(self, rag_pipeline, mock_llm):
        """RagResponse.answer is the generated text from the LLM."""
        response = rag_pipeline.run("What is AI?", top_k=3)
        assert hasattr(response, "answer")
        assert response.answer == "This is the answer."

    def test_pipeline_response_has_citations(self, rag_pipeline):
        """RagResponse.citations is a list (not .chunks)."""
        response = rag_pipeline.run("What is AI?", top_k=3)
        assert hasattr(response, "citations")
        assert isinstance(response.citations, list)

    def test_pipeline_response_has_no_chunks_attribute(self, rag_pipeline):
        """RagResponse does NOT have a .chunks attribute (use .citations)."""
        response = rag_pipeline.run("What is AI?", top_k=3)
        assert not hasattr(response, "chunks"), (
            "RagResponse uses .citations, not .chunks — update your code."
        )

    def test_pipeline_citations_are_retrieved_chunks(self, rag_pipeline):
        """citations list contains RetrievedChunk instances."""
        response = rag_pipeline.run("test question", top_k=3)
        for citation in response.citations:
            assert isinstance(citation, RetrievedChunk)

    def test_pipeline_search_called(self, rag_pipeline, mock_searcher):
        """Vector searcher is invoked during pipeline execution."""
        rag_pipeline.run("test question", top_k=3)
        assert mock_searcher.call_count > 0

    def test_pipeline_llm_called(self, rag_pipeline, mock_llm):
        """LLM generate() is called at least once during execution."""
        initial_count = mock_llm.call_count
        rag_pipeline.run("What is machine learning?", top_k=3)
        assert mock_llm.call_count > initial_count

    def test_pipeline_with_metadata_hint(self, rag_pipeline):
        """Pipeline handles metadata_hint without raising."""
        response = rag_pipeline.run(
            "What is AI?",
            metadata_hint={"source": "academic"},
            top_k=5,
        )
        assert response is not None
        assert isinstance(response, RagResponse)

    def test_pipeline_handles_no_results(self, mock_llm):
        """Pipeline works gracefully when searcher returns no results."""
        empty_searcher = MockSearchStrategy(results=[])
        rewriter = QueryRewriter(mock_llm)
        reranker = _make_mock_reranker(mock_llm)
        assembler = ContextAssembler()

        pipeline = RagPipeline(
            vector_searcher=empty_searcher,
            rewriter=rewriter,
            reranker=reranker,
            assembler=assembler,
            generator_llm=mock_llm,
        )

        response = pipeline.run("question", top_k=5)
        assert response is not None
        assert isinstance(response, RagResponse)
        assert isinstance(response.citations, list)

    def test_pipeline_reranker_called(self, rag_pipeline, mock_reranker):
        """Reranker.rerank() is called during execution."""
        rag_pipeline.run("test question", top_k=3)
        mock_reranker.rerank.assert_called()

    def test_pipeline_citations_count_bounded_by_top_k(self, mock_llm):
        """Citations count should be <= top_k (assembler may trim further)."""
        many_results = [
            {"text": f"Context {i}", "score": 1.0 - i * 0.01, "id": str(i)}
            for i in range(20)
        ]
        searcher = MockSearchStrategy(results=many_results)
        rewriter = QueryRewriter(mock_llm)
        reranker = _make_mock_reranker(mock_llm)
        assembler = ContextAssembler(max_tokens=50)  # very small budget

        pipeline = RagPipeline(
            vector_searcher=searcher,
            rewriter=rewriter,
            reranker=reranker,
            assembler=assembler,
            generator_llm=mock_llm,
        )

        response = pipeline.run("question", top_k=5)
        # With very small token budget, few or no citations expected
        assert len(response.citations) <= 5
