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
from app.services.advanced_insights_service import AdvancedInsightsService
from app.services.enhanced_report_generator import EnhancedReportGenerator

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

    This endpoint uses Gemini 2.5 models to analyze all responses
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


@router.get("/focus-groups/{focus_group_id}/advanced-insights")
async def get_advanced_insights(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get advanced analytics for focus group

    Returns comprehensive insights including:
    - Demographic-sentiment correlations
    - Temporal analysis (sentiment evolution over time)
    - Behavioral segmentation (participant clusters)
    - Response quality metrics
    - Comparative question analysis
    - Outlier detection
    - Engagement patterns

    This is computationally intensive and may take a few seconds.
    """
    try:
        advanced_service = AdvancedInsightsService()
        insights = await advanced_service.generate_advanced_insights(
            db=db,
            focus_group_id=str(focus_group_id)
        )

        return insights

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to generate advanced insights", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate advanced insights: {str(e)}"
        )


@router.get("/focus-groups/{focus_group_id}/enhanced-report")
async def generate_enhanced_report(
    focus_group_id: UUID,
    include_ai_summary: bool = Query(True, description="Include AI-generated executive summary"),
    include_advanced_insights: bool = Query(True, description="Include advanced analytics"),
    use_pro_model: bool = Query(False, description="Use Gemini 2.5 Pro for AI summary (slower but higher quality)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate enhanced PDF report with AI summary and advanced insights

    Returns a comprehensive professional PDF report including:
    - Cover page with project overview and health score
    - AI executive summary (optional, uses Gemini 2.5 Flash/Pro)
    - Key insights and strategic recommendations
    - Detailed metrics with explanations and context
    - Advanced analytics (correlations, segments, quality metrics)
    - Professional formatting with color-coded sections

    **Performance notes:**
    - Basic report: ~2-3 seconds
    - With AI summary (Flash): ~5-8 seconds
    - With AI summary (Pro): ~10-15 seconds
    - With advanced insights: +2-3 seconds
    """
    try:
        from fastapi.responses import StreamingResponse

        generator = EnhancedReportGenerator()
        pdf_bytes = await generator.generate_enhanced_pdf_report(
            db=db,
            focus_group_id=focus_group_id,
            include_ai_summary=include_ai_summary,
            include_advanced_insights=include_advanced_insights,
            use_pro_model=use_pro_model,
        )

        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=focus_group_{focus_group_id}_enhanced_report.pdf"
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to generate enhanced report", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate enhanced report: {str(e)}"
        )
