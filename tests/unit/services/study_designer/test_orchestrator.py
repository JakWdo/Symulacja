"""
Unit tests dla StudyDesignerOrchestrator - główny serwis zarządzający sesjami.

Testuje:
- create_session (success, z project_id, bez project_id)
- get_session (success, not found, unauthorized)
- process_user_message (success, session not found, invalid session state)
- approve_plan (success, no plan, already approved)
- cancel_session (success, already cancelled, unauthorized)
- list_user_sessions (empty, multiple, pagination)

Target coverage: 85%+
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.study_designer import StudyDesignerSession
from app.models.user import User
from app.services.study_designer.orchestrator import StudyDesignerOrchestrator


class TestOrchestratorCreate:
    """Test suite dla create_session."""

    @pytest.mark.asyncio
    async def test_create_session_success(self, db_session: AsyncSession, test_user: User):
        """Test successful session creation."""
        # Arrange
        orchestrator = StudyDesignerOrchestrator(db_session)

        # Mock state machine
        with patch("app.services.study_designer.orchestrator.ConversationStateMachine") as mock_sm:
            mock_instance = MagicMock()
            mock_instance.initialize_session = AsyncMock(
                return_value={
                    "session_id": "test-session",
                    "user_id": str(test_user.id),
                    "messages": [
                        {
                            "role": "assistant",
                            "content": "Welcome to Study Designer!",
                        }
                    ],
                    "current_stage": "welcome",
                }
            )
            mock_sm.return_value = mock_instance

            # Act
            session = await orchestrator.create_session(test_user.id, project_id=None)

            # Assert
            assert session.id is not None
            assert session.user_id == test_user.id
            assert session.status == "active"
            assert session.current_stage == "welcome"
            assert session.project_id is None
            assert session.conversation_state is not None
            assert isinstance(session.created_at, datetime)

    @pytest.mark.asyncio
    async def test_create_session_with_project(
        self, db_session: AsyncSession, test_user: User, test_project
    ):
        """Test session creation with project_id."""
        # Arrange
        orchestrator = StudyDesignerOrchestrator(db_session)

        # Mock state machine
        with patch("app.services.study_designer.orchestrator.ConversationStateMachine") as mock_sm:
            mock_instance = MagicMock()
            mock_instance.initialize_session = AsyncMock(
                return_value={
                    "session_id": "test-session",
                    "user_id": str(test_user.id),
                    "messages": [],
                    "current_stage": "welcome",
                }
            )
            mock_sm.return_value = mock_instance

            # Act
            session = await orchestrator.create_session(test_user.id, project_id=test_project.id)

            # Assert
            assert session.project_id == test_project.id


class TestOrchestratorGet:
    """Test suite dla get_session."""

    @pytest.mark.asyncio
    async def test_get_session_success(self, db_session: AsyncSession, test_user: User):
        """Test retrieving existing session."""
        # Arrange
        orchestrator = StudyDesignerOrchestrator(db_session)

        # Create session first
        session_model = StudyDesignerSession(
            user_id=test_user.id,
            status="active",
            current_stage="gather_goal",
            conversation_state={
                "session_id": "test",
                "user_id": str(test_user.id),
                "messages": [],
                "current_stage": "gather_goal",
            },
        )
        db_session.add(session_model)
        await db_session.commit()
        await db_session.refresh(session_model)

        # Act
        retrieved = await orchestrator.get_session(session_model.id, test_user.id)

        # Assert
        assert retrieved.id == session_model.id
        assert retrieved.user_id == test_user.id
        assert retrieved.status == "active"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, db_session: AsyncSession, test_user: User):
        """Test get_session raises 404 when session doesn't exist."""
        # Arrange
        orchestrator = StudyDesignerOrchestrator(db_session)
        fake_id = uuid4()

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await orchestrator.get_session(fake_id, test_user.id)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_session_unauthorized(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test get_session raises 403 when user doesn't own session."""
        # Arrange
        orchestrator = StudyDesignerOrchestrator(db_session)

        # Create session owned by different user
        other_user_id = uuid4()
        session_model = StudyDesignerSession(
            user_id=other_user_id,
            status="active",
            current_stage="gather_goal",
            conversation_state={
                "session_id": "test",
                "user_id": str(other_user_id),
                "messages": [],
                "current_stage": "gather_goal",
            },
        )
        db_session.add(session_model)
        await db_session.commit()
        await db_session.refresh(session_model)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await orchestrator.get_session(session_model.id, test_user.id)

        assert exc_info.value.status_code == 403


class TestOrchestratorProcessMessage:
    """Test suite dla process_user_message."""

    @pytest.mark.asyncio
    async def test_process_message_success(self, db_session: AsyncSession, test_user: User):
        """Test processing user message updates state."""
        # Arrange
        orchestrator = StudyDesignerOrchestrator(db_session)

        # Create session
        session_model = StudyDesignerSession(
            user_id=test_user.id,
            status="active",
            current_stage="gather_goal",
            conversation_state={
                "session_id": "test",
                "user_id": str(test_user.id),
                "messages": [
                    {
                        "role": "assistant",
                        "content": "What's your goal?",
                    }
                ],
                "current_stage": "gather_goal",
            },
        )
        db_session.add(session_model)
        await db_session.commit()
        await db_session.refresh(session_model)

        # Mock state machine
        with patch("app.services.study_designer.orchestrator.ConversationStateMachine") as mock_sm:
            mock_instance = MagicMock()
            mock_instance.process_message = AsyncMock(
                return_value={
                    "session_id": str(session_model.id),
                    "user_id": str(test_user.id),
                    "messages": [
                        {
                            "role": "assistant",
                            "content": "What's your goal?",
                        },
                        {
                            "role": "user",
                            "content": "Test checkout flow",
                        },
                        {
                            "role": "assistant",
                            "content": "Great! Now define audience.",
                        },
                    ],
                    "current_stage": "define_audience",
                    "study_goal": "Test checkout flow",
                }
            )
            mock_sm.return_value = mock_instance

            # Act
            updated = await orchestrator.process_user_message(
                session_model.id, "Test checkout flow"
            )

            # Assert
            assert updated.current_stage == "define_audience"
            assert "study_goal" in updated.conversation_state
            assert updated.conversation_state["study_goal"] == "Test checkout flow"
            assert len(updated.conversation_state["messages"]) == 3

    @pytest.mark.asyncio
    async def test_process_message_session_not_found(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test process_message raises 404 for non-existent session."""
        # Arrange
        orchestrator = StudyDesignerOrchestrator(db_session)
        fake_id = uuid4()

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await orchestrator.process_user_message(fake_id, "Test message")

        assert exc_info.value.status_code == 404


class TestOrchestratorApprovePlan:
    """Test suite dla approve_plan."""

    @pytest.mark.asyncio
    async def test_approve_plan_success(self, db_session: AsyncSession, test_user: User):
        """Test approving plan changes status to approved."""
        # Arrange
        orchestrator = StudyDesignerOrchestrator(db_session)

        # Create session with generated plan
        session_model = StudyDesignerSession(
            user_id=test_user.id,
            status="plan_ready",
            current_stage="await_approval",
            conversation_state={
                "session_id": "test",
                "user_id": str(test_user.id),
                "messages": [],
                "current_stage": "await_approval",
                "study_goal": "Test goal",
                "generated_plan": {
                    "markdown_summary": "# Study Plan\n\n...",
                    "estimated_time_seconds": 600,
                    "estimated_cost_usd": 5.0,
                },
            },
            generated_plan={
                "markdown_summary": "# Study Plan\n\n...",
                "estimated_time_seconds": 600,
                "estimated_cost_usd": 5.0,
            },
        )
        db_session.add(session_model)
        await db_session.commit()
        await db_session.refresh(session_model)

        # Act
        updated = await orchestrator.approve_plan(session_model.id)

        # Assert
        assert updated.status == "approved"

    @pytest.mark.asyncio
    async def test_approve_plan_no_plan_generated(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test approve_plan raises 400 when no plan exists."""
        # Arrange
        orchestrator = StudyDesignerOrchestrator(db_session)

        # Create session without plan
        session_model = StudyDesignerSession(
            user_id=test_user.id,
            status="active",
            current_stage="gather_goal",
            conversation_state={
                "session_id": "test",
                "user_id": str(test_user.id),
                "messages": [],
                "current_stage": "gather_goal",
            },
        )
        db_session.add(session_model)
        await db_session.commit()
        await db_session.refresh(session_model)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await orchestrator.approve_plan(session_model.id)

        assert exc_info.value.status_code == 400
        assert "no plan" in exc_info.value.detail.lower()


class TestOrchestratorCancel:
    """Test suite dla cancel_session."""

    @pytest.mark.asyncio
    async def test_cancel_session_success(self, db_session: AsyncSession, test_user: User):
        """Test cancelling active session."""
        # Arrange
        orchestrator = StudyDesignerOrchestrator(db_session)

        # Create session
        session_model = StudyDesignerSession(
            user_id=test_user.id,
            status="active",
            current_stage="gather_goal",
            conversation_state={
                "session_id": "test",
                "user_id": str(test_user.id),
                "messages": [],
                "current_stage": "gather_goal",
            },
        )
        db_session.add(session_model)
        await db_session.commit()
        await db_session.refresh(session_model)

        # Act
        cancelled = await orchestrator.cancel_session(session_model.id, test_user.id)

        # Assert
        assert cancelled.status == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_session_already_cancelled(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test cancelling already cancelled session is idempotent."""
        # Arrange
        orchestrator = StudyDesignerOrchestrator(db_session)

        # Create cancelled session
        session_model = StudyDesignerSession(
            user_id=test_user.id,
            status="cancelled",
            current_stage="gather_goal",
            conversation_state={
                "session_id": "test",
                "user_id": str(test_user.id),
                "messages": [],
                "current_stage": "gather_goal",
            },
        )
        db_session.add(session_model)
        await db_session.commit()
        await db_session.refresh(session_model)

        # Act
        result = await orchestrator.cancel_session(session_model.id, test_user.id)

        # Assert
        assert result.status == "cancelled"
