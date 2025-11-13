"""
API Endpoints dla Podstawowych Operacji CRUD na Projektach Badawczych

Ten moduł zawiera podstawowe operacje CRUD dla zarządzania projektami:
- POST /projects - Tworzenie nowego projektu
- GET /projects - Lista wszystkich aktywnych projektów
- GET /projects/{id} - Szczegóły konkretnego projektu
- PUT /projects/{id} - Aktualizacja projektu
- Snapshots - zarządzanie snapshotami zasobów projektu
- Export - eksport raportów PDF/DOCX projektu

Soft delete operations znajdują się w project_demographics.py
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List
from pydantic import BaseModel, Field

from app.db import get_db
from app.models import Project, User, ProjectSnapshot, Persona, Workflow, FocusGroup, Survey
from app.api.dependencies import get_current_user, get_project_for_user
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.export import PDFGenerator, DOCXGenerator

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


@router.get("/projects/{project_id}/export/pdf", tags=["Projects", "Export"])
async def export_project_pdf(
    project_id: UUID,
    include_full_personas: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Eksportuj raport projektu do PDF.

    Generuje kompletny raport PDF zawierający:
    - Opis projektu i cele badawcze
    - Statystyki demograficzne person
    - Przykładowe persony (top 10 lub wszystkie)
    - Kluczowe insighty z grup fokusowych
    - Agregaty odpowiedzi z ankiet
    - Podsumowanie

    Args:
        project_id: UUID projektu
        include_full_personas: Czy dołączyć wszystkie persony (domyślnie: False = tylko top 10)
        db: Sesja bazy danych
        current_user: Zalogowany użytkownik

    Returns:
        Plik PDF (application/pdf)

    Raises:
        HTTPException 404: Jeśli projekt nie istnieje lub użytkownik nie ma dostępu
        HTTPException 500: Jeśli generowanie PDF się nie powiodło
    """
    # Sprawdź dostęp do projektu
    await get_project_for_user(project_id, current_user, db)

    # Pobierz projekt z eager-loaded relationshipami
    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.personas),
            selectinload(Project.focus_groups),
            selectinload(Project.surveys),
        )
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Konwertuj modele ORM do dict
    project_data = {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "target_audience": project.target_audience,
        "research_objectives": project.research_objectives,
        "target_demographics": project.target_demographics,
        "target_sample_size": project.target_sample_size,
        "is_statistically_valid": project.is_statistically_valid,
        "personas": [
            {
                "id": str(p.id),
                "full_name": p.full_name,
                "name": p.full_name,
                "age": p.age,
                "gender": p.gender,
                "occupation": p.occupation,
                "education_level": p.education_level,
                "location": p.location,
                "values": p.values or [],
                "interests": p.interests or [],
            }
            for p in project.personas
        ],
        "focus_groups": [
            {
                "id": str(fg.id),
                "name": fg.name,
                "persona_ids": [str(pid) for pid in fg.persona_ids] if fg.persona_ids else [],
                "questions": fg.questions or [],
                "ai_summary": fg.ai_summary,
            }
            for fg in project.focus_groups
        ],
        "surveys": [
            {
                "id": str(s.id),
                "title": s.title,
                "status": s.status,
                "actual_responses": s.actual_responses,
                "target_responses": s.target_responses,
            }
            for s in project.surveys
        ],
    }

    # Określ tier użytkownika (TODO: pobrać z modelu User gdy będzie zaimplementowany)
    user_tier = "free"  # Placeholder

    try:
        # Generuj PDF
        pdf_generator = PDFGenerator()
        pdf_bytes = await pdf_generator.generate_project_pdf(
            project_data=project_data,
            user_tier=user_tier,
            include_full_personas=include_full_personas,
        )

        # Zwróć jako plik do pobrania
        filename = f"projekt_{project.name.replace(' ', '_')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd generowania PDF: {str(e)}")


@router.get("/projects/{project_id}/export/docx", tags=["Projects", "Export"])
async def export_project_docx(
    project_id: UUID,
    include_full_personas: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Eksportuj raport projektu do DOCX (Microsoft Word).

    Generuje kompletny raport DOCX zawierający:
    - Opis projektu i cele badawcze
    - Statystyki demograficzne person
    - Przykładowe persony (top 10 lub wszystkie)
    - Kluczowe insighty z grup fokusowych
    - Agregaty odpowiedzi z ankiet
    - Podsumowanie

    Args:
        project_id: UUID projektu
        include_full_personas: Czy dołączyć wszystkie persony (domyślnie: False = tylko top 10)
        db: Sesja bazy danych
        current_user: Zalogowany użytkownik

    Returns:
        Plik DOCX (application/vnd.openxmlformats-officedocument.wordprocessingml.document)

    Raises:
        HTTPException 404: Jeśli projekt nie istnieje lub użytkownik nie ma dostępu
        HTTPException 500: Jeśli generowanie DOCX się nie powiodło
    """
    # Sprawdź dostęp do projektu
    await get_project_for_user(project_id, current_user, db)

    # Pobierz projekt z eager-loaded relationshipami
    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.personas),
            selectinload(Project.focus_groups),
            selectinload(Project.surveys),
        )
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Konwertuj modele ORM do dict (ta sama logika co PDF)
    project_data = {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "target_audience": project.target_audience,
        "research_objectives": project.research_objectives,
        "target_demographics": project.target_demographics,
        "target_sample_size": project.target_sample_size,
        "is_statistically_valid": project.is_statistically_valid,
        "personas": [
            {
                "id": str(p.id),
                "full_name": p.full_name,
                "name": p.full_name,
                "age": p.age,
                "gender": p.gender,
                "occupation": p.occupation,
                "education_level": p.education_level,
                "location": p.location,
                "values": p.values or [],
                "interests": p.interests or [],
            }
            for p in project.personas
        ],
        "focus_groups": [
            {
                "id": str(fg.id),
                "name": fg.name,
                "persona_ids": [str(pid) for pid in fg.persona_ids] if fg.persona_ids else [],
                "questions": fg.questions or [],
                "ai_summary": fg.ai_summary,
            }
            for fg in project.focus_groups
        ],
        "surveys": [
            {
                "id": str(s.id),
                "title": s.title,
                "status": s.status,
                "actual_responses": s.actual_responses,
                "target_responses": s.target_responses,
            }
            for s in project.surveys
        ],
    }

    # Określ tier użytkownika
    user_tier = "free"  # Placeholder

    try:
        # Generuj DOCX
        docx_generator = DOCXGenerator()
        docx_bytes = await docx_generator.generate_project_docx(
            project_data=project_data,
            user_tier=user_tier,
            include_full_personas=include_full_personas,
        )

        # Zwróć jako plik do pobrania
        filename = f"projekt_{project.name.replace(' ', '_')}.docx"
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd generowania DOCX: {str(e)}")
