"""
Unit tests dla WorkflowValidator - podstawowa walidacja DAG.

Testuje:
- Empty workflow validation (no nodes, single node)
- Valid DAG structures (simple, complex with branches, long linear)
- Cycle detection (Kahn's algorithm) - simple, complex, self-loops, nested
- Topological sort (valid order, cycle detection, empty graph)

Graph algorithms tested:
- Kahn's algorithm (cycle detection, topological sort)

Target coverage: 95%+ dla WorkflowValidator
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


# ==================== 3. CYCLE DETECTION TESTS (KAHN'S ALGORITHM) ====================


class TestCycleDetection:
    """Test suite dla cycle detection using Kahn's algorithm."""

    @pytest.mark.asyncio
    async def test_detect_cycle_simple(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test cycle detection: A → B → C → A."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Simple Cycle",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "A", "type": "start", "data": {}},
                    {"id": "B", "type": "generate-personas", "data": {}},
                    {"id": "C", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "A", "target": "B"},
                    {"id": "e2", "source": "B", "target": "C"},
                    {"id": "e3", "source": "C", "target": "A"},  # Creates cycle
                ],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert
        assert result.is_valid is False
        assert any("cykl" in err.lower() for err in result.errors)

    @pytest.mark.asyncio
    async def test_detect_cycle_complex(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test cycle in complex graph: start → A → B → C → B (cycle at B-C)."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Complex Cycle",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {"id": "A", "type": "generate-personas", "data": {}},
                    {"id": "B", "type": "create-survey", "data": {}},
                    {"id": "C", "type": "analyze-results", "data": {}},
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "A"},
                    {"id": "e2", "source": "A", "target": "B"},
                    {"id": "e3", "source": "B", "target": "C"},
                    {"id": "e4", "source": "C", "target": "B"},  # Cycle: B → C → B
                    {"id": "e5", "source": "C", "target": "end-1"},
                ],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert
        assert result.is_valid is False
        assert any("cykl" in err.lower() for err in result.errors)

    @pytest.mark.asyncio
    async def test_detect_self_loop(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test self-loop detection: A → A."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Self Loop",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "A", "type": "start", "data": {}},
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "A", "target": "A"},  # Self-loop
                    {"id": "e2", "source": "A", "target": "end-1"},
                ],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert
        assert result.is_valid is False
        assert any("cykl" in err.lower() for err in result.errors)

    @pytest.mark.asyncio
    async def test_detect_nested_cycles(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test detection of nested cycles: A → B → C → A, C → D → C."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Nested Cycles",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "A", "type": "start", "data": {}},
                    {"id": "B", "type": "generate-personas", "data": {}},
                    {"id": "C", "type": "create-survey", "data": {}},
                    {"id": "D", "type": "analyze-results", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "A", "target": "B"},
                    {"id": "e2", "source": "B", "target": "C"},
                    {"id": "e3", "source": "C", "target": "A"},  # Cycle 1: A-B-C-A
                    {"id": "e4", "source": "C", "target": "D"},
                    {"id": "e5", "source": "D", "target": "C"},  # Cycle 2: C-D-C
                ],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert
        assert result.is_valid is False
        assert any("cykl" in err.lower() for err in result.errors)


# ==================== 7. TOPOLOGICAL SORT TESTS ====================


class TestTopologicalSort:
    """Test suite dla topological sort algorithm."""

    def test_topological_sort_valid_dag(self):
        """Test topological sort returns valid execution order."""
        # Arrange
        validator = WorkflowValidator(None)  # No DB needed for this test

        nodes = [
            {"id": "start-1", "type": "start", "data": {}},
            {"id": "A", "type": "generate-personas", "data": {}},
            {"id": "B", "type": "create-survey", "data": {}},
            {"id": "end-1", "type": "end", "data": {}},
        ]
        edges = [
            {"id": "e1", "source": "start-1", "target": "A"},
            {"id": "e2", "source": "A", "target": "B"},
            {"id": "e3", "source": "B", "target": "end-1"},
        ]

        # Act
        topo_order = validator._topological_sort(nodes, edges)

        # Assert
        # Verify order: start should come before A, A before B, B before end
        assert topo_order.index("start-1") < topo_order.index("A")
        assert topo_order.index("A") < topo_order.index("B")
        assert topo_order.index("B") < topo_order.index("end-1")

    def test_topological_sort_with_branches(self):
        """Test topological sort with parallel branches."""
        # Arrange
        validator = WorkflowValidator(None)

        nodes = [
            {"id": "start", "type": "start"},
            {"id": "A", "type": "node1"},
            {"id": "B", "type": "node2"},
            {"id": "C", "type": "node3"},
            {"id": "end", "type": "end"},
        ]
        edges = [
            {"source": "start", "target": "A"},
            {"source": "start", "target": "B"},  # Parallel branch
            {"source": "A", "target": "C"},
            {"source": "B", "target": "C"},
            {"source": "C", "target": "end"},
        ]

        # Act
        topo_order = validator._topological_sort(nodes, edges)

        # Assert
        # Start should be first, end should be last
        assert topo_order[0] == "start"
        assert topo_order[-1] == "end"
        # C should come after both A and B
        assert topo_order.index("C") > topo_order.index("A")
        assert topo_order.index("C") > topo_order.index("B")

    def test_topological_sort_with_cycle_fails(self):
        """Test topological sort returns empty when cycle exists."""
        # Arrange
        validator = WorkflowValidator(None)

        nodes = [
            {"id": "A", "type": "start"},
            {"id": "B", "type": "generate-personas"},
            {"id": "C", "type": "end"},
        ]
        edges = [
            {"id": "e1", "source": "A", "target": "B"},
            {"id": "e2", "source": "B", "target": "C"},
            {"id": "e3", "source": "C", "target": "A"},  # Cycle
        ]

        # Act
        topo_order = validator._topological_sort(nodes, edges)

        # Assert - should return empty list or None when cycle detected
        assert topo_order == [] or topo_order is None

    def test_topological_sort_empty_graph(self):
        """Test topological sort with no nodes."""
        # Arrange
        validator = WorkflowValidator(None)

        # Act
        topo_order = validator._topological_sort([], [])

        # Assert
        assert topo_order == []
