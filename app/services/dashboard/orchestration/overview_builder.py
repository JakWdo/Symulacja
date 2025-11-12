"""Overview Builder - Generowanie dashboard overview z metrykami i trendami.

Moduł odpowiada za:
- Budowanie karty overview dashboardu (8 metric cards)
- Kalkulację trendów (build_trend helper)
- Agregację danych z różnych źródeł
- Caching wyników w Redis (30s TTL)
"""

import logging
from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DashboardMetric, InsightEvidence, Project
from app.services.dashboard.metrics import DashboardMetricsService
from app.services.dashboard.insights import QuickActionsService
from app.services.dashboard.metrics import ProjectHealthService
from app.core.redis import redis_get_json, redis_set_json
from app.utils import get_utc_now

logger = logging.getLogger(__name__)


def build_trend(
    current_value: float | None,
    previous_value: float | None,
    *,
    invert: bool = False
) -> dict[str, Any] | None:
    """Helper to build trend dictionary.

    Args:
        current_value: Current numeric value
        previous_value: Previous numeric value
        invert: Treat decrease as positive trend

    Returns:
        Trend dict or None if not enough data
    """
    if current_value is None or previous_value is None:
        return None

    if previous_value == 0:
        if current_value == 0:
            change_percent = 0.0
        else:
            change_percent = 100.0
    else:
        change_percent = ((current_value - previous_value) / abs(previous_value)) * 100.0

    direction = "stable"
    if change_percent > 0.5:
        direction = "up"
    elif change_percent < -0.5:
        direction = "down"

    if invert and direction != "stable":
        direction = "down" if direction == "up" else "up"

    return {
        "value": current_value,
        "change_percent": change_percent,
        "direction": direction,
    }


