"""
Unit tests dla configure_details node - konfiguracja szczegółów badania.

Testuje:
- Sukces ekstrakcji szczegółów (details_complete=true)
- Loop-back gdy szczegóły niekompletne (details_complete=false)
- Parsowanie liczby uczestników, pytań, etc.
- Parsowanie JSON z LLM response
- Obsługa błędów LLM

Target coverage: 90%+
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.study_designer.nodes.configure_details import configure_details_node
from app.services.study_designer.state_schema import ConversationState


class TestConfigureDetailsNode:
    """Test suite dla configure_details node."""

    @pytest.mark.asyncio
    async def test_configure_details_success(self):
        """Test successful details extraction."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {"role": "assistant", "content": "Ile uczestników?"},
                {"role": "user", "content": "20 uczestników, 5 pytań badawczych"},
            ],
            "current_stage": "configure_details",
            "study_goal": "Test goal",
            "target_audience": {"age": "25-35"},
            "research_method": "focus_group",
        }

        llm_response_content = """
        {
            "details_complete": true,
            "num_participants": 20,
            "num_questions": 5,
            "additional_requirements": null,
            "confidence": "high",
            "follow_up_question": null,
            "assistant_message": "Świetnie! 20 uczestników i 5 pytań badawczych."
        }
        """

        # Mock LLM
        with patch("app.services.study_designer.nodes.configure_details.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content=llm_response_content)
            mock_build.return_value = mock_llm

            # Act
            result = await configure_details_node(state)

            # Assert
            assert result["study_details"] is not None
            assert "20" in str(result["study_details"]) or 20 in str(result["study_details"])
            assert result["current_stage"] == "generate_plan"
            assert "Świetnie" in result["messages"][-1]["content"]

    @pytest.mark.asyncio
    async def test_configure_details_needs_clarification(self):
        """Test loop-back when details incomplete."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {"role": "assistant", "content": "Szczegóły?"},
                {"role": "user", "content": "Nie wiem ile"},
            ],
            "current_stage": "configure_details",
            "study_goal": "Goal",
            "target_audience": {},
            "research_method": "personas",
        }

        llm_response_content = """
        {
            "details_complete": false,
            "num_participants": null,
            "num_questions": null,
            "additional_requirements": null,
            "confidence": "low",
            "follow_up_question": "Ile person chcesz wygenerować? Standardowo 10-20.",
            "assistant_message": "Ile person chcesz wygenerować? Standardowo 10-20."
        }
        """

        # Mock LLM
        with patch("app.services.study_designer.nodes.configure_details.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content=llm_response_content)
            mock_build.return_value = mock_llm

            # Act
            result = await configure_details_node(state)

            # Assert
            assert "study_details" not in result or result.get("study_details") is None
            assert result["current_stage"] == "configure_details"  # Loop-back
            assert "person" in result["messages"][-1]["content"].lower()

    @pytest.mark.asyncio
    async def test_configure_details_with_requirements(self):
        """Test extracting additional requirements."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {"role": "assistant", "content": "Details?"},
                {"role": "user", "content": "15 personas, focus on mobile users"},
            ],
            "current_stage": "configure_details",
            "study_goal": "Mobile UX",
            "target_audience": {"device": "mobile"},
            "research_method": "personas",
        }

        llm_response_content = """
        {
            "details_complete": true,
            "num_participants": 15,
            "num_questions": null,
            "additional_requirements": "Focus on mobile users",
            "confidence": "high",
            "follow_up_question": null,
            "assistant_message": "15 personas focused on mobile users."
        }
        """

        # Mock LLM
        with patch("app.services.study_designer.nodes.configure_details.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content=llm_response_content)
            mock_build.return_value = mock_llm

            # Act
            result = await configure_details_node(state)

            # Assert
            assert result["study_details"] is not None
            assert result["current_stage"] == "generate_plan"

    @pytest.mark.asyncio
    async def test_configure_details_json_in_markdown(self):
        """Test parsing JSON wrapped in markdown."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {"role": "assistant", "content": "Details?"},
                {"role": "user", "content": "10 participants"},
            ],
            "current_stage": "configure_details",
            "study_goal": "Test",
            "target_audience": {},
            "research_method": "survey",
        }

        llm_response_content = """
        ```json
        {
            "details_complete": true,
            "num_participants": 10,
            "num_questions": 3,
            "additional_requirements": null,
            "confidence": "high",
            "follow_up_question": null,
            "assistant_message": "10 participants, 3 questions."
        }
        ```
        """

        # Mock LLM
        with patch("app.services.study_designer.nodes.configure_details.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content=llm_response_content)
            mock_build.return_value = mock_llm

            # Act
            result = await configure_details_node(state)

            # Assert
            assert result["study_details"] is not None
            assert result["current_stage"] == "generate_plan"

    @pytest.mark.asyncio
    async def test_configure_details_llm_error(self):
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
            "current_stage": "configure_details",
            "study_goal": "Test",
            "target_audience": {},
            "research_method": "personas",
        }

        # Mock LLM error
        with patch("app.services.study_designer.nodes.configure_details.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.side_effect = Exception("API Error")
            mock_build.return_value = mock_llm

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await configure_details_node(state)

            assert "API Error" in str(exc_info.value)
