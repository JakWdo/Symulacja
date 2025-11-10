"""
Unit tests dla define_audience node - ekstrakcja grupy docelowej z konwersacji.

Testuje:
- Sukces ekstrakcji demografii (audience_defined=true)
- Loop-back gdy demografii niejasna (audience_defined=false)
- Parsowanie JSON z LLM response
- Obsługa błędów LLM
- Brak wiadomości od użytkownika

Target coverage: 90%+
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.study_designer.nodes.define_audience import define_audience_node
from app.services.study_designer.state_schema import ConversationState


class TestDefineAudienceNode:
    """Test suite dla define_audience node."""

    @pytest.mark.asyncio
    async def test_define_audience_success(self):
        """Test successful audience extraction z clear demographics."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {"role": "assistant", "content": "Jaka jest grupa docelowa?"},
                {"role": "user", "content": "Kobiety 25-35 lat, mieszkające w dużych miastach, zainteresowane modą"},
            ],
            "current_stage": "define_audience",
            "study_goal": "Zbadać preferencje zakupowe",
        }

        llm_response_content = """
        {
            "audience_defined": true,
            "target_demographics": {
                "age_range": "25-35",
                "gender": "female",
                "location": "duże miasta",
                "interests": ["moda", "zakupy"]
            },
            "confidence": "high",
            "follow_up_question": null,
            "assistant_message": "Rozumiem! Grupa docelowa to kobiety 25-35 lat z dużych miast zainteresowane modą."
        }
        """

        # Mock LLM
        with patch("app.services.study_designer.nodes.define_audience.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content=llm_response_content)
            mock_build.return_value = mock_llm

            # Act
            result = await define_audience_node(state)

            # Assert
            assert result["target_audience"] is not None
            assert "25-35" in str(result["target_audience"])
            assert result["current_stage"] == "select_method"
            assert len(result["messages"]) == 3  # Existing + new assistant
            assert result["messages"][-1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_define_audience_needs_clarification(self):
        """Test loop-back when audience is unclear."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {"role": "assistant", "content": "Jaka jest grupa docelowa?"},
                {"role": "user", "content": "Różni ludzie"},
            ],
            "current_stage": "define_audience",
            "study_goal": "Badanie użyteczności",
        }

        llm_response_content = """
        {
            "audience_defined": false,
            "target_demographics": null,
            "confidence": "low",
            "follow_up_question": "Czy możesz podać konkretny wiek, płeć lub zainteresowania?",
            "assistant_message": "Potrzebuję więcej szczegółów. Czy możesz podać konkretny wiek, płeć lub zainteresowania?"
        }
        """

        # Mock LLM
        with patch("app.services.study_designer.nodes.define_audience.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content=llm_response_content)
            mock_build.return_value = mock_llm

            # Act
            result = await define_audience_node(state)

            # Assert
            assert "target_audience" not in result or result.get("target_audience") is None
            assert result["current_stage"] == "define_audience"  # Loop-back
            assert "szczegółów" in result["messages"][-1]["content"]

    @pytest.mark.asyncio
    async def test_define_audience_json_in_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {"role": "assistant", "content": "Opisz grupę docelową"},
                {"role": "user", "content": "Młodzi profesjonaliści 28-35"},
            ],
            "current_stage": "define_audience",
            "study_goal": "Test",
        }

        llm_response_content = """
        ```json
        {
            "audience_defined": true,
            "target_demographics": {"age_range": "28-35", "occupation": "professionals"},
            "confidence": "high",
            "follow_up_question": null,
            "assistant_message": "Zrozumiałem - młodzi profesjonaliści 28-35 lat."
        }
        ```
        """

        # Mock LLM
        with patch("app.services.study_designer.nodes.define_audience.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content=llm_response_content)
            mock_build.return_value = mock_llm

            # Act
            result = await define_audience_node(state)

            # Assert
            assert result["target_audience"] is not None
            assert result["current_stage"] == "select_method"

    @pytest.mark.asyncio
    async def test_define_audience_no_user_message(self):
        """Test graceful handling when no user message exists."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [{"role": "assistant", "content": "Question"}],
            "current_stage": "define_audience",
            "study_goal": "Test",
        }

        # Act
        result = await define_audience_node(state)

        # Assert
        assert result["current_stage"] == "define_audience"
        assert "target_audience" not in result or result.get("target_audience") is None

    @pytest.mark.asyncio
    async def test_define_audience_llm_error_handling(self):
        """Test error handling when LLM fails."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {"role": "assistant", "content": "Question"},
                {"role": "user", "content": "Answer"},
            ],
            "current_stage": "define_audience",
            "study_goal": "Test",
        }

        # Mock LLM to raise exception
        with patch("app.services.study_designer.nodes.define_audience.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.side_effect = Exception("LLM API Error")
            mock_build.return_value = mock_llm

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await define_audience_node(state)

            assert "LLM API Error" in str(exc_info.value)
