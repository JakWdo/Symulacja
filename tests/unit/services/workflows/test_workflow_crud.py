"""
Unit tests dla WorkflowService - CRUD operations.

Testuje:
- Create workflow (success, invalid project, duplicate names, minimal data)
- Get workflow (exists, not found, unauthorized, soft-deleted)
- List workflows (by project, empty, soft-deleted excluded, template filtering, ordering)
- Soft delete (success, already deleted, unauthorized, not hard delete)

Target coverage: 90%+
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, User
from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowCreate
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
