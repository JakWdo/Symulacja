from collections import defaultdict
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import FocusGroup, Persona, PersonaResponse
from app.services import InsightService
from app.services.report_generator import ReportGenerator

router = APIRouter()

insight_service = InsightService()


@router.post("/focus-groups/{focus_group_id}/insights")
async def generate_insights(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Generate or refresh insight metrics for a completed focus group."""

    focus_group = await _get_focus_group(db, focus_group_id)

    if focus_group.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Focus group must be completed before analysis. Current status: {focus_group.status}",
        )

    try:
        return await insight_service.generate_focus_group_insights(db, str(focus_group_id))
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/focus-groups/{focus_group_id}/insights")
async def get_cached_insights(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return the newest cached insights if they exist."""

    focus_group = await _get_focus_group(db, focus_group_id)

    if not focus_group.polarization_clusters:
        raise HTTPException(status_code=404, detail="No insights generated yet")

    return focus_group.polarization_clusters


@router.get("/focus-groups/{focus_group_id}/responses")
async def get_focus_group_responses(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return full response transcripts grouped by question."""

    focus_group = await _get_focus_group(db, focus_group_id)

    result = await db.execute(
        select(PersonaResponse)
        .where(PersonaResponse.focus_group_id == focus_group_id)
        .order_by(PersonaResponse.created_at)
    )
    responses = result.scalars().all()

    grouped = defaultdict(list)
    for response in responses:
        grouped[response.question].append(
            {
                "persona_id": str(response.persona_id),
                "response": response.response,
                "response_time_ms": response.response_time_ms,
                "consistency_score": response.consistency_score,
                "contradicts_events": response.contradicts_events,
                "created_at": response.created_at.isoformat(),
                "sentiment": insight_service.sentiment_score(response.response),
            }
        )

    ordered_questions = []
    for question in focus_group.questions or []:
        ordered_questions.append(
            {
                "question": question,
                "responses": grouped.get(question, []),
            }
        )

    # Include any questions that might not exist on the focus group definition (defensive)
    for question, entries in grouped.items():
        if question not in (focus_group.questions or []):
            ordered_questions.append({"question": question, "responses": entries})

    return {
        "focus_group_id": str(focus_group_id),
        "total_responses": len(responses),
        "questions": ordered_questions,
    }


@router.get("/personas/{persona_id}/history")
async def get_persona_history(
    persona_id: UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Return chronological memory events for a persona."""
    from app.models import PersonaEvent

    persona = await _get_persona(db, persona_id)

    result = await db.execute(
        select(PersonaEvent)
        .where(PersonaEvent.persona_id == persona_id)
        .order_by(PersonaEvent.sequence_number.desc())
        .limit(limit)
    )
    events = result.scalars().all()

    return {
        "persona_id": str(persona_id),
        "total_events": len(events),
        "events": [
            {
                "id": str(event.id),
                "event_type": event.event_type,
                "event_data": event.event_data,
                "sequence_number": event.sequence_number,
                "timestamp": event.timestamp.isoformat(),
                "focus_group_id": str(event.focus_group_id) if event.focus_group_id else None,
            }
            for event in reversed(events)
        ],
    }


@router.get("/personas/{persona_id}/insights")
async def get_persona_insights(
    persona_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return persona traits and expectation cues for visualization."""

    persona = await _get_persona(db, persona_id)

    trait_fields = [
        "openness",
        "conscientiousness",
        "extraversion",
        "agreeableness",
        "neuroticism",
        "power_distance",
        "individualism",
        "masculinity",
        "uncertainty_avoidance",
        "long_term_orientation",
        "indulgence",
    ]

    trait_scores = {
        field: getattr(persona, field)
        for field in trait_fields
        if getattr(persona, field) is not None
    }

    expectations = []

    if persona.values:
        expectations.append(
            "Values-driven: highlight " + ", ".join(persona.values[:3])
        )

    if persona.interests:
        expectations.append(
            "Engage with content about " + ", ".join(persona.interests[:3])
        )

    if persona.background_story:
        summary = persona.background_story.split(". ")[0].strip()
        if summary:
            expectations.append(summary)

    if persona.education_level:
        expectations.append(f"Appreciates {persona.education_level.lower()} level detail")

    persona_profile = {
        "id": str(persona.id),
        "age": persona.age,
        "gender": persona.gender,
        "location": persona.location,
        "education_level": persona.education_level,
        "income_bracket": persona.income_bracket,
        "occupation": persona.occupation,
        "values": persona.values or [],
        "interests": persona.interests or [],
        "background_story": persona.background_story,
    }

    return {
        "persona": persona_profile,
        "trait_scores": trait_scores,
        "expectations": expectations,
    }


@router.get("/focus-groups/{focus_group_id}/export/pdf")
async def export_analysis_pdf(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Export focus group insights as PDF."""

    analysis_data = await _ensure_insights(db, focus_group_id)

    report_gen = ReportGenerator()
    pdf_bytes = await report_gen.generate_pdf_report(db, focus_group_id, analysis_data)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=focus_group_analysis_{focus_group_id}.pdf"
        },
    )


@router.get("/focus-groups/{focus_group_id}/export/csv")
async def export_analysis_csv(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Export focus group insights as spreadsheet."""

    analysis_data = await _ensure_insights(db, focus_group_id)

    report_gen = ReportGenerator()
    csv_bytes = await report_gen.generate_csv_report(db, focus_group_id, analysis_data)

    return Response(
        content=csv_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=focus_group_analysis_{focus_group_id}.xlsx"
        },
    )


async def _get_focus_group(db: AsyncSession, focus_group_id: UUID) -> FocusGroup:
    result = await db.execute(
        select(FocusGroup).where(FocusGroup.id == focus_group_id)
    )
    focus_group = result.scalar_one_or_none()
    if not focus_group:
        raise HTTPException(status_code=404, detail="Focus group not found")
    return focus_group


async def _get_persona(db: AsyncSession, persona_id: UUID) -> Persona:
    result = await db.execute(select(Persona).where(Persona.id == persona_id))
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona


async def _ensure_insights(
    db: AsyncSession,
    focus_group_id: UUID,
) -> Dict[str, Any]:
    focus_group = await _get_focus_group(db, focus_group_id)

    if focus_group.polarization_clusters:
        return focus_group.polarization_clusters

    try:
        return await insight_service.generate_focus_group_insights(db, str(focus_group_id))
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=404, detail=str(exc)) from exc
