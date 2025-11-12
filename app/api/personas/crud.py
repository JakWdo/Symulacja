"""
Persona API - CRUD Operations

CRUD endpoints for persona management (list, summary, delete, undo, bulk-delete).
"""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Persona, User
from app.api.dependencies import get_current_user, get_project_for_user, get_persona_for_user
from app.schemas.persona import PersonaResponse
from app.schemas.persona_details import (
    PersonaDeleteRequest,
    PersonaDeleteResponse,
    PersonaUndoDeleteResponse,
    PersonasSummaryResponse,
    PersonaBulkDeleteRequest,
    PersonaBulkDeleteResponse,
)
from app.services.personas import PersonaAuditService
from app.services.dashboard.cache_invalidation import invalidate_project_cache
from .helpers import _normalize_rag_citations


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/projects/{project_id}/personas/summary", response_model=PersonasSummaryResponse)
async def get_personas_summary(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Zwróć podsumowanie person projektu (liczebność, segmenty)."""
    await get_project_for_user(project_id, current_user, db)

    totals_row = await db.execute(
        select(
            func.count().label("total"),
            func.sum(case((Persona.is_active.is_(True), 1), else_=0)).label("active"),
            func.sum(case((Persona.is_active.is_(False), 1), else_=0)).label("archived"),
        ).where(Persona.project_id == project_id)
    )
    totals = totals_row.first()
    total_personas = int(totals.total or 0) if totals else 0
    active_personas = int(totals.active or 0) if totals else 0
    archived_personas = int(totals.archived or 0) if totals else 0

    segments_result = await db.execute(
        select(
            Persona.segment_id,
            Persona.segment_name,
            func.sum(case((Persona.is_active.is_(True), 1), else_=0)).label("active"),
            func.sum(case((Persona.is_active.is_(False), 1), else_=0)).label("archived"),
        )
        .where(Persona.project_id == project_id)
        .group_by(Persona.segment_id, Persona.segment_name)
    )

    segment_rows = segments_result.all()
    segments = [
        {
            "segment_id": row.segment_id,
            "segment_name": row.segment_name,
            "active_personas": int(row.active or 0),
            "archived_personas": int(row.archived or 0),
        }
        for row in segment_rows
    ]

    return PersonasSummaryResponse(
        project_id=project_id,
        total_personas=total_personas,
        active_personas=active_personas,
        archived_personas=archived_personas,
        segments=segments,
    )


@router.get("/projects/{project_id}/personas", response_model=list[PersonaResponse])
async def list_personas(
    project_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List personas for a project"""
    await get_project_for_user(project_id, current_user, db)
    result = await db.execute(
        select(Persona)
        .where(
            Persona.project_id == project_id,
            Persona.is_active.is_(True),
            Persona.deleted_at.is_(None),
        )
        .offset(skip)
        .limit(limit)
    )
    personas = result.scalars().all()

    # Normalizuj rag_citations dla każdej persony (backward compatibility)
    for persona in personas:
        if persona.rag_citations:
            persona.rag_citations = _normalize_rag_citations(persona.rag_citations)

    return personas


@router.delete("/personas/{persona_id}", response_model=PersonaDeleteResponse)
async def delete_persona(
    persona_id: UUID,
    delete_request: PersonaDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete persona z audit logging

    Args:
        persona_id: UUID persony do usunięcia
        delete_request: Powód usunięcia (reason + optional reason_detail)
        db: DB session
        current_user: Authenticated user

    Returns:
        PersonaDeleteResponse

    RBAC:
        - MVP: Wszyscy zalogowani użytkownicy mogą usuwać własne persony
        - Production: Tylko Admin może usuwać
        - 🔴 SECURITY TODO: Add RBAC check (@requires_role('admin'))
        - See: docs/TODO_TRACKING.md #1 (P0 Security)

    Audit:
        - Loguje delete action z reason w persona_audit_log
    """
    persona = await get_persona_for_user(persona_id, current_user, db)

    if persona.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Persona already deleted",
        )

    deleted_at = datetime.utcnow()
    undo_deadline = deleted_at + timedelta(days=7)
    permanent_delete_at = deleted_at + timedelta(days=7)

    # Miękkie usunięcie rekordu
    persona.is_active = False
    persona.deleted_at = deleted_at
    persona.deleted_by = current_user.id

    # Log delete action (audit trail)
    audit_service = PersonaAuditService()
    await audit_service.log_action(
        persona_id=persona_id,
        user_id=current_user.id,
        action="delete",
        details={
            "reason": delete_request.reason,
            "reason_detail": delete_request.reason_detail,
        },
        db=db,
    )

    await db.commit()

    # Invalidate dashboard cache
    await invalidate_project_cache(current_user.id, persona.project_id)

    return PersonaDeleteResponse(
        persona_id=persona_id,
        full_name=persona.full_name,
        status="deleted",
        deleted_at=deleted_at,
        deleted_by=current_user.id,
        undo_available_until=undo_deadline,
        permanent_deletion_scheduled_at=permanent_delete_at,
        message="Persona deleted successfully. You can undo this action within 7 days.",
    )


@router.post("/personas/{persona_id}/undo-delete", response_model=PersonaUndoDeleteResponse)
async def undo_delete_persona(
    persona_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Przywróć personę jeśli okno undo (7 dni) nie wygasło."""
    persona = await get_persona_for_user(
        persona_id,
        current_user,
        db,
        include_inactive=True,
    )

    if persona.deleted_at is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona is not deleted")

    undo_deadline = persona.deleted_at + timedelta(days=7)
    now = datetime.utcnow()
    if now > undo_deadline:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Restore window expired (7 days passed). Persona will be permanently deleted.",
            headers={
                "X-Undo-Deadline": undo_deadline.isoformat(),
                "X-Deleted-At": persona.deleted_at.isoformat(),
            },
        )

    persona.is_active = True
    persona.deleted_at = None
    persona.deleted_by = None

    audit_service = PersonaAuditService()
    await audit_service.log_action(
        persona_id=persona_id,
        user_id=current_user.id,
        action="undo_delete",
        details={"source": "undo"},
        db=db,
    )

    await db.commit()

    # Invalidate dashboard cache
    await invalidate_project_cache(current_user.id, persona.project_id)

    return PersonaUndoDeleteResponse(
        persona_id=persona_id,
        full_name=persona.full_name,
        status="active",
        restored_at=now,
        restored_by=current_user.id,
        message="Persona restored successfully",
    )


@router.post("/personas/bulk-delete", response_model=PersonaBulkDeleteResponse)
async def bulk_delete_personas(
    bulk_request: PersonaBulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Usuń wiele person jednocześnie (bulk soft delete z audit logging)

    Args:
        bulk_request: PersonaBulkDeleteRequest z listą persona_ids i powodem
        db: DB session
        current_user: Authenticated user

    Returns:
        PersonaBulkDeleteResponse ze statystykami (deleted_count, failed_count, failed_ids)

    Flow:
        1. Loop przez wszystkie persona_ids
        2. Dla każdej persony: weryfikuj ownership, soft delete, log w audit
        3. Zbieraj statystyki (successes vs failures)
        4. Zwróć response z undo_available_until (7 dni)

    RBAC:
        - MVP: Wszyscy zalogowani użytkownicy mogą usuwać własne persony
        - Production: Tylko Admin może usuwać
        - 🔴 SECURITY TODO: Add RBAC check (@requires_role('admin'))
        - See: docs/TODO_TRACKING.md #1 (P0 Security)

    Audit:
        - Loguje delete action dla każdej persony z reason w persona_audit_log
    """
    deleted_at = datetime.utcnow()
    undo_deadline = deleted_at + timedelta(days=7)

    deleted_count = 0
    failed_count = 0
    failed_ids: list[UUID] = []

    audit_service = PersonaAuditService()

    # Loop przez wszystkie persona_ids
    for persona_id in bulk_request.persona_ids:
        try:
            # Pobierz personę i weryfikuj ownership
            persona = await get_persona_for_user(persona_id, current_user, db)

            # Sprawdź czy już usunięta
            if persona.deleted_at is not None:
                failed_count += 1
                failed_ids.append(persona_id)
                continue

            # Soft delete
            persona.is_active = False
            persona.deleted_at = deleted_at
            persona.deleted_by = current_user.id

            # Log delete action (audit trail)
            await audit_service.log_action(
                persona_id=persona_id,
                user_id=current_user.id,
                action="delete",
                details={
                    "reason": bulk_request.reason,
                    "reason_detail": bulk_request.reason_detail,
                    "bulk_operation": True,
                },
                db=db,
            )

            deleted_count += 1

        except HTTPException:
            # Persona nie znaleziona lub brak dostępu
            failed_count += 1
            failed_ids.append(persona_id)
        except Exception as e:
            # Niespodziewany błąd
            logger.error(f"Error deleting persona {persona_id}: {str(e)}")
            failed_count += 1
            failed_ids.append(persona_id)

    # Commit wszystkich zmian naraz
    await db.commit()

    # Invalidate dashboard cache if any personas were deleted
    if deleted_count > 0:
        from app.services.dashboard.cache_invalidation import invalidate_dashboard_cache
        await invalidate_dashboard_cache(current_user.id)

    # Przygotuj komunikat
    if deleted_count == len(bulk_request.persona_ids):
        message = f"Successfully deleted {deleted_count} persona(s). You can undo this action within 7 days."
    elif deleted_count > 0:
        message = f"Deleted {deleted_count} persona(s), {failed_count} failed. Check failed_ids for details."
    else:
        message = "Failed to delete all personas. Check failed_ids for details."

    return PersonaBulkDeleteResponse(
        deleted_count=deleted_count,
        failed_count=failed_count,
        failed_ids=failed_ids,
        undo_available_until=undo_deadline,
        message=message,
    )
