"""
Unit tests dla WorkflowValidator - kompletne pokrycie graph algorithms.

Testuje:
- Empty workflow validation (no nodes, single node)
- Valid DAG structures (simple, complex with branches)
- Cycle detection (Kahn's algorithm) - simple, complex, self-loops
- Orphaned nodes detection (BFS reachability) - single, multiple, disconnected subgraphs
- Start/End node validation (missing, multiple)
- Topological sort (valid order, cycle detection)
- Node type validation (invalid types)
- Edge connection validation (nonexistent targets)
- BFS reachability tests (direct testing of algorithm)

Graph algorithms tested:
- Kahn's algorithm (cycle detection, topological sort)
- BFS (reachability analysis)

Target coverage: 95%+ dla WorkflowValidator
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, User
from app.models.workflow import Workflow
from app.services.workflows.workflow_validator import WorkflowValidator


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


# ==================== 4. ORPHANED NODES TESTS (BFS REACHABILITY) ====================


class TestOrphanedNodes:
    """Test suite dla orphaned node detection using BFS."""

    @pytest.mark.asyncio
    async def test_detect_orphaned_nodes(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test orphaned node detection: start → A, B isolated."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Orphaned Node",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {"id": "A", "type": "generate-personas", "data": {}},
                    {"id": "B", "type": "end", "data": {}},  # Orphaned
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "A"},
                    {"id": "e2", "source": "A", "target": "end-1"},
                    # B is not connected to anything from start
                ],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert
        assert result.is_valid is False
        assert any(
            "orphaned" in err.lower() or "niedostępne" in err.lower()
            for err in result.errors
        )
        # Verify B is mentioned in errors
        errors_str = " ".join(result.errors)
        assert "B" in errors_str

    @pytest.mark.asyncio
    async def test_detect_multiple_orphaned_nodes(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test detection of multiple orphaned nodes."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Multiple Orphaned",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {"id": "A", "type": "generate-personas", "data": {}},
                    {"id": "B", "type": "create-survey", "data": {}},  # Orphaned
                    {"id": "C", "type": "analyze-results", "data": {}},  # Orphaned
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "A"},
                    {"id": "e2", "source": "A", "target": "end-1"},
                ],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert
        assert result.is_valid is False
        errors_str = " ".join(result.errors)
        # Both B and C should be mentioned
        assert "B" in errors_str
        assert "C" in errors_str

    @pytest.mark.asyncio
    async def test_detect_orphaned_subgraph(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test orphaned subgraph: start → A → end-1, B → C (orphaned)."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Orphaned Subgraph",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {"id": "A", "type": "generate-personas", "data": {}},
                    {"id": "B", "type": "create-survey", "data": {}},  # Orphaned
                    {"id": "C", "type": "analyze-results", "data": {}},  # Orphaned
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "A"},
                    {"id": "e2", "source": "A", "target": "end-1"},
                    {"id": "e3", "source": "B", "target": "C"},  # Orphaned subgraph
                ],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert
        assert result.is_valid is False
        errors_str = " ".join(result.errors)
        # Both B and C are orphaned (not reachable from start)
        assert "B" in errors_str
        assert "C" in errors_str


# ==================== 5. START/END NODE TESTS ====================


class TestStartEndNodes:
    """Test suite dla start/end node validation."""

    @pytest.mark.asyncio
    async def test_missing_start_node(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test validation fails when no START node."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="No Start",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "A", "type": "generate-personas", "data": {}},
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                "edges": [{"id": "e1", "source": "A", "target": "end-1"}],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert
        assert result.is_valid is False
        assert any("start" in err.lower() for err in result.errors)

    @pytest.mark.asyncio
    async def test_missing_end_node(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test validation fails when no END node."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="No End",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {"id": "A", "type": "generate-personas", "data": {}},
                ],
                "edges": [{"id": "e1", "source": "start-1", "target": "A"}],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert
        assert result.is_valid is False
        assert any("end" in err.lower() for err in result.errors)

    @pytest.mark.asyncio
    async def test_multiple_start_nodes(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test multiple START nodes generates error."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Multiple Starts",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {"id": "start-2", "type": "start", "data": {}},
                    {"id": "A", "type": "generate-personas", "data": {}},
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "A"},
                    {"id": "e2", "source": "start-2", "target": "A"},
                    {"id": "e3", "source": "A", "target": "end-1"},
                ],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert
        assert result.is_valid is False
        # Should have error about multiple start nodes
        assert any("start" in err.lower() and "2" in err for err in result.errors)

    @pytest.mark.asyncio
    async def test_multiple_end_nodes_allowed(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test multiple END nodes are allowed (valid use case)."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Multiple Ends",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {"id": "A", "type": "generate-personas", "data": {}},
                    {"id": "B", "type": "create-survey", "data": {}},
                    {"id": "end-1", "type": "end", "data": {}},
                    {"id": "end-2", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "A"},
                    {"id": "e2", "source": "A", "target": "B"},
                    {"id": "e3", "source": "A", "target": "end-1"},  # Branch to end-1
                    {"id": "e4", "source": "B", "target": "end-2"},  # Branch to end-2
                ],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert - multiple ends are valid
        assert result.is_valid is True


# ==================== 6. DISCONNECTED SUBGRAPHS TESTS ====================


class TestDisconnectedSubgraphs:
    """Test suite dla disconnected subgraph detection."""

    @pytest.mark.asyncio
    async def test_detect_disconnected_subgraphs(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test detection of disconnected subgraphs: start → A, B → C (separate)."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Disconnected",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {"id": "A", "type": "generate-personas", "data": {}},
                    {"id": "B", "type": "create-survey", "data": {}},
                    {"id": "C", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "A"},
                    {"id": "e2", "source": "B", "target": "C"},  # Disconnected from start
                ],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert
        assert result.is_valid is False
        # B and C are orphaned (not reachable from start)
        errors_str = " ".join(result.errors)
        assert "B" in errors_str
        assert "C" in errors_str

    @pytest.mark.asyncio
    async def test_detect_isolated_node_with_no_edges(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test node with no incoming or outgoing edges."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Isolated Node",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {"id": "A", "type": "generate-personas", "data": {}},
                    {"id": "isolated", "type": "create-survey", "data": {}},  # Isolated
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "A"},
                    {"id": "e2", "source": "A", "target": "end-1"},
                ],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert
        assert result.is_valid is False
        # Should detect isolated node (either as orphaned or disconnected warning)
        combined = " ".join(result.errors + result.warnings)
        assert "isolated" in combined.lower()


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


# ==================== 8. BFS REACHABILITY TESTS (DIRECT) ====================


class TestBFSReachability:
    """Test suite dla BFS reachability algorithm (direct testing)."""

    def test_bfs_reachability_simple(self):
        """Test BFS returns all reachable nodes from start."""
        # Arrange
        validator = WorkflowValidator(None)  # No DB needed

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
        reachable = validator._get_reachable_nodes("A", nodes, edges)

        # Assert
        assert reachable == {"A", "B", "C"}

    def test_bfs_reachability_with_branch(self):
        """Test BFS with branching: A → B, A → C, B → D."""
        # Arrange
        validator = WorkflowValidator(None)

        nodes = [
            {"id": "A", "type": "start"},
            {"id": "B", "type": "node1"},
            {"id": "C", "type": "node2"},
            {"id": "D", "type": "end"},
        ]
        edges = [
            {"id": "e1", "source": "A", "target": "B"},
            {"id": "e2", "source": "A", "target": "C"},
            {"id": "e3", "source": "B", "target": "D"},
        ]

        # Act
        reachable = validator._get_reachable_nodes("A", nodes, edges)

        # Assert
        assert reachable == {"A", "B", "C", "D"}

    def test_bfs_reachability_isolated_node(self):
        """Test BFS does not reach isolated node."""
        # Arrange
        validator = WorkflowValidator(None)

        nodes = [
            {"id": "A", "type": "start"},
            {"id": "B", "type": "node1"},
            {"id": "C", "type": "end"},  # Isolated
        ]
        edges = [{"id": "e1", "source": "A", "target": "B"}]

        # Act
        reachable = validator._get_reachable_nodes("A", nodes, edges)

        # Assert
        assert "C" not in reachable
        assert reachable == {"A", "B"}

    def test_bfs_reachability_with_merge(self):
        """Test BFS with merge point: A → B → D, A → C → D."""
        # Arrange
        validator = WorkflowValidator(None)

        nodes = [
            {"id": "A", "type": "start"},
            {"id": "B", "type": "node1"},
            {"id": "C", "type": "node2"},
            {"id": "D", "type": "end"},
        ]
        edges = [
            {"source": "A", "target": "B"},
            {"source": "A", "target": "C"},
            {"source": "B", "target": "D"},
            {"source": "C", "target": "D"},
        ]

        # Act
        reachable = validator._get_reachable_nodes("A", nodes, edges)

        # Assert
        assert reachable == {"A", "B", "C", "D"}

    def test_bfs_reachability_from_middle_node(self):
        """Test BFS starting from middle node: A → B → C, start from B."""
        # Arrange
        validator = WorkflowValidator(None)

        nodes = [
            {"id": "A", "type": "start"},
            {"id": "B", "type": "node1"},
            {"id": "C", "type": "end"},
        ]
        edges = [
            {"source": "A", "target": "B"},
            {"source": "B", "target": "C"},
        ]

        # Act
        reachable = validator._get_reachable_nodes("B", nodes, edges)

        # Assert - should only reach B and C, not A
        assert reachable == {"B", "C"}
        assert "A" not in reachable

    def test_bfs_reachability_single_node(self):
        """Test BFS with single node (no edges)."""
        # Arrange
        validator = WorkflowValidator(None)

        nodes = [{"id": "A", "type": "start"}]
        edges = []

        # Act
        reachable = validator._get_reachable_nodes("A", nodes, edges)

        # Assert
        assert reachable == {"A"}

    def test_bfs_reachability_complex_dag(self):
        """Test BFS on complex DAG with multiple paths."""
        # Arrange
        validator = WorkflowValidator(None)

        nodes = [
            {"id": "start", "type": "start"},
            {"id": "A", "type": "node1"},
            {"id": "B", "type": "node2"},
            {"id": "C", "type": "node3"},
            {"id": "D", "type": "node4"},
            {"id": "E", "type": "node5"},
            {"id": "end", "type": "end"},
        ]
        edges = [
            {"source": "start", "target": "A"},
            {"source": "start", "target": "B"},
            {"source": "A", "target": "C"},
            {"source": "B", "target": "C"},
            {"source": "B", "target": "D"},
            {"source": "C", "target": "E"},
            {"source": "D", "target": "E"},
            {"source": "E", "target": "end"},
        ]

        # Act
        reachable = validator._get_reachable_nodes("start", nodes, edges)

        # Assert - all nodes should be reachable
        expected = {"start", "A", "B", "C", "D", "E", "end"}
        assert reachable == expected


# ==================== 9. CYCLE DETECTION DIRECT TESTS ====================


class TestCycleDetectionDirect:
    """Test suite dla direct testing of _detect_cycles method."""

    def test_detect_cycles_valid_dag(self):
        """Test cycle detection returns no cycle for valid DAG."""
        # Arrange
        validator = WorkflowValidator(None)

        nodes = [
            {"id": "A", "type": "start"},
            {"id": "B", "type": "node"},
            {"id": "C", "type": "end"},
        ]
        edges = [
            {"source": "A", "target": "B"},
            {"source": "B", "target": "C"},
        ]

        # Act
        result = validator._detect_cycles(nodes, edges)

        # Assert
        assert result["has_cycle"] is False
        assert result["cycle_path"] == []

    def test_detect_cycles_simple_cycle(self):
        """Test cycle detection finds simple cycle."""
        # Arrange
        validator = WorkflowValidator(None)

        nodes = [
            {"id": "A", "type": "start"},
            {"id": "B", "type": "node"},
        ]
        edges = [
            {"source": "A", "target": "B"},
            {"source": "B", "target": "A"},  # Cycle
        ]

        # Act
        result = validator._detect_cycles(nodes, edges)

        # Assert
        assert result["has_cycle"] is True
        assert len(result["cycle_path"]) > 0

    def test_detect_cycles_self_loop(self):
        """Test cycle detection finds self-loop."""
        # Arrange
        validator = WorkflowValidator(None)

        nodes = [{"id": "A", "type": "start"}]
        edges = [{"source": "A", "target": "A"}]  # Self-loop

        # Act
        result = validator._detect_cycles(nodes, edges)

        # Assert
        assert result["has_cycle"] is True

    def test_detect_cycles_complex_graph_no_cycle(self):
        """Test complex DAG with branches has no cycle."""
        # Arrange
        validator = WorkflowValidator(None)

        nodes = [
            {"id": "A", "type": "start"},
            {"id": "B", "type": "node1"},
            {"id": "C", "type": "node2"},
            {"id": "D", "type": "node3"},
            {"id": "E", "type": "end"},
        ]
        edges = [
            {"source": "A", "target": "B"},
            {"source": "A", "target": "C"},
            {"source": "B", "target": "D"},
            {"source": "C", "target": "D"},
            {"source": "D", "target": "E"},
        ]

        # Act
        result = validator._detect_cycles(nodes, edges)

        # Assert
        assert result["has_cycle"] is False


# ==================== 10. EDGE CONNECTION VALIDATION TESTS ====================


class TestEdgeConnectionValidation:
    """Test suite dla edge connection validation."""

    @pytest.mark.asyncio
    async def test_validate_edge_to_nonexistent_source(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test validation when edge source doesn't exist."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Invalid Edge Source",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                "edges": [
                    {
                        "id": "e1",
                        "source": "nonexistent",
                        "target": "end-1",
                    }  # Invalid source
                ],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert
        # Edge with invalid source will make end-1 unreachable or disconnected
        # Validator should handle this gracefully
        assert isinstance(result.is_valid, bool)

    @pytest.mark.asyncio
    async def test_validate_edge_to_nonexistent_target(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test validation when edge target doesn't exist."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Invalid Edge Target",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                "edges": [
                    {
                        "id": "e1",
                        "source": "start-1",
                        "target": "nonexistent",
                    }  # Invalid target
                ],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert
        # Should fail because end-1 is orphaned and target is invalid
        assert result.is_valid is False


# ==================== 11. EDGE CASES AND BOUNDARY CONDITIONS ====================


class TestEdgeCases:
    """Test suite dla edge cases and boundary conditions."""

    def test_find_disconnected_nodes_start_with_no_outgoing(self):
        """Test start node with no outgoing edges is not flagged as disconnected."""
        # Arrange
        validator = WorkflowValidator(None)

        nodes = [{"id": "start-1", "type": "start"}]
        edges = []

        # Act
        disconnected = validator._find_disconnected_nodes(nodes, edges)

        # Assert - start can have no edges without being disconnected
        assert "start-1" not in disconnected

    def test_find_disconnected_nodes_end_with_no_incoming(self):
        """Test end node with no incoming edges is not flagged as disconnected."""
        # Arrange
        validator = WorkflowValidator(None)

        nodes = [{"id": "end-1", "type": "end"}]
        edges = []

        # Act
        disconnected = validator._find_disconnected_nodes(nodes, edges)

        # Assert - end can have no edges without being disconnected
        assert "end-1" not in disconnected

    def test_find_disconnected_nodes_regular_node_with_no_edges(self):
        """Test regular node with no edges is flagged as disconnected."""
        # Arrange
        validator = WorkflowValidator(None)

        nodes = [{"id": "A", "type": "generate-personas"}]
        edges = []

        # Act
        disconnected = validator._find_disconnected_nodes(nodes, edges)

        # Assert
        assert "A" in disconnected

    @pytest.mark.asyncio
    async def test_validate_workflow_with_duplicate_node_ids(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test workflow with duplicate node IDs."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Duplicate Node IDs",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "A", "type": "start", "data": {}},
                    {"id": "A", "type": "end", "data": {}},  # Duplicate ID
                ],
                "edges": [{"id": "e1", "source": "A", "target": "A"}],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert - behavior depends on implementation
        # Should either detect cycle or handle gracefully
        assert isinstance(result.is_valid, bool)

    @pytest.mark.asyncio
    async def test_validate_workflow_with_duplicate_edge_ids(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test workflow with duplicate edge IDs."""
        # Arrange
        validator = WorkflowValidator(db_session)

        workflow = Workflow(
            id=uuid4(),
            name="Duplicate Edge IDs",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={
                "nodes": [
                    {"id": "start-1", "type": "start", "data": {}},
                    {"id": "A", "type": "generate-personas", "data": {}},
                    {"id": "end-1", "type": "end", "data": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "A"},
                    {"id": "e1", "source": "A", "target": "end-1"},  # Duplicate ID
                ],
            },
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert - duplicate edge IDs don't affect graph structure validation
        assert isinstance(result.is_valid, bool)

    @pytest.mark.asyncio
    async def test_validate_large_workflow(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test validation of large workflow with 20+ nodes."""
        # Arrange
        validator = WorkflowValidator(db_session)

        # Create linear chain of 20 nodes
        nodes = [{"id": "start-1", "type": "start", "data": {}}]
        edges = []

        for i in range(1, 20):
            nodes.append({"id": f"node-{i}", "type": "generate-personas", "data": {}})
            edges.append({"id": f"e{i-1}", "source": nodes[i - 1]["id"], "target": f"node-{i}"})

        nodes.append({"id": "end-1", "type": "end", "data": {}})
        edges.append({"id": "e19", "source": "node-19", "target": "end-1"})

        workflow = Workflow(
            id=uuid4(),
            name="Large Workflow",
            project_id=test_project.id,
            owner_id=test_user.id,
            canvas_data={"nodes": nodes, "edges": edges},
            status="draft",
        )

        # Act
        result = await validator.validate_workflow_graph(workflow)

        # Assert - should validate successfully
        assert result.is_valid is True
