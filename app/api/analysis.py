from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.db import get_db
from app.models import FocusGroup
from app.services import PolarizationService

router = APIRouter()


@router.post("/focus-groups/{focus_group_id}/analyze-polarization")
async def analyze_polarization(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Analyze polarization in focus group responses"""

    # Verify focus group exists and is completed
    result = await db.execute(
        select(FocusGroup).where(FocusGroup.id == focus_group_id)
    )
    focus_group = result.scalar_one_or_none()

    if not focus_group:
        raise HTTPException(status_code=404, detail="Focus group not found")

    if focus_group.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Focus group must be completed before analysis. Current status: {focus_group.status}",
        )

    # Run polarization analysis
    service = PolarizationService()
    analysis = await service.analyze_polarization(db, str(focus_group_id))

    return analysis


@router.get("/focus-groups/{focus_group_id}/responses")
async def get_focus_group_responses(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all responses from a focus group"""
    from app.models import PersonaResponse

    result = await db.execute(
        select(PersonaResponse).where(
            PersonaResponse.focus_group_id == focus_group_id
        )
    )
    responses = result.scalars().all()

    if not responses:
        raise HTTPException(status_code=404, detail="No responses found")

    # Group by question
    responses_by_question = {}
    for response in responses:
        if response.question not in responses_by_question:
            responses_by_question[response.question] = []

        responses_by_question[response.question].append(
            {
                "persona_id": str(response.persona_id),
                "response": response.response,
                "response_time_ms": response.response_time_ms,
                "consistency_score": response.consistency_score,
                "contradicts_events": response.contradicts_events,
                "created_at": response.created_at.isoformat(),
            }
        )

    return {
        "focus_group_id": str(focus_group_id),
        "total_responses": len(responses),
        "responses_by_question": responses_by_question,
    }


@router.get("/personas/{persona_id}/history")
async def get_persona_history(
    persona_id: UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Get interaction history for a persona"""
    from app.models import PersonaEvent, Persona

    # Verify persona exists
    result = await db.execute(
        select(Persona).where(Persona.id == persona_id)
    )
    persona = result.scalar_one_or_none()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Get events
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
            for event in reversed(events)  # Show chronologically
        ],
    }
