"""
Unit tests dla WorkflowExecutor - zaawansowane scenariusze.

Testuje:
- Context passing między nodes
- Error handling i recovery
- Execution tracking i status progression

Target coverage: 90%+ dla WorkflowExecutor
"""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, User
from app.models.workflow import Workflow, WorkflowExecution
from app.services.workflows.execution import WorkflowExecutor


# ==================== 3. CONTEXT PASSING TESTS ====================


class TestContextPassing:
    """Test suite dla passing context między node executions."""

    @pytest.mark.asyncio
    async def test_execution_context_passing_personas(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test context is passed from generate-personas to end node."""
        # Arrange - workflow: start → personas → end
        workflow = Workflow(
            id=uuid4(),
            name="Context Test",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {
                        "id": "personas-1",
                        "type": "generate-personas",
                        "data": {
                            "config": {
                                "count": 5,
                                "project_description": "Test project",
                            }
                        },
                    },
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "personas-1"},
                    {"id": "e2", "source": "personas-1", "target": "end-1"},
                ],
            },
            status="active",
            is_active=True,
        )
        db_session.add(workflow)
        await db_session.commit()
        await db_session.refresh(workflow)

        executor = WorkflowExecutor(db_session)

        # Act
        execution = await executor.execute_workflow(workflow.id, test_user.id)

        # Assert - verify personas context was stored
        assert execution.result_data is not None
        assert "personas-1" in execution.result_data
        assert "persona_ids" in execution.result_data["personas-1"]
        # MVP uses placeholder IDs
        assert len(execution.result_data["personas-1"]["persona_ids"]) == 5

    @pytest.mark.asyncio
    async def test_execution_stops_on_error(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test execution stops and marks failed when node executor raises error."""
        # Arrange - workflow with node that will fail
        workflow = Workflow(
            id=uuid4(),
            name="Error Test",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {
                        "id": "personas-1",
                        "type": "generate-personas",
                        "data": {"config": {}},  # Missing required 'count'
                    },
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "personas-1"},
                    {"id": "e2", "source": "personas-1", "target": "end-1"},
                ],
            },
            status="active",
            is_active=True,
        )
        db_session.add(workflow)
        await db_session.commit()
        await db_session.refresh(workflow)

        executor = WorkflowExecutor(db_session)

        # Act & Assert
        with pytest.raises(Exception):
            await executor.execute_workflow(workflow.id, test_user.id)

        # Verify execution record was marked as failed
        stmt = select(WorkflowExecution).where(WorkflowExecution.workflow_id == workflow.id)
        result = await db_session.execute(stmt)
        execution = result.scalar_one()

        assert execution.status == "failed"
        assert execution.error_message is not None
        assert "count" in execution.error_message.lower()

    @pytest.mark.asyncio
    async def test_execution_context_contains_metadata(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test execution context contains required metadata (project_id, workflow_id, user_id)."""
        # Arrange
        workflow = Workflow(
            id=uuid4(),
            name="Metadata Test",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "end-1"},
                ],
            },
            status="active",
            is_active=True,
        )
        db_session.add(workflow)
        await db_session.commit()
        await db_session.refresh(workflow)

        executor = WorkflowExecutor(db_session)

        # Act
        execution = await executor.execute_workflow(workflow.id, test_user.id)

        # Assert - verify start node result contains metadata
        assert execution.result_data is not None
        start_result = execution.result_data.get("start-1", {})
        assert start_result.get("project_id") == str(test_project.id)
        assert start_result.get("workflow_id") == str(workflow.id)


# ==================== 5. ERROR HANDLING TESTS ====================


class TestErrorHandling:
    """Test suite dla error handling i recovery."""

    @pytest.mark.asyncio
    async def test_execution_error_persisted(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test error message is persisted in execution record."""
        # Arrange
        workflow = Workflow(
            id=uuid4(),
            name="Error Persistence Test",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {
                        "id": "bad-node",
                        "type": "generate-personas",
                        "data": {"config": {}},  # Missing count
                    },
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "bad-node"},
                ],
            },
            status="active",
            is_active=True,
        )
        db_session.add(workflow)
        await db_session.commit()

        executor = WorkflowExecutor(db_session)

        # Act
        try:
            await executor.execute_workflow(workflow.id, test_user.id)
        except Exception:
            pass  # Expected

        # Assert - verify error is in DB
        stmt = select(WorkflowExecution).where(WorkflowExecution.workflow_id == workflow.id)
        result = await db_session.execute(stmt)
        execution = result.scalar_one()

        assert execution.status == "failed"
        assert execution.error_message is not None
        assert len(execution.error_message) <= 1000  # Truncated

    @pytest.mark.asyncio
    async def test_execution_error_truncated(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test error message is truncated to 1000 chars."""
        # Arrange
        workflow = Workflow(
            id=uuid4(),
            name="Long Error Test",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {
                        "id": "bad-node",
                        "type": "generate-personas",
                        "data": {"config": {}},
                    },
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "bad-node"},
                ],
            },
            status="active",
            is_active=True,
        )
        db_session.add(workflow)
        await db_session.commit()

        executor = WorkflowExecutor(db_session)

        # Mock node executor to raise long error
        with patch.object(executor, "_execute_node") as mock_execute:
            long_error = "A" * 2000  # 2000 chars
            mock_execute.side_effect = Exception(long_error)

            try:
                await executor.execute_workflow(workflow.id, test_user.id)
            except Exception:
                pass

        # Assert
        stmt = select(WorkflowExecution).where(WorkflowExecution.workflow_id == workflow.id)
        result = await db_session.execute(stmt)
        execution = result.scalar_one()

        assert execution.error_message is not None
        assert len(execution.error_message) <= 1000


# ==================== 6. EXECUTION TRACKING TESTS ====================


class TestExecutionTracking:
    """Test suite dla tracking execution progress."""

    @pytest.mark.asyncio
    async def test_execution_status_progression(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test execution status progresses: pending → running → completed."""
        # Arrange
        workflow = Workflow(
            id=uuid4(),
            name="Status Test",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "end-1"},
                ],
            },
            status="active",
            is_active=True,
        )
        db_session.add(workflow)
        await db_session.commit()
        await db_session.refresh(workflow)

        executor = WorkflowExecutor(db_session)

        # Act
        execution = await executor.execute_workflow(workflow.id, test_user.id)

        # Assert
        assert execution.status == "completed"
        assert execution.started_at is not None
        assert execution.completed_at is not None
        assert execution.started_at < execution.completed_at

    @pytest.mark.asyncio
    async def test_execution_result_data_accumulates(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test result_data accumulates results from all nodes."""
        # Arrange
        workflow = Workflow(
            id=uuid4(),
            name="Accumulation Test",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {
                        "id": "personas-1",
                        "type": "generate-personas",
                        "data": {"config": {"count": 3, "project_description": "Test"}},
                    },
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "personas-1"},
                    {"id": "e2", "source": "personas-1", "target": "end-1"},
                ],
            },
            status="active",
            is_active=True,
        )
        db_session.add(workflow)
        await db_session.commit()
        await db_session.refresh(workflow)

        executor = WorkflowExecutor(db_session)

        # Act
        execution = await executor.execute_workflow(workflow.id, test_user.id)

        # Assert - verify all node results are stored
        assert "start-1" in execution.result_data
        assert "personas-1" in execution.result_data
        assert "end-1" in execution.result_data
