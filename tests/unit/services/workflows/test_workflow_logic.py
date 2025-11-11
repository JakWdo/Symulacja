"""
Unit tests dla WorkflowService - business logic operations.

Testuje:
- Update workflow (success, partial, not found, unauthorized, template read-only, status changes)
- Save canvas state (success, complex data, unauthorized, not found)
- Edge cases (empty canvas, long name/description, no-op updates, multiple projects)

Target coverage: 90%+
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, User
from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate
from app.services.workflows.workflow_service import WorkflowService


class TestWorkflowServiceUpdate:
    """Test suite dla updating workflows."""

    @pytest.mark.asyncio
    async def test_update_workflow_success(
        self, db_session: AsyncSession, test_user: User, test_workflow: Workflow
    ):
        """Test successful workflow update."""
        # Arrange
        service = WorkflowService(db_session)
        original_updated_at = test_workflow.updated_at

        update_data = WorkflowUpdate(
            name="Updated Name",
            description="Updated description",
            status="active",
        )

        # Act
        updated = await service.update_workflow(test_workflow.id, update_data, test_user.id)

        # Assert
        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"
        assert updated.status == "active"
        assert updated.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_update_workflow_partial_update(
        self, db_session: AsyncSession, test_user: User, test_workflow: Workflow
    ):
        """Test updating tylko niektóre fields."""
        # Arrange
        service = WorkflowService(db_session)
        original_description = test_workflow.description
        original_status = test_workflow.status

        update_data = WorkflowUpdate(name="New Name Only")

        # Act
        updated = await service.update_workflow(test_workflow.id, update_data, test_user.id)

        # Assert
        assert updated.name == "New Name Only"
        assert updated.description == original_description  # Unchanged
        assert updated.status == original_status  # Unchanged

    @pytest.mark.asyncio
    async def test_update_workflow_canvas_data(
        self, db_session: AsyncSession, test_user: User, test_workflow: Workflow
    ):
        """Test updating canvas_data."""
        # Arrange
        service = WorkflowService(db_session)
        new_canvas = {
            "nodes": [
                {"id": "1", "type": "start", "position": {"x": 0, "y": 0}},
                {"id": "2", "type": "end", "position": {"x": 200, "y": 200}},
            ],
            "edges": [{"source": "1", "target": "2"}],
        }

        update_data = WorkflowUpdate(canvas_data=new_canvas)

        # Act
        updated = await service.update_workflow(test_workflow.id, update_data, test_user.id)

        # Assert
        assert updated.canvas_data == new_canvas

    @pytest.mark.asyncio
    async def test_update_workflow_not_found(self, db_session: AsyncSession, test_user: User):
        """Test 404 gdy updating non-existent workflow."""
        # Arrange
        service = WorkflowService(db_session)
        invalid_id = uuid4()

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.update_workflow(invalid_id, WorkflowUpdate(name="Test"), test_user.id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_workflow_unauthorized(
        self, db_session: AsyncSession, test_user: User, other_user: User, test_workflow: Workflow
    ):
        """Test 403/404 gdy unauthorized user tries to update."""
        # Arrange
        service = WorkflowService(db_session)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.update_workflow(test_workflow.id, WorkflowUpdate(name="Hack"), other_user.id)

        # Note: get_workflow_by_id returns 404 for unauthorized, not 403
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_workflow_template_read_only(
        self, db_session: AsyncSession, test_user: User, test_template_workflow: Workflow
    ):
        """Test że templates są read-only (cannot update)."""
        # Arrange
        service = WorkflowService(db_session)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.update_workflow(
                test_template_workflow.id, WorkflowUpdate(name="Updated Template"), test_user.id
            )

        assert exc_info.value.status_code == 400
        assert "template" in str(exc_info.value.detail).lower()
        assert "read-only" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_update_workflow_status_change(
        self, db_session: AsyncSession, test_user: User, test_workflow: Workflow
    ):
        """Test changing workflow status (draft -> active -> archived)."""
        # Arrange
        service = WorkflowService(db_session)

        # Act - draft -> active
        updated = await service.update_workflow(test_workflow.id, WorkflowUpdate(status="active"), test_user.id)
        assert updated.status == "active"

        # Act - active -> archived
        updated = await service.update_workflow(test_workflow.id, WorkflowUpdate(status="archived"), test_user.id)
        assert updated.status == "archived"


class TestWorkflowServiceSaveCanvasState:
    """Test suite dla quick canvas state saving."""

    @pytest.mark.asyncio
    async def test_save_canvas_state_success(
        self, db_session: AsyncSession, test_user: User, test_workflow: Workflow
    ):
        """Test saving canvas data."""
        # Arrange
        service = WorkflowService(db_session)
        original_updated_at = test_workflow.updated_at

        new_canvas = {
            "nodes": [
                {"id": "1", "type": "start", "position": {"x": 0, "y": 0}},
                {"id": "2", "type": "end", "position": {"x": 200, "y": 200}},
            ],
            "edges": [{"source": "1", "target": "2"}],
        }

        # Act
        updated = await service.save_canvas_state(test_workflow.id, new_canvas, test_user.id)

        # Assert
        assert updated.canvas_data == new_canvas
        assert updated.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_save_canvas_state_complex_data(
        self, db_session: AsyncSession, test_user: User, test_workflow: Workflow
    ):
        """Test saving complex canvas z multiple nodes i edges."""
        # Arrange
        service = WorkflowService(db_session)

        complex_canvas = {
            "nodes": [
                {"id": "1", "type": "start", "position": {"x": 0, "y": 0}, "data": {}},
                {"id": "2", "type": "generate-personas", "position": {"x": 200, "y": 0}, "data": {"count": 20}},
                {"id": "3", "type": "run-focus-group", "position": {"x": 400, "y": 0}, "data": {"topics": ["Q1"]}},
                {"id": "4", "type": "end", "position": {"x": 600, "y": 0}, "data": {}},
            ],
            "edges": [
                {"id": "e1-2", "source": "1", "target": "2"},
                {"id": "e2-3", "source": "2", "target": "3"},
                {"id": "e3-4", "source": "3", "target": "4"},
            ],
        }

        # Act
        updated = await service.save_canvas_state(test_workflow.id, complex_canvas, test_user.id)

        # Assert
        assert len(updated.canvas_data["nodes"]) == 4
        assert len(updated.canvas_data["edges"]) == 3

    @pytest.mark.asyncio
    async def test_save_canvas_state_unauthorized(
        self, db_session: AsyncSession, test_user: User, other_user: User, test_workflow: Workflow
    ):
        """Test że unauthorized user nie może save canvas state."""
        # Arrange
        service = WorkflowService(db_session)
        new_canvas = {"nodes": [], "edges": []}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.save_canvas_state(test_workflow.id, new_canvas, other_user.id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_save_canvas_state_not_found(self, db_session: AsyncSession, test_user: User):
        """Test 404 gdy workflow doesn't exist."""
        # Arrange
        service = WorkflowService(db_session)
        invalid_id = uuid4()
        new_canvas = {"nodes": [], "edges": []}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.save_canvas_state(invalid_id, new_canvas, test_user.id)

        assert exc_info.value.status_code == 404


