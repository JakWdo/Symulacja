from collections import defaultdict
from typing import Any, Dict
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import FocusGroup, Persona, PersonaResponse
from app.services.discussion_summarizer import DiscussionSummarizerService

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
        summarizer = DiscussionSummarizerService(use_pro_model=use_pro_model)

        summary = await summarizer.generate_discussion_summary(
            db=db,
            focus_group_id=str(focus_group_id),
            include_demographics=True,
            include_recommendations=include_recommendations,
        )

        return summary

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to generate AI summary", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate AI summary: {str(e)}"
        )


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

    # Include any questions that might not exist on the focus group definition (defensive)
    for question, entries in grouped.items():
        if question not in (focus_group.questions or []):
            ordered_questions.append({"question": question, "responses": entries})

    return {
        "focus_group_id": str(focus_group_id),
        "total_responses": len(responses),
        "questions": ordered_questions,
    }




async def _get_focus_group(db: AsyncSession, focus_group_id: UUID) -> FocusGroup:
    result = await db.execute(
        select(FocusGroup).where(FocusGroup.id == focus_group_id)
    )
    focus_group = result.scalar_one_or_none()
    if not focus_group:
        raise HTTPException(status_code=404, detail="Focus group not found")
    return focus_group


