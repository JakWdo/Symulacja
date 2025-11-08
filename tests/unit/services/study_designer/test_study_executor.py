"""
Unit tests dla StudyExecutor - wykonanie zatwierdzonego planu badania.

Testuje:
- execute_approved_plan() success - tworzy workflow z execution_steps
- execute_approved_plan() gdy status != approved (error)
- execute_approved_plan() gdy brak generated_plan (error)
- execute_approved_plan() gdy brak execution_steps (error)
- _build_canvas_from_steps() - generacja nodes i edges
- _get_node_label() - generacja czytelnych labels
- _generate_workflow_name() - generacja nazwy workflow

Target coverage: 85%+
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.study_designer import StudyDesignerSession
from app.models.user import User
from app.services.study_designer.study_executor import StudyExecutor


class TestExecuteApprovedPlan:
    """Test suite dla execute_approved_plan."""

    @pytest.mark.asyncio
    async def test_execute_approved_plan_success(
        self, db_session: AsyncSession, test_user: User, test_project
    ):
        """Test successful execution z pełnymi execution_steps."""
        # Arrange
        executor = StudyExecutor(db_session)

        session = StudyDesignerSession(
            user_id=test_user.id,
            project_id=test_project.id,
            status="approved",
            current_stage="await_approval",
            conversation_state={
                "session_id": "test",
                "user_id": str(test_user.id),
                "messages": [],
                "current_stage": "await_approval",
                "study_goal": "Test checkout abandonment",
            },
            generated_plan={
                "markdown_summary": "# Study Plan\n\n...",
                "estimated_time_seconds": 1200,
                "estimated_cost_usd": 10.0,
                "execution_steps": [
                    {"type": "personas_generation", "config": {"num_personas": 20}},
                    {
                        "type": "focus_group_discussion",
                        "config": {"num_questions": 5},
                    },
                ],
            },
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        # Mock WorkflowService.create_workflow
        mock_workflow = MagicMock()
        mock_workflow.id = uuid4()

        with patch(
            "app.services.study_designer.study_executor.WorkflowService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.create_workflow.return_value = mock_workflow
            mock_service_class.return_value = mock_service

            # Act
            workflow_id = await executor.execute_approved_plan(session, test_user.id)

            # Assert
            assert workflow_id == mock_workflow.id
            assert session.status == "executing"
            assert session.created_workflow_id == workflow_id

            # Verify create_workflow was called
            mock_service.create_workflow.assert_called_once()
            call_args = mock_service.create_workflow.call_args
            workflow_data = call_args[0][0]

            assert "Test checkout abandonment" in workflow_data.name
            assert workflow_data.project_id == test_project.id
            assert len(workflow_data.canvas_data.nodes) == 4  # start + 2 steps + end
            assert len(workflow_data.canvas_data.edges) == 3  # 3 connections

    @pytest.mark.asyncio
    async def test_execute_approved_plan_wrong_status(
        self, db_session: AsyncSession, test_user: User, test_project
    ):
        """Test error gdy session status != approved."""
        # Arrange
        executor = StudyExecutor(db_session)

        session = StudyDesignerSession(
            user_id=test_user.id,
            project_id=test_project.id,
            status="active",  # Wrong status
            current_stage="gather_goal",
            conversation_state={
                "session_id": "test",
                "user_id": str(test_user.id),
                "messages": [],
                "current_stage": "gather_goal",
            },
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await executor.execute_approved_plan(session, test_user.id)

        assert exc_info.value.status_code == 400
        assert "must be 'approved'" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_execute_approved_plan_no_plan(
        self, db_session: AsyncSession, test_user: User, test_project
    ):
        """Test error gdy brak generated_plan."""
        # Arrange
        executor = StudyExecutor(db_session)

        session = StudyDesignerSession(
            user_id=test_user.id,
            project_id=test_project.id,
            status="approved",
            current_stage="await_approval",
            conversation_state={
                "session_id": "test",
                "user_id": str(test_user.id),
                "messages": [],
                "current_stage": "await_approval",
            },
            generated_plan=None,  # No plan
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await executor.execute_approved_plan(session, test_user.id)

        assert exc_info.value.status_code == 400
        assert "no plan generated" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_execute_approved_plan_no_execution_steps(
        self, db_session: AsyncSession, test_user: User, test_project
    ):
        """Test error gdy brak execution_steps w planie."""
        # Arrange
        executor = StudyExecutor(db_session)

        session = StudyDesignerSession(
            user_id=test_user.id,
            project_id=test_project.id,
            status="approved",
            current_stage="await_approval",
            conversation_state={
                "session_id": "test",
                "user_id": str(test_user.id),
                "messages": [],
                "current_stage": "await_approval",
            },
            generated_plan={
                "markdown_summary": "# Plan without steps",
                # Missing execution_steps
            },
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await executor.execute_approved_plan(session, test_user.id)

        assert exc_info.value.status_code == 400
        assert "execution_steps" in exc_info.value.detail.lower()


class TestBuildCanvasFromSteps:
    """Test suite dla _build_canvas_from_steps."""

    def test_build_canvas_single_step(self, db_session: AsyncSession):
        """Test budowania canvas z jednym krokiem."""
        # Arrange
        executor = StudyExecutor(db_session)
        execution_steps = [
            {"type": "personas_generation", "config": {"num_personas": 20}}
        ]

        # Act
        canvas_data = executor._build_canvas_from_steps(execution_steps)

        # Assert
        assert len(canvas_data.nodes) == 3  # start + 1 step + end
        assert len(canvas_data.edges) == 2  # start→step, step→end

        # Check start node
        assert canvas_data.nodes[0]["id"] == "node-start"
        assert canvas_data.nodes[0]["type"] == "start"

        # Check step node
        assert canvas_data.nodes[1]["id"] == "node-1"
        assert canvas_data.nodes[1]["type"] == "personas"
        assert canvas_data.nodes[1]["data"]["config"]["num_personas"] == 20

        # Check end node
        assert canvas_data.nodes[2]["id"] == "node-end"
        assert canvas_data.nodes[2]["type"] == "end"

    def test_build_canvas_multiple_steps(self, db_session: AsyncSession):
        """Test budowania canvas z wieloma krokami."""
        # Arrange
        executor = StudyExecutor(db_session)
        execution_steps = [
            {"type": "personas_generation", "config": {"num_personas": 20}},
            {"type": "focus_group_discussion", "config": {"num_questions": 5}},
            {"type": "ai_analysis", "config": {"analysis_type": "themes"}},
        ]

        # Act
        canvas_data = executor._build_canvas_from_steps(execution_steps)

        # Assert
        assert len(canvas_data.nodes) == 5  # start + 3 steps + end
        assert len(canvas_data.edges) == 4  # 4 connections

        # Check vertical positioning (y increases)
        y_positions = [node["position"]["y"] for node in canvas_data.nodes]
        assert y_positions == sorted(y_positions)  # Sorted ascending

        # Check edges connect correctly
        assert canvas_data.edges[0]["source"] == "node-start"
        assert canvas_data.edges[0]["target"] == "node-1"

        assert canvas_data.edges[1]["source"] == "node-1"
        assert canvas_data.edges[1]["target"] == "node-2"

        assert canvas_data.edges[2]["source"] == "node-2"
        assert canvas_data.edges[2]["target"] == "node-3"

        assert canvas_data.edges[3]["source"] == "node-3"
        assert canvas_data.edges[3]["target"] == "node-end"

    def test_build_canvas_unknown_step_type(self, db_session: AsyncSession):
        """Test że nieznane typy kroków są obsługiwane gracefully."""
        # Arrange
        executor = StudyExecutor(db_session)
        execution_steps = [{"type": "custom_unknown_type", "config": {}}]

        # Act
        canvas_data = executor._build_canvas_from_steps(execution_steps)

        # Assert
        assert len(canvas_data.nodes) == 3
        # Unknown type should map to "custom"
        assert canvas_data.nodes[1]["type"] == "custom"


class TestGetNodeLabel:
    """Test suite dla _get_node_label."""

    def test_get_node_label_personas(self, db_session: AsyncSession):
        """Test label dla personas_generation."""
        executor = StudyExecutor(db_session)

        label = executor._get_node_label(
            "personas_generation", {"num_personas": 30}
        )

        assert label == "Generate 30 Personas"

    def test_get_node_label_focus_group(self, db_session: AsyncSession):
        """Test label dla focus_group_discussion."""
        executor = StudyExecutor(db_session)

        label = executor._get_node_label(
            "focus_group_discussion", {"num_questions": 8}
        )

        assert label == "Focus Group (8 questions)"

    def test_get_node_label_survey(self, db_session: AsyncSession):
        """Test label dla survey_generation."""
        executor = StudyExecutor(db_session)

        label = executor._get_node_label("survey_generation", {"num_questions": 15})

        assert label == "Survey (15 questions)"

    def test_get_node_label_ai_analysis(self, db_session: AsyncSession):
        """Test label dla ai_analysis."""
        executor = StudyExecutor(db_session)

        label = executor._get_node_label("ai_analysis", {"analysis_type": "themes"})

        assert label == "AI Analysis: Themes"

    def test_get_node_label_unknown_type(self, db_session: AsyncSession):
        """Test label dla nieznanego typu."""
        executor = StudyExecutor(db_session)

        label = executor._get_node_label("custom_unknown", {})

        assert label == "Custom Unknown"


class TestGenerateWorkflowName:
    """Test suite dla _generate_workflow_name."""

    def test_generate_workflow_name_with_goal(
        self, db_session: AsyncSession, test_user: User, test_project
    ):
        """Test generowania nazwy z study_goal."""
        executor = StudyExecutor(db_session)

        session = StudyDesignerSession(
            user_id=test_user.id,
            project_id=test_project.id,
            status="approved",
            current_stage="await_approval",
            conversation_state={
                "session_id": "test",
                "user_id": str(test_user.id),
                "messages": [],
                "current_stage": "await_approval",
                "study_goal": "Understand checkout abandonment patterns",
            },
        )

        name = executor._generate_workflow_name(session)

        assert name == "Study: Understand checkout abandonment patterns"
        assert len(name) <= 255

    def test_generate_workflow_name_long_goal(
        self, db_session: AsyncSession, test_user: User, test_project
    ):
        """Test że długi goal jest skracany."""
        executor = StudyExecutor(db_session)

        long_goal = "A" * 250  # Very long goal

        session = StudyDesignerSession(
            user_id=test_user.id,
            project_id=test_project.id,
            status="approved",
            current_stage="await_approval",
            conversation_state={
                "session_id": "test",
                "user_id": str(test_user.id),
                "messages": [],
                "current_stage": "await_approval",
                "study_goal": long_goal,
            },
        )

        name = executor._generate_workflow_name(session)

        assert len(name) <= 255
        assert name.endswith("...")

    def test_generate_workflow_name_without_goal(
        self, db_session: AsyncSession, test_user: User, test_project
    ):
        """Test generowania nazwy bez study_goal (fallback)."""
        executor = StudyExecutor(db_session)

        session = StudyDesignerSession(
            user_id=test_user.id,
            project_id=test_project.id,
            status="approved",
            current_stage="await_approval",
            conversation_state={
                "session_id": "test",
                "user_id": str(test_user.id),
                "messages": [],
                "current_stage": "await_approval",
                # No study_goal
            },
        )

        name = executor._generate_workflow_name(session)

        assert name.startswith("Study from Session ")
        assert str(session.id)[:8] in name
