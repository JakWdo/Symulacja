"""
Dashboard Metrics Aggregator - Agregacja metryk tygodniowych i chartów

Odpowiedzialny za:
- Agregację danych weekly completion
- Zliczanie persons/focus groups/insights per tydzień
- Formatowanie chart data
"""

from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models import FocusGroup, Persona, Survey, InsightEvidence, Project
from app.core.redis import redis_get_json, redis_set_json
from app.utils import get_utc_now


async def get_weekly_completion(
    db: AsyncSession,
    user_id: UUID,
    weeks: int = 8,
    project_id: UUID | None = None,
) -> dict[str, Any]:
    """
    Pobierz weekly completion chart data

    Cached: Redis 30s

    Args:
        db: Database session
        user_id: UUID użytkownika
        weeks: Liczba tygodni wstecz
        project_id: Opcjonalne UUID projektu (filter dla konkretnego projektu)

    Returns:
        {
            "weeks": ["2025-W01", "2025-W02", ...],
            "personas": [10, 20, ...],
            "focus_groups": [2, 3, ...],
            "insights": [5, 8, ...],
        }
    """
    # Check Redis cache (30s TTL)
    cache_key = f"dashboard:weekly:{user_id}:{weeks}:{project_id or 'all'}"
    cached = await redis_get_json(cache_key)
    if cached is not None:
        return cached

    now = get_utc_now()
    weeks_data = []
    personas_data = []
    focus_groups_data = []
    surveys_data = []
    insights_data = []

    for i in range(weeks - 1, -1, -1):
        # Calculate week start/end
        week_start = now - timedelta(weeks=i)
        week_start = week_start - timedelta(days=week_start.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)

        # Week label (ISO week)
        week_label = week_start.strftime("%Y-W%V")
        weeks_data.append(week_label)

        # Base filters
        personas_filters = [
            Project.owner_id == user_id,
            Project.deleted_at.is_(None),
            Persona.deleted_at.is_(None),
            Persona.created_at >= week_start,
            Persona.created_at < week_end,
        ]
        focus_groups_filters = [
            Project.owner_id == user_id,
            Project.deleted_at.is_(None),
            FocusGroup.deleted_at.is_(None),
            FocusGroup.status == "completed",
            FocusGroup.completed_at >= week_start,
            FocusGroup.completed_at < week_end,
        ]
        surveys_filters = [
            Project.owner_id == user_id,
            Project.deleted_at.is_(None),
            Survey.deleted_at.is_(None),
            Survey.status == "completed",
            Survey.completed_at >= week_start,
            Survey.completed_at < week_end,
        ]
        insights_filters = [
            Project.owner_id == user_id,
            Project.deleted_at.is_(None),
            InsightEvidence.created_at >= week_start,
            InsightEvidence.created_at < week_end,
        ]

        # Add project_id filter if provided
        if project_id:
            personas_filters.append(Persona.project_id == project_id)
            focus_groups_filters.append(FocusGroup.project_id == project_id)
            surveys_filters.append(Survey.project_id == project_id)
            insights_filters.append(InsightEvidence.project_id == project_id)

        # Count personas
        personas_count = await db.scalar(
            select(func.count(Persona.id))
            .join(Project, Persona.project_id == Project.id)
            .where(and_(*personas_filters))
        )
        personas_data.append(personas_count or 0)

        # Count focus groups
        focus_groups_count = await db.scalar(
            select(func.count(FocusGroup.id))
            .join(Project, FocusGroup.project_id == Project.id)
            .where(and_(*focus_groups_filters))
        )
        focus_groups_data.append(focus_groups_count or 0)

        # Count surveys
        surveys_count = await db.scalar(
            select(func.count(Survey.id))
            .join(Project, Survey.project_id == Project.id)
            .where(and_(*surveys_filters))
        )
        surveys_data.append(surveys_count or 0)

        # Count insights
        insights_count = await db.scalar(
            select(func.count(InsightEvidence.id))
            .join(Project, InsightEvidence.project_id == Project.id)
            .where(and_(*insights_filters))
        )
        insights_data.append(insights_count or 0)

    result = {
        "weeks": weeks_data,
        "personas": personas_data,
        "focus_groups": focus_groups_data,
        "surveys": surveys_data,
        "insights": insights_data,
    }

    # Store in Redis cache (30s TTL)
    await redis_set_json(cache_key, result, ttl_seconds=30)
    return result
