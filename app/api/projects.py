"""
API Endpoints dla Projektów Badawczych

Ten moduł zawiera CRUD endpoints dla zarządzania projektami:
- POST /projects - Tworzenie nowego projektu
- GET /projects - Lista wszystkich projektów
- GET /projects/{id} - Szczegóły konkretnego projektu
- PUT /projects/{id} - Aktualizacja projektu
- DELETE /projects/{id} - Usunięcie projektu (soft delete)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.db import get_db
from app.models import Project, User
from app.api.dependencies import get_current_user, get_project_for_user
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

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


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Usuń projekt (soft delete)

    Soft delete oznacza że projekt nie jest faktycznie usuwany z bazy,
    tylko oznaczany jako nieaktywny (is_active=False). Dane pozostają
    w bazie dla celów audytu.

    Cascade delete: Wszystkie persony i grupy fokusowe powiązane z projektem
    zostaną również usunięte (ON DELETE CASCADE w SQL).

    Args:
        project_id: UUID projektu do usunięcia
        db: Sesja bazy danych

    Returns:
        None (204 No Content)

    Raises:
        HTTPException 404: Jeśli projekt nie istnieje
    """
    project = await get_project_for_user(project_id, current_user, db, include_inactive=True)

    # Miękkie usunięcie – ustaw is_active na False zamiast usuwać z bazy
    project.is_active = False
    await db.commit()

    return None