class TestWorkflowServiceEdgeCases:
    """Test suite dla edge cases i unusual scenarios."""

    @pytest.mark.asyncio
    async def test_workflow_with_empty_canvas_data(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test creating workflow z empty canvas data."""
        # Arrange
        service = WorkflowService(db_session)
        data = WorkflowCreate(
            name="Empty Canvas Workflow",
            project_id=test_project.id,
            canvas_data={"nodes": [], "edges": []},
        )

        # Act
        workflow = await service.create_workflow(data, test_user.id)

        # Assert
        assert workflow.canvas_data == {"nodes": [], "edges": []}

    @pytest.mark.asyncio
    async def test_workflow_with_long_name(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test workflow creation z long name (near 255 char limit)."""
        # Arrange
        service = WorkflowService(db_session)
        long_name = "A" * 250  # Close to 255 limit
        data = WorkflowCreate(
            name=long_name,
            project_id=test_project.id,
            canvas_data={"nodes": [], "edges": []},
        )

        # Act
        workflow = await service.create_workflow(data, test_user.id)

        # Assert
        assert workflow.name == long_name
        assert len(workflow.name) == 250

    @pytest.mark.asyncio
    async def test_workflow_with_long_description(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test workflow creation z long description."""
        # Arrange
        service = WorkflowService(db_session)
        long_description = "Description " * 100  # Long text
        data = WorkflowCreate(
            name="Workflow",
            description=long_description,
            project_id=test_project.id,
            canvas_data={"nodes": [], "edges": []},
        )

        # Act
        workflow = await service.create_workflow(data, test_user.id)

        # Assert
        assert workflow.description == long_description

    @pytest.mark.asyncio
    async def test_update_workflow_to_same_values(
        self, db_session: AsyncSession, test_user: User, test_workflow: Workflow
    ):
        """Test updating workflow do same values (no-op update)."""
        # Arrange
        service = WorkflowService(db_session)
        original_name = test_workflow.name

        update_data = WorkflowUpdate(name=original_name)

        # Act
        updated = await service.update_workflow(test_workflow.id, update_data, test_user.id)

        # Assert
        assert updated.name == original_name

    @pytest.mark.asyncio
    async def test_list_workflows_multiple_projects(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test że workflows są correctly scoped do projektu."""
        # Arrange
        service = WorkflowService(db_session)

        # Create 2 projects
        project1 = Project(
            id=uuid4(),
            owner_id=test_user.id,
            name="Project 1",
            target_sample_size=20,
            is_active=True,
        )
        project2 = Project(
            id=uuid4(),
            owner_id=test_user.id,
            name="Project 2",
            target_sample_size=20,
            is_active=True,
        )
        db_session.add_all([project1, project2])
        await db_session.commit()

        # Create workflows for each project
        data1 = WorkflowCreate(name="WF P1", project_id=project1.id, canvas_data={"nodes": [], "edges": []})
        await service.create_workflow(data1, test_user.id)

        data2 = WorkflowCreate(name="WF P2", project_id=project2.id, canvas_data={"nodes": [], "edges": []})
        await service.create_workflow(data2, test_user.id)

        # Act - List workflows for project1
        workflows_p1 = await service.list_workflows_by_project(project1.id, test_user.id, False)
        workflows_p2 = await service.list_workflows_by_project(project2.id, test_user.id, False)

        # Assert
        assert len(workflows_p1) == 1
        assert len(workflows_p2) == 1
        assert workflows_p1[0].project_id == project1.id
        assert workflows_p2[0].project_id == project2.id
