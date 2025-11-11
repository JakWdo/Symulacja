"""
API Endpoints dla Soft Delete Operations i Archiwizacji Projektów

Ten moduł zawiera endpointy związane z usuwaniem i przywracaniem projektów:
- GET /projects/{id}/delete-impact - Sprawdź wpływ usunięcia
- DELETE /projects/{id} - Soft delete projektu
- POST /projects/{id}/undo-delete - Przywracanie usuniętego projektu
- POST /projects/bulk-delete - Masowe usuwanie projektów
- GET /projects/archived - Lista usuniętych projektów

Podstawowe operacje CRUD znajdują się w project_crud.py
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from uuid import UUID

from app.db import get_db
from app.models import Project, User, Persona, FocusGroup, Survey, PersonaResponse, SurveyResponse
from app.api.dependencies import get_current_user, get_project_for_user
from app.schemas.project import (
    ProjectResponse,
    ProjectDeleteResponse,
    ProjectUndoDeleteResponse,
    ProjectDeleteImpactResponse,
    ProjectBulkDeleteRequest,
    ProjectBulkDeleteResponse,
)
from app.services.dashboard.cache_invalidation import invalidate_dashboard_cache

router = APIRouter()


@router.get("/projects/{project_id}/delete-impact", response_model=ProjectDeleteImpactResponse, tags=["Projects"])
async def get_project_delete_impact(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Sprawdź wpływ usunięcia projektu (cascade delete impact)

    Zwraca liczby entities które zostaną usunięte wraz z projektem:
    - Personas
    - Focus Groups
    - Surveys
    - Total Responses (focus group + survey responses)

    Ten endpoint jest używany przez frontend żeby pokazać ostrzeżenie
    przed usunięciem projektu, np: "Usunie 15 person, 8 focus groups, 3 ankiety"

    Args:
        project_id: UUID projektu
        db: DB session
        current_user: Authenticated user

    Returns:
        ProjectDeleteImpactResponse z licznikami

    Raises:
        HTTPException 404: Jeśli projekt nie istnieje
    """
    # Verify project exists and user has access (raises HTTPException if not)
    _ = await get_project_for_user(project_id, current_user, db)

    # Count personas
    personas_count_result = await db.execute(
        select(func.count(Persona.id)).where(Persona.project_id == project_id)
    )
    personas_count = personas_count_result.scalar() or 0

    # Count focus groups
    focus_groups_count_result = await db.execute(
        select(func.count(FocusGroup.id)).where(FocusGroup.project_id == project_id)
    )
    focus_groups_count = focus_groups_count_result.scalar() or 0

    # Count surveys
    surveys_count_result = await db.execute(
        select(func.count(Survey.id)).where(Survey.project_id == project_id)
    )
    surveys_count = surveys_count_result.scalar() or 0

    # Count total responses (PersonaResponse from focus groups)
    # PersonaResponse has focus_group_id, so we count where focus_group.project_id == project_id
    fg_responses_count_result = await db.execute(
        select(func.count(PersonaResponse.id))
        .join(FocusGroup, PersonaResponse.focus_group_id == FocusGroup.id)
        .where(FocusGroup.project_id == project_id)
    )
    fg_responses_count = fg_responses_count_result.scalar() or 0

    # Count survey responses
    survey_responses_count_result = await db.execute(
        select(func.count(SurveyResponse.id))
        .join(Survey, SurveyResponse.survey_id == Survey.id)
        .where(Survey.project_id == project_id)
    )
    survey_responses_count = survey_responses_count_result.scalar() or 0

    total_responses_count = fg_responses_count + survey_responses_count

    # Build warning message
    warning_parts = []
    if personas_count > 0:
        warning_parts.append(f"{personas_count} persona{'s' if personas_count != 1 else ''}")
    if focus_groups_count > 0:
        warning_parts.append(f"{focus_groups_count} focus group{'s' if focus_groups_count != 1 else ''}")
    if surveys_count > 0:
        warning_parts.append(f"{surveys_count} survey{'s' if surveys_count != 1 else ''}")

    if warning_parts:
        warning = f"Deleting this project will permanently remove: {', '.join(warning_parts)}."
        if total_responses_count > 0:
            warning += f" This includes {total_responses_count} response{'s' if total_responses_count != 1 else ''}."
    else:
        warning = "This project has no associated data. Safe to delete."

    return ProjectDeleteImpactResponse(
        project_id=project_id,
        personas_count=personas_count,
        focus_groups_count=focus_groups_count,
        surveys_count=surveys_count,
        total_responses_count=total_responses_count,
        warning=warning,
    )


