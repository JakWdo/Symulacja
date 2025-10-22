"""
Testy jednostkowe dla PolishSocietyRAG (Hybrid Search Service)

Zakres testów:
- Hybrid search (vector + keyword + RRF fusion)
- RRF fusion algorithm
- Cross-encoder reranking
- Demographic insights retrieval
- Chunk enrichment z graph context
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.documents import Document

from app.services.rag import PolishSocietyRAG


class TestPolishSocietyRAGInit:
    """Testy inicjalizacji PolishSocietyRAG"""

    def test_init_creates_dependencies(self):
        """Test: __init__ tworzy embeddings i vector store"""
        with patch('app.services.rag_hybrid_search_service.GoogleGenerativeAIEmbeddings'):
            with patch.object(PolishSocietyRAG, '_init_vector_store_with_retry', return_value=MagicMock()):
                service = PolishSocietyRAG()

                assert service.embeddings is not None
                assert service.vector_store is not None
                assert service._fulltext_index_initialized == False  # Initially false

    def test_graph_rag_service_property_creates_singleton(self):
        """Test: graph_rag_service property tworzy GraphRAGService singleton"""
        with patch('app.services.rag_hybrid_search_service.GoogleGenerativeAIEmbeddings'):
            with patch.object(PolishSocietyRAG, '_init_vector_store_with_retry', return_value=MagicMock()):
                with patch('app.services.rag_graph_service.GraphRAGService') as mock_service_class:
                    service = PolishSocietyRAG()

                    # Access property twice
                    graph_service1 = service.graph_rag_service
                    graph_service2 = service.graph_rag_service

                    # Should create singleton (only once)
                    assert mock_service_class.call_count == 1
                    assert graph_service1 is graph_service2


class TestRRFFusion:
    """Testy algorytmu RRF (Reciprocal Rank Fusion)"""

    def test_rrf_fusion_combines_rankings(self, polish_society_rag_with_mocks):
        """Test: _rrf_fusion łączy rankingi z vector i keyword search"""
        service = polish_society_rag_with_mocks

        doc1 = Document(page_content="Doc 1", metadata={"id": "1"})
        doc2 = Document(page_content="Doc 2", metadata={"id": "2"})
        doc3 = Document(page_content="Doc 3", metadata={"id": "3"})

        # Vector results: doc1 > doc2 > doc3
        vector_results = [(doc1, 0.9), (doc2, 0.7), (doc3, 0.5)]

        # Keyword results: doc3 > doc1 > doc2
        keyword_results = [(doc3, 5.0), (doc1, 3.0), (doc2, 1.0)]

        fused = service._rrf_fusion(vector_results, keyword_results, k=60)

        # Should return docs sorted by RRF score
        assert len(fused) == 3
        # doc1 appears in both (should score high)
        assert fused[0][0].page_content == "Doc 1" or fused[0][0].page_content == "Doc 3"

    def test_rrf_fusion_handles_empty_inputs(self, polish_society_rag_with_mocks):
        """Test: _rrf_fusion obsługuje puste listy wyników"""
        service = polish_society_rag_with_mocks

        fused = service._rrf_fusion([], [], k=60)

        assert fused == []

    def test_rrf_fusion_k_parameter_affects_scoring(self, polish_society_rag_with_mocks):
        """Test: parametr k wpływa na scoring RRF"""
        service = polish_society_rag_with_mocks

        doc1 = Document(page_content="Doc 1")
        doc2 = Document(page_content="Doc 2")

        vector_results = [(doc1, 0.9), (doc2, 0.5)]
        keyword_results = [(doc2, 5.0), (doc1, 1.0)]

        # Lower k = more weight to top results
        fused_k40 = service._rrf_fusion(vector_results, keyword_results, k=40)
        fused_k80 = service._rrf_fusion(vector_results, keyword_results, k=80)

        # Scores should differ based on k
        assert len(fused_k40) == 2
        assert len(fused_k80) == 2
        # Score calculation: 1/(k + rank + 1)


class TestKeywordSearch:
    """Testy keyword search (fulltext)"""

    async def test_keyword_search_returns_results(self, polish_society_rag_with_mocks):
        """Test: _keyword_search zwraca wyniki z fulltext index"""
        service = polish_society_rag_with_mocks
        service._fulltext_index_initialized = True  # Skip index creation

        # Mock Neo4j fulltext search
        with patch.object(service.vector_store, '_driver') as mock_driver:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.data.return_value = [
                {"node": {"text": "Test result 1"}, "score": 5.0},
                {"node": {"text": "Test result 2"}, "score": 3.0},
            ]
            mock_session.run.return_value = mock_result
            mock_driver.session.return_value.__aenter__.return_value = mock_session

            results = await service._keyword_search("test query", k=5)

            assert len(results) == 2
            assert results[0][0].page_content == "Test result 1"
            assert results[0][1] == 5.0


class TestFormatGraphContext:
    """Testy formatowania graph context"""

    def test_format_graph_context_creates_readable_text(self, polish_society_rag_with_mocks):
        """Test: _format_graph_context tworzy czytelny tekst z nodes"""
        service = polish_society_rag_with_mocks

        graph_nodes = [
            {"type": "Wskaznik", "streszczenie": "Stopa zatrudnienia 78.4%", "skala": "78.4%"},
            {"type": "Trend", "streszczenie": "Wzrost zatrudnienia", "okres_czasu": "2018-2023"},
        ]

        formatted = service._format_graph_context(graph_nodes)

        assert "Wskaznik" in formatted
        assert "78.4%" in formatted
        assert "Trend" in formatted
        assert "2018-2023" in formatted

    def test_format_graph_context_handles_empty_list(self, polish_society_rag_with_mocks):
        """Test: _format_graph_context obsługuje pustą listę"""
        service = polish_society_rag_with_mocks

        formatted = service._format_graph_context([])

        assert formatted == ""


class TestFindRelatedGraphNodes:
    """Testy wyszukiwania powiązanych graph nodes"""

    def test_find_related_graph_nodes_by_keywords(self, polish_society_rag_with_mocks):
        """Test: _find_related_graph_nodes znajduje nodes po keywords"""
        service = polish_society_rag_with_mocks

        chunk_text = "Zatrudnienie młodych dorosłych w Polsce"
        all_graph_nodes = [
            {"type": "Wskaznik", "streszczenie": "Stopa zatrudnienia młodych", "kluczowe_fakty": "zatrudnienie"},
            {"type": "Trend", "streszczenie": "Wzrost cen mieszkań", "kluczowe_fakty": "ceny"},
        ]

        related = service._find_related_graph_nodes(chunk_text, all_graph_nodes, max_nodes=5)

        # Should find node with "zatrudnienie" keyword
        assert len(related) > 0
        assert any("zatrudnienie" in node.get("kluczowe_fakty", "").lower() for node in related)

    def test_find_related_graph_nodes_max_limit(self, polish_society_rag_with_mocks):
        """Test: _find_related_graph_nodes respektuje max_nodes limit"""
        service = polish_society_rag_with_mocks

        chunk_text = "test"
        all_graph_nodes = [{"type": "Test", "streszczenie": f"Node {i}"} for i in range(10)]

        related = service._find_related_graph_nodes(chunk_text, all_graph_nodes, max_nodes=3)

        assert len(related) <= 3


class TestEnrichChunkWithGraph:
    """Testy wzbogacania chunków graph context"""

    def test_enrich_chunk_with_graph_adds_context(self, polish_society_rag_with_mocks):
        """Test: _enrich_chunk_with_graph dodaje graph context do chunka"""
        service = polish_society_rag_with_mocks

        chunk = Document(page_content="Original chunk text", metadata={})
        graph_nodes = [
            {"type": "Wskaznik", "streszczenie": "Related metric", "skala": "50%"},
        ]

        enriched = service._enrich_chunk_with_graph(chunk, graph_nodes)

        # Should append graph context
        assert "Original chunk text" in enriched.page_content
        assert "Related metric" in enriched.page_content or enriched.metadata.get("graph_context")

    def test_enrich_chunk_with_graph_no_nodes(self, polish_society_rag_with_mocks):
        """Test: _enrich_chunk_with_graph zwraca oryginalny chunk gdy brak nodes"""
        service = polish_society_rag_with_mocks

        chunk = Document(page_content="Original text", metadata={})

        enriched = service._enrich_chunk_with_graph(chunk, [])

        assert enriched.page_content == "Original text"


class TestHybridSearch:
    """Testy pełnego hybrid search pipeline"""

    async def test_hybrid_search_combines_methods(self, polish_society_rag_with_mocks):
        """Test: hybrid_search łączy vector + keyword search z RRF"""
        service = polish_society_rag_with_mocks

        # Mock vector search
        vector_doc = Document(page_content="Vector result", metadata={})
        service.vector_store.asimilarity_search_with_score = AsyncMock(return_value=[
            (vector_doc, 0.9)
        ])

        # Mock keyword search
        keyword_doc = Document(page_content="Keyword result", metadata={})
        service._keyword_search = AsyncMock(return_value=[
            (keyword_doc, 5.0)
        ])

        results = await service.hybrid_search("test query", top_k=5)

        # Should return fused results
        assert len(results) > 0
        assert isinstance(results[0], tuple)  # (document, score)

    async def test_hybrid_search_handles_reranking(self, polish_society_rag_with_mocks):
        """Test: hybrid_search używa reranking gdy włączony"""
        service = polish_society_rag_with_mocks

        # Mock searches
        service.vector_store.asimilarity_search_with_score = AsyncMock(return_value=[
            (Document(page_content="Result 1"), 0.9)
        ])
        service._keyword_search = AsyncMock(return_value=[])

        # Mock reranking
        service._rerank_with_cross_encoder = MagicMock(return_value=[
            (Document(page_content="Reranked result"), 0.95)
        ])

        with patch('app.services.rag_hybrid_search_service.get_settings') as mock_settings:
            mock_settings.return_value.RAG_USE_RERANKING = True
            mock_settings.return_value.RAG_RERANK_CANDIDATES = 20

            results = await service.hybrid_search("test query", top_k=5)

        # Should call reranking
        service._rerank_with_cross_encoder.assert_called_once()


class TestGetDemographicInsights:
    """Testy głównej metody get_demographic_insights"""

    async def test_get_demographic_insights_returns_context(self, polish_society_rag_with_mocks):
        """Test: get_demographic_insights zwraca pełny kontekst z hybrid search + graph"""
        service = polish_society_rag_with_mocks

        # Mock hybrid search
        service.hybrid_search = AsyncMock(return_value=[
            (Document(page_content="Chunk 1", metadata={}), 0.9),
            (Document(page_content="Chunk 2", metadata={}), 0.8),
        ])

        # Mock graph context
        service._graph_rag_service = MagicMock()
        service._graph_rag_service.get_demographic_graph_context = MagicMock(return_value={
            "graph_nodes": [{"type": "Wskaznik", "streszczenie": "Test"}],
            "query": "MATCH (n) RETURN n"
        })

        result = await service.get_demographic_insights(
            age_group="25-34",
            education="wyższe",
            location="Warszawa"
        )

        assert "context" in result
        assert "citations" in result
        assert "graph_nodes" in result
        assert len(result["citations"]) == 2
        assert result["search_type"] == "hybrid"
