"""
Unit tests dla ConversationStateMachine - routing i orchestration logic.

Testuje:
- Inicjalizacja sesji (welcome node)
- Routing z welcome do gather_goal
- Routing z gather_goal do define_audience (success) lub loop-back
- Routing z define_audience do select_method (success) lub loop-back
- Routing z select_method do configure_details
- Routing z configure_details do generate_plan
- Routing z generate_plan do await_approval
- Conditional routing logic

Target coverage: 85%+
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.services.study_designer.state_machine import ConversationStateMachine
from app.services.study_designer.state_schema import ConversationState


class TestConversationStateMachineRouting:
    """Test suite dla state machine routing logic."""

    def test_state_machine_initialization(self):
        """Test successful initialization of state machine."""
        # Act
        machine = ConversationStateMachine()

        # Assert
        assert machine.graph is not None
        assert hasattr(machine, "_route_from_welcome")
        assert hasattr(machine, "_route_from_gather_goal")
        assert hasattr(machine, "_route_from_define_audience")
        assert hasattr(machine, "_route_from_select_method")
        assert hasattr(machine, "_route_from_configure_details")

    def test_route_from_welcome(self):
        """Test routing from welcome always goes to gather_goal."""
        # Arrange
        machine = ConversationStateMachine()
        state: ConversationState = {
            "session_id": str(uuid4()),
            "user_id": str(uuid4()),
            "messages": [],
            "current_stage": "welcome",
        }

        # Act
        next_node = machine._route_from_welcome(state)

        # Assert
        assert next_node == "gather_goal"

    def test_route_from_gather_goal_success(self):
        """Test routing from gather_goal to define_audience when goal extracted."""
        # Arrange
        machine = ConversationStateMachine()
        state: ConversationState = {
            "session_id": str(uuid4()),
            "user_id": str(uuid4()),
            "messages": [],
            "current_stage": "define_audience",  # Node set this after success
            "study_goal": "Test goal extracted",
        }

        # Act
        next_node = machine._route_from_gather_goal(state)

        # Assert
        assert next_node == "define_audience"

    def test_route_from_gather_goal_loop_back(self):
        """Test routing from gather_goal loops back when goal unclear."""
        # Arrange
        machine = ConversationStateMachine()
        state: ConversationState = {
            "session_id": str(uuid4()),
            "user_id": str(uuid4()),
            "messages": [],
            "current_stage": "gather_goal",  # Node keeps stage same for loop-back
        }

        # Act
        next_node = machine._route_from_gather_goal(state)

        # Assert
        assert next_node == "gather_goal"

    def test_route_from_define_audience_success(self):
        """Test routing from define_audience to select_method when audience defined."""
        # Arrange
        machine = ConversationStateMachine()
        state: ConversationState = {
            "session_id": str(uuid4()),
            "user_id": str(uuid4()),
            "messages": [],
            "current_stage": "select_method",
            "study_goal": "Test goal",
            "target_audience": {
                "age_range": "25-40",
                "demographics": "Urban professionals",
            },
        }

        # Act
        next_node = machine._route_from_define_audience(state)

        # Assert
        assert next_node == "select_method"

    def test_route_from_define_audience_loop_back(self):
        """Test routing from define_audience loops back when unclear."""
        # Arrange
        machine = ConversationStateMachine()
        state: ConversationState = {
            "session_id": str(uuid4()),
            "user_id": str(uuid4()),
            "messages": [],
            "current_stage": "define_audience",
            "study_goal": "Test goal",
        }

        # Act
        next_node = machine._route_from_define_audience(state)

        # Assert
        assert next_node == "define_audience"

    def test_route_from_select_method_success(self):
        """Test routing from select_method to configure_details when method selected."""
        # Arrange
        machine = ConversationStateMachine()
        state: ConversationState = {
            "session_id": str(uuid4()),
            "user_id": str(uuid4()),
            "messages": [],
            "current_stage": "configure_details",
            "study_goal": "Test goal",
            "target_audience": {"age_range": "25-40"},
            "research_method": "focus_group",
        }

        # Act
        next_node = machine._route_from_select_method(state)

        # Assert
        assert next_node == "configure_details"

    def test_route_from_select_method_loop_back(self):
        """Test routing from select_method loops back when unclear."""
        # Arrange
        machine = ConversationStateMachine()
        state: ConversationState = {
            "session_id": str(uuid4()),
            "user_id": str(uuid4()),
            "messages": [],
            "current_stage": "select_method",
            "study_goal": "Test goal",
            "target_audience": {"age_range": "25-40"},
        }

        # Act
        next_node = machine._route_from_select_method(state)

        # Assert
        assert next_node == "select_method"

    def test_route_from_configure_details_success(self):
        """Test routing from configure_details to generate_plan when details complete."""
        # Arrange
        machine = ConversationStateMachine()
        state: ConversationState = {
            "session_id": str(uuid4()),
            "user_id": str(uuid4()),
            "messages": [],
            "current_stage": "generate_plan",
            "study_goal": "Test goal",
            "target_audience": {"age_range": "25-40"},
            "research_method": "focus_group",
            "configuration": {
                "num_participants": 20,
                "num_questions": 5,
            },
        }

        # Act
        next_node = machine._route_from_configure_details(state)

        # Assert
        assert next_node == "generate_plan"

    def test_route_from_configure_details_loop_back(self):
        """Test routing from configure_details loops back when incomplete."""
        # Arrange
        machine = ConversationStateMachine()
        state: ConversationState = {
            "session_id": str(uuid4()),
            "user_id": str(uuid4()),
            "messages": [],
            "current_stage": "configure_details",
            "study_goal": "Test goal",
            "target_audience": {"age_range": "25-40"},
            "research_method": "focus_group",
        }

        # Act
        next_node = machine._route_from_configure_details(state)

        # Assert
        assert next_node == "configure_details"


class TestConversationStateMachineExecution:
    """Test suite dla full state machine execution (integration style)."""

    @pytest.mark.asyncio
    async def test_initialize_session(self):
        """Test initializing session executes welcome node."""
        # Arrange
        machine = ConversationStateMachine()
        initial_state: ConversationState = {
            "session_id": str(uuid4()),
            "user_id": str(uuid4()),
            "messages": [],
            "current_stage": "welcome",
        }

        # Act
        result = await machine.initialize_session(initial_state)

        # Assert
        assert result["current_stage"] == "welcome"
        assert len(result["messages"]) > 0
        # Welcome message should be added
        assert any(msg["role"] == "assistant" for msg in result["messages"])

    @pytest.mark.asyncio
    async def test_process_message_adds_user_message(self):
        """Test process_message adds user message to state before node execution."""
        # Arrange
        machine = ConversationStateMachine()
        state: ConversationState = {
            "session_id": str(uuid4()),
            "user_id": str(uuid4()),
            "messages": [
                {
                    "role": "assistant",
                    "content": "Welcome",
                }
            ],
            "current_stage": "gather_goal",
        }
        user_message = "I want to test my new feature"

        # Act
        # This will fail at LLM call but we can test message addition
        try:
            await machine.process_message(state, user_message)
        except Exception:
            # Expected - we're not mocking LLM here
            pass

        # Assert - state should have user message added before node execution
        # Check original state was modified
        assert any(
            msg["role"] == "user" and msg["content"] == user_message
            for msg in state["messages"]
        )
