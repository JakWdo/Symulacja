"""
Unit tests dla await_approval node - oczekiwanie na zatwierdzenie planu.

Testuje:
- Pozostanie w stanie await_approval (końcowy node)
- Zachowanie istniejących danych
- Brak zmian w messages (static node)

Target coverage: 95%+
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.services.study_designer.nodes.await_approval import await_approval_node
from app.services.study_designer.state_schema import ConversationState


class TestAwaitApprovalNode:
    """Test suite dla await_approval node."""

    @pytest.mark.asyncio
    async def test_await_approval_preserves_state(self):
        """Test await_approval preserves all state data."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        generated_plan = {
            "markdown_summary": "# Test Plan",
            "estimated_time_seconds": 300,
            "estimated_cost_usd": 10.00,
            "execution_steps": ["Step 1", "Step 2"],
        }
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [
                {"role": "assistant", "content": "Plan generated"},
            ],
            "current_stage": "await_approval",
            "study_goal": "Test goal",
            "target_audience": {"age": "25-35"},
            "research_method": "personas",
            "study_details": {"num": 10},
            "generated_plan": generated_plan,
        }

        # Act
        result = await await_approval_node(state)

        # Assert
        # Stage should remain await_approval (terminal node for conversation)
        assert result["current_stage"] == "await_approval"
        # All data should be preserved
        assert result["study_goal"] == "Test goal"
        assert result["target_audience"] == {"age": "25-35"}
        assert result["research_method"] == "personas"
        assert result["generated_plan"] == generated_plan
        # Messages unchanged (static node)
        assert len(result["messages"]) == 1

    @pytest.mark.asyncio
    async def test_await_approval_with_minimal_state(self):
        """Test await_approval works with minimal required state."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "current_stage": "await_approval",
        }

        # Act
        result = await await_approval_node(state)

        # Assert
        assert result["current_stage"] == "await_approval"
        assert result["session_id"] == session_id
        assert result["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_await_approval_with_full_conversation_history(self):
        """Test await_approval preserves full conversation history."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        messages = [
            {"role": "assistant", "content": "Welcome"},
            {"role": "user", "content": "I want to do research"},
            {"role": "assistant", "content": "Great! What's your goal?"},
            {"role": "user", "content": "Understand users"},
            {"role": "assistant", "content": "Plan generated. Approve?"},
        ]
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": messages,
            "current_stage": "await_approval",
            "study_goal": "Understand users",
            "target_audience": {"all": True},
            "research_method": "personas",
            "study_details": {"num": 15},
            "generated_plan": {
                "markdown_summary": "Plan",
                "estimated_time_seconds": 500,
                "estimated_cost_usd": 15.00,
                "execution_steps": ["Generate"],
            },
        }

        # Act
        result = await await_approval_node(state)

        # Assert
        assert result["current_stage"] == "await_approval"
        assert len(result["messages"]) == 5
        assert result["messages"] == messages  # Unchanged

    @pytest.mark.asyncio
    async def test_await_approval_idempotent(self):
        """Test await_approval is idempotent (can be called multiple times)."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [{"role": "assistant", "content": "Approve?"}],
            "current_stage": "await_approval",
            "study_goal": "Goal",
            "generated_plan": {"markdown_summary": "Plan"},
        }

        # Act - call twice
        result1 = await await_approval_node(state)
        result2 = await await_approval_node(result1)

        # Assert - both calls produce same result
        assert result1["current_stage"] == "await_approval"
        assert result2["current_stage"] == "await_approval"
        assert result1["messages"] == result2["messages"]

    @pytest.mark.asyncio
    async def test_await_approval_terminal_node(self):
        """Test await_approval is a terminal node for the conversation flow."""
        # Arrange
        session_id = str(uuid4())
        user_id = str(uuid4())
        state: ConversationState = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "current_stage": "await_approval",
        }

        # Act
        result = await await_approval_node(state)

        # Assert
        # Should stay in await_approval - this is where conversation ends
        # Next action (approve/reject) happens via API endpoint, not through state machine
        assert result["current_stage"] == "await_approval"
