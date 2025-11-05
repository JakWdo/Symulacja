"""Serwis CRUD dla workflow.

Ten serwis zawiera podstawowe operacje na workflow:
- Tworzenie nowych workflow
- Pobieranie workflow (z authorization check)
- Listowanie workflow per projekt
- Aktualizacja workflow (name, description, canvas_data, status)
- Quick save dla canvas state
- Soft delete workflow

Wszystkie operacje są asynchroniczne i używają SQLAlchemy async session.
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate

logger = logging.getLogger(__name__)


class WorkflowService:
    """Serwis CRUD dla workflow."""

    def __init__(self, db: AsyncSession):
        """Inicjalizuje serwis z database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db
        logger.debug("WorkflowService zainicjalizowany")

    async def create_workflow(self, data: WorkflowCreate, user_id: UUID) -> Workflow:
        """Tworzy nowy workflow.

        Args:
            data: Dane workflow do utworzenia (WorkflowCreate schema)
            user_id: UUID użytkownika tworzącego workflow (owner)

        Returns:
            Utworzony obiekt Workflow

        Raises:
            HTTPException: 400 jeśli project nie istnieje lub user nie ma dostępu
        """
        logger.info(f"Creating workflow '{data.name}' for user {user_id}")

        # 1. Weryfikuj że projekt istnieje i user ma do niego dostęp
        from app.models import Project  # Avoid circular import

        project_stmt = select(Project).where(and_(Project.id == data.project_id, Project.owner_id == user_id, Project.is_active))
        project_result = await self.db.execute(project_stmt)
        project = project_result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {data.project_id} not found or access denied")

        # 2. Utwórz workflow
        workflow = Workflow(
            name=data.name,
            description=data.description,
            project_id=data.project_id,
            owner_id=user_id,
            canvas_data=data.canvas_data,
            status="draft",  # Zawsze zaczynamy od draft
            is_template=False,  # Tylko templates mają True
            is_active=True,
        )

        self.db.add(workflow)
        await self.db.commit()
        await self.db.refresh(workflow)

        logger.info(f"Workflow {workflow.id} created successfully")
        return workflow

    async def get_workflow_by_id(self, workflow_id: UUID, user_id: UUID) -> Workflow:
        """Pobiera workflow po ID z authorization check.

        Args:
            workflow_id: UUID workflow
            user_id: UUID użytkownika (dla auth check)

        Returns:
            Workflow object

        Raises:
            HTTPException: 404 jeśli workflow nie istnieje lub brak dostępu
        """
        logger.debug(f"Fetching workflow {workflow_id} for user {user_id}")

        stmt = (
            select(Workflow)
            .where(
                and_(
                    Workflow.id == workflow_id,
                    Workflow.owner_id == user_id,  # Auth check
                    Workflow.is_active,  # Tylko aktywne (nie soft-deleted)
                )
            )
            .options(
                selectinload(Workflow.steps),  # Eager load steps
                selectinload(Workflow.executions),  # Eager load executions
            )
        )

        result = await self.db.execute(stmt)
        workflow = result.scalar_one_or_none()

        if not workflow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow {workflow_id} not found or access denied")

        return workflow

    async def list_workflows_by_project(self, project_id: UUID, user_id: UUID, include_templates: bool = False) -> list[Workflow]:
        """Listuje wszystkie workflow dla projektu.

        Args:
            project_id: UUID projektu
            user_id: UUID użytkownika (dla auth check)
            include_templates: Czy dołączyć workflow oznaczone jako templates (default: False)

        Returns:
            Lista obiektów Workflow (sorted by created_at desc)

        Raises:
            HTTPException: 404 jeśli projekt nie istnieje lub brak dostępu
        """
        logger.debug(f"Listing workflows for project {project_id}")

        # 1. Weryfikuj że projekt istnieje i user ma dostęp
        from app.models import Project

        project_stmt = select(Project).where(and_(Project.id == project_id, Project.owner_id == user_id))
        project_result = await self.db.execute(project_stmt)
        project = project_result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found or access denied")

        # 2. Pobierz workflows
        conditions = [Workflow.project_id == project_id, Workflow.is_active]

        if not include_templates:
            conditions.append(~Workflow.is_template)

        stmt = select(Workflow).where(and_(*conditions)).order_by(Workflow.created_at.desc())

        result = await self.db.execute(stmt)
        workflows = result.scalars().all()

        logger.info(f"Found {len(workflows)} workflows for project {project_id}")
        return list(workflows)

    async def list_workflows_by_user(self, user_id: UUID, include_templates: bool = False) -> list[Workflow]:
        """Listuje wszystkie workflow użytkownika (dla wszystkich projektów).

        Args:
            user_id: UUID użytkownika
            include_templates: Czy dołączyć workflow oznaczone jako templates (default: False)

        Returns:
            Lista obiektów Workflow (sorted by created_at desc)
        """
        logger.debug(f"Listing all workflows for user {user_id}")

        conditions = [Workflow.owner_id == user_id, Workflow.is_active]

        if not include_templates:
            conditions.append(~Workflow.is_template)

        stmt = select(Workflow).where(and_(*conditions)).order_by(Workflow.created_at.desc())

        result = await self.db.execute(stmt)
        workflows = result.scalars().all()

        logger.info(f"Found {len(workflows)} workflows for user {user_id}")
        return list(workflows)

    async def update_workflow(self, workflow_id: UUID, data: WorkflowUpdate, user_id: UUID) -> Workflow:
        """Aktualizuje workflow.

        Args:
            workflow_id: UUID workflow do aktualizacji
            data: Dane do aktualizacji (WorkflowUpdate schema - wszystkie pola opcjonalne)
            user_id: UUID użytkownika (dla auth check)

        Returns:
            Zaktualizowany obiekt Workflow

        Raises:
            HTTPException: 404 jeśli workflow nie istnieje lub brak dostępu
            HTTPException: 400 jeśli workflow jest template (nie można edytować)
        """
        logger.info(f"Updating workflow {workflow_id}")

        # 1. Pobierz workflow z auth check
        workflow = await self.get_workflow_by_id(workflow_id, user_id)

        # 2. Sprawdź czy nie jest template (templates są read-only)
        if workflow.is_template:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot update workflow template (read-only)")

        # 3. Aktualizuj pola (tylko jeśli podane)
        if data.name is not None:
            workflow.name = data.name

        if data.description is not None:
            workflow.description = data.description

        if data.canvas_data is not None:
            workflow.canvas_data = data.canvas_data

        if data.status is not None:
            workflow.status = data.status

        # 4. Zapisz zmiany
        await self.db.commit()
        await self.db.refresh(workflow)

        logger.info(f"Workflow {workflow_id} updated successfully")
        return workflow

    async def save_canvas_state(self, workflow_id: UUID, canvas_data: dict, user_id: UUID) -> Workflow:
        """Quick save dla canvas state (bez walidacji całego workflow).

        To jest optymalizacja dla frequent auto-save - tylko canvas_data.

        Args:
            workflow_id: UUID workflow
            canvas_data: Canvas state {nodes: [], edges: []}
            user_id: UUID użytkownika (dla auth check)

        Returns:
            Zaktualizowany obiekt Workflow

        Raises:
            HTTPException: 404 jeśli workflow nie istnieje lub brak dostępu
        """
        logger.debug(f"Quick saving canvas for workflow {workflow_id}")

        # Pobierz workflow z auth check
        workflow = await self.get_workflow_by_id(workflow_id, user_id)

        # Update tylko canvas_data
        workflow.canvas_data = canvas_data

        await self.db.commit()
        await self.db.refresh(workflow)

        return workflow

    async def soft_delete_workflow(self, workflow_id: UUID, user_id: UUID) -> None:
        """Soft delete workflow (ustawia is_active=False, deleted_at, deleted_by).

        Args:
            workflow_id: UUID workflow do usunięcia
            user_id: UUID użytkownika (dla auth check i deleted_by)

        Raises:
            HTTPException: 404 jeśli workflow nie istnieje lub brak dostępu
        """
        logger.info(f"Soft deleting workflow {workflow_id}")

        # Pobierz workflow z auth check
        workflow = await self.get_workflow_by_id(workflow_id, user_id)

        # Soft delete pattern
        workflow.is_active = False
        workflow.deleted_at = datetime.utcnow()
        workflow.deleted_by = user_id

        await self.db.commit()

        logger.info(f"Workflow {workflow_id} soft deleted")
