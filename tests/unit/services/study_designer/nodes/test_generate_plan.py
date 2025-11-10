"""
Unit tests dla generate_plan node - generacja kompletnego planu badania.

Testuje:
- Sukces generacji planu z markdown summary
- Ekstrakcja estimated_time i estimated_cost
- Parsowanie JSON z LLM response
- Obsługa błędów LLM
- Walidacja struktury planu

Target coverage: 90%+
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.study_designer.nodes.generate_plan import generate_plan_node
from app.services.study_designer.state_schema import ConversationState


class TestGeneratePlanNode:
    """Test suite dla generate_plan node."""

    @pytest.mark.asyncio
    async def test_generate_plan_success(self):
        """Test successful plan generation with all required fields."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {"role": "assistant", "content": "Generating plan..."},
            ],
            "current_stage": "generate_plan",
            "study_goal": "Understand checkout abandonment",
            "target_audience": {"age": "25-35", "location": "urban"},
            "research_method": "focus_group",
            "study_details": {"num_participants": 20, "num_questions": 5},
        }

        llm_response_content = """
        {
            "plan_ready": true,
            "markdown_summary": "# Plan Badania\\n\\n## Cel\\nZrozumieć porzucanie checkout\\n\\n## Metoda\\nGrupa fokusowa z 20 uczestnikami\\n\\n## Timeline\\n1. Rekrutacja (3 dni)\\n2. Dyskusja (2 dni)\\n3. Analiza (2 dni)",
            "estimated_time_seconds": 604800,
            "estimated_cost_usd": 150.00,
            "execution_steps": ["Generuj 20 person", "Przeprowadź dyskusję", "Generuj podsumowanie"],
            "assistant_message": "Oto kompletny plan badania. Czy zatwierdzasz?"
        }
        """

        # Mock LLM
        with patch("app.services.study_designer.nodes.generate_plan.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content=llm_response_content)
            mock_build.return_value = mock_llm

            # Act
            result = await generate_plan_node(state)

            # Assert
            assert result["generated_plan"] is not None
            plan = result["generated_plan"]
            assert "markdown_summary" in plan
            assert "Plan Badania" in plan["markdown_summary"]
            assert "estimated_time_seconds" in plan
            assert plan["estimated_time_seconds"] == 604800
            assert "estimated_cost_usd" in plan
            assert plan["estimated_cost_usd"] == 150.00
            assert result["current_stage"] == "await_approval"
            assert "Czy zatwierdzasz" in result["messages"][-1]["content"]

    @pytest.mark.asyncio
    async def test_generate_plan_minimal(self):
        """Test plan generation with minimal required fields."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "current_stage": "generate_plan",
            "study_goal": "Test",
            "target_audience": {},
            "research_method": "personas",
            "study_details": {"num_participants": 10},
        }

        llm_response_content = """
        {
            "plan_ready": true,
            "markdown_summary": "# Simple Plan\\n\\nGenerate 10 personas.",
            "estimated_time_seconds": 300,
            "estimated_cost_usd": 5.00,
            "execution_steps": ["Generate personas"],
            "assistant_message": "Plan ready!"
        }
        """

        # Mock LLM
        with patch("app.services.study_designer.nodes.generate_plan.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content=llm_response_content)
            mock_build.return_value = mock_llm

            # Act
            result = await generate_plan_node(state)

            # Assert
            assert result["generated_plan"] is not None
            assert result["generated_plan"]["estimated_time_seconds"] == 300
            assert result["current_stage"] == "await_approval"

    @pytest.mark.asyncio
    async def test_generate_plan_json_in_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "current_stage": "generate_plan",
            "study_goal": "Survey",
            "target_audience": {"age": "all"},
            "research_method": "survey",
            "study_details": {"num_questions": 5},
        }

        llm_response_content = """
        Here's your plan:

        ```json
        {
            "plan_ready": true,
            "markdown_summary": "# Survey Plan\\n\\n5 questions for all ages.",
            "estimated_time_seconds": 180,
            "estimated_cost_usd": 3.50,
            "execution_steps": ["Create survey"],
            "assistant_message": "Survey plan created!"
        }
        ```
        """

        # Mock LLM
        with patch("app.services.study_designer.nodes.generate_plan.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content=llm_response_content)
            mock_build.return_value = mock_llm

            # Act
            result = await generate_plan_node(state)

            # Assert
            assert result["generated_plan"] is not None
            assert "Survey Plan" in result["generated_plan"]["markdown_summary"]
            assert result["current_stage"] == "await_approval"

    @pytest.mark.asyncio
    async def test_generate_plan_with_complex_steps(self):
        """Test plan generation with complex execution steps."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "current_stage": "generate_plan",
            "study_goal": "Mixed research",
            "target_audience": {"type": "mixed"},
            "research_method": "mixed",
            "study_details": {"personas": 15, "focus_groups": 2},
        }

        llm_response_content = """
        {
            "plan_ready": true,
            "markdown_summary": "# Mixed Method Plan\\n\\n## Phase 1: Personas\\n15 personas\\n\\n## Phase 2: Focus Groups\\n2 discussions",
            "estimated_time_seconds": 1209600,
            "estimated_cost_usd": 250.00,
            "execution_steps": [
                "Generate 15 personas",
                "Conduct focus group 1 with 10 personas",
                "Conduct focus group 2 with 5 personas",
                "Cross-analyze results"
            ],
            "assistant_message": "Complex plan ready with personas and focus groups."
        }
        """

        # Mock LLM
        with patch("app.services.study_designer.nodes.generate_plan.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content=llm_response_content)
            mock_build.return_value = mock_llm

            # Act
            result = await generate_plan_node(state)

            # Assert
            assert result["generated_plan"] is not None
            plan = result["generated_plan"]
            assert len(plan["execution_steps"]) == 4
            assert "Mixed Method Plan" in plan["markdown_summary"]
            assert result["current_stage"] == "await_approval"

    @pytest.mark.asyncio
    async def test_generate_plan_llm_error(self):
        """Test LLM error handling."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "current_stage": "generate_plan",
            "study_goal": "Test",
            "target_audience": {},
            "research_method": "personas",
            "study_details": {},
        }

        # Mock LLM error
        with patch("app.services.study_designer.nodes.generate_plan.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.side_effect = Exception("API Error")
            mock_build.return_value = mock_llm

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await generate_plan_node(state)

            assert "API Error" in str(exc_info.value)
