"""
Unit tests dla gather_goal node - ekstrakcja celu badania z konwersacji.

Testuje:
- Sukces ekstrakcji celu (goal_extracted=true)
- Loop-back gdy cel niejasny (goal_extracted=false)
- Parsowanie JSON z LLM response
- Obsługa błędów LLM
- Brak wiadomości od użytkownika

Target coverage: 90%+
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.study_designer.nodes.gather_goal import gather_goal_node
from app.services.study_designer.state_schema import ConversationState


class TestGatherGoalNode:
    """Test suite dla gather_goal node."""

    @pytest.mark.asyncio
    async def test_gather_goal_success(self):
        """Test successful goal extraction z clear user message."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {
                    "role": "system",
                    "content": "Welcome message",
                },
                {
                    "role": "user",
                    "content": "Chcę zrozumieć, dlaczego użytkownicy opuszczają checkout w moim e-commerce",
                },
            ],
            "current_stage": "gather_goal",
        }

        llm_response_content = """
        {
            "goal_extracted": true,
            "goal": "Zrozumieć przyczyny porzucania koszyka w procesie checkout e-commerce",
            "confidence": "high",
            "follow_up_question": null,
            "assistant_message": "Rozumiem! Twój cel to zrozumienie przyczyn porzucania koszyka w checkout."
        }
        """

        # Mock LLM
        with patch("app.services.study_designer.nodes.gather_goal.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content=llm_response_content)
            mock_build.return_value = mock_llm

            # Act
            result = await gather_goal_node(state)

            # Assert
            assert result["study_goal"] == "Zrozumieć przyczyny porzucania koszyka w procesie checkout e-commerce"
            assert result["current_stage"] == "define_audience"
            assert len(result["messages"]) == 3  # system + user + assistant
            assert result["messages"][-1]["role"] == "assistant"
            assert "Rozumiem" in result["messages"][-1]["content"]

    @pytest.mark.asyncio
    async def test_gather_goal_needs_clarification(self):
        """Test loop-back when goal is unclear (goal_extracted=false)."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {
                    "role": "system",
                    "content": "Welcome message",
                },
                {
                    "role": "user",
                    "content": "Chcę zrobić badanie",
                },
            ],
            "current_stage": "gather_goal",
        }

        llm_response_content = """
        {
            "goal_extracted": false,
            "goal": null,
            "confidence": "low",
            "follow_up_question": "Jaki konkretny problem lub pytanie biznesowe chcesz zbadać?",
            "assistant_message": "Rozumiem, że chcesz przeprowadzić badanie. Powiedz mi więcej - jaki konkretny problem lub pytanie biznesowe chcesz zbadać?"
        }
        """

        # Mock LLM
        with patch("app.services.study_designer.nodes.gather_goal.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content=llm_response_content)
            mock_build.return_value = mock_llm

            # Act
            result = await gather_goal_node(state)

            # Assert
            assert "study_goal" not in result or result.get("study_goal") is None
            assert result["current_stage"] == "gather_goal"  # Loop-back
            assert len(result["messages"]) == 3
            assert "Powiedz mi więcej" in result["messages"][-1]["content"]

    @pytest.mark.asyncio
    async def test_gather_goal_json_in_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {
                    "role": "system",
                    "content": "Welcome",
                },
                {
                    "role": "user",
                    "content": "Badanie użyteczności nowej funkcji",
                },
            ],
            "current_stage": "gather_goal",
        }

        # LLM wraps JSON in markdown
        llm_response_content = """
        Oto analiza:

        ```json
        {
            "goal_extracted": true,
            "goal": "Ocena użyteczności nowej funkcji produktu",
            "confidence": "high",
            "follow_up_question": null,
            "assistant_message": "Doskonale! Zbadamy użyteczność nowej funkcji."
        }
        ```
        """

        # Mock LLM
        with patch("app.services.study_designer.nodes.gather_goal.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content=llm_response_content)
            mock_build.return_value = mock_llm

            # Act
            result = await gather_goal_node(state)

            # Assert
            assert result["study_goal"] == "Ocena użyteczności nowej funkcji produktu"
            assert result["current_stage"] == "define_audience"

    @pytest.mark.asyncio
    async def test_gather_goal_no_user_message(self):
        """Test graceful handling when no user message exists."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {
                    "role": "system",
                    "content": "Welcome",
                },
            ],
            "current_stage": "gather_goal",
        }

        # Act
        result = await gather_goal_node(state)

        # Assert
        assert result["current_stage"] == "gather_goal"  # Stays in same stage
        assert "study_goal" not in result or result.get("study_goal") is None

    @pytest.mark.asyncio
    async def test_gather_goal_llm_error_handling(self):
        """Test error handling when LLM fails."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {
                    "role": "system",
                    "content": "Welcome",
                },
                {
                    "role": "user",
                    "content": "Test goal",
                },
            ],
            "current_stage": "gather_goal",
        }

        # Mock LLM to raise exception
        with patch("app.services.study_designer.nodes.gather_goal.build_chat_model") as mock_build:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.side_effect = Exception("LLM API Error")
            mock_build.return_value = mock_llm

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await gather_goal_node(state)

            assert "LLM API Error" in str(exc_info.value)
