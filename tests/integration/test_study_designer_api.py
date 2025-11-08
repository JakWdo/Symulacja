"""
Integration tests dla Study Designer API endpoints.

Testuje:
- POST /study-designer/sessions (create session)
- GET /study-designer/sessions/{id} (get session)
- POST /study-designer/sessions/{id}/message (send message)
- POST /study-designer/sessions/{id}/approve (approve plan)
- DELETE /study-designer/sessions/{id} (cancel session)
- GET /study-designer/sessions (list sessions)

Używa prawdziwej bazy danych (z rollback) ale mockuje LLM.

Target coverage: 80%+
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.study_designer import StudyDesignerSession
from app.models.user import User


class TestStudyDesignerAPICreate:
    """Test suite dla POST /study-designer/sessions."""

    @pytest.mark.asyncio
    async def test_create_session_success(
        self, db_session: AsyncSession, test_user: User, auth_headers
    ):
        """Test successful session creation."""
        # Mock state machine
        with patch(
            "app.services.study_designer.orchestrator.ConversationStateMachine"
        ) as mock_sm:
            mock_instance = MagicMock()
            mock_instance.initialize_session = AsyncMock(
                return_value={
                    "session_id": "test",
                    "user_id": str(test_user.id),
                    "messages": [
                        {
                            "role": "assistant",
                            "content": "Witaj! Pomogę Ci zaprojektować badanie UX.",
                        }
                    ],
                    "current_stage": "welcome",
                }
            )
            mock_sm.return_value = mock_instance

            async with AsyncClient(app=app, base_url="http://test") as client:
                # Act
                response = await client.post(
                    "/api/v1/study-designer/sessions",
                    json={},
                    headers=auth_headers,
                )

                # Assert
                assert response.status_code == 200
                data = response.json()
                assert "session" in data
                assert data["session"]["status"] == "active"
                assert data["session"]["current_stage"] == "welcome"
                assert len(data["session"]["messages"]) > 0

    @pytest.mark.asyncio
    async def test_create_session_with_project(
        self, db_session: AsyncSession, test_user: User, test_project, auth_headers
    ):
        """Test session creation with project_id."""
        # Mock state machine
        with patch(
            "app.services.study_designer.orchestrator.ConversationStateMachine"
        ) as mock_sm:
            mock_instance = MagicMock()
            mock_instance.initialize_session = AsyncMock(
                return_value={
                    "session_id": "test",
                    "user_id": str(test_user.id),
                    "messages": [],
                    "current_stage": "welcome",
                }
            )
            mock_sm.return_value = mock_instance

            async with AsyncClient(app=app, base_url="http://test") as client:
                # Act
                response = await client.post(
                    "/api/v1/study-designer/sessions",
                    json={"project_id": str(test_project.id)},
                    headers=auth_headers,
                )

                # Assert
                assert response.status_code == 200
                data = response.json()
                assert data["session"]["project_id"] == str(test_project.id)

    @pytest.mark.asyncio
    async def test_create_session_unauthorized(self):
        """Test session creation requires authentication."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Act
            response = await client.post(
                "/api/v1/study-designer/sessions",
                json={},
            )

            # Assert
            assert response.status_code == 401


class TestStudyDesignerAPIGet:
    """Test suite dla GET /study-designer/sessions/{id}."""

    @pytest.mark.asyncio
    async def test_get_session_success(
        self, db_session: AsyncSession, test_user: User, auth_headers
    ):
        """Test retrieving existing session."""
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

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Act
            response = await client.get(
                f"/api/v1/study-designer/sessions/{session_model.id}",
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(session_model.id)
            assert data["status"] == "active"
            assert data["current_stage"] == "gather_goal"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, auth_headers):
        """Test get session returns 404 for non-existent session."""
        fake_id = uuid4()

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Act
            response = await client.get(
                f"/api/v1/study-designer/sessions/{fake_id}",
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 404


class TestStudyDesignerAPISendMessage:
    """Test suite dla POST /study-designer/sessions/{id}/message."""

    @pytest.mark.asyncio
    async def test_send_message_success(
        self, db_session: AsyncSession, test_user: User, auth_headers
    ):
        """Test sending message updates conversation."""
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
        with patch(
            "app.services.study_designer.orchestrator.ConversationStateMachine"
        ) as mock_sm:
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

            async with AsyncClient(app=app, base_url="http://test") as client:
                # Act
                response = await client.post(
                    f"/api/v1/study-designer/sessions/{session_model.id}/message",
                    json={"message": "Test checkout flow"},
                    headers=auth_headers,
                )

                # Assert
                assert response.status_code == 200
                data = response.json()
                assert data["session"]["current_stage"] == "define_audience"
                assert len(data["session"]["messages"]) == 3

    @pytest.mark.asyncio
    async def test_send_message_empty_content(
        self, db_session: AsyncSession, test_user: User, auth_headers
    ):
        """Test sending empty message is rejected."""
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

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Act
            response = await client.post(
                f"/api/v1/study-designer/sessions/{session_model.id}/message",
                json={"message": ""},
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 422  # Validation error


class TestStudyDesignerAPIApprovePlan:
    """Test suite dla POST /study-designer/sessions/{id}/approve."""

    @pytest.mark.asyncio
    async def test_approve_plan_success(
        self, db_session: AsyncSession, test_user: User, auth_headers
    ):
        """Test approving plan changes status."""
        # Create session with plan
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
                    "markdown_summary": "# Plan\n\n...",
                    "estimated_time_seconds": 600,
                    "estimated_cost_usd": 5.0,
                },
            },
            generated_plan={
                "markdown_summary": "# Plan\n\n...",
                "estimated_time_seconds": 600,
                "estimated_cost_usd": 5.0,
            },
        )
        db_session.add(session_model)
        await db_session.commit()
        await db_session.refresh(session_model)

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Act
            response = await client.post(
                f"/api/v1/study-designer/sessions/{session_model.id}/approve",
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["session"]["status"] == "approved"

    @pytest.mark.asyncio
    async def test_approve_plan_no_plan(
        self, db_session: AsyncSession, test_user: User, auth_headers
    ):
        """Test approve plan fails when no plan exists."""
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

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Act
            response = await client.post(
                f"/api/v1/study-designer/sessions/{session_model.id}/approve",
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 400


class TestStudyDesignerAPICancelSession:
    """Test suite dla DELETE /study-designer/sessions/{id}."""

    @pytest.mark.asyncio
    async def test_cancel_session_success(
        self, db_session: AsyncSession, test_user: User, auth_headers
    ):
        """Test cancelling active session."""
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

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Act
            response = await client.delete(
                f"/api/v1/study-designer/sessions/{session_model.id}",
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Session cancelled successfully"


class TestStudyDesignerAPIListSessions:
    """Test suite dla GET /study-designer/sessions."""

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, auth_headers):
        """Test listing sessions returns empty array when none exist."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Act
            response = await client.get(
                "/api/v1/study-designer/sessions",
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["sessions"] == []
            assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_sessions_multiple(
        self, db_session: AsyncSession, test_user: User, auth_headers
    ):
        """Test listing multiple sessions."""
        # Create 3 sessions
        for i in range(3):
            session = StudyDesignerSession(
                user_id=test_user.id,
                status="active",
                current_stage="gather_goal",
                conversation_state={
                    "session_id": f"test-{i}",
                    "user_id": str(test_user.id),
                    "messages": [],
                    "current_stage": "gather_goal",
                },
            )
            db_session.add(session)
        await db_session.commit()

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Act
            response = await client.get(
                "/api/v1/study-designer/sessions",
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data["sessions"]) == 3
            assert data["total"] == 3
