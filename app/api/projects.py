"""
API Endpoints dla Projektów Badawczych

Ten moduł zawiera CRUD endpoints dla zarządzania projektami:
- POST /projects - Tworzenie nowego projektu
- GET /projects - Lista wszystkich projektów
- GET /projects/{id} - Szczegóły konkretnego projektu
- PUT /projects/{id} - Aktualizacja projektu
- DELETE /projects/{id} - Usunięcie projektu (soft delete)
- POST /projects/{id}/undo-delete - Przywracanie usuniętego projektu
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.db import get_db
from app.models import Project, User
from app.api.dependencies import get_current_user, get_project_for_user
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ProjectDeleteResponse,
    ProjectUndoDeleteResponse,
)

router = APIRouter()


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Utwórz nowy projekt badawczy

    Projekt to kontener na:
    - Persony (generowane zgodnie z target_demographics)
    - Grupy fokusowe (dyskusje z personami)
    - Wyniki walidacji statystycznej

    Args:
        project: Dane nowego projektu (name, description, target_demographics, target_sample_size)
        db: Sesja bazy danych

    Returns:
        Utworzony projekt z ID i timestampami

    Raises:
        HTTPException 422: Jeśli dane są niepoprawne (walidacja Pydantic)
    """
    db_project = Project(
        name=project.name,
        description=project.description,
        target_audience=project.target_audience,
        research_objectives=project.research_objectives,
        additional_notes=project.additional_notes,
        target_demographics=project.target_demographics,  # JSON z rozkładami
        target_sample_size=project.target_sample_size,
        owner_id=current_user.id,
    )

    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)

    return db_project


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pobierz listę wszystkich aktywnych projektów

    Paginacja:
    - skip: Ile projektów pominąć (dla paginacji)
    - limit: Maksymalna liczba projektów do zwrócenia

    Args:
        skip: Offset dla paginacji (domyślnie 0)
        limit: Limit wyników (domyślnie 100, max 100)
        db: Sesja bazy danych

    Returns:
        Lista projektów (tylko is_active=True)
    """
    result = await db.execute(
        select(Project)
        .where(
            Project.is_active.is_(True),
            Project.owner_id == current_user.id,
            Project.deleted_at.is_(None),  # Hide soft-deleted projects
        )
        .offset(skip)
        .limit(limit)
    )
    projects = result.scalars().all()
    return projects


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pobierz szczegóły konkretnego projektu

    Args:
        project_id: UUID projektu
        db: Sesja bazy danych

    Returns:
        Szczegóły projektu

    Raises:
        HTTPException 404: Jeśli projekt nie istnieje
    """
    project = await get_project_for_user(project_id, current_user, db)
    return project


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Zaktualizuj istniejący projekt

    Wszystkie pola są opcjonalne - tylko podane pola zostaną zaktualizowane.
    Pola null w ProjectUpdate są ignorowane.

    Args:
        project_id: UUID projektu do aktualizacji
        project_update: Nowe wartości pól (wszystkie opcjonalne)
        db: Sesja bazy danych

    Returns:
        Zaktualizowany projekt

    Raises:
        HTTPException 404: Jeśli projekt nie istnieje
    """
    project = await get_project_for_user(project_id, current_user, db, include_inactive=True)

    # Zaktualizuj tylko podane pola (partial update)
    if project_update.name is not None:
        project.name = project_update.name
    if project_update.description is not None:
        project.description = project_update.description
    if project_update.target_audience is not None:
        project.target_audience = project_update.target_audience
    if project_update.research_objectives is not None:
        project.research_objectives = project_update.research_objectives
    if project_update.additional_notes is not None:
        project.additional_notes = project_update.additional_notes
    if project_update.target_demographics is not None:
        project.target_demographics = project_update.target_demographics
    if project_update.target_sample_size is not None:
        project.target_sample_size = project_update.target_sample_size

    await db.commit()
    await db.refresh(project)

    return project


@router.delete("/projects/{project_id}", response_model=ProjectDeleteResponse)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Usuń projekt (soft delete z możliwością restore)

    Soft delete oznacza że projekt nie jest faktycznie usuwany z bazy,
    tylko oznaczany jako nieaktywny z timestampem deleted_at. Projekt
    może być przywrócony przez 30 dni.

    Cascade soft delete: Wszystkie persony powiązane z projektem zostaną
    również oznaczone jako usunięte (is_active=False, deleted_at).

    Args:
        project_id: UUID projektu do usunięcia
        db: Sesja bazy danych
        current_user: Authenticated user

    Returns:
        ProjectDeleteResponse z informacją o deleted_at, permanent_deletion_scheduled_at

    Raises:
        HTTPException 404: Jeśli projekt nie istnieje
        HTTPException 409: Jeśli projekt jest już usunięty
    """
    project = await get_project_for_user(project_id, current_user, db, include_inactive=True)

    # Check if already deleted
    if project.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project already deleted",
        )

    # Soft delete
    deleted_at = datetime.utcnow()
    permanent_delete_at = deleted_at + timedelta(days=30)

    project.is_active = False
    project.deleted_at = deleted_at
    project.deleted_by = current_user.id

    await db.commit()

    return ProjectDeleteResponse(
        project_id=project_id,
        name=project.name,
        status="deleted",
        deleted_at=deleted_at,
        deleted_by=current_user.id,
        permanent_deletion_scheduled_at=permanent_delete_at,
        message=f"Project '{project.name}' deleted successfully. Can be restored within 30 days.",
    )


@router.post("/projects/{project_id}/undo-delete", response_model=ProjectUndoDeleteResponse)
async def undo_delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Przywróć usunięty projekt (undo delete)

    Przywraca projekt który został soft-deleted, o ile nie minęło 30 dni
    od usunięcia.

    Args:
        project_id: UUID projektu do przywrócenia
        db: Sesja bazy danych
        current_user: Authenticated user

    Returns:
        ProjectUndoDeleteResponse z informacją o restored_at, restored_by

    Raises:
        HTTPException 404: Jeśli projekt nie istnieje
        HTTPException 404: Jeśli projekt nie jest usunięty
        HTTPException 410: Jeśli minęło 30 dni od usunięcia (permanent deletion)
    """
    project = await get_project_for_user(
        project_id,
        current_user,
        db,
        include_inactive=True,
    )

    # Check if project is deleted
    if project.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project is not deleted",
        )

    # Check if 30-day window expired
    permanent_delete_deadline = project.deleted_at + timedelta(days=30)
    now = datetime.utcnow()
    if now > permanent_delete_deadline:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Project restore window expired (30 days passed). Project will be permanently deleted.",
            headers={
                "X-Deleted-At": project.deleted_at.isoformat(),
                "X-Permanent-Deletion-Date": permanent_delete_deadline.isoformat(),
            },
        )

    # Restore project
    project.is_active = True
    project.deleted_at = None
    project.deleted_by = None

    await db.commit()

    return ProjectUndoDeleteResponse(
        project_id=project_id,
        name=project.name,
        status="active",
        restored_at=now,
        restored_by=current_user.id,
        message=f"Project '{project.name}' restored successfully",
    )