@router.delete("/projects/{project_id}", response_model=ProjectDeleteResponse, tags=["Projects"])
async def soft_delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Usuń projekt (soft delete z możliwością restore)

    Soft delete oznacza że projekt nie jest faktycznie usuwany z bazy,
    tylko oznaczany jako nieaktywny z timestampem deleted_at. Projekt
    może być przywrócony przez 7 dni.

    Cascade soft delete: Wszystkie powiązane entities zostaną również
    oznaczone jako usunięte (is_active=False, deleted_at):
    - Personas
    - Focus Groups
    - Surveys

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
    from fastapi import HTTPException, status

    project = await get_project_for_user(project_id, current_user, db, include_inactive=True)

    # Check if already deleted
    if project.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project already deleted",
        )

    # Soft delete
    deleted_at = datetime.utcnow()
    permanent_delete_at = deleted_at + timedelta(days=7)  # Changed from 30 to 7 days

    project.is_active = False
    project.deleted_at = deleted_at
    project.deleted_by = current_user.id

    # CASCADE soft delete to all related entities
    # 1. Soft delete all personas in this project
    await db.execute(
        update(Persona)
        .where(Persona.project_id == project_id)
        .values(
            is_active=False,
            deleted_at=deleted_at,
            deleted_by=current_user.id,
        )
    )

    # 2. Soft delete all focus groups in this project
    await db.execute(
        update(FocusGroup)
        .where(FocusGroup.project_id == project_id)
        .values(
            is_active=False,
            deleted_at=deleted_at,
            deleted_by=current_user.id,
        )
    )

    # 3. Soft delete all surveys in this project
    await db.execute(
        update(Survey)
        .where(Survey.project_id == project_id)
        .values(
            is_active=False,
            deleted_at=deleted_at,
            deleted_by=current_user.id,
        )
    )

    await db.commit()

    # Invalidate dashboard cache
    await invalidate_dashboard_cache(current_user.id)

    return ProjectDeleteResponse(
        project_id=project_id,
        name=project.name,
        status="deleted",
        deleted_at=deleted_at,
        deleted_by=current_user.id,
        permanent_deletion_scheduled_at=permanent_delete_at,
        message=f"Project '{project.name}' and all related data (personas, focus groups, surveys) deleted successfully. Can be restored within 7 days.",
    )


