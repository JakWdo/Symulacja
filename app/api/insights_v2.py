"""
Enhanced insights API endpoints
Provides AI summaries, metric explanations, and advanced analytics
"""

import logging
from typing import Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.services.discussion_summarizer import DiscussionSummarizerService
from app.services.metrics_explainer import MetricsExplainerService
from app.services.insight_service import InsightService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/focus-groups/{focus_group_id}/ai-summary")
async def generate_ai_summary(
    focus_group_id: UUID,
    use_pro_model: bool = Query(
        False,
        description="Use Gemini 2.5 Pro for highest quality (slower) vs Gemini 2.0 Flash (faster)"
    ),
    include_recommendations: bool = Query(True, description="Include strategic recommendations"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Generate AI-powered discussion summary for a focus group

    This endpoint uses advanced LLMs (Gemini 2.0/2.5) to analyze all responses
    and generate executive summaries, key insights, and strategic recommendations.

    **Response includes:**
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


@router.get("/focus-groups/{focus_group_id}/metric-explanations")
async def get_metric_explanations(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get human-readable explanations for all insight metrics

    Returns contextual explanations for each metric including:
    - What the value means
    - Why it matters
    - What action to take
    - Benchmark comparison
    """
    try:
        # First, get the insights data
        insight_service = InsightService()
        insights_data = await insight_service.generate_focus_group_insights(
            db=db,
            focus_group_id=str(focus_group_id)
        )

        # Generate explanations
        explainer = MetricsExplainerService()
        explanations = explainer.explain_all_metrics(insights_data)

        # Get overall health assessment
        health_assessment = explainer.get_overall_health_assessment(insights_data)

        # Convert MetricExplanation objects to dicts
        explanations_dict = {
            key: {
                "name": exp.name,
                "value": exp.value,
                "interpretation": exp.interpretation,
                "context": exp.context,
                "action": exp.action,
                "benchmark": exp.benchmark,
            }
            for key, exp in explanations.items()
        }

        return {
            "focus_group_id": str(focus_group_id),
            "explanations": explanations_dict,
            "health_assessment": health_assessment,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to generate metric explanations", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate metric explanations: {str(e)}"
        )


@router.get("/focus-groups/{focus_group_id}/health-check")
async def get_health_check(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Quick health check for focus group results

    Returns overall health score and status without full explanations.
    Useful for dashboard views and quick assessments.
    """
    try:
        insight_service = InsightService()
        insights_data = await insight_service.generate_focus_group_insights(
            db=db,
            focus_group_id=str(focus_group_id)
        )

        explainer = MetricsExplainerService()
        health_assessment = explainer.get_overall_health_assessment(insights_data)

        return {
            "focus_group_id": str(focus_group_id),
            **health_assessment
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to get health check", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get health check: {str(e)}"
        )
