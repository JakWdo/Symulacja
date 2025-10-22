"""
API Endpoints - Persona Details & Export

Szczegółowe widoki persony i eksport danych:
- GET /personas/{persona_id}/details - pełny detail view (MVP)
- POST /personas/{persona_id}/actions/export - eksport persony do JSON

Detail view zawiera:
- Base persona data (demographics, psychographics)
- Needs and pains (JTBD, desired outcomes, pain points - opcjonalne)
- RAG insights (z rag_context_details)
- Audit log (last 20 actions)
"""

import logging
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.services.personas import PersonaAuditService
from app.services.personas_details import PersonaDetailsService
from app.api.dependencies import get_current_user, get_persona_for_user
from app.schemas.persona_details import (
    PersonaDetailsResponse,
    PersonaExportRequest,
    PersonaExportResponse,
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)


@router.get("/personas/{persona_id}/details", response_model=PersonaDetailsResponse)
async def get_persona_details(
    persona_id: UUID,
    force_refresh: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pobierz pełny detail view persony (MVP)

    Pełny widok szczegółowy persony z:
    - Base persona data (demographics, psychographics)
    - Needs and pains (JTBD, desired outcomes, pain points - opcjonalne)
    - RAG insights (z rag_context_details)
    - Audit log (last 20 actions)

    Note: KPI snapshot i customer journey zostały usunięte z modelu.
    Dla KPI metrics użyj PersonaKPIService, dla journey - PersonaJourneyService.

    Args:
        persona_id: UUID persony
        force_refresh: Wymuś recalculation (bypass cache)
        db: DB session
        current_user: Authenticated user

    Returns:
        PersonaDetailsResponse z pełnym detail view

    RBAC:
        - MVP: Wszyscy zalogowani użytkownicy mogą przeglądać persony
        - Production: Role-based permissions (Viewer+)

    Performance:
        - Cache hit: < 50ms (Redis) - TODO: implement caching
        - Cache miss: < 500ms (parallel fetch + 1 DB query)

    Audit:
        - Loguje "view" action w persona_audit_log (async, non-blocking)
    """
    # Verify access
    await get_persona_for_user(persona_id, current_user, db)

    # Fetch details (orchestration service)
    details_service = PersonaDetailsService(db)
    try:
        details = await details_service.get_persona_details(
            persona_id=persona_id,
            user_id=current_user.id,
            force_refresh=force_refresh,
        )
        return details
    except ValueError as e:
        # Persona not found
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Unexpected error
        logger.error(f"Failed to fetch persona details: {e}", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch persona details. Please try again later.",
        )


@router.post(
    "/personas/{persona_id}/actions/export",
    response_model=PersonaExportResponse,
)
@limiter.limit("30/minute")
async def export_persona_details(
    request: Request,  # Required by slowapi limiter
    persona_id: UUID,
    payload: PersonaExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.format != "json":
        raise HTTPException(status_code=400, detail="Only JSON export is supported in this environment.")

    details_service = PersonaDetailsService(db)
    details = await details_service.get_persona_details(
        persona_id=persona_id,
        user_id=current_user.id,
        force_refresh=False,
    )

    # Note: Removed "journey" section (deprecated customer_journey field)
    # Available sections: ["overview", "profile", "needs", "insights"]
    sections = payload.sections or ["overview", "profile", "needs", "insights"]
    content: Dict[str, Any] = {}

    if "overview" in sections:
        content["overview"] = {
            # kpi_snapshot removed - deprecated field
            "rag_citations": details.rag_citations,
        }
    if "profile" in sections:
        content["profile"] = {
            "full_name": details.full_name,
            "persona_title": details.persona_title,
            "headline": details.headline,
            "demographics": {
                "age": details.age,
                "gender": details.gender,
                "location": details.location,
                "education_level": details.education_level,
                "income_bracket": details.income_bracket,
                "occupation": details.occupation,
            },
            "big_five": details.big_five,
            "values": details.values,
            "interests": details.interests,
            "background_story": details.background_story,
        }
    # "journey" section removed - customer_journey field deprecated
    # For journey data, use PersonaJourneyService directly
    if "needs" in sections:
        content["needs"] = details.needs_and_pains.model_dump(mode="json") if details.needs_and_pains else None
    if "insights" in sections:
        content["insights"] = {
            "rag_context_details": details.rag_context_details,
            "audit_log": [entry.model_dump(mode="json") for entry in details.audit_log],
        }

    audit_service = PersonaAuditService()
    await audit_service.log_action(
        persona_id=persona_id,
        user_id=current_user.id,
        action="export",
        details={"format": payload.format, "sections": sections},
        db=db,
    )

    return PersonaExportResponse(format="json", sections=sections, content=content)
