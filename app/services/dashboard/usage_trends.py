"""
Dashboard Usage Trends - Analityka insightów i wzorców odpowiedzi

Odpowiedzialny za:
- Analitykę top concepts z insightów
- Dystrybucję sentiment
- Wykrywanie wzorców odpowiedzi (polskie + angielskie keywords)
- Caching wyników
"""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import InsightEvidence, Project
from app.core.redis import redis_get_json, redis_set_json


async def get_insight_analytics(
    db: AsyncSession,
    user_id: UUID,
    project_id: UUID | None = None,
    top_n: int = 10,
) -> dict[str, Any]:
    """
    Pobierz insight analytics (top concepts, sentiment, patterns)

    Cached: Redis 30s

    Args:
        db: Database session
        user_id: UUID użytkownika
        project_id: Opcjonalne UUID projektu (filter dla konkretnego projektu)
        top_n: Liczba top concepts do zwrócenia (default: 10)

    Returns:
        Analytics data
    """
    # Check Redis cache (30s TTL)
    cache_key = f"dashboard:analytics:insights:{user_id}:{project_id or 'all'}:{top_n}"
    cached = await redis_get_json(cache_key)
    if cached is not None:
        return cached

    # Get all insights for user (with optional project filter)
    filters = [
        Project.owner_id == user_id,
        Project.deleted_at.is_(None),
    ]
    if project_id:
        filters.append(InsightEvidence.project_id == project_id)

    stmt = (
        select(InsightEvidence)
        .join(Project, InsightEvidence.project_id == Project.id)
        .where(and_(*filters))
    )

    result = await db.execute(stmt)
    insights = list(result.scalars().all())

    # Top concepts
    concept_counts: dict[str, int] = {}
    for insight in insights:
        for concept in insight.concepts:
            concept_counts[concept] = concept_counts.get(concept, 0) + 1

    top_concepts = [
        {"concept": concept, "count": count}
        for concept, count in sorted(
            concept_counts.items(), key=lambda x: x[1], reverse=True
        )[:top_n]
    ]

    # Sentiment distribution
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
    for insight in insights:
        sentiment = insight.sentiment or "neutral"
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

    # Insight types distribution
    insight_type_counts = {"opportunity": 0, "risk": 0, "trend": 0, "pattern": 0}
    for insight in insights:
        insight_type = insight.insight_type
        if insight_type in insight_type_counts:
            insight_type_counts[insight_type] += 1

    # Response patterns (heuristics based on evidence and sentiment)
    # Polish + English keywords for better detection
    keyword_patterns = {
        "Wrażliwość cenowa": [
            # Polish
            "cena", "cennik", "ceny", "cenowy", "kosztowny", "drogi", "droga", "drogie",
            "tani", "tania", "tanie", "koszt", "kosztów", "wydatek", "opłata", "płatność",
            "zbyt drogo", "za drogo", "ekonomiczny", "budżet",
            # English
            "price", "pricing", "cost", "expensive", "cheap", "affordable", "budget",
        ],
        "Jakość produktu": [
            # Polish
            "jakość", "jakości", "trwałość", "trwały", "niezawodny", "niezawodność",
            "awaria", "usterka", "defekt", "zepsuty", "uszkodzony", "wadliwy",
            "solidny", "solidność", "wytrzymały",
            # English
            "quality", "durable", "reliable", "defect", "faulty", "broken", "damaged",
            "solid", "robust", "sturdy",
        ],
        "Doświadczenie klienta": [
            # Polish
            "doświadczenie", "obsługa", "obsługi", "wsparcie", "pomoc", "kontakt",
            "onboarding", "wdrożenie", "użyteczność", "łatwość", "intuicyjny",
            "przyjazny", "serwis", "service", "UX",
            # English
            "experience", "journey", "onboarding", "support", "service", "help",
            "customer service", "usability", "user-friendly", "intuitive",
        ],
        "Brakujące funkcje": [
            # Polish
            "brakuje", "brak", "brakująca", "brakujący", "funkcja", "funkcji",
            "dodać", "dodania", "ulepszyć", "ulepszenie", "poprawić", "poprawa",
            "rozszerzyć", "rozszerzenie", "wprowadzić", "chciałbym", "potrzeba",
            # English
            "feature", "missing", "lack", "add", "improve", "enhance", "extend",
            "would like", "need", "request", "wish",
        ],
        "Problemy wydajnościowe": [
            # Polish
            "wolny", "wolno", "zacina", "zawieszenie", "wydajność", "opóźnienie",
            "lag", "powolny", "crash", "błąd", "awaria", "nie działa", "problem techniczny",
            # English
            "slow", "lag", "performance", "crash", "bug", "error", "freeze",
            "hang", "loading", "latency",
        ],
    }

    pattern_counts: dict[str, int] = {}

    def add_pattern(label: str) -> None:
        pattern_counts[label] = pattern_counts.get(label, 0) + 1

    for insight in insights:
        add_pattern(f"{insight.insight_type.title()} signals")
        if insight.sentiment:
            add_pattern(f"{insight.sentiment.capitalize()} sentiment")

        for evidence in insight.evidence or []:
            text_source = ""
            if isinstance(evidence, dict):
                text_source = str(evidence.get("text", ""))
            else:
                text_source = str(getattr(evidence, "text", ""))

            text = text_source.lower()
            if not text:
                continue
            for label, keywords in keyword_patterns.items():
                if any(keyword in text for keyword in keywords):
                    add_pattern(label)

    response_patterns = [
        {"pattern": label, "count": count}
        for label, count in sorted(pattern_counts.items(), key=lambda item: item[1], reverse=True)[:5]
    ]

    result = {
        "top_concepts": top_concepts,
        "sentiment_distribution": sentiment_counts,
        "insight_types": insight_type_counts,
        "response_patterns": response_patterns,
    }

    # Store in Redis cache (30s TTL)
    await redis_set_json(cache_key, result, ttl_seconds=30)
    return result