@router.post("/projects/{project_id}/undo-delete", response_model=ProjectUndoDeleteResponse, tags=["Projects"])
async def undo_delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Przywróć usunięty projekt (undo delete)

    Przywraca projekt który został soft-deleted, o ile nie minęło 7 dni
    od usunięcia. Cascade restore: wszystkie powiązane entities (personas,
    focus groups, surveys) również zostaną przywrócone.

    Args:
        project_id: UUID projektu do przywrócenia
        db: Sesja bazy danych
        current_user: Authenticated user

    Returns:
        ProjectUndoDeleteResponse z informacją o restored_at, restored_by

    Raises:
        HTTPException 404: Jeśli projekt nie istnieje
        HTTPException 404: Jeśli projekt nie jest usunięty
        HTTPException 410: Jeśli minęło 7 dni od usunięcia (permanent deletion)
    """
    from fastapi import HTTPException, status

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

    # Check if 7-day window expired
    permanent_delete_deadline = project.deleted_at + timedelta(days=7)
    now = datetime.utcnow()
    if now > permanent_delete_deadline:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Project restore window expired (7 days passed). Project will be permanently deleted.",
            headers={
                "X-Deleted-At": project.deleted_at.isoformat(),
                "X-Permanent-Deletion-Date": permanent_delete_deadline.isoformat(),
            },
        )

    # Restore project
    project.is_active = True
    project.deleted_at = None
    project.deleted_by = None

    # CASCADE restore all related entities
    # 1. Restore all personas in this project
    await db.execute(
        update(Persona)
        .where(Persona.project_id == project_id)
        .where(Persona.is_active.is_(False))
        .values(
            is_active=True,
            deleted_at=None,
            deleted_by=None,
        )
    )

    # 2. Restore all focus groups in this project
    await db.execute(
        update(FocusGroup)
        .where(FocusGroup.project_id == project_id)
        .where(FocusGroup.is_active.is_(False))
        .values(
            is_active=True,
            deleted_at=None,
            deleted_by=None,
        )
    )

    # 3. Restore all surveys in this project
    await db.execute(
        update(Survey)
        .where(Survey.project_id == project_id)
        .where(Survey.is_active.is_(False))
        .values(
            is_active=True,
            deleted_at=None,
            deleted_by=None,
        )
    )

    await db.commit()

    # Invalidate dashboard cache
    await invalidate_dashboard_cache(current_user.id)

    return ProjectUndoDeleteResponse(
        project_id=project_id,
        name=project.name,
        status="active",
        restored_at=now,
        restored_by=current_user.id,
        message=f"Project '{project.name}' and all related data (personas, focus groups, surveys) restored successfully",
    )


@router.post("/projects/bulk-delete", response_model=ProjectBulkDeleteResponse, tags=["Projects"])
async def bulk_delete_projects(
    bulk_request: ProjectBulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Usuń wiele projektów jednocześnie (bulk soft delete z CASCADE)

    Soft delete oznacza że projekty nie są faktycznie usuwane z bazy,
    tylko oznaczane jako nieaktywne z timestampem deleted_at. Projekty
    mogą być przywrócone przez 7 dni.

    CASCADE soft delete: Wszystkie powiązane entities zostaną również
    oznaczone jako usunięte (is_active=False, deleted_at):
    - Personas
    - Focus Groups
    - Surveys

    Args:
        bulk_request: ProjectBulkDeleteRequest z listą project_ids i powodem
        db: Sesja bazy danych
        current_user: Authenticated user

    Returns:
        ProjectBulkDeleteResponse ze statystykami (deleted_count, cascade_deleted)

    Flow:
        1. Loop przez wszystkie project_ids
        2. Dla każdego projektu: weryfikuj ownership, soft delete + CASCADE
        3. Zbieraj statystyki (deleted projects + cascade counts)
        4. Zwróć response z undo_available_until (7 dni)

    Raises:
        HTTPException 404: Jeśli któryś z projektów nie istnieje lub brak dostępu
    """
    from fastapi import HTTPException

    deleted_at = datetime.utcnow()
    permanent_delete_at = deleted_at + timedelta(days=7)
    undo_deadline = deleted_at + timedelta(days=7)

    deleted_count = 0
    failed_count = 0
    failed_ids: list[UUID] = []

    # Cascade counters (suma dla wszystkich projektów)
    total_personas_deleted = 0
    total_focus_groups_deleted = 0
    total_surveys_deleted = 0

    # Loop przez wszystkie project_ids
    for project_id in bulk_request.project_ids:
        try:
            # Pobierz projekt i weryfikuj ownership
            project = await get_project_for_user(
                project_id,
                current_user,
                db,
                include_inactive=True,
            )

            # Sprawdź czy już usunięty
            if project.deleted_at is not None:
                failed_count += 1
                failed_ids.append(project_id)
                continue

            # Soft delete projektu
            project.is_active = False
            project.deleted_at = deleted_at
            project.deleted_by = current_user.id

            # CASCADE soft delete do powiązanych entities
            # 1. Soft delete all personas in this project
            personas_result = await db.execute(
                update(Persona)
                .where(Persona.project_id == project_id)
                .values(
                    is_active=False,
                    deleted_at=deleted_at,
                    deleted_by=current_user.id,
                )
            )
            total_personas_deleted += personas_result.rowcount

            # 2. Soft delete all focus groups in this project
            focus_groups_result = await db.execute(
                update(FocusGroup)
                .where(FocusGroup.project_id == project_id)
                .values(
                    is_active=False,
                    deleted_at=deleted_at,
                    deleted_by=current_user.id,
                )
            )
            total_focus_groups_deleted += focus_groups_result.rowcount

            # 3. Soft delete all surveys in this project
            surveys_result = await db.execute(
                update(Survey)
                .where(Survey.project_id == project_id)
                .values(
                    is_active=False,
                    deleted_at=deleted_at,
                    deleted_by=current_user.id,
                )
            )
            total_surveys_deleted += surveys_result.rowcount

            deleted_count += 1

        except HTTPException:
            # Projekt nie znaleziony lub brak dostępu
            failed_count += 1
            failed_ids.append(project_id)
        except Exception:
            # Niespodziewany błąd
            failed_count += 1
            failed_ids.append(project_id)

    # Commit wszystkich zmian naraz
    await db.commit()

    # Invalidate dashboard cache if any projects were deleted
    if deleted_count > 0:
        await invalidate_dashboard_cache(current_user.id)

    # Przygotuj komunikat
    if deleted_count == len(bulk_request.project_ids):
        message = f"Successfully deleted {deleted_count} project(s) and all related data. You can undo this action within 7 days."
    elif deleted_count > 0:
        message = f"Deleted {deleted_count} project(s), {failed_count} failed. Check failed_ids for details."
    else:
        message = "Failed to delete all projects. Check failed_ids for details."

    return ProjectBulkDeleteResponse(
        deleted_count=deleted_count,
        failed_count=failed_count,
        failed_ids=failed_ids,
        cascade_deleted={
            "personas": total_personas_deleted,
            "focus_groups": total_focus_groups_deleted,
            "surveys": total_surveys_deleted,
        },
        undo_available_until=undo_deadline,
        permanent_deletion_scheduled_at=permanent_delete_at,
        message=message,
    )


