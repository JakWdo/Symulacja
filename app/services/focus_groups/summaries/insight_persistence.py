"""
Insight persistence utilities.

Stores insights extracted from discussion summaries into the database.
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FocusGroup
from app.services.dashboard.insights import InsightTraceabilityService
from .insight_classification import (
    determine_sentiment,
    classify_insight_type,
    calculate_confidence,
    calculate_impact,
    build_evidence,
)

logger = logging.getLogger(__name__)


async def store_insights_from_summary(
    db: AsyncSession,
    focus_group: FocusGroup,
    parsed_summary: dict[str, Any],
    prompt_text: str,
    model_name: str,
) -> list:
    """
    Ekstrakcja i zapis rekordów InsightEvidence z podsumowania AI.

    Konwertuje 3-7 kluczowych spostrzeżeń z podsumowania na rekordy InsightEvidence
    z śledzeniem pochodzenia (model, prompt, źródła).

    Args:
        db: Sesja bazy danych
        focus_group: Instancja FocusGroup
        parsed_summary: Sparsowany słownik podsumowania AI
        prompt_text: Oryginalny prompt użyty do generacji
        model_name: Nazwa użytego modelu LLM

    Returns:
        Lista utworzonych instancji InsightEvidence
    """
    traceability_service = InsightTraceabilityService(db)

    key_insights = parsed_summary.get("key_insights", [])
    if not key_insights:
        return []

    created_insights = []

    # Extract concepts from executive summary and sentiment narrative
    concepts_text = (
        parsed_summary.get("executive_summary", "")
        + " "
        + parsed_summary.get("sentiment_narrative", "")
    )
    # TODO: Implement concept extraction - temporarily using empty list
    # Previously used: extract_concepts(concepts_text, min_frequency=2, max_concepts=15) from nlp module
    concepts = []

    # Determine overall sentiment
    overall_sentiment = determine_sentiment(
        parsed_summary.get("sentiment_narrative", "")
    )

    for idx, insight_text in enumerate(key_insights[:7]):  # Max 7 insights
        # Determine insight type from text
        insight_type = classify_insight_type(insight_text)

        # Calculate confidence and impact scores (heuristic)
        confidence_score = calculate_confidence(insight_text)
        impact_score = calculate_impact(insight_text, idx)

        # Extract evidence (use surprising findings or recommendations as supporting evidence)
        evidence = build_evidence(parsed_summary, insight_text)

        # Build sources reference
        sources = [
            {
                "type": "focus_group_discussion",
                "focus_group_id": str(focus_group.id),
                "focus_group_name": focus_group.name,
            }
        ]

        # Store insight
        try:
            insight_record = await traceability_service.store_insight_evidence(
                project_id=focus_group.project_id,
                insight_text=insight_text,
                insight_type=insight_type,
                confidence_score=confidence_score,
                impact_score=impact_score,
                evidence=evidence,
                concepts=concepts[:10],  # Max 10 concepts
                sentiment=overall_sentiment,
                model_version=model_name,
                prompt=prompt_text,
                sources=sources,
                focus_group_id=focus_group.id,
            )
            created_insights.append(insight_record)
        except Exception as e:
            # Log error but don't fail the entire summary generation
            logger.warning(f"Failed to store insight {idx}: {e}")
            continue

    return created_insights
