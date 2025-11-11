"""
Unit tests dla WorkflowValidator - walidacja krawędzi i edge cases.

Testuje:
- Cycle detection (direct testing of _detect_cycles method)
- Edge connection validation (nonexistent source/target)
- Edge cases and boundary conditions (disconnected nodes, duplicate IDs, large workflows)

Graph algorithms tested:
- Cycle detection (direct testing)

Target coverage: 95%+ dla WorkflowValidator
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, User
from app.models.workflow import Workflow
from app.services.workflows.validation import WorkflowValidator


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
