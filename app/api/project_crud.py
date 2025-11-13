"""
API Endpoints dla Podstawowych Operacji CRUD na Projektach Badawczych

Ten moduł zawiera podstawowe operacje CRUD dla zarządzania projektami:
- POST /projects - Tworzenie nowego projektu
- GET /projects - Lista wszystkich aktywnych projektów
- GET /projects/{id} - Szczegóły konkretnego projektu
- PUT /projects/{id} - Aktualizacja projektu
- Snapshots - zarządzanie snapshotami zasobów projektu

Soft delete operations znajdują się w project_demographics.py
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
from typing import List
from pydantic import BaseModel, Field

from app.db import get_db
from app.models import Project, User, ProjectSnapshot, Persona, Workflow
from app.api.dependencies import get_current_user, get_project_for_user
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)

router = APIRouter()


@router.post("/projects", response_model=ProjectResponse, status_code=201, tags=["Projects"])
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


@router.get("/projects", response_model=list[ProjectResponse], tags=["Projects"])
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


@router.get("/projects/{project_id}", response_model=ProjectResponse, tags=["Projects"])
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


@router.put("/projects/{project_id}", response_model=ProjectResponse, tags=["Projects"])
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


# === Project Snapshots ===

class SnapshotCreate(BaseModel):
    """Schema dla tworzenia snapshotu."""
    name: str = Field(..., min_length=1, max_length=255)
    resource_type: str = Field(..., description="Typ zasobu (persona, workflow)")


class SnapshotResponse(BaseModel):
    """Schema dla response snapshotu."""
    id: UUID
    project_id: UUID
    name: str
    resource_type: str
    resource_ids: List[UUID]
    created_at: str

    class Config:
        from_attributes = True


@router.post("/projects/{project_id}/snapshots", response_model=SnapshotResponse, status_code=201, tags=["Snapshots"])
async def create_project_snapshot(
    project_id: UUID,
    data: SnapshotCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Tworzy snapshot zasobów projektu (immutable).

    Snapshot "zamraża" aktualny stan zasobów (personas, workflows) przypisanych
    do projektu, zapewniając reprodukowalność badań.

    Args:
        project_id: UUID projektu
        data: Nazwa i typ zasobu dla snapshotu
        db: Sesja bazy danych

    Returns:
        Utworzony snapshot z listą resource_ids

    Raises:
        HTTPException 404: Jeśli projekt nie istnieje
        HTTPException 404: Jeśli brak zasobów do snapshotowania
    """
    # Sprawdź dostęp do projektu
    project = await get_project_for_user(project_id, current_user, db)

    # Pobierz zasoby do snapshotowania
    resource_ids = []

    if data.resource_type == "persona":
        # Pobierz wszystkie aktywne persony projektu
        result = await db.execute(
            select(Persona.id).where(
                and_(
                    Persona.project_id == project_id,
                    Persona.is_active == True,
                )
            )
        )
        resource_ids = [row[0] for row in result.all()]

    elif data.resource_type == "workflow":
        # Pobierz wszystkie aktywne workflows projektu
        result = await db.execute(
            select(Workflow.id).where(
                and_(
                    Workflow.project_id == project_id,
                    Workflow.is_active == True,
                )
            )
        )
        resource_ids = [row[0] for row in result.all()]

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported resource_type: {data.resource_type}. Allowed: persona, workflow"
        )

    if not resource_ids:
        raise HTTPException(
            status_code=404,
            detail=f"No {data.resource_type} resources found for this project"
        )

    # Utwórz snapshot
    snapshot = ProjectSnapshot(
        project_id=project_id,
        name=data.name,
        resource_type=data.resource_type,
        resource_ids=[str(rid) for rid in resource_ids],  # JSONB as list of strings
    )

    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)

    return snapshot


@router.get("/projects/{project_id}/snapshots", response_model=List[SnapshotResponse], tags=["Snapshots"])
async def list_project_snapshots(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Listuje wszystkie snapshoty projektu.

    Args:
        project_id: UUID projektu
        db: Sesja bazy danych

    Returns:
        Lista snapshotów

    Raises:
        HTTPException 404: Jeśli projekt nie istnieje
    """
    # Sprawdź dostęp do projektu
    await get_project_for_user(project_id, current_user, db)

    # Pobierz snapshoty
    result = await db.execute(
        select(ProjectSnapshot)
        .where(ProjectSnapshot.project_id == project_id)
        .order_by(ProjectSnapshot.created_at.desc())
    )
    snapshots = result.scalars().all()

    return snapshots


@router.get("/projects/{project_id}/snapshots/{snapshot_id}", response_model=SnapshotResponse, tags=["Snapshots"])
async def get_project_snapshot(
    project_id: UUID,
    snapshot_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pobiera szczegóły snapshotu.

    Args:
        project_id: UUID projektu
        snapshot_id: UUID snapshotu
        db: Sesja bazy danych

    Returns:
        Szczegóły snapshotu

    Raises:
        HTTPException 404: Jeśli projekt lub snapshot nie istnieje
    """
    # Sprawdź dostęp do projektu
    await get_project_for_user(project_id, current_user, db)

    # Pobierz snapshot
    result = await db.execute(
        select(ProjectSnapshot).where(
            and_(
                ProjectSnapshot.id == snapshot_id,
                ProjectSnapshot.project_id == project_id,
            )
        )
    )
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return snapshot
