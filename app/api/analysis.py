"""
API Endpoints dla Analiz i Podsumowań AI

Ten moduł zawiera endpoints do zaawansowanej analizy grup fokusowych:
- POST /focus-groups/{id}/ai-summary - AI-powered podsumowanie dyskusji (Gemini)
- GET /focus-groups/{id}/sentiment-analysis - Analiza sentymentu odpowiedzi

Podsumowania używają Google Gemini (2.5 Pro lub Flash) do:
- Executive summary
- Key insights i surprising findings
- Segment analysis (różnice demograficzne)
- Strategic recommendations
- Sentiment narrative
"""
from collections import defaultdict
from typing import Any, Dict
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import FocusGroup, Persona, PersonaResponse, User
from app.api.dependencies import get_current_user, get_focus_group_for_user
from app.services.focus_groups.discussion_summarizer import DiscussionSummarizerService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/focus-groups/{focus_group_id}/ai-summary")
async def generate_ai_summary(
    focus_group_id: UUID,
    use_pro_model: bool = Query(
        True,
        description="Use Gemini 2.5 Pro for highest-quality analysis (toggle off for Gemini 2.5 Flash)"
    ),
    include_recommendations: bool = Query(True, description="Include strategic recommendations"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Generate AI-powered discussion summary for a focus group

    Uses Gemini 2.5 to analyze all responses and generate:
    - Executive summary (150-200 words)
    - Key insights (5-7 bullet points)
    - Surprising findings
    - Segment analysis (demographic differences)
    - Strategic recommendations
    - Sentiment narrative
    """
    try:
        await _get_focus_group(db, focus_group_id, current_user)
        summarizer = DiscussionSummarizerService(use_pro_model=use_pro_model)

        summary = await summarizer.generate_discussion_summary(
            db=db,
            focus_group_id=str(focus_group_id),
            include_demographics=True,
            include_recommendations=include_recommendations,
        )

        await db.commit()

        return summary

    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to generate AI summary", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate AI summary: {str(e)}"
        )


@router.get("/focus-groups/{focus_group_id}/ai-summary")
async def get_ai_summary(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Retrieve cached AI summary for a focus group.

    Alias for GET /focus-groups/{id}/insights to keep backwards compatibility.
    """
    return await get_insights(focus_group_id, db, current_user)


@router.post("/focus-groups/{focus_group_id}/insights")
async def generate_insights(
    focus_group_id: UUID,
    use_pro_model: bool = Query(
        True,
        description="Use Gemini 2.5 Pro for highest-quality analysis"
    ),
    include_recommendations: bool = Query(True, description="Include strategic recommendations"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Alias for /ai-summary - Generate AI-powered insights for a focus group

    This endpoint provides the same functionality as /ai-summary
    """
    return await generate_ai_summary(
        focus_group_id,
        use_pro_model,
        include_recommendations,
        db,
        current_user,
    )


@router.get("/focus-groups/{focus_group_id}/insights")
async def get_insights(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get cached insights for a focus group

    Returns the most recently generated AI summary cached on the focus group.
    """
    focus_group = await _get_focus_group(db, focus_group_id, current_user)

    if not focus_group.ai_summary:
        raise HTTPException(
            status_code=404,
            detail="Insights not found. Generate them first using POST /focus-groups/{id}/insights"
        )

    return focus_group.ai_summary


@router.get("/focus-groups/{focus_group_id}/responses")
async def get_focus_group_responses(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return full response transcripts grouped by question."""

    focus_group = await _get_focus_group(db, focus_group_id, current_user)

    result = await db.execute(
        select(PersonaResponse)
        .where(PersonaResponse.focus_group_id == focus_group_id)
        .order_by(PersonaResponse.created_at)
    )
    responses = result.scalars().all()

    grouped = defaultdict(list)
    for response in responses:
        grouped[response.question_text].append(
            {
                "persona_id": str(response.persona_id),
                "response": response.response_text,
                "created_at": response.created_at.isoformat(),
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

    # Dodaj także pytania, które mogły nie trafić do definicji grupy
    for question, entries in grouped.items():
        if question not in (focus_group.questions or []):
            ordered_questions.append({"question": question, "responses": entries})

    return {
        "focus_group_id": str(focus_group_id),
        "total_responses": len(responses),
        "questions": ordered_questions,
    }




async def _get_focus_group(
    db: AsyncSession,
    focus_group_id: UUID,
    current_user: User,
) -> FocusGroup:
    return await get_focus_group_for_user(focus_group_id, current_user, db)