@router.get("/projects/archived", response_model=list[ProjectResponse], tags=["Projects"])
async def list_archived_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pobierz listę usuniętych projektów (archiwum) z ostatnich 7 dni

    Zwraca projekty które zostały soft-deleted i nadal mogą być przywrócone
    (restore window: 7 dni od deleted_at).

    Args:
        db: Sesja bazy danych
        current_user: Authenticated user

    Returns:
        List[ProjectResponse]: Lista usuniętych projektów (ordered by deleted_at DESC)

    Query:
        - is_active = False
        - deleted_at IS NOT NULL
        - deleted_at > now() - 7 days (restore window)
        - owner_id = current_user.id

    RBAC:
        - Użytkownik widzi tylko własne projekty
    """
    # Calculate restore window cutoff (7 days ago)
    restore_window_start = datetime.utcnow() - timedelta(days=7)

    # Query: pobierz usunięte projekty z ostatnich 7 dni
    result = await db.execute(
        select(Project)
        .where(
            Project.is_active.is_(False),
            Project.deleted_at.isnot(None),
            Project.deleted_at > restore_window_start,
            Project.owner_id == current_user.id,
        )
        .order_by(Project.deleted_at.desc())
    )
    projects = result.scalars().all()

    # Convert to ProjectResponse
    return [
        ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            target_demographics=project.target_demographics,
            target_sample_size=project.target_sample_size,
            owner_id=project.owner_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
        for project in projects
    ]
