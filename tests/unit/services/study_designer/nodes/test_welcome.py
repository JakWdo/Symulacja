"""
Unit tests dla welcome node - wiadomość powitalna dla Study Designer Chat.

Testuje:
- Generacja welcome message
- Ustawienie initial stage
- Dodanie system message do konwersacji

Target coverage: 95%+
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.services.study_designer.nodes.welcome import welcome_node
from app.services.study_designer.state_schema import ConversationState


class TestWelcomeNode:
    """Test suite dla welcome node."""

    @pytest.mark.asyncio
    async def test_welcome_generates_message(self):
        """Test welcome message generation with proper structure."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "current_stage": "welcome",
        }

        # Act
        result = await welcome_node(state)

        # Assert
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "assistant"
        assert "Witaj" in result["messages"][0]["content"] or "witaj" in result["messages"][0]["content"]
        assert result["current_stage"] == "gather_goal"

    @pytest.mark.asyncio
    async def test_welcome_with_existing_messages(self):
        """Test welcome preserves existing messages (idempotent)."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {
                    "role": "system",
                    "content": "Previous message",
                },
            ],
            "current_stage": "welcome",
        }

        # Act
        result = await welcome_node(state)

        # Assert
        assert len(result["messages"]) == 2  # Previous + welcome
        assert result["messages"][1]["role"] == "assistant"
        assert result["current_stage"] == "gather_goal"

    @pytest.mark.asyncio
    async def test_welcome_message_content(self):
        """Test welcome message contains key information."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "current_stage": "welcome",
        }

        # Act
        result = await welcome_node(state)

        # Assert
        welcome_text = result["messages"][0]["content"]
        # Should mention key steps
        assert any(keyword in welcome_text.lower() for keyword in ["cel", "goal", "badanie", "study"])

    @pytest.mark.asyncio
    async def test_welcome_always_transitions_to_gather_goal(self):
        """Test welcome always moves to gather_goal stage."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "current_stage": "welcome",
        }

        # Act
        result = await welcome_node(state)

        # Assert
        assert result["current_stage"] == "gather_goal"
