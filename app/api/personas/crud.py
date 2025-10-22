"""
API Endpoints - Persona CRUD Operations

Podstawowe operacje CRUD dla person:
- GET /projects/{project_id}/personas - lista person projektu (z paginacją)
- GET /projects/{project_id}/personas/summary - statystyki i segmenty
- GET /personas/{persona_id} - pojedyncza persona
- DELETE /personas/{persona_id} - soft delete persony (z audit log)
- POST /personas/{persona_id}/undo-delete - przywróć usuniętą personę (30s window)
"""

import logging
from datetime import datetime, timedelta
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Persona, User
from app.services.personas import PersonaAuditService
from app.api.dependencies import get_current_user, get_project_for_user, get_persona_for_user
from app.schemas.persona import PersonaResponse
from app.schemas.persona_details import (
    PersonaDeleteRequest,
    PersonaDeleteResponse,
    PersonaUndoDeleteResponse,
    PersonasSummaryResponse,
)

# Import utility functions
from .utils import _normalize_rag_citations

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


@router.get("/projects/{project_id}/personas", response_model=List[PersonaResponse])
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


@router.get("/personas/{persona_id}", response_model=PersonaResponse)
async def get_persona(
    persona_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific persona"""
    persona = await get_persona_for_user(persona_id, current_user, db)

    # Normalizuj rag_citations (backward compatibility)
    if persona.rag_citations:
        persona.rag_citations = _normalize_rag_citations(persona.rag_citations)

    return persona


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
        - Production: Tylko Admin może usuwać (TODO: add RBAC check)

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
    undo_deadline = deleted_at + timedelta(seconds=30)
    permanent_delete_at = deleted_at + timedelta(days=90)

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

    return PersonaDeleteResponse(
        persona_id=persona_id,
        full_name=persona.full_name,
        status="deleted",
        deleted_at=deleted_at,
        deleted_by=current_user.id,
        undo_available_until=undo_deadline,
        permanent_deletion_scheduled_at=permanent_delete_at,
        message="Persona deleted successfully. You can undo this action within 30 seconds.",
    )


@router.post("/personas/{persona_id}/undo-delete", response_model=PersonaUndoDeleteResponse)
async def undo_delete_persona(
    persona_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Przywróć personę jeśli okno undo (30s) nie wygasło."""
    persona = await get_persona_for_user(
        persona_id,
        current_user,
        db,
        include_inactive=True,
    )

    if persona.deleted_at is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona is not deleted")

    undo_deadline = persona.deleted_at + timedelta(seconds=30)
    now = datetime.utcnow()
    if now > undo_deadline:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Undo window expired. Persona can be restored from Archived view.",
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

    return PersonaUndoDeleteResponse(
        persona_id=persona_id,
        full_name=persona.full_name,
        status="active",
        restored_at=now,
        restored_by=current_user.id,
        message="Persona restored successfully",
    )
