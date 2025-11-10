"""
Unit tests dla select_method node - wybór metody badawczej.

Testuje:
- Sukces wyboru metody (method_selected=true)
- Loop-back gdy wybór niejasny (method_selected=false)
- Różne metody: personas, focus_group, survey, mixed
- Parsowanie JSON z LLM response
- Obsługa błędów LLM

Target coverage: 90%+
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.study_designer.nodes.select_method import select_method_node
from app.services.study_designer.state_schema import ConversationState


class TestSelectMethodNode:
    """Test suite dla select_method node."""

    @pytest.mark.asyncio
    async def test_select_method_personas(self):
        """Test successful method selection - personas."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {"role": "assistant", "content": "Jaka metoda?"},
                {"role": "user", "content": "Chcę stworzyć persony użytkowników"},
            ],
            "current_stage": "select_method",
            "study_goal": "Zrozumieć użytkowników",
            "target_audience": {"age_range": "25-35"},
        }

        llm_response_content = """
        {
            "method_selected": true,
            "recommended_method": "personas",
            "rationale": "Persony są idealne do zrozumienia różnych typów użytkowników",
            "confidence": "high",
            "follow_up_question": null,
            "assistant_message": "Doskonały wybór! Persony pomogą Ci zrozumieć różne typy użytkowników."
        }
        """

        # Mock LLM
        with patch("app.services.study_designer.nodes.select_method.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content=llm_response_content)
            mock_build.return_value = mock_llm

            # Act
            result = await select_method_node(state)

            # Assert
            assert result["research_method"] == "personas"
            assert result["current_stage"] == "configure_details"
            assert "Doskonały wybór" in result["messages"][-1]["content"]

    @pytest.mark.asyncio
    async def test_select_method_focus_group(self):
        """Test successful method selection - focus group."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {"role": "assistant", "content": "Jaka metoda?"},
                {"role": "user", "content": "Chcę przeprowadzić dyskusję grupową"},
            ],
            "current_stage": "select_method",
            "study_goal": "Zbadać opinie",
            "target_audience": {"age_range": "30-40"},
        }

        llm_response_content = """
        {
            "method_selected": true,
            "recommended_method": "focus_group",
            "rationale": "Grupa fokusowa pozwoli zebrać głębokie opinie",
            "confidence": "high",
            "follow_up_question": null,
            "assistant_message": "Grupa fokusowa to świetny wybór dla tego celu."
        }
        """

        # Mock LLM
        with patch("app.services.study_designer.nodes.select_method.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content=llm_response_content)
            mock_build.return_value = mock_llm

            # Act
            result = await select_method_node(state)

            # Assert
            assert result["research_method"] == "focus_group"
            assert result["current_stage"] == "configure_details"

    @pytest.mark.asyncio
    async def test_select_method_needs_clarification(self):
        """Test loop-back when method unclear."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {"role": "assistant", "content": "Jaka metoda?"},
                {"role": "user", "content": "Nie wiem"},
            ],
            "current_stage": "select_method",
            "study_goal": "Badanie",
            "target_audience": {},
        }

        llm_response_content = """
        {
            "method_selected": false,
            "recommended_method": null,
            "rationale": null,
            "confidence": "low",
            "follow_up_question": "Czy chcesz zrozumieć typy użytkowników (persony) czy zebrać opinie (grupa fokusowa)?",
            "assistant_message": "Pomogę Ci wybrać. Czy chcesz zrozumieć typy użytkowników czy zebrać opinie?"
        }
        """

        # Mock LLM
        with patch("app.services.study_designer.nodes.select_method.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content=llm_response_content)
            mock_build.return_value = mock_llm

            # Act
            result = await select_method_node(state)

            # Assert
            assert "research_method" not in result or result.get("research_method") is None
            assert result["current_stage"] == "select_method"  # Loop-back
            assert "Pomogę" in result["messages"][-1]["content"]

    @pytest.mark.asyncio
    async def test_select_method_json_in_markdown(self):
        """Test parsing JSON wrapped in markdown."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {"role": "assistant", "content": "Method?"},
                {"role": "user", "content": "Survey"},
            ],
            "current_stage": "select_method",
            "study_goal": "Collect data",
            "target_audience": {},
        }

        llm_response_content = """
        ```json
        {
            "method_selected": true,
            "recommended_method": "survey",
            "rationale": "Survey is best for quantitative data",
            "confidence": "high",
            "follow_up_question": null,
            "assistant_message": "Survey chosen!"
        }
        ```
        """

        # Mock LLM
        with patch("app.services.study_designer.nodes.select_method.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content=llm_response_content)
            mock_build.return_value = mock_llm

            # Act
            result = await select_method_node(state)

            # Assert
            assert result["research_method"] == "survey"
            assert result["current_stage"] == "configure_details"

    @pytest.mark.asyncio
    async def test_select_method_llm_error(self):
        """Test LLM error handling."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {"role": "assistant", "content": "Q"},
                {"role": "user", "content": "A"},
            ],
            "current_stage": "select_method",
            "study_goal": "Test",
            "target_audience": {},
        }

        # Mock LLM error
        with patch("app.services.study_designer.nodes.select_method.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.side_effect = Exception("API Error")
            mock_build.return_value = mock_llm

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await select_method_node(state)

            assert "API Error" in str(exc_info.value)
