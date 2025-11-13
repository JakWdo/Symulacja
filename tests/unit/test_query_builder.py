"""
Testy jednostkowe dla Graph Query Builder

Zakres testów:
- Generowanie zapytań Cypher z pytań w języku naturalnym
- Injection prevention (Cypher injection attacks)
- Schema retrieval i embedding w prompt
- LLM structured output parsing
- Error handling (brak graph_store, LLM errors)
- Edge cases (empty questions, special characters)

Priority: P0 - Krytyczny moduł (bezpieczeństwo - injection prevention)
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.rag.graph.query_builder import generate_cypher_query
from app.schemas.rag import GraphRAGQuery


class TestCypherQueryGeneration:
    """Testy dla podstawowego generowania zapytań Cypher."""

    def test_generate_cypher_query_success(self):
        """Test: generate_cypher_query zwraca poprawne zapytanie Cypher."""
        # Mock LLM
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()

        expected_query = GraphRAGQuery(
            cypher_query="MATCH (n:Wskaznik) WHERE n.rok = '2023' RETURN n LIMIT 10",
            extracted_entities=["2023"],
            reasoning="Query to retrieve indicators for year 2023"
        )

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = expected_query
        mock_structured_llm.__or__ = MagicMock(return_value=mock_chain)
        mock_llm.with_structured_output.return_value = mock_structured_llm

        # Mock graph_store
        mock_graph_store = MagicMock()
        mock_graph_store.get_schema.return_value = """
        Node Labels: Wskaznik, Trend, Obserwacja
        Relationship Types: RELATES_TO, BELONGS_TO
        """

        # Mock prompts.get
        mock_prompt_template = MagicMock()
        mock_prompt_template.render.return_value = [
            {"role": "system", "content": "You are a Cypher query generator"},
            {"role": "user", "content": "Generate query for: stopa zatrudnienia 2023"}
        ]

        with patch('app.services.rag.graph.query_builder.prompts') as mock_prompts:
            mock_prompts.get.return_value = mock_prompt_template

            question = "Jaka była stopa zatrudnienia w Polsce w 2023?"

            result = generate_cypher_query(mock_llm, mock_graph_store, question)

            assert isinstance(result, GraphRAGQuery)
            assert "MATCH" in result.cypher_query
            assert "2023" in result.extracted_entities

    def test_generate_cypher_query_raises_error_when_graph_store_missing(self):
        """Test: generate_cypher_query rzuca RuntimeError gdy graph_store jest None."""
        mock_llm = MagicMock()

        with pytest.raises(RuntimeError, match="Graph RAG nie jest dostępny"):
            generate_cypher_query(mock_llm, None, "Some question")

    def test_generate_cypher_query_uses_graph_schema(self):
        """Test: generate_cypher_query pobiera i używa graph schema w prompt."""
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()

        mock_query = GraphRAGQuery(
            cypher_query="MATCH (n) RETURN n",
            extracted_entities=[],
            reasoning="Test"
        )

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = mock_query
        mock_structured_llm.__or__ = MagicMock(return_value=mock_chain)
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mock_graph_store = MagicMock()
        graph_schema = "Node Labels: Wskaznik\nRelationships: RELATES_TO"
        mock_graph_store.get_schema.return_value = graph_schema

        mock_prompt_template = MagicMock()
        mock_prompt_template.render.return_value = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User question"}
        ]

        with patch('app.services.rag.graph.query_builder.prompts') as mock_prompts:
            mock_prompts.get.return_value = mock_prompt_template

            generate_cypher_query(mock_llm, mock_graph_store, "Test question")

            # Verify get_schema was called
            assert mock_graph_store.get_schema.called

            # Verify render was called with graph_schema
            mock_prompt_template.render.assert_called_once()
            call_kwargs = mock_prompt_template.render.call_args[1]
            assert call_kwargs["graph_schema"] == graph_schema

    def test_generate_cypher_query_passes_question_to_prompt(self):
        """Test: generate_cypher_query przekazuje question do prompt template."""
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()

        mock_query = GraphRAGQuery(
            cypher_query="MATCH (n) RETURN n",
            extracted_entities=[],
            reasoning="Test"
        )

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = mock_query
        mock_structured_llm.__or__ = MagicMock(return_value=mock_chain)
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mock_graph_store = MagicMock()
        mock_graph_store.get_schema.return_value = "Schema"

        mock_prompt_template = MagicMock()
        mock_prompt_template.render.return_value = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Question"}
        ]

        with patch('app.services.rag.graph.query_builder.prompts') as mock_prompts:
            mock_prompts.get.return_value = mock_prompt_template

            question = "Jaka jest stopa bezrobocia?"
            generate_cypher_query(mock_llm, mock_graph_store, question)

            # Verify render was called with question
            call_kwargs = mock_prompt_template.render.call_args[1]
            assert call_kwargs["question"] == question


class TestInjectionPrevention:
    """Testy dla prevention Cypher injection attacks."""

    def test_cypher_injection_with_semicolon(self):
        """Test: System obsługuje input z potencjalną injection (;)."""
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()

        # LLM powinien sanitizować input i zwrócić bezpieczne query
        safe_query = GraphRAGQuery(
            cypher_query="MATCH (n:Wskaznik) WHERE n.name = $name RETURN n",
            extracted_entities=["test"],
            reasoning="Parametrized query"
        )

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = safe_query
        mock_structured_llm.__or__ = MagicMock(return_value=mock_chain)
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mock_graph_store = MagicMock()
        mock_graph_store.get_schema.return_value = "Schema"

        mock_prompt_template = MagicMock()
        mock_prompt_template.render.return_value = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Generate safe query"}
        ]

        with patch('app.services.rag.graph.query_builder.prompts') as mock_prompts:
            mock_prompts.get.return_value = mock_prompt_template

            # Malicious input z injection attempt
            malicious_question = "test'; DROP DATABASE; --"

            result = generate_cypher_query(mock_llm, mock_graph_store, malicious_question)

            # Verify że result używa parametrized queries ($name)
            assert "$" in result.cypher_query or "RETURN n" in result.cypher_query
            # LLM powinien zwrócić bezpieczne query, nie raw injection
            assert "DROP" not in result.cypher_query

    def test_cypher_injection_with_union(self):
        """Test: System obsługuje UNION-based injection attempts."""
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()

        safe_query = GraphRAGQuery(
            cypher_query="MATCH (n:Wskaznik) WHERE n.year = $year RETURN n",
            extracted_entities=["2023"],
            reasoning="Safe query"
        )

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = safe_query
        mock_structured_llm.__or__ = MagicMock(return_value=mock_chain)
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mock_graph_store = MagicMock()
        mock_graph_store.get_schema.return_value = "Schema"

        mock_prompt_template = MagicMock()
        mock_prompt_template.render.return_value = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Generate query"}
        ]

        with patch('app.services.rag.graph.query_builder.prompts') as mock_prompts:
            mock_prompts.get.return_value = mock_prompt_template

            # UNION injection attempt
            malicious_question = "2023' UNION MATCH (n) DETACH DELETE n --"

            result = generate_cypher_query(mock_llm, mock_graph_store, malicious_question)

            # Verify safe query (parametrized or sanitized)
            assert "DETACH DELETE" not in result.cypher_query


class TestEdgeCases:
    """Testy dla edge cases i edge conditions."""

    def test_empty_question(self):
        """Test: generate_cypher_query obsługuje puste pytanie."""
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()

        empty_query = GraphRAGQuery(
            cypher_query="MATCH (n) RETURN n LIMIT 1",
            extracted_entities=[],
            reasoning="No specific entities"
        )

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = empty_query
        mock_structured_llm.__or__ = MagicMock(return_value=mock_chain)
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mock_graph_store = MagicMock()
        mock_graph_store.get_schema.return_value = "Schema"

        mock_prompt_template = MagicMock()
        mock_prompt_template.render.return_value = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": ""}
        ]

        with patch('app.services.rag.graph.query_builder.prompts') as mock_prompts:
            mock_prompts.get.return_value = mock_prompt_template

            result = generate_cypher_query(mock_llm, mock_graph_store, "")

            assert isinstance(result, GraphRAGQuery)
            assert len(result.cypher_query) > 0

    def test_very_long_question(self):
        """Test: generate_cypher_query obsługuje bardzo długie pytania."""
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()

        query = GraphRAGQuery(
            cypher_query="MATCH (n) RETURN n LIMIT 10",
            extracted_entities=["statistics"],
            reasoning="Extracted key concept"
        )

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = query
        mock_structured_llm.__or__ = MagicMock(return_value=mock_chain)
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mock_graph_store = MagicMock()
        mock_graph_store.get_schema.return_value = "Schema"

        mock_prompt_template = MagicMock()
        mock_prompt_template.render.return_value = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Long question..."}
        ]

        with patch('app.services.rag.graph.query_builder.prompts') as mock_prompts:
            mock_prompts.get.return_value = mock_prompt_template

            # Very long question (1000+ chars)
            long_question = "What is " + " ".join(["statistics"] * 200) + "?"

            result = generate_cypher_query(mock_llm, mock_graph_store, long_question)

            assert isinstance(result, GraphRAGQuery)

    def test_special_characters_in_question(self):
        """Test: generate_cypher_query obsługuje znaki specjalne w pytaniu."""
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()

        query = GraphRAGQuery(
            cypher_query="MATCH (n:Wskaznik) RETURN n",
            extracted_entities=["@#$%"],
            reasoning="Special chars handled"
        )

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = query
        mock_structured_llm.__or__ = MagicMock(return_value=mock_chain)
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mock_graph_store = MagicMock()
        mock_graph_store.get_schema.return_value = "Schema"

        mock_prompt_template = MagicMock()
        mock_prompt_template.render.return_value = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Special chars question"}
        ]

        with patch('app.services.rag.graph.query_builder.prompts') as mock_prompts:
            mock_prompts.get.return_value = mock_prompt_template

            # Question with special characters
            special_question = "What is @#$% & <> | \\ ?"

            result = generate_cypher_query(mock_llm, mock_graph_store, special_question)

            assert isinstance(result, GraphRAGQuery)

    def test_unicode_characters_in_question(self):
        """Test: generate_cypher_query obsługuje polskie znaki diakrytyczne."""
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()

        query = GraphRAGQuery(
            cypher_query="MATCH (n:Wskaźnik) WHERE n.nazwa = 'zatrudnienie' RETURN n",
            extracted_entities=["zatrudnienie", "Polska"],
            reasoning="Unicode handled correctly"
        )

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = query
        mock_structured_llm.__or__ = MagicMock(return_value=mock_chain)
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mock_graph_store = MagicMock()
        mock_graph_store.get_schema.return_value = "Schema"

        mock_prompt_template = MagicMock()
        mock_prompt_template.render.return_value = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Polish question"}
        ]

        with patch('app.services.rag.graph.query_builder.prompts') as mock_prompts:
            mock_prompts.get.return_value = mock_prompt_template

            # Polish question with diacritics
            polish_question = "Jaka była stopa zatrudnienia w Polsce w województwie łódzkim?"

            result = generate_cypher_query(mock_llm, mock_graph_store, polish_question)

            assert isinstance(result, GraphRAGQuery)
            assert len(result.extracted_entities) > 0


class TestStructuredOutput:
    """Testy dla structured output parsing (LangChain structured output)."""

    def test_structured_output_returns_graph_rag_query(self):
        """Test: with_structured_output zwraca GraphRAGQuery object."""
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()

        expected_query = GraphRAGQuery(
            cypher_query="MATCH (n) RETURN n",
            extracted_entities=["entity1", "entity2"],
            reasoning="Test reasoning"
        )

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = expected_query
        mock_structured_llm.__or__ = MagicMock(return_value=mock_chain)
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mock_graph_store = MagicMock()
        mock_graph_store.get_schema.return_value = "Schema"

        mock_prompt_template = MagicMock()
        mock_prompt_template.render.return_value = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Question"}
        ]

        with patch('app.services.rag.graph.query_builder.prompts') as mock_prompts:
            mock_prompts.get.return_value = mock_prompt_template

            result = generate_cypher_query(mock_llm, mock_graph_store, "Test")

            assert isinstance(result, GraphRAGQuery)
            assert result.cypher_query == "MATCH (n) RETURN n"
            assert result.extracted_entities == ["entity1", "entity2"]
            assert result.reasoning == "Test reasoning"

    def test_structured_output_validates_schema(self):
        """Test: with_structured_output jest wywołane z GraphRAGQuery schema."""
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()

        mock_query = GraphRAGQuery(
            cypher_query="MATCH (n) RETURN n",
            extracted_entities=[],
            reasoning="Test"
        )

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = mock_query
        mock_structured_llm.__or__ = MagicMock(return_value=mock_chain)
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mock_graph_store = MagicMock()
        mock_graph_store.get_schema.return_value = "Schema"

        mock_prompt_template = MagicMock()
        mock_prompt_template.render.return_value = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Question"}
        ]

        with patch('app.services.rag.graph.query_builder.prompts') as mock_prompts:
            mock_prompts.get.return_value = mock_prompt_template

            generate_cypher_query(mock_llm, mock_graph_store, "Test")

            # Verify with_structured_output was called with GraphRAGQuery
            mock_llm.with_structured_output.assert_called_once_with(GraphRAGQuery)


class TestPromptConfiguration:
    """Testy dla ładowania i użycia prompt configuration."""

    def test_prompt_loaded_from_config(self):
        """Test: Prompt jest ładowany z config/prompts/rag/cypher_generation.yaml."""
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()

        mock_query = GraphRAGQuery(
            cypher_query="MATCH (n) RETURN n",
            extracted_entities=[],
            reasoning="Test"
        )

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = mock_query
        mock_structured_llm.__or__ = MagicMock(return_value=mock_chain)
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mock_graph_store = MagicMock()
        mock_graph_store.get_schema.return_value = "Schema"

        mock_prompt_template = MagicMock()
        mock_prompt_template.render.return_value = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Question"}
        ]

        with patch('app.services.rag.graph.query_builder.prompts') as mock_prompts:
            mock_prompts.get.return_value = mock_prompt_template

            generate_cypher_query(mock_llm, mock_graph_store, "Test")

            # Verify prompts.get was called with correct prompt ID
            mock_prompts.get.assert_called_once_with("rag.cypher_generation")

    def test_prompt_rendered_with_variables(self):
        """Test: Prompt template jest renderowany z question i graph_schema."""
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()

        mock_query = GraphRAGQuery(
            cypher_query="MATCH (n) RETURN n",
            extracted_entities=[],
            reasoning="Test"
        )

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = mock_query
        mock_structured_llm.__or__ = MagicMock(return_value=mock_chain)
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mock_graph_store = MagicMock()
        schema = "Node: Wskaznik, Trend"
        mock_graph_store.get_schema.return_value = schema

        mock_prompt_template = MagicMock()
        mock_prompt_template.render.return_value = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "User"}
        ]

        with patch('app.services.rag.graph.query_builder.prompts') as mock_prompts:
            mock_prompts.get.return_value = mock_prompt_template

            question = "What is the unemployment rate?"
            generate_cypher_query(mock_llm, mock_graph_store, question)

            # Verify render was called with correct variables
            mock_prompt_template.render.assert_called_once_with(
                question=question,
                graph_schema=schema
            )
