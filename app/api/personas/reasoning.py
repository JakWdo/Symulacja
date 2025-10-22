"""
API Endpoints - Persona Reasoning

GET /personas/{persona_id}/reasoning - Wyświetl reasoning persony (zakładka "Uzasadnienie" w UI)

Zwraca szczegółowe uzasadnienie generowania persony:
- Orchestration brief: Zwięzły edukacyjny brief od Gemini 2.5 Pro (900-1200 znaków)
- Graph insights: Lista wskaźników z Graph RAG z wyjaśnieniami "dlaczego to ważne"
- Allocation reasoning: Dlaczego tyle person w tej grupie demograficznej
- Demographics: Docelowa demografia tej grupy
- Overall context: Ogólny kontekst społeczny Polski
- Segment metadata: Nazwa, ID, opis segmentu

Output style: Edukacyjny, konwersacyjny, wyjaśniający, production-ready
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.api.dependencies import get_current_user, get_persona_for_user
from app.schemas.persona import PersonaReasoningResponse, GraphInsightResponse

# Import utility functions
from .utils import (
    _graph_node_to_insight_response,
    _build_segment_metadata,
    _compose_segment_description,
    _sanitize_brief_text,
)

router = APIRouter()
logger = logging.getLogger(__name__)


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
    rag_details: Dict[str, Any] = persona.rag_context_details or {}
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

    orch_reasoning: Dict[str, Any] = rag_details.get("orchestration_reasoning") or {}
    if not orch_reasoning:
        logger.warning(
            "Persona %s nie ma orchestration_reasoning - korzystam tylko z danych RAG",
            persona_id,
        )

    # Parsuj graph insights z orchestration lub fallbacku
    graph_insights: List[GraphInsightResponse] = []
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
        segment_name = _build_segment_metadata(
            fallback_demographics,
            orchestration_brief,
            allocation_reasoning,
            0,
        ).get("segment_name")

    if not segment_description and segment_name:
        segment_description = _compose_segment_description(fallback_demographics, segment_name)

    if not segment_social_context:
        characteristic_summary = ""
        if segment_characteristics:
            characteristic_summary = (
                " Kluczowe wyróżniki: "
                + ", ".join(segment_characteristics[:4])
                + "."
            )
        demographic_sentence = _compose_segment_description(
            fallback_demographics,
            segment_name or "Ten segment",
        )
        brief_snippet = _sanitize_brief_text(orchestration_brief, max_length=280)
        segment_social_context = (
            f"{demographic_sentence}{characteristic_summary} "
            f"{brief_snippet}" if brief_snippet else f"{demographic_sentence}{characteristic_summary}"
        ).strip()

    segment_social_context = _sanitize_brief_text(segment_social_context)

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
