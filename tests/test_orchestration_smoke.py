"""
Smoke tests dla systemu orchestration.

Te testy sprawdzają czy podstawowa funkcjonalność działa poprawnie.
NIE testują quality ani szczegółów - tylko czy kod się wykonuje bez błędów.
"""

import pytest
from app.services.personas import PersonaOrchestrationService, PersonaAllocationPlan


class TestOrchestrationSmoke:
    """Smoke tests dla orchestration service."""

    def test_orchestration_service_init(self):
        """Test czy orchestration service inicjalizuje się poprawnie."""
        service = PersonaOrchestrationService()

        assert service is not None
        assert service.llm is not None
        assert service.rag_service is not None
        assert "gemini-2.5-pro" in service.llm.model  # Model może mieć prefix "models/"

    def test_orchestration_models(self):
        """Test czy używane są prawidłowe modele."""
        from app.core.config import get_settings
        settings = get_settings()

        # Orchestration powinien używać Gemini 2.5 Pro
        service = PersonaOrchestrationService()
        assert "2.5-pro" in service.llm.model.lower()

        # Individual generation używa Flash (sprawdzamy w generator)
        from app.services.personas import PersonaGeneratorLangChain
        generator = PersonaGeneratorLangChain()
        # Generator może używać różnych modeli, ale sprawdzamy że się inicjalizuje
        assert generator.llm is not None

    def test_allocation_plan_structure(self):
        """Test struktury PersonaAllocationPlan (Pydantic validation)."""
        # Test że możemy utworzyć plan z minimalnymi danymi
        plan = PersonaAllocationPlan(
            total_personas=10,
            groups=[],
            overall_context="Test context"
        )

        assert plan.total_personas == 10
        assert plan.groups == []
        assert plan.overall_context == "Test context"

    def test_graph_insight_structure(self):
        """Test struktury GraphInsight (Pydantic validation)."""
        from app.services.persona_orchestration import GraphInsight

        insight = GraphInsight(
            type="Indicator",
            summary="Test indicator",
            magnitude="78.4%",
            confidence="high",
            time_period="2022",
            source="GUS",
            why_matters="Test reasoning"
        )

        assert insight.type == "Indicator"
        assert insight.magnitude == "78.4%"
        assert insight.confidence == "high"

    def test_demographic_group_structure(self):
        """Test struktury DemographicGroup (Pydantic validation)."""
        from app.services.persona_orchestration import DemographicGroup, GraphInsight

        group = DemographicGroup(
            count=5,
            demographics={"age": "25-34", "gender": "kobieta"},
            brief="Test brief",
            graph_insights=[
                GraphInsight(
                    type="Indicator",
                    summary="Test",
                    confidence="high",
                    why_matters="Test reasoning"
                )
            ],
            allocation_reasoning="Test allocation"
        )

        assert group.count == 5
        assert len(group.graph_insights) == 1
        assert group.brief == "Test brief"

    def test_persona_orchestration_prompt_building(self):
        """Test czy prompt building działa."""
        service = PersonaOrchestrationService()

        # Test pomocniczej metody format_graph_context
        test_docs = []  # Empty docs
        formatted = service._format_graph_context(test_docs)

        assert "Brak dostępnego kontekstu" in formatted

    def test_json_extraction(self):
        """Test ekstrakcji JSON z odpowiedzi LLM."""
        service = PersonaOrchestrationService()

        # Test z markdown code blocks
        response_with_markdown = '''```json
        {"test": "value"}
        ```'''

        result = service._extract_json_from_response(response_with_markdown)
        assert result == {"test": "value"}

        # Test bez markdown
        response_plain = '{"test": "value"}'
        result = service._extract_json_from_response(response_plain)
        assert result == {"test": "value"}


class TestPersonaGeneratorOrchestration:
    """Smoke tests dla integracji orchestration z generator."""

    def test_generator_accepts_orchestration_brief(self):
        """Test czy generator akceptuje orchestration brief w advanced_options."""
        from app.services.personas import PersonaGeneratorLangChain

        generator = PersonaGeneratorLangChain()

        # Test że prompt building akceptuje orchestration_brief
        demo = {"age_group": "25-34", "gender": "kobieta"}
        psych = {"openness": 0.7}

        prompt = generator._create_persona_prompt(
            demographic=demo,
            psychological=psych,
            rag_context=None,
            target_audience_description=None,
            orchestration_brief="Test brief from orchestration"
        )

        # Sprawdź że brief jest w promptcie
        assert "Test brief from orchestration" in prompt
        assert "ORCHESTRATION BRIEF" in prompt


class TestReasoningSchemas:
    """Smoke tests dla Pydantic schemas."""

    def test_graph_insight_response_schema(self):
        """Test PersonaReasoningResponse schema."""
        from app.schemas.persona import GraphInsightResponse, PersonaReasoningResponse

        insight = GraphInsightResponse(
            type="Indicator",
            summary="Test summary",
            confidence="high",
            why_matters="Test explanation"
        )

        response = PersonaReasoningResponse(
            orchestration_brief="Test brief",
            graph_insights=[insight],
            allocation_reasoning="Test reasoning"
        )

        assert response.orchestration_brief == "Test brief"
        assert len(response.graph_insights) == 1
        assert response.graph_insights[0].type == "Indicator"


if __name__ == "__main__":
    # Możesz uruchomić te testy bezpośrednio
    pytest.main([__file__, "-v", "-s"])
