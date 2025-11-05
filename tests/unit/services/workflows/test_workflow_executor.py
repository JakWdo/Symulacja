"""
Unit tests dla WorkflowExecutor - orchestracja wykonywania workflow.

Testuje:
- Execution orchestration (success, validation errors, error handling)
- Topological sort (linear, branching, complex graphs)
- Context passing między nodes
- Execution record creation i tracking statusu
- Error handling i recovery
- Decision node branching

Target coverage: 90%+ dla WorkflowExecutor
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, User
from app.models.workflow import Workflow, WorkflowExecution
from app.services.workflows.workflow_executor import WorkflowExecutor
from app.services.workflows.workflow_validator import ValidationResult


# ==================== 1. EXECUTION ORCHESTRATION TESTS ====================


class TestExecutionOrchestration:
    """Test suite dla orchestracji wykonywania workflow."""

    @pytest.mark.asyncio
    async def test_execute_workflow_success_simple(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test successful execution of simple workflow: start → end."""
        # Arrange
        workflow = Workflow(
            id=uuid4(),
            name="Simple Workflow",
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
        assert execution.id is not None
        assert execution.workflow_id == workflow.id
        assert execution.status == "completed"
        assert execution.started_at is not None
        assert execution.completed_at is not None
        assert execution.error_message is None
        assert execution.result_data is not None
        # Verify both nodes executed
        assert "start-1" in execution.result_data
        assert "end-1" in execution.result_data

    @pytest.mark.asyncio
    async def test_execute_workflow_validation_fails(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test execution aborts when validation fails (cycle detected)."""
        # Arrange - workflow z cycle
        workflow = Workflow(
            id=uuid4(),
            name="Invalid Workflow",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "a", "type": "start", "data": {}},
                    {"id": "b", "type": "generate-personas", "data": {}},
                    {"id": "c", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "a", "target": "b"},
                    {"id": "e2", "source": "b", "target": "c"},
                    {"id": "e3", "source": "c", "target": "b"},  # Cycle!
                ],
            },
            status="active",
            is_active=True,
        )
        db_session.add(workflow)
        await db_session.commit()

        executor = WorkflowExecutor(db_session)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await executor.execute_workflow(workflow.id, test_user.id)

        assert "validation" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_execute_workflow_creates_execution_record(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test that execution record is created and persisted in DB."""
        # Arrange
        workflow = Workflow(
            id=uuid4(),
            name="Test Workflow",
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

        # Assert - verify record exists in DB
        stmt = select(WorkflowExecution).where(WorkflowExecution.id == execution.id)
        result = await db_session.execute(stmt)
        db_execution = result.scalar_one()

        assert db_execution is not None
        assert db_execution.workflow_id == workflow.id
        assert db_execution.triggered_by == test_user.id
        assert db_execution.status == "completed"
        assert db_execution.started_at is not None
        assert db_execution.completed_at is not None

    @pytest.mark.asyncio
    async def test_execute_workflow_invalid_workflow_id(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test ValueError when workflow doesn't exist."""
        # Arrange
        executor = WorkflowExecutor(db_session)
        invalid_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await executor.execute_workflow(invalid_id, test_user.id)

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_execute_workflow_unauthorized_user(
        self,
        db_session: AsyncSession,
        test_user: User,
        other_user: User,
        test_project: Project,
    ):
        """Test ValueError when user doesn't own workflow."""
        # Arrange - workflow owned by test_user
        workflow = Workflow(
            id=uuid4(),
            name="Test Workflow",
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

        executor = WorkflowExecutor(db_session)

        # Act & Assert - try execute jako other_user
        with pytest.raises(ValueError) as exc_info:
            await executor.execute_workflow(workflow.id, other_user.id)

        assert "not found" in str(exc_info.value).lower() or "access denied" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_execute_workflow_inactive_workflow(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test ValueError when workflow is inactive (soft-deleted)."""
        # Arrange - soft-deleted workflow
        workflow = Workflow(
            id=uuid4(),
            name="Deleted Workflow",
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
            is_active=False,  # Soft-deleted
            deleted_at=datetime.now(timezone.utc),
        )
        db_session.add(workflow)
        await db_session.commit()

        executor = WorkflowExecutor(db_session)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await executor.execute_workflow(workflow.id, test_user.id)

        assert "not found" in str(exc_info.value).lower()


# ==================== 2. TOPOLOGICAL SORT TESTS ====================


class TestTopologicalSort:
    """Test suite dla topological sort algorithm (Kahn's algorithm)."""

    def test_topological_sort_linear(self, db_session: AsyncSession):
        """Test topological sort for linear workflow: A → B → C."""
        # Arrange
        executor = WorkflowExecutor(db_session)

        nodes = [
            {"id": "A", "type": "start"},
            {"id": "B", "type": "generate-personas"},
            {"id": "C", "type": "end"},
        ]
        edges = [
            {"id": "e1", "source": "A", "target": "B"},
            {"id": "e2", "source": "B", "target": "C"},
        ]

        # Act
        order = executor._topological_sort(nodes, edges)

        # Assert
        assert order == ["A", "B", "C"]

    def test_topological_sort_with_branch(self, db_session: AsyncSession):
        """Test topological sort with branch: A → B, A → C, B → D, C → D."""
        # Arrange
        executor = WorkflowExecutor(db_session)

        nodes = [
            {"id": "A", "type": "start"},
            {"id": "B", "type": "generate-personas"},
            {"id": "C", "type": "create-survey"},
            {"id": "D", "type": "end"},
        ]
        edges = [
            {"id": "e1", "source": "A", "target": "B"},
            {"id": "e2", "source": "A", "target": "C"},
            {"id": "e3", "source": "B", "target": "D"},
            {"id": "e4", "source": "C", "target": "D"},
        ]

        # Act
        order = executor._topological_sort(nodes, edges)

        # Assert
        # Valid orders: [A, B, C, D] or [A, C, B, D]
        assert order[0] == "A"
        assert order[3] == "D"
        assert set(order[1:3]) == {"B", "C"}

    def test_topological_sort_complex_graph(self, db_session: AsyncSession):
        """Test topological sort with complex dependencies."""
        # Arrange
        executor = WorkflowExecutor(db_session)

        nodes = [
            {"id": "A", "type": "start"},
            {"id": "B", "type": "generate-personas"},
            {"id": "C", "type": "run-focus-group"},
            {"id": "D", "type": "create-survey"},
            {"id": "E", "type": "analyze-results"},
            {"id": "F", "type": "end"},
        ]
        edges = [
            {"id": "e1", "source": "A", "target": "B"},
            {"id": "e2", "source": "B", "target": "C"},
            {"id": "e3", "source": "B", "target": "D"},
            {"id": "e4", "source": "C", "target": "E"},
            {"id": "e5", "source": "D", "target": "E"},
            {"id": "e6", "source": "E", "target": "F"},
        ]

        # Act
        order = executor._topological_sort(nodes, edges)

        # Assert
        assert order[0] == "A"
        assert order[1] == "B"
        assert order[-1] == "F"
        # C i D mogą być w dowolnej kolejności
        assert set(order[2:4]) == {"C", "D"}
        # E musi być przed F
        assert order.index("E") < order.index("F")

    def test_topological_sort_cycle_detection(self, db_session: AsyncSession):
        """Test that cycle detection raises ValueError."""
        # Arrange
        executor = WorkflowExecutor(db_session)

        nodes = [
            {"id": "A", "type": "start"},
            {"id": "B", "type": "generate-personas"},
            {"id": "C", "type": "end"},
        ]
        edges = [
            {"id": "e1", "source": "A", "target": "B"},
            {"id": "e2", "source": "B", "target": "C"},
            {"id": "e3", "source": "C", "target": "B"},  # Cycle: B → C → B
        ]

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            executor._topological_sort(nodes, edges)

        assert "cycle" in str(exc_info.value).lower()

    def test_topological_sort_single_node(self, db_session: AsyncSession):
        """Test topological sort with single node (no edges)."""
        # Arrange
        executor = WorkflowExecutor(db_session)

        nodes = [{"id": "A", "type": "start"}]
        edges = []

        # Act
        order = executor._topological_sort(nodes, edges)

        # Assert
        assert order == ["A"]

    def test_topological_sort_disconnected_nodes(self, db_session: AsyncSession):
        """Test topological sort with multiple disconnected components."""
        # Arrange
        executor = WorkflowExecutor(db_session)

        nodes = [
            {"id": "A", "type": "start"},
            {"id": "B", "type": "generate-personas"},
            {"id": "C", "type": "create-survey"},  # Disconnected
            {"id": "D", "type": "end"},
        ]
        edges = [
            {"id": "e1", "source": "A", "target": "B"},
            {"id": "e2", "source": "B", "target": "D"},
            # C jest disconnected (no edges)
        ]

        # Act
        order = executor._topological_sort(nodes, edges)

        # Assert - wszystkie nodes powinny być w order
        assert len(order) == 4
        assert set(order) == {"A", "B", "C", "D"}


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


# ==================== 4. NODE EXECUTION TESTS ====================


class TestNodeExecution:
    """Test suite dla individual node execution logic."""

    @pytest.mark.asyncio
    async def test_execute_node_not_implemented_type(
        self,
        db_session: AsyncSession,
    ):
        """Test NotImplementedError for unknown node type."""
        # Arrange
        executor = WorkflowExecutor(db_session)

        node = {
            "id": "unknown-1",
            "type": "unknown-type",
            "data": {"label": "Unknown Node"},
        }
        execution_context = {"project_id": uuid4(), "workflow_id": uuid4(), "user_id": uuid4(), "results": {}}

        # Act & Assert
        with pytest.raises(NotImplementedError) as exc_info:
            await executor._execute_node(node, execution_context)

        assert "unknown-type" in str(exc_info.value).lower()
        assert "not implemented" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_execute_node_with_label(
        self,
        db_session: AsyncSession,
    ):
        """Test node execution uses label for logging."""
        # Arrange
        executor = WorkflowExecutor(db_session)

        node = {
            "id": "start-1",
            "type": "start",
            "data": {"label": "Custom Start Label"},
        }
        execution_context = {
            "project_id": uuid4(),
            "workflow_id": uuid4(),
            "user_id": uuid4(),
            "results": {},
        }

        # Act
        result = await executor._execute_node(node, execution_context)

        # Assert - verify execution completed (no error means label was used correctly)
        assert result is not None
        assert "node_type" in result


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
