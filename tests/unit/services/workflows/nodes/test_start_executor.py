"""
Unit tests dla StartExecutor - entry point node workflow.

Testuje:
- Podstawowe wykonanie (inicjalizacja kontekstu)
- Logowanie rozpoczęcia workflow
- Zwracanie metadanych (workflow_id, project_id)
- Brak modyfikacji istniejącego kontekstu

Target coverage: 100% dla StartExecutor
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.workflows.nodes.start import StartExecutor


class TestStartExecutor:
    """Test suite dla StartExecutor node."""

    @pytest.mark.asyncio
    async def test_execute_returns_metadata(self, db_session: AsyncSession):
        """Test start executor returns workflow metadata."""
        # Arrange
        executor = StartExecutor(db_session)

        workflow_id = uuid4()
        project_id = uuid4()
        user_id = uuid4()

        node = {"id": "start-1", "type": "start", "data": {}}
        context = {
            "workflow_id": workflow_id,
            "project_id": project_id,
            "user_id": user_id,
            "results": {},
        }

        # Act
        result = await executor.execute(node, context)

        # Assert
        assert result is not None
        assert result["node_type"] == "start"
        assert result["status"] == "initialized"
        assert result["workflow_id"] == str(workflow_id)
        assert result["project_id"] == str(project_id)

    @pytest.mark.asyncio
    async def test_execute_does_not_modify_context(self, db_session: AsyncSession):
        """Test start executor doesn't modify existing context."""
        # Arrange
        executor = StartExecutor(db_session)

        workflow_id = uuid4()
        project_id = uuid4()
        user_id = uuid4()

        node = {"id": "start-1", "type": "start", "data": {}}
        context = {
            "workflow_id": workflow_id,
            "project_id": project_id,
            "user_id": user_id,
            "results": {"existing_key": "existing_value"},
        }

        original_context = context.copy()

        # Act
        result = await executor.execute(node, context)

        # Assert - context should be unchanged
        assert context["workflow_id"] == original_context["workflow_id"]
        assert context["project_id"] == original_context["project_id"]
        assert context["user_id"] == original_context["user_id"]
        assert context["results"]["existing_key"] == "existing_value"

    @pytest.mark.asyncio
    async def test_execute_with_label(self, db_session: AsyncSession):
        """Test start executor works with custom label."""
        # Arrange
        executor = StartExecutor(db_session)

        workflow_id = uuid4()
        project_id = uuid4()

        node = {
            "id": "start-1",
            "type": "start",
            "data": {"label": "Custom Start Point"},
        }
        context = {
            "workflow_id": workflow_id,
            "project_id": project_id,
            "user_id": uuid4(),
            "results": {},
        }

        # Act
        result = await executor.execute(node, context)

        # Assert - should execute successfully regardless of label
        assert result is not None
        assert result["node_type"] == "start"

    @pytest.mark.asyncio
    async def test_execute_minimal_context(self, db_session: AsyncSession):
        """Test start executor requires minimal context (workflow_id, project_id)."""
        # Arrange
        executor = StartExecutor(db_session)

        workflow_id = uuid4()
        project_id = uuid4()

        node = {"id": "start-1", "type": "start", "data": {}}
        context = {
            "workflow_id": workflow_id,
            "project_id": project_id,
        }

        # Act
        result = await executor.execute(node, context)

        # Assert
        assert result is not None
        assert result["workflow_id"] == str(workflow_id)
        assert result["project_id"] == str(project_id)

    @pytest.mark.asyncio
    async def test_execute_multiple_calls_consistent(self, db_session: AsyncSession):
        """Test multiple executions produce consistent results."""
        # Arrange
        executor = StartExecutor(db_session)

        workflow_id = uuid4()
        project_id = uuid4()

        node = {"id": "start-1", "type": "start", "data": {}}
        context = {
            "workflow_id": workflow_id,
            "project_id": project_id,
            "user_id": uuid4(),
            "results": {},
        }

        # Act
        result1 = await executor.execute(node, context)
        result2 = await executor.execute(node, context)

        # Assert - should produce identical results
        assert result1["node_type"] == result2["node_type"]
        assert result1["status"] == result2["status"]
        assert result1["workflow_id"] == result2["workflow_id"]
        assert result1["project_id"] == result2["project_id"]
