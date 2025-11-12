"""
Insight classification and analysis utilities.

Classifies insights by type, determines sentiment, calculates confidence/impact scores,
and builds evidence from discussion data.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def determine_sentiment(narrative: str) -> str:
    """
    Określa ogólny sentyment z narracji.

    Args:
        narrative: Tekst narracji sentymentalnej

    Returns:
        "positive", "negative", "mixed", lub "neutral"
    """
    if not narrative:
        return "neutral"

    # TODO: Implement sentiment analysis - temporarily using neutral default
    # Previously used: simple_sentiment_score(narrative) from nlp module
    score = 0.0
    if score > 0.2:
        return "positive"
    elif score < -0.2:
        return "negative"
    elif "mixed" in narrative.lower() or "polarizing" in narrative.lower():
        return "mixed"
    else:
        return "neutral"


def classify_insight_type(insight_text: str) -> str:
    """
    Klasyfikacja typu spostrzeżenia (insight) na podstawie słów kluczowych.

    Obsługiwane typy:
    - opportunity: szanse, potencjał wzrostu, przewagi
    - risk: ryzyka, zagrożenia, problemy
    - trend: trendy, zmiany w czasie, przesunięcia
    - pattern: wzorce, powtarzające się zachowania

    Wspiera język polski i angielski.

    Args:
        insight_text: Tekst spostrzeżenia do klasyfikacji

    Returns:
        Typ spostrzeżenia: "opportunity", "risk", "trend", lub "pattern"
    """
    insight_lower = insight_text.lower()

    # Keyword patterns for classification (PL + EN)
    # Priority order: opportunity > risk > trend > pattern
    # This ensures specific types are detected before generic "pattern"

    # 1. OPPORTUNITY - szanse, potencjał, wzrost, przewagi
    opportunity_keywords = [
        # Polish
        "szansa", "szanse", "potencjał", "wzrost", "przewaga", "okazja",
        "możliwość", "korzyść", "zaleta", "zysk", "rozwój", "ekspansja",
        "innowacja", "ulepszenie",
        # English
        "opportunity", "potential", "growth", "advantage", "benefit",
        "gain", "upside", "improvement", "innovation",
    ]

    # 2. RISK - ryzyko, zagrożenia, problemy, wyzwania
    risk_keywords = [
        # Polish
        "ryzyko", "zagrożenie", "obawa", "problem", "wyzwanie",
        "bariera", "trudność", "niebezpieczeństwo", "słabość", "ograniczenie",
        "kryzys", "utrata", "odpływ", "negatywny wpływ",
        # English
        "risk", "threat", "concern", "problem", "issue", "challenge",
        "barrier", "difficulty", "danger", "weakness", "limitation",
        "crisis", "loss", "churn", "negative impact",
    ]

    # 3. TREND - trendy, zmiany w czasie, przesunięcia
    trend_keywords = [
        # Polish
        "trend", "tendencja", "zmiana", "przesunięcie", "ewolucja",
        "wzrostowy", "spadkowy", "rosnący", "malejący", "coraz więcej",
        "coraz mniej", "stopniowo", "dynamika",
        # English
        "trend", "tendency", "shift", "change", "evolution",
        "increasing", "decreasing", "growing", "declining", "more and more",
        "less and less", "gradually", "dynamics",
    ]

    # 4. PATTERN - wzorce, powtarzalność, konsekwencja
    pattern_keywords = [
        # Polish
        "wzorzec", "schemat", "powtarzalny", "konsekwentny", "regularny",
        "częsty", "powszechny", "typowy", "stały", "większość", "wszyscy",
        "systematyczny",
        # English
        "pattern", "consistent", "regular", "frequent", "common",
        "typical", "recurring", "systematic", "across", "all", "majority",
    ]

    # Check for opportunities (highest priority for positive insights)
    if any(keyword in insight_lower for keyword in opportunity_keywords):
        return "opportunity"

    # Check for risks (high priority for negative insights)
    if any(keyword in insight_lower for keyword in risk_keywords):
        return "risk"

    # Check for trends (changes over time)
    if any(keyword in insight_lower for keyword in trend_keywords):
        return "trend"

    # Check for patterns (recurring behaviors)
    if any(keyword in insight_lower for keyword in pattern_keywords):
        return "pattern"

    # Default fallback logic: infer from context if no keywords matched
    # If text mentions change/time, likely a trend
    # If text mentions positive outcome, likely opportunity
    # Otherwise default to "opportunity" (more actionable than "pattern")

    time_indicators = ["czas", "ostatnio", "wcześniej", "teraz", "obecnie", "recently", "now", "before", "time"]
    positive_indicators = ["dobrze", "lepiej", "pozytywnie", "sukces", "well", "better", "positive", "success"]

    if any(indicator in insight_lower for indicator in time_indicators):
        return "trend"
    elif any(indicator in insight_lower for indicator in positive_indicators):
        return "opportunity"
    else:
        # Final fallback: opportunity (more actionable than pattern)
        return "opportunity"


def calculate_confidence(insight_text: str) -> float:
    """
    Oblicza współczynnik pewności na podstawie siły języka (0-1).

    Args:
        insight_text: Tekst spostrzeżenia

    Returns:
        Współczynnik pewności od 0.5 do 1.0
    """
    insight_lower = insight_text.lower()

    # Strong confidence indicators
    strong_words = ["all", "every", "consistently", "clearly", "definitely", "strongly"]
    # Weak confidence indicators
    weak_words = ["some", "may", "might", "possibly", "potentially", "could"]

    strong_count = sum(1 for word in strong_words if word in insight_lower)
    weak_count = sum(1 for word in weak_words if word in insight_lower)

    # Base confidence: 0.7
    base_confidence = 0.7
    confidence = base_confidence + (strong_count * 0.1) - (weak_count * 0.1)

    return max(0.5, min(1.0, confidence))  # Clamp between 0.5 and 1.0


def calculate_impact(insight_text: str, position: int) -> int:
    """
    Oblicza współczynnik wpływu na podstawie ważności spostrzeżenia (1-10).

    Args:
        insight_text: Tekst spostrzeżenia
        position: Pozycja w liście (pierwsze spostrzeżenia są ważniejsze)

    Returns:
        Współczynnik wpływu od 1 do 10
    """
    # First insights are typically more important
    position_score = max(10 - position * 2, 3)  # 10, 8, 6, 4, 3...

    # High-impact keywords
    high_impact_words = ["critical", "major", "significant", "key", "essential", "crucial"]
    impact_multiplier = 1.0

    insight_lower = insight_text.lower()
    if any(word in insight_lower for word in high_impact_words):
        impact_multiplier = 1.2

    impact = int(position_score * impact_multiplier)
    return max(1, min(10, impact))  # Clamp between 1 and 10


def build_evidence(parsed_summary: dict[str, Any], insight_text: str) -> list[dict]:
    """
    Buduje listę dowodów z komponentów podsumowania.

    Args:
        parsed_summary: Sparsowane podsumowanie AI
        insight_text: Tekst spostrzeżenia

    Returns:
        Lista dowodów (maks 5 elementów)
    """
    evidence = []

    # Add executive summary as context
    if parsed_summary.get("executive_summary"):
        evidence.append({
            "type": "summary",
            "text": parsed_summary["executive_summary"][:300],  # Truncate
            "source": "executive_summary",
        })

    # Add surprising findings as supporting evidence
    for finding in parsed_summary.get("surprising_findings", [])[:2]:
        evidence.append({
            "type": "supporting_finding",
            "text": finding,
            "source": "surprising_findings",
        })

    # Add segment analysis if relevant
    segment_analysis = parsed_summary.get("segment_analysis", {})
    if segment_analysis:
        # Take first 2 segments
        for segment_name, analysis in list(segment_analysis.items())[:2]:
            evidence.append({
                "type": "segment_insight",
                "text": f"{segment_name}: {analysis}",
                "source": "segment_analysis",
            })

    return evidence[:5]  # Max 5 evidence items
