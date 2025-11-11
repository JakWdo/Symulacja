"""Utilities dla filtrowania graph insights i RAG citations.

Ten moduł zawiera helper functions dla:
- Filtrowania insights per segment (age relevance, confidence)
- Filtrowania RAG citations (confidence threshold)
"""

from __future__ import annotations

from typing import Any


def filter_graph_insights_for_segment(
    insights: list[Any],
    segment_data: dict[str, Any]
) -> list[Any]:
    """Filtruje graph insights dla konkretnego segmentu demograficznego.

    Zwraca tylko insights relevantne dla tego segmentu (np. insights o młodych
    dla segmentu 18-24).

    Args:
        insights: Wszystkie graph insights (GraphInsight objects lub dicts)
        segment_data: Dict z demographics (age, gender, education, etc.)

    Returns:
        Filtrowana lista insights (max 10), sorted by confidence
    """
    if not insights:
        return []

    demographics = segment_data.get('demographics', {})

    # Extract age range for filtering
    age_str = demographics.get('age', demographics.get('age_group', ''))

    filtered = []
    for insight in insights:
        # Handle both GraphInsight objects and dicts
        summary = insight.summary if hasattr(insight, 'summary') else insight.get('summary', '')

        # Filter by age relevance (check if age range mentioned in summary)
        age_relevant = True
        if age_str and summary:
            # Simple heuristic: if insight mentions age, check if it's relevant
            summary_lower = summary.lower()
            if any(age_term in summary_lower for age_term in ['wiek', 'lat', 'young', 'old', 'młod', 'star']):
                # Check if age range overlaps (simplified)
                age_relevant = age_str.lower() in summary_lower or not any(
                    other_age in summary_lower
                    for other_age in ['18-24', '25-34', '35-44', '45-54', '55+']
                    if other_age != age_str
                )

        if age_relevant:
            filtered.append(insight)

    # Sort by confidence (high first) and return top 10
    confidence_order = {'high': 3, 'medium': 2, 'low': 1}

    def get_confidence(ins: Any) -> int:
        """Extract confidence from GraphInsight object or dict."""
        if hasattr(ins, 'confidence'):
            return confidence_order.get(ins.confidence, 0)
        else:
            return confidence_order.get(ins.get('confidence', 'medium'), 0)

    filtered.sort(key=get_confidence, reverse=True)

    return filtered[:10]


def filter_rag_citations(
    citations: list[Any],
    min_confidence: float = 0.7
) -> list[Any]:
    """Filtruje RAG citations - tylko high-quality (confidence > threshold).

    Args:
        citations: Lista RAG citations (Document objects lub dicts)
        min_confidence: Minimalny confidence score (default 0.7)

    Returns:
        Filtrowana lista citations (max 10)
    """
    if not citations:
        return []

    filtered = []
    for cit in citations:
        # Check if citation has confidence score in metadata
        confidence = 1.0  # Default if not available
        if hasattr(cit, 'metadata') and cit.metadata:
            confidence = cit.metadata.get('confidence', cit.metadata.get('score', 1.0))

        # Filter by confidence
        if confidence >= min_confidence:
            filtered.append(cit)

    # Return top 10
    return filtered[:10]