async def get_dashboard_overview(
    db: AsyncSession,
    user_id: UUID,
    metrics_service: DashboardMetricsService,
    health_service: ProjectHealthService,
    quick_actions_service: QuickActionsService,
) -> dict[str, Any]:
    """Pobierz overview dashboardu (8 metric cards + caching).

    Cached: Redis 30s

    Returns:
        {
            "active_research": MetricCard,
            "pending_actions": MetricCard,
            "insights_ready": MetricCard,
            "this_week_activity": MetricCard,
            "time_to_insight": MetricCard,
            "insight_adoption_rate": MetricCard,
            "persona_coverage": MetricCard,
            "blockers_count": MetricCard,
        }
    """
    # Check Redis cache (30s TTL)
    cache_key = f"dashboard:overview:{user_id}"
    cached = await redis_get_json(cache_key)
    if cached is not None:
        return cached

    last_state_key = f"dashboard:overview:last-state:{user_id}"
    previous_state = await redis_get_json(last_state_key) or {}

    now = get_utc_now()
    this_week_start = now - timedelta(days=now.weekday())
    this_week_start = this_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    last_week_start = this_week_start - timedelta(days=7)
    last_week_end = this_week_start

    # Count active projects
    active_projects_count = await db.scalar(
        select(func.count(Project.id)).where(
            and_(
                Project.owner_id == user_id,
                Project.is_active.is_(True),
                Project.deleted_at.is_(None),
            )
        )
    )

    # Count pending actions
    actions = await quick_actions_service.recommend_actions(user_id, limit=10)
    pending_actions_count = len(actions)

    # Count unviewed insights
    insights_ready_count = await db.scalar(
        select(func.count(InsightEvidence.id))
        .join(Project, InsightEvidence.project_id == Project.id)
        .where(
            and_(
                Project.owner_id == user_id,
                InsightEvidence.viewed_at.is_(None),
            )
        )
    )

    # Weekly trends
    trends = await metrics_service.get_weekly_trends(user_id)
    this_week_total = (
        trends["this_week"]["personas_generated"]
        + trends["this_week"]["focus_groups_completed"]
        + trends["this_week"]["insights_extracted"]
    )
    last_week_total = (
        trends["last_week"]["personas_generated"]
        + trends["last_week"]["focus_groups_completed"]
        + trends["last_week"]["insights_extracted"]
    )
    activity_trend = build_trend(this_week_total, last_week_total)

    # TTI metrics
    tti_overall = await metrics_service.calculate_time_to_insight(user_id)
    tti_current = await metrics_service.calculate_time_to_insight(
        user_id, start_date=this_week_start, end_date=now
    )
    tti_previous = await metrics_service.calculate_time_to_insight(
        user_id, start_date=last_week_start, end_date=last_week_end
    )

    tti_median_minutes = (
        (tti_overall["median_seconds"] / 60) if tti_overall["median_seconds"] else None
    )
    tti_current_minutes = (
        (tti_current["median_seconds"] / 60) if tti_current["median_seconds"] else None
    )
    tti_previous_minutes = (
        (tti_previous["median_seconds"] / 60) if tti_previous["median_seconds"] else None
    )
    tti_trend = build_trend(tti_current_minutes, tti_previous_minutes, invert=True)

    # Adoption rate
    adoption_overall = await metrics_service.calculate_adoption_rate(user_id)
    adoption_current = await metrics_service.calculate_adoption_rate(
        user_id, start_date=this_week_start, end_date=now
    )
    adoption_previous = await metrics_service.calculate_adoption_rate(
        user_id, start_date=last_week_start, end_date=last_week_end
    )
    adoption_trend = build_trend(adoption_current, adoption_previous)

    # Persona coverage
    persona_coverage = await metrics_service.calculate_persona_coverage(user_id)

    # Blockers count
    blockers_count = 0
    projects_stmt = select(Project).where(
        and_(
            Project.owner_id == user_id,
            Project.is_active.is_(True),
            Project.deleted_at.is_(None),
        )
    )
    result = await db.execute(projects_stmt)
    projects = list(result.scalars().all())

    for project in projects:
        health = await health_service.assess_project_health(project.id)
        if health["health_status"] != "on_track":
            blockers_count += 1

    # Get previous metric for trend baseline
    previous_metric_stmt = (
        select(DashboardMetric)
        .where(DashboardMetric.user_id == user_id)
        .order_by(DashboardMetric.metric_date.desc())
        .limit(1)
    )
    previous_metric_result = await db.execute(previous_metric_stmt)
    previous_metric = previous_metric_result.scalar_one_or_none()

    # Build trends
    active_trend = build_trend(
        float(active_projects_count or 0),
        float(previous_state.get("active_research"))
        if "active_research" in previous_state
        else (float(previous_metric.active_projects_count) if previous_metric else None),
    )
    pending_trend = build_trend(
        float(pending_actions_count),
        float(previous_state.get("pending_actions")) if "pending_actions" in previous_state else None,
    )
    insights_trend = build_trend(
        float(insights_ready_count or 0),
        float(previous_state.get("insights_ready")) if "insights_ready" in previous_state else None,
    )
    coverage_trend = build_trend(
        float(persona_coverage),
        float(previous_state.get("persona_coverage"))
        if "persona_coverage" in previous_state
        else (
            float(previous_metric.persona_coverage_avg)
            if previous_metric and previous_metric.persona_coverage_avg is not None
            else None
        ),
    )
    blockers_trend = build_trend(
        float(blockers_count),
        float(previous_state.get("blockers_count"))
        if "blockers_count" in previous_state
        else (float(previous_metric.blocked_projects_count) if previous_metric else None),
    )

    # Build overview response
    overview = {
        "active_research": {
            "label": "Aktywne badania",
            "value": str(active_projects_count or 0),
            "raw_value": active_projects_count or 0,
            "trend": active_trend,
            "tooltip": "Liczba aktywnych projektów badawczych",
        },
        "pending_actions": {
            "label": "Oczekujące akcje",
            "value": str(pending_actions_count),
            "raw_value": pending_actions_count,
            "trend": pending_trend,
            "tooltip": "Zalecane akcje do wykonania",
        },
        "insights_ready": {
            "label": "Spostrzeżenia gotowe",
            "value": str(insights_ready_count or 0),
            "raw_value": insights_ready_count or 0,
            "trend": insights_trend,
            "tooltip": "Nowe spostrzeżenia do przejrzenia",
        },
        "this_week_activity": {
            "label": "Ten tydzień",
            "value": str(this_week_total),
            "raw_value": this_week_total,
            "trend": activity_trend,
            "tooltip": "Całkowita aktywność w tym tygodniu (persony + grupy fokusowe + spostrzeżenia)",
        },
        "time_to_insight": {
            "label": "Czas do spostrzeżenia",
            "value": (
                f"{tti_median_minutes:.1f} min"
                if tti_median_minutes
                else "Brak danych"
            ),
            "raw_value": tti_median_minutes if tti_median_minutes is not None else 0.0,
            "trend": tti_trend,
            "tooltip": "Mediana czasu od utworzenia projektu do pierwszego spostrzeżenia",
        },
        "insight_adoption_rate": {
            "label": "Wskaźnik adopcji",
            "value": f"{adoption_overall * 100:.0f}%",
            "raw_value": adoption_overall,
            "trend": adoption_trend,
            "tooltip": "Procent spostrzeżeń, na które podjęto działania (wyświetlone/udostępnione/wyeksportowane/zaadoptowane)",
        },
        "persona_coverage": {
            "label": "Pokrycie person",
            "value": f"{persona_coverage * 100:.0f}%",
            "raw_value": persona_coverage,
            "trend": coverage_trend,
            "tooltip": "Średnie pokrycie demograficzne w projektach",
        },
        "blockers_count": {
            "label": "Projekty z problemami",
            "value": str(blockers_count),
            "raw_value": blockers_count,
            "trend": blockers_trend,
            "tooltip": "Projekty z problemami lub zagrożone",
        },
    }

    # Save current state for next trend calculation
    await redis_set_json(
        last_state_key,
        {
            "active_research": float(active_projects_count or 0),
            "pending_actions": float(pending_actions_count),
            "insights_ready": float(insights_ready_count or 0),
            "persona_coverage": float(persona_coverage),
            "blockers_count": float(blockers_count),
        },
        ttl_seconds=86400,
    )

    # Cache overview (30s TTL)
    await redis_set_json(cache_key, overview, ttl_seconds=30)
    return overview
