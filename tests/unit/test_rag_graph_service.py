"""
Testy jednostkowe dla GraphRAGService

Zakres testów:
- Enrich graph nodes (metadata validation)
- Cypher query generation
- Answer question (Graph RAG pipeline)
- Demographic graph context retrieval
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.services.rag import GraphRAGService


class TestGraphRAGServiceInit:
    """Testy inicjalizacji Graph RAG Service"""

    def test_init_creates_dependencies(self):
        """Test: __init__ tworzy wszystkie zależności (graph_store, embeddings, vector_store)"""
        with patch('app.services.rag.rag_graph_service.GoogleGenerativeAIEmbeddings'):
            with patch('app.services.rag.rag_graph_service.Neo4jGraph'):
                with patch('app.services.rag.rag_graph_service.Neo4jVector'):
                    service = GraphRAGService()

                    assert service.graph_store is not None
                    assert service.embeddings is not None
                    assert service.vector_store is not None


class TestEnrichGraphNodes:
    """Testy wzbogacania węzłów grafu"""

    def test_enrich_graph_nodes_adds_metadata(self):
        """Test: _enrich_graph_nodes dodaje doc_id i chunk_index do nodes"""
        with patch('app.services.rag.rag_graph_service.GoogleGenerativeAIEmbeddings'):
            with patch('app.services.rag.rag_graph_service.Neo4jGraph'):
                with patch('app.services.rag.rag_graph_service.Neo4jVector'):
                    service = GraphRAGService()

        nodes = [
            MagicMock(id="node1", type="Wskaznik", properties={}),
            MagicMock(id="node2", type="Trend", properties={}),
        ]
        metadata = {"doc_id": "test-doc-123", "chunk_index": 5}

        enriched = service._enrich_graph_nodes(nodes, metadata)

        assert len(enriched) == 2
        assert enriched[0].properties.get("doc_id") == "test-doc-123"
        assert enriched[0].properties.get("chunk_index") == 5
        assert enriched[1].properties.get("doc_id") == "test-doc-123"

    def test_enrich_graph_nodes_validates_required_properties(self):
        """Test: _enrich_graph_nodes waliduje wymagane properties (streszczenie, pewnosc)"""
        with patch('app.services.rag.rag_graph_service.GoogleGenerativeAIEmbeddings'):
            with patch('app.services.rag.rag_graph_service.Neo4jGraph'):
                with patch('app.services.rag.rag_graph_service.Neo4jVector'):
                    service = GraphRAGService()

        nodes = [
            MagicMock(id="node1", type="Wskaznik", properties={"streszczenie": "Test", "pewnosc": "wysoka"}),
            MagicMock(id="node2", type="Trend", properties={}),  # Missing required properties
        ]
        metadata = {"doc_id": "test-doc"}

        enriched = service._enrich_graph_nodes(nodes, metadata)

        # Should keep node with valid properties
        assert len(enriched) >= 1
        assert enriched[0].properties.get("streszczenie") == "Test"

    def test_enrich_graph_nodes_handles_empty_list(self):
        """Test: _enrich_graph_nodes obsługuje pustą listę nodes"""
        with patch('app.services.rag.rag_graph_service.GoogleGenerativeAIEmbeddings'):
            with patch('app.services.rag.rag_graph_service.Neo4jGraph'):
                with patch('app.services.rag.rag_graph_service.Neo4jVector'):
                    service = GraphRAGService()

        enriched = service._enrich_graph_nodes([], {"doc_id": "test"})

        assert enriched == []


class TestGenerateCypherQuery:
    """Testy generowania Cypher queries"""

    def test_generate_cypher_query_returns_valid_query(self):
        """Test: _generate_cypher_query zwraca poprawne Cypher query"""
        with patch('app.services.rag.rag_graph_service.GoogleGenerativeAIEmbeddings'):
            with patch('app.services.rag.rag_graph_service.Neo4jGraph'):
                with patch('app.services.rag.rag_graph_service.Neo4jVector'):
                    with patch('app.services.rag.rag_graph_service.ChatGoogleGenerativeAI') as mock_llm_class:
                        mock_llm = AsyncMock()
                        mock_llm.ainvoke.return_value = MagicMock(
                            content='```json\n{"cypher": "MATCH (n:Wskaznik) RETURN n LIMIT 10", "reasoning": "Test"}\n```'
                        )
                        mock_llm_class.return_value = mock_llm

                        service = GraphRAGService()

        result = service._generate_cypher_query("Jakie są największe wskaźniki?")

        assert result.cypher == "MATCH (n:Wskaznik) RETURN n LIMIT 10"
        assert result.reasoning == "Test"

    def test_generate_cypher_query_handles_json_parse_error(self):
        """Test: _generate_cypher_query obsługuje błędy parsowania JSON"""
        with patch('app.services.rag.rag_graph_service.GoogleGenerativeAIEmbeddings'):
            with patch('app.services.rag.rag_graph_service.Neo4jGraph'):
                with patch('app.services.rag.rag_graph_service.Neo4jVector'):
                    with patch('app.services.rag.rag_graph_service.ChatGoogleGenerativeAI') as mock_llm_class:
                        mock_llm = AsyncMock()
                        mock_llm.ainvoke.return_value = MagicMock(
                            content='invalid json'
                        )
                        mock_llm_class.return_value = mock_llm

                        service = GraphRAGService()

        with pytest.raises(Exception):
            service._generate_cypher_query("Test question")


class TestAnswerQuestion:
    """Testy pełnego pipeline Graph RAG"""

    async def test_answer_question_success(self):
        """Test: answer_question zwraca odpowiedź z graph context i vector context"""
        with patch('app.services.rag.rag_graph_service.GoogleGenerativeAIEmbeddings'):
            with patch('app.services.rag.rag_graph_service.Neo4jGraph') as mock_graph:
                with patch('app.services.rag.rag_graph_service.Neo4jVector') as mock_vector:
                    with patch('app.services.rag.rag_graph_service.ChatGoogleGenerativeAI') as mock_llm_class:
                        # Mock LLM for Cypher generation
                        mock_cypher_llm = AsyncMock()
                        mock_cypher_llm.ainvoke.return_value = MagicMock(
                            content='```json\n{"cypher": "MATCH (n) RETURN n LIMIT 1", "reasoning": "test"}\n```'
                        )

                        # Mock LLM for answer generation
                        mock_answer_llm = AsyncMock()
                        mock_answer_llm.ainvoke.return_value = MagicMock(
                            content="Test answer based on graph"
                        )

                        mock_llm_class.side_effect = [mock_cypher_llm, mock_answer_llm]

                        # Mock graph query
                        mock_graph_instance = MagicMock()
                        mock_graph_instance.query.return_value = [{"n": {"streszczenie": "Test node"}}]
                        mock_graph.return_value = mock_graph_instance

                        # Mock vector search
                        mock_vector_instance = MagicMock()
                        mock_vector_instance.asimilarity_search.return_value = []
                        mock_vector.from_existing_index.return_value = mock_vector_instance

                        service = GraphRAGService()

        result = await service.answer_question("Test question")

        assert "answer" in result
        assert "graph_context" in result
        assert "vector_context" in result
        assert "cypher_query" in result
        assert result["answer"] == "Test answer based on graph"


class TestGetDemographicGraphContext:
    """Testy pobierania graph context dla demografii"""

    def test_get_demographic_graph_context_builds_query(self):
        """Test: get_demographic_graph_context buduje Cypher query dla demografii"""
        with patch('app.services.rag.rag_graph_service.GoogleGenerativeAIEmbeddings'):
            with patch('app.services.rag.rag_graph_service.Neo4jGraph') as mock_graph:
                with patch('app.services.rag.rag_graph_service.Neo4jVector'):
                    mock_graph_instance = MagicMock()
                    mock_graph_instance.query.return_value = []
                    mock_graph.return_value = mock_graph_instance

                    service = GraphRAGService()

        result = service.get_demographic_graph_context(
            age_group="25-34",
            education="wyższe",
            location="Warszawa",
            gender="kobieta"
        )

        # Should call graph query
        assert mock_graph_instance.query.called

        # Result should have expected structure
        assert isinstance(result, dict)
        assert "graph_nodes" in result
        assert "query" in result

    def test_get_demographic_graph_context_handles_empty_results(self):
        """Test: get_demographic_graph_context obsługuje brak wyników z grafu"""
        with patch('app.services.rag.rag_graph_service.GoogleGenerativeAIEmbeddings'):
            with patch('app.services.rag.rag_graph_service.Neo4jGraph') as mock_graph:
                with patch('app.services.rag.rag_graph_service.Neo4jVector'):
                    mock_graph_instance = MagicMock()
                    mock_graph_instance.query.return_value = []
                    mock_graph.return_value = mock_graph_instance

                    service = GraphRAGService()

        result = service.get_demographic_graph_context(
            age_group="25-34",
            education="wyższe"
        )

        assert result["graph_nodes"] == []
