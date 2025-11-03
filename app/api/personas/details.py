"""
Persona API - Detail & Read Operations

Detail-heavy read endpoints (reasoning, details, archived personas).
"""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Persona, Project, User
from app.api.dependencies import get_current_user, get_persona_for_user
from app.schemas.persona import PersonaResponse, PersonaReasoningResponse, GraphInsightResponse
from app.schemas.persona_details import PersonaDetailsResponse
from app.services.personas import PersonaDetailsService
from app.services.personas.segment_constructor import SegmentConstructor
from .helpers import _graph_node_to_insight_response


router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize segment constructor (used in reasoning endpoint)
segment_constructor = SegmentConstructor()


@router.get("/personas/{persona_id}/reasoning", response_model=PersonaReasoningResponse)
async def get_persona_reasoning(
    persona_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pobierz szczegółowe reasoning persony (dla zakładki 'Uzasadnienie' w UI)

    Zwraca:
    - orchestration_brief: Zwięzły (900-1200 znaków) edukacyjny brief od Gemini 2.5 Pro
    - graph_insights: Lista wskaźników z Graph RAG z wyjaśnieniami "dlaczego to ważne"
    - allocation_reasoning: Dlaczego tyle person w tej grupie demograficznej
    - demographics: Docelowa demografia tej grupy
    - overall_context: Ogólny kontekst społeczny Polski

    Output style: Edukacyjny, konwersacyjny, wyjaśniający, production-ready

    Raises:
        HTTPException 404: Jeśli persona nie istnieje lub nie ma reasoning data
    """
    # Pobierz personę (weryfikacja uprawnień)
    persona = await get_persona_for_user(persona_id, current_user, db)

    # Graceful handling: zwróć pustą response jeśli brak orchestration data
    # (zamiast 404 - lepsze UX)
    rag_details: dict[str, Any] = persona.rag_context_details or {}
    if not rag_details:
        logger.warning(
            "Persona %s nie ma rag_context_details - zwracam pustą response", persona_id
        )
        return PersonaReasoningResponse(
            orchestration_brief=None,
            graph_insights=[],
            allocation_reasoning=None,
            demographics=None,
            overall_context=None,
        )

    orch_reasoning: dict[str, Any] = rag_details.get("orchestration_reasoning") or {}
    if not orch_reasoning:
        logger.warning(
            "Persona %s nie ma orchestration_reasoning - korzystam tylko z danych RAG",
            persona_id,
        )

    # Parsuj graph insights z orchestration lub fallbacku
    graph_insights: list[GraphInsightResponse] = []
    raw_graph_insights = orch_reasoning.get("graph_insights") or rag_details.get(
        "graph_insights", []
    )
    for insight_dict in raw_graph_insights or []:
        try:
            graph_insights.append(GraphInsightResponse(**insight_dict))
        except Exception as exc:
            logger.warning(
                "Failed to parse graph insight: %s, insight=%s", exc, insight_dict
            )

    # Fallback: konwertuj surowe węzły grafu na insights
    if not graph_insights and rag_details.get("graph_nodes"):
        for node in rag_details["graph_nodes"]:
            converted = _graph_node_to_insight_response(node)
            if converted:
                graph_insights.append(converted)

    # Wyprowadź pola segmentowe i kontekstowe
    segment_name = orch_reasoning.get("segment_name") or rag_details.get("segment_name")
    segment_description = orch_reasoning.get("segment_description") or rag_details.get(
        "segment_description"
    )
    segment_social_context = (
        orch_reasoning.get("segment_social_context")
        or rag_details.get("segment_social_context")
        or rag_details.get("segment_context")
    )
    raw_characteristics = (
        orch_reasoning.get("segment_characteristics")
        or rag_details.get("segment_characteristics")
        or []
    )
    segment_characteristics = [str(item).strip() for item in raw_characteristics if str(item).strip()]

    orchestration_brief = orch_reasoning.get("brief") or rag_details.get("brief")
    allocation_reasoning = orch_reasoning.get("allocation_reasoning") or rag_details.get(
        "allocation_reasoning"
    )
    demographics = orch_reasoning.get("demographics") or rag_details.get("demographics")
    overall_context = (
        orch_reasoning.get("overall_context")
        or rag_details.get("overall_context")
        or rag_details.get("graph_context")
    )

    # Fallback demografia (używana również do budowania opisów segmentu)
    fallback_demographics = demographics or {
        "age": str(persona.age) if persona.age else None,
        "gender": persona.gender,
        "education": persona.education_level,
        "income": persona.income_bracket,
        "location": persona.location,
    }
    if not isinstance(fallback_demographics, dict):
        try:
            fallback_demographics = dict(fallback_demographics)
        except Exception:
            fallback_demographics = {
                "age": str(persona.age) if persona.age else None,
                "gender": persona.gender,
                "education": persona.education_level,
                "income": persona.income_bracket,
                "location": persona.location,
            }

    # Preferuj catchy segment name zapisany przy personie
    if persona.segment_name:
        segment_name = persona.segment_name
    if persona.segment_id:
        segment_id_value = persona.segment_id
    else:
        segment_id_value = orch_reasoning.get("segment_id") or rag_details.get("segment_id")

    if not segment_name:
        segment_name = segment_constructor.build_segment_metadata(
            fallback_demographics,
            orchestration_brief,
            allocation_reasoning,
            0,
        ).get("segment_name")

    if not segment_description and segment_name:
        segment_description = segment_constructor.compose_segment_description(fallback_demographics, segment_name)

    if not segment_social_context:
        characteristic_summary = ""
        if segment_characteristics:
            characteristic_summary = (
                " Kluczowe wyróżniki: "
                + ", ".join(segment_characteristics[:4])
                + "."
            )
        demographic_sentence = segment_constructor.compose_segment_description(
            fallback_demographics,
            segment_name or "Ten segment",
        )
        brief_snippet = segment_constructor.sanitize_brief_text(orchestration_brief, max_length=280)
        segment_social_context = (
            f"{demographic_sentence}{characteristic_summary} "
            f"{brief_snippet}" if brief_snippet else f"{demographic_sentence}{characteristic_summary}"
        ).strip()

    segment_social_context = segment_constructor.sanitize_brief_text(segment_social_context)

    response = PersonaReasoningResponse(
        orchestration_brief=orchestration_brief,
        graph_insights=graph_insights,
        allocation_reasoning=allocation_reasoning,
        demographics=demographics,
        overall_context=overall_context,
        segment_name=segment_name,
        segment_id=segment_id_value,
        segment_description=segment_description,
        segment_social_context=segment_social_context,
        segment_characteristics=segment_characteristics,
    )

    return response


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
        - Cache hit: < 50ms (Redis cache with TTL 1h, auto-invalidation on update)
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


@router.get("/personas/archived", response_model=list[PersonaResponse])
async def get_archived_personas(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pobierz listę usuniętych person (archiwum) z ostatnich 7 dni

    Zwraca persony które zostały soft-deleted i nadal mogą być przywrócone
    (restore window: 7 dni od deleted_at).

    Args:
        db: DB session
        current_user: Authenticated user

    Returns:
        List[PersonaResponse]: Lista usuniętych person (ordered by deleted_at DESC)

    Query:
        - is_active = False
        - deleted_at IS NOT NULL
        - deleted_at > now() - 7 days (restore window)
        - User ma dostęp poprzez project ownership

    RBAC:
        - Użytkownik widzi tylko persony z własnych projektów
    """
    # Calculate restore window cutoff (7 days ago)
    restore_window_start = datetime.utcnow() - timedelta(days=7)

    # Query: pobierz usunięte persony z ostatnich 7 dni
    result = await db.execute(
        select(Persona)
        .join(Project, Persona.project_id == Project.id)
        .where(
            Persona.is_active.is_(False),
            Persona.deleted_at.isnot(None),
            Persona.deleted_at > restore_window_start,
            Project.owner_id == current_user.id,
        )
        .order_by(Persona.deleted_at.desc())
    )
    personas = result.scalars().all()

    # Convert to PersonaResponse
    return [
        PersonaResponse(
            id=persona.id,
            project_id=persona.project_id,
            full_name=persona.full_name,
            persona_title=persona.persona_title,
            headline=persona.headline,
            age=persona.age,
            gender=persona.gender,
            location=persona.location,
            education_level=persona.education_level,
            income_bracket=persona.income_bracket,
            occupation=persona.occupation,
            created_at=persona.created_at,
        )
        for persona in personas
    ]
