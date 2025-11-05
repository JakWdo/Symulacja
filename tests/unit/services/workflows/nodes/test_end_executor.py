"""
Unit tests dla EndExecutor - completion node workflow.

Testuje:
- Podstawowe wykonanie (mark completion)
- Zwracanie final context
- Liczenie wykonanych nodes
- Success message z config
- Multiple end nodes (różne ścieżki)

Target coverage: 100% dla EndExecutor
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.workflows.nodes.end import EndExecutor


class TestEndExecutor:
    """Test suite dla EndExecutor node."""

    @pytest.mark.asyncio
    async def test_execute_returns_completion_status(self, db_session: AsyncSession):
        """Test end executor returns completion status."""
        # Arrange
        executor = EndExecutor(db_session)

        workflow_id = uuid4()
        project_id = uuid4()

        node = {"id": "end-1", "type": "end", "data": {}}
        context = {
            "workflow_id": workflow_id,
            "project_id": project_id,
            "user_id": uuid4(),
            "results": {
                "start-1": {"status": "initialized"},
                "personas-1": {"persona_ids": ["id1", "id2"]},
            },
        }

        # Act
        result = await executor.execute(node, context)

        # Assert
        assert result is not None
        assert result["node_type"] == "end"
        assert result["status"] == "completed"
        assert result["workflow_id"] == str(workflow_id)
        assert result["total_nodes_executed"] == 2

    @pytest.mark.asyncio
    async def test_execute_counts_executed_nodes(self, db_session: AsyncSession):
        """Test end executor counts total executed nodes from results."""
        # Arrange
        executor = EndExecutor(db_session)

        workflow_id = uuid4()

        node = {"id": "end-1", "type": "end", "data": {}}
        context = {
            "workflow_id": workflow_id,
            "project_id": uuid4(),
            "results": {
                "start-1": {},
                "personas-1": {},
                "focus-group-1": {},
                "survey-1": {},
            },
        }

        # Act
        result = await executor.execute(node, context)

        # Assert
        assert result["total_nodes_executed"] == 4

    @pytest.mark.asyncio
    async def test_execute_with_empty_results(self, db_session: AsyncSession):
        """Test end executor with no previous results."""
        # Arrange
        executor = EndExecutor(db_session)

        workflow_id = uuid4()

        node = {"id": "end-1", "type": "end", "data": {}}
        context = {
            "workflow_id": workflow_id,
            "project_id": uuid4(),
            "results": {},
        }

        # Act
        result = await executor.execute(node, context)

        # Assert
        assert result["total_nodes_executed"] == 0

    @pytest.mark.asyncio
    async def test_execute_with_success_message_config(self, db_session: AsyncSession):
        """Test end executor with custom success message in config."""
        # Arrange
        executor = EndExecutor(db_session)

        workflow_id = uuid4()

        node = {
            "id": "end-1",
            "type": "end",
            "data": {
                "config": {
                    "success_message": "Workflow completed successfully! All personas generated and analyzed."
                }
            },
        }
        context = {
            "workflow_id": workflow_id,
            "project_id": uuid4(),
            "results": {"start-1": {}},
        }

        # Act
        result = await executor.execute(node, context)

        # Assert
        # Note: EndExecutor nie używa success_message w obecnej implementacji
        # ale powinna zwrócić completion status
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_with_label(self, db_session: AsyncSession):
        """Test end executor works with custom label."""
        # Arrange
        executor = EndExecutor(db_session)

        workflow_id = uuid4()

        node = {
            "id": "end-1",
            "type": "end",
            "data": {"label": "Completion Point"},
        }
        context = {
            "workflow_id": workflow_id,
            "project_id": uuid4(),
            "results": {},
        }

        # Act
        result = await executor.execute(node, context)

        # Assert
        assert result is not None
        assert result["node_type"] == "end"

    @pytest.mark.asyncio
    async def test_execute_multiple_end_nodes(self, db_session: AsyncSession):
        """Test multiple end nodes (different paths) produce consistent results."""
        # Arrange
        executor = EndExecutor(db_session)

        workflow_id = uuid4()
        context = {
            "workflow_id": workflow_id,
            "project_id": uuid4(),
            "results": {
                "start-1": {},
                "decision-1": {},
                "personas-1": {},
            },
        }

        node1 = {"id": "end-true", "type": "end", "data": {"label": "True Path End"}}
        node2 = {"id": "end-false", "type": "end", "data": {"label": "False Path End"}}

        # Act
        result1 = await executor.execute(node1, context)
        result2 = await executor.execute(node2, context)

        # Assert - both should mark completion
        assert result1["status"] == "completed"
        assert result2["status"] == "completed"
        assert result1["total_nodes_executed"] == result2["total_nodes_executed"]

    @pytest.mark.asyncio
    async def test_execute_preserves_workflow_id(self, db_session: AsyncSession):
        """Test end executor preserves workflow_id from context."""
        # Arrange
        executor = EndExecutor(db_session)

        workflow_id = uuid4()

        node = {"id": "end-1", "type": "end", "data": {}}
        context = {
            "workflow_id": workflow_id,
            "project_id": uuid4(),
            "results": {},
        }

        # Act
        result = await executor.execute(node, context)

        # Assert
        assert result["workflow_id"] == str(workflow_id)

    @pytest.mark.asyncio
    async def test_execute_missing_results_key(self, db_session: AsyncSession):
        """Test end executor handles missing 'results' key in context."""
        # Arrange
        executor = EndExecutor(db_session)

        workflow_id = uuid4()

        node = {"id": "end-1", "type": "end", "data": {}}
        context = {
            "workflow_id": workflow_id,
            "project_id": uuid4(),
            # No 'results' key
        }

        # Act
        result = await executor.execute(node, context)

        # Assert - should default to 0 nodes executed
        assert result["total_nodes_executed"] == 0
