"""
Unit tests dla WorkflowValidator - walidacja węzłów.

Testuje:
- Orphaned nodes detection (BFS reachability) - single, multiple, orphaned subgraphs
- Start/End node validation (missing, multiple)
- Disconnected subgraphs detection
- BFS reachability tests (direct testing of algorithm)

Graph algorithms tested:
- BFS (reachability analysis)

Target coverage: 95%+ dla WorkflowValidator
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, User
from app.models.workflow import Workflow
from app.services.workflows.validation import WorkflowValidator


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
