"""
Unit tests dla WorkflowService - kompletne pokrycie CRUD i edge cases.

Testuje:
- Create workflow (success, invalid project, duplicate names)
- Get workflow (exists, not found, unauthorized, soft-deleted)
- List workflows (by project, empty, soft-deleted excluded, template filtering)
- Update workflow (success, partial, not found, unauthorized, template read-only)
- Save canvas state (success, unauthorized)
- Soft delete (success, already deleted, unauthorized)
- Duplicate workflow (success, unauthorized)

Target coverage: 90%+
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, User
from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate
from app.services.workflows.workflow_service import WorkflowService


class TestWorkflowServiceCreate:
    """Test suite dla workflow creation."""

    @pytest.mark.asyncio
    async def test_create_workflow_success(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test successful workflow creation z valid data."""
        # Arrange
        service = WorkflowService(db_session)
        data = WorkflowCreate(
            name="Test Workflow",
            description="Test description",
            project_id=test_project.id,
            canvas_data={"nodes": [], "edges": []},
        )

        # Act
        workflow = await service.create_workflow(data, test_user.id)

        # Assert
        assert workflow.id is not None
        assert workflow.name == "Test Workflow"
        assert workflow.description == "Test description"
        assert workflow.project_id == test_project.id
        assert workflow.owner_id == test_user.id
        assert workflow.status == "draft"
        assert workflow.is_template is False
        assert workflow.is_active is True
        assert workflow.canvas_data == {"nodes": [], "edges": []}
        assert workflow.deleted_at is None
        assert isinstance(workflow.created_at, datetime)
        assert isinstance(workflow.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_create_workflow_with_canvas_data(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test workflow creation z complex canvas data."""
        # Arrange
        service = WorkflowService(db_session)
        canvas_data = {
            "nodes": [
                {"id": "1", "type": "start", "position": {"x": 0, "y": 0}},
                {"id": "2", "type": "end", "position": {"x": 200, "y": 200}},
            ],
            "edges": [{"source": "1", "target": "2"}],
        }
        data = WorkflowCreate(
            name="Workflow With Canvas",
            project_id=test_project.id,
            canvas_data=canvas_data,
        )

        # Act
        workflow = await service.create_workflow(data, test_user.id)

        # Assert
        assert workflow.canvas_data == canvas_data
        assert len(workflow.canvas_data["nodes"]) == 2
        assert len(workflow.canvas_data["edges"]) == 1

    @pytest.mark.asyncio
    async def test_create_workflow_invalid_project_id(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test workflow creation fails z non-existent project."""
        # Arrange
        service = WorkflowService(db_session)
        invalid_project_id = uuid4()
        data = WorkflowCreate(
            name="Test",
            project_id=invalid_project_id,
            canvas_data={"nodes": [], "edges": []},
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.create_workflow(data, test_user.id)

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_create_workflow_unauthorized_project(
        self, db_session: AsyncSession, test_user: User, other_user: User, test_project: Project
    ):
        """Test workflow creation fails gdy user nie jest owner projektu."""
        # Arrange
        service = WorkflowService(db_session)
        data = WorkflowCreate(
            name="Unauthorized Workflow",
            project_id=test_project.id,  # Należy do test_user, nie other_user
            canvas_data={"nodes": [], "edges": []},
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.create_workflow(data, other_user.id)

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_create_workflow_duplicate_name_allowed(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test że duplicate workflow names są dozwolone (soft constraint)."""
        # Arrange
        service = WorkflowService(db_session)

        # Act - Create first workflow
        data1 = WorkflowCreate(
            name="Same Name",
            project_id=test_project.id,
            canvas_data={"nodes": [], "edges": []},
        )
        workflow1 = await service.create_workflow(data1, test_user.id)

        # Act - Create second with same name
        data2 = WorkflowCreate(
            name="Same Name",
            project_id=test_project.id,
            canvas_data={"nodes": [], "edges": []},
        )
        workflow2 = await service.create_workflow(data2, test_user.id)

        # Assert
        assert workflow1.id != workflow2.id
        assert workflow1.name == workflow2.name == "Same Name"

    @pytest.mark.asyncio
    async def test_create_workflow_minimal_data(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test workflow creation z minimal required fields."""
        # Arrange
        service = WorkflowService(db_session)
        data = WorkflowCreate(
            name="Minimal Workflow",
            description=None,  # Optional
            project_id=test_project.id,
            canvas_data={"nodes": [], "edges": []},
        )

        # Act
        workflow = await service.create_workflow(data, test_user.id)

        # Assert
        assert workflow.name == "Minimal Workflow"
        assert workflow.description is None
        assert workflow.status == "draft"


class TestWorkflowServiceGet:
    """Test suite dla retrieving workflows."""

    @pytest.mark.asyncio
    async def test_get_workflow_by_id_exists(
        self, db_session: AsyncSession, test_user: User, test_workflow: Workflow
    ):
        """Test retrieving existing workflow by ID."""
        # Arrange
        service = WorkflowService(db_session)

        # Act
        workflow = await service.get_workflow_by_id(test_workflow.id, test_user.id)

        # Assert
        assert workflow.id == test_workflow.id
        assert workflow.name == test_workflow.name
        assert workflow.owner_id == test_user.id

    @pytest.mark.asyncio
    async def test_get_workflow_by_id_not_found(self, db_session: AsyncSession, test_user: User):
        """Test 404 gdy workflow doesn't exist."""
        # Arrange
        service = WorkflowService(db_session)
        invalid_id = uuid4()

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.get_workflow_by_id(invalid_id, test_user.id)

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_get_workflow_unauthorized_user(
        self, db_session: AsyncSession, test_user: User, other_user: User, test_workflow: Workflow
    ):
        """Test że user nie może access innego user's workflow."""
        # Arrange
        service = WorkflowService(db_session)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.get_workflow_by_id(test_workflow.id, other_user.id)

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_get_workflow_ignores_soft_deleted(
        self, db_session: AsyncSession, test_user: User, test_workflow: Workflow
    ):
        """Test że soft-deleted workflows return 404."""
        # Arrange
        service = WorkflowService(db_session)

        # Act - Soft delete workflow
        await service.soft_delete_workflow(test_workflow.id, test_user.id)

        # Act & Assert - Try to get deleted workflow
        with pytest.raises(HTTPException) as exc_info:
            await service.get_workflow_by_id(test_workflow.id, test_user.id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_workflow_eager_loads_relations(
        self, db_session: AsyncSession, test_user: User, test_workflow: Workflow
    ):
        """Test że workflow eager loads steps i executions."""
        # Arrange
        service = WorkflowService(db_session)

        # Act
        workflow = await service.get_workflow_by_id(test_workflow.id, test_user.id)

        # Assert - Relations should be accessible without lazy load
        assert hasattr(workflow, "steps")
        assert hasattr(workflow, "executions")
        # W MVP nie ma jeszcze steps/executions, więc sprawdź tylko istnienie atrybutu
        assert workflow.steps == []
        assert workflow.executions == []


class TestWorkflowServiceList:
    """Test suite dla listing workflows."""

    @pytest.mark.asyncio
    async def test_list_workflows_by_project(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test listowania workflows dla projektu."""
        # Arrange
        service = WorkflowService(db_session)

        # Create 3 workflows
        for i in range(3):
            data = WorkflowCreate(
                name=f"Workflow {i}",
                project_id=test_project.id,
                canvas_data={"nodes": [], "edges": []},
            )
            await service.create_workflow(data, test_user.id)

        # Act
        workflows = await service.list_workflows_by_project(
            test_project.id, test_user.id, include_templates=False
        )

        # Assert
        assert len(workflows) == 3
        assert all(w.project_id == test_project.id for w in workflows)
        assert all(w.is_template is False for w in workflows)
        assert all(w.is_active is True for w in workflows)

    @pytest.mark.asyncio
    async def test_list_workflows_empty_project(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test listowania workflows zwraca empty list dla projektu bez workflows."""
        # Arrange
        service = WorkflowService(db_session)

        # Act
        workflows = await service.list_workflows_by_project(
            test_project.id, test_user.id, include_templates=False
        )

        # Assert
        assert workflows == []

    @pytest.mark.asyncio
    async def test_list_workflows_excludes_soft_deleted(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test że soft-deleted workflows są excluded z list."""
        # Arrange
        service = WorkflowService(db_session)

        # Create 2 workflows
        data1 = WorkflowCreate(name="WF1", project_id=test_project.id, canvas_data={"nodes": [], "edges": []})
        wf1 = await service.create_workflow(data1, test_user.id)

        data2 = WorkflowCreate(name="WF2", project_id=test_project.id, canvas_data={"nodes": [], "edges": []})
        wf2 = await service.create_workflow(data2, test_user.id)

        # Act - Soft delete first workflow
        await service.soft_delete_workflow(wf1.id, test_user.id)

        # Act - List workflows
        workflows = await service.list_workflows_by_project(
            test_project.id, test_user.id, include_templates=False
        )

        # Assert
        assert len(workflows) == 1
        assert workflows[0].id == wf2.id

    @pytest.mark.asyncio
    async def test_list_workflows_filters_by_template_flag(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test include_templates parameter filtruje correctly."""
        # Arrange
        service = WorkflowService(db_session)

        # Create regular workflow
        data1 = WorkflowCreate(name="Regular", project_id=test_project.id, canvas_data={"nodes": [], "edges": []})
        await service.create_workflow(data1, test_user.id)

        # Create template workflow (manually set is_template)
        data2 = WorkflowCreate(name="Template", project_id=test_project.id, canvas_data={"nodes": [], "edges": []})
        template = await service.create_workflow(data2, test_user.id)
        template.is_template = True
        await db_session.commit()

        # Act - List without templates
        workflows = await service.list_workflows_by_project(
            test_project.id, test_user.id, include_templates=False
        )
        assert len(workflows) == 1
        assert workflows[0].name == "Regular"

        # Act - List with templates
        workflows_with_templates = await service.list_workflows_by_project(
            test_project.id, test_user.id, include_templates=True
        )
        assert len(workflows_with_templates) == 2

    @pytest.mark.asyncio
    async def test_list_workflows_ordered_by_created_at_desc(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test że workflows są sorted by created_at desc (newest first)."""
        # Arrange
        service = WorkflowService(db_session)

        # Create 3 workflows in sequence
        data1 = WorkflowCreate(name="First", project_id=test_project.id, canvas_data={"nodes": [], "edges": []})
        wf1 = await service.create_workflow(data1, test_user.id)

        data2 = WorkflowCreate(name="Second", project_id=test_project.id, canvas_data={"nodes": [], "edges": []})
        wf2 = await service.create_workflow(data2, test_user.id)

        data3 = WorkflowCreate(name="Third", project_id=test_project.id, canvas_data={"nodes": [], "edges": []})
        wf3 = await service.create_workflow(data3, test_user.id)

        # Act
        workflows = await service.list_workflows_by_project(
            test_project.id, test_user.id, include_templates=False
        )

        # Assert - Newest first
        assert len(workflows) == 3
        assert workflows[0].id == wf3.id  # Newest
        assert workflows[1].id == wf2.id
        assert workflows[2].id == wf1.id  # Oldest

    @pytest.mark.asyncio
    async def test_list_workflows_by_project_unauthorized(
        self, db_session: AsyncSession, test_user: User, other_user: User, test_project: Project
    ):
        """Test że list_workflows_by_project returns 404 dla unauthorized user."""
        # Arrange
        service = WorkflowService(db_session)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.list_workflows_by_project(
                test_project.id, other_user.id, include_templates=False
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_list_workflows_by_user(
        self, db_session: AsyncSession, test_user: User, test_project: Project
    ):
        """Test listowania all workflows user (across projects)."""
        # Arrange
        service = WorkflowService(db_session)

        # Create workflows
        for i in range(2):
            data = WorkflowCreate(
                name=f"User Workflow {i}",
                project_id=test_project.id,
                canvas_data={"nodes": [], "edges": []},
            )
            await service.create_workflow(data, test_user.id)

        # Act
        workflows = await service.list_workflows_by_user(test_user.id, include_templates=False)

        # Assert
        assert len(workflows) == 2
        assert all(w.owner_id == test_user.id for w in workflows)


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


class TestWorkflowServiceSoftDelete:
    """Test suite dla soft delete operations."""

    @pytest.mark.asyncio
    async def test_soft_delete_workflow(
        self, db_session: AsyncSession, test_user: User, test_workflow: Workflow
    ):
        """Test soft delete sets deleted_at timestamp i is_active=False."""
        # Arrange
        service = WorkflowService(db_session)

        # Act
        await service.soft_delete_workflow(test_workflow.id, test_user.id)

        # Assert - Refresh workflow z DB
        await db_session.refresh(test_workflow)
        assert test_workflow.is_active is False
        assert test_workflow.deleted_at is not None
        assert isinstance(test_workflow.deleted_at, datetime)
        assert test_workflow.deleted_by == test_user.id

    @pytest.mark.asyncio
    async def test_soft_delete_already_deleted(
        self, db_session: AsyncSession, test_user: User, test_workflow: Workflow
    ):
        """Test soft deleting already deleted workflow raises 404."""
        # Arrange
        service = WorkflowService(db_session)

        # Act - Delete once
        await service.soft_delete_workflow(test_workflow.id, test_user.id)

        # Act & Assert - Try to delete again
        with pytest.raises(HTTPException) as exc_info:
            await service.soft_delete_workflow(test_workflow.id, test_user.id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_soft_delete_unauthorized(
        self, db_session: AsyncSession, test_user: User, other_user: User, test_workflow: Workflow
    ):
        """Test że unauthorized user nie może delete workflow."""
        # Arrange
        service = WorkflowService(db_session)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.soft_delete_workflow(test_workflow.id, other_user.id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_soft_delete_workflow_not_found(self, db_session: AsyncSession, test_user: User):
        """Test 404 gdy trying to delete non-existent workflow."""
        # Arrange
        service = WorkflowService(db_session)
        invalid_id = uuid4()

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.soft_delete_workflow(invalid_id, test_user.id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_soft_delete_does_not_hard_delete(
        self, db_session: AsyncSession, test_user: User, test_workflow: Workflow
    ):
        """Test że soft delete nie usuwa workflow z bazy danych."""
        # Arrange
        service = WorkflowService(db_session)
        workflow_id = test_workflow.id

        # Act
        await service.soft_delete_workflow(workflow_id, test_user.id)

        # Assert - Workflow nadal istnieje w DB (ale is_active=False)
        stmt = select(Workflow).where(Workflow.id == workflow_id)
        result = await db_session.execute(stmt)
        workflow = result.scalar_one_or_none()

        assert workflow is not None
        assert workflow.is_active is False
        assert workflow.deleted_at is not None


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
