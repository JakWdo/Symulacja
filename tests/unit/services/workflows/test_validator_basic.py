"""
Unit tests dla WorkflowValidator - basic validation tests.

Testuje:
- Empty workflow validation (no nodes, single node)
- Valid DAG structures (simple, complex with branches, long linear)

Target coverage: 95%+ dla WorkflowValidator (basic validation logic)
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, User
from app.models.workflow import Workflow
from app.services.workflows.validation import WorkflowValidator


# ==================== 1. EMPTY WORKFLOW TESTS ====================


class TestEmptyWorkflows:
    """Test suite dla empty/minimal workflows."""

    @pytest.mark.asyncio
    async def test_validate_empty_workflow(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test validation of workflow z no nodes."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Empty",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={"nodes": [], "edges": []},
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert
        assert result.is_valid is False
        assert len(result.errors) > 0
        # Should contain error about no nodes
        assert any(
            "co najmniej jeden node" in err.lower() or "musi zawierać" in err.lower()
            for err in result.errors
        )

    @pytest.mark.asyncio
    async def test_validate_single_node_no_edges(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test validation of workflow z single node and no edges."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Single Node",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [{"id": "start-1", "type": "start", "data": {}}],
                "edges": [],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert - single start node with no edges is invalid (no end node)
        assert result.is_valid is False
        assert any("end" in err.lower() for err in result.errors)


# ==================== 2. VALID DAG TESTS ====================


class TestValidDAGs:
    """Test suite dla valid directed acyclic graphs."""

    @pytest.mark.asyncio
    async def test_validate_valid_dag_structure(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test validation passes for valid DAG: start → personas → end."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Valid DAG",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {
                        "id": "personas-1",
                        "type": "generate-personas",
                        "data": {"config": {}},
                    },
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "personas-1"},
                    {"id": "e2", "source": "personas-1", "target": "end-1"},
                ],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_complex_valid_dag(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test validation for complex DAG with branches and merge."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Complex DAG",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {"id": "personas-1", "type": "generate-personas", "data": {}},
                    {"id": "survey-1", "type": "create-survey", "data": {}},
                    {"id": "focus-1", "type": "run-focus-group", "data": {}},
                    {"id": "analysis-1", "type": "analyze-results", "data": {}},
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "personas-1"},
                    {
                        "id": "e2",
                        "source": "personas-1",
                        "target": "survey-1",
                    },  # Branch 1
                    {
                        "id": "e3",
                        "source": "personas-1",
                        "target": "focus-1",
                    },  # Branch 2
                    {
                        "id": "e4",
                        "source": "survey-1",
                        "target": "analysis-1",
                    },  # Merge
                    {"id": "e5", "source": "focus-1", "target": "analysis-1"},  # Merge
                    {"id": "e6", "source": "analysis-1", "target": "end-1"},
                ],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_long_linear_dag(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test validation for long linear DAG: start → A → B → C → D → end."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Long Linear DAG",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {"id": "A", "type": "generate-personas", "data": {}},
                    {"id": "B", "type": "create-survey", "data": {}},
                    {"id": "C", "type": "run-focus-group", "data": {}},
                    {"id": "D", "type": "analyze-results", "data": {}},
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "A"},
                    {"id": "e2", "source": "A", "target": "B"},
                    {"id": "e3", "source": "B", "target": "C"},
                    {"id": "e4", "source": "C", "target": "D"},
                    {"id": "e5", "source": "D", "target": "end-1"},
                ],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0
