"""
Dashboard Core - Główna klasa orkiestracji dashboardu

Orkiestruje wszystkie serwisy dashboard:
- Metrics, Health, QuickActions, Insights, Usage, Notifications
- Caching wyników w Redis (30s TTL)
- Formatowanie odpowiedzi API
- Delegacja do metrics_aggregator, cost_calculator, usage_trends
"""

from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, func

from app.models import DashboardMetric, InsightEvidence, Project
from app.services.dashboard.metrics import ProjectHealthService, DashboardMetricsService, get_weekly_completion
from app.services.dashboard.insights import InsightTraceabilityService, QuickActionsService
from app.services.dashboard.usage import UsageTrackingService, get_insight_analytics
from app.services.dashboard.costs import get_usage_budget
from app.services.dashboard.notification_service import NotificationService
from app.core.redis import redis_get_json, redis_set_json
from app.utils import get_utc_now


class DashboardOrchestrator:
    """
    Orchestrator agregujący wszystkie serwisy dashboard

    Odpowiedzialny za:
    - Agregację danych z wielu serwisów
    - Caching w Redis
    - Formatowanie odpowiedzi API
    - Delegację do wyspecjalizowanych modułów
    """

    def __init__(
        self,
        db: AsyncSession,
        metrics_service: DashboardMetricsService,
        health_service: ProjectHealthService,
        quick_actions_service: QuickActionsService,
        insight_service: InsightTraceabilityService,
        usage_service: UsageTrackingService,
        notification_service: NotificationService,
    ):
        self.db = db
        self.metrics_service = metrics_service
        self.health_service = health_service
        self.quick_actions_service = quick_actions_service
        self.insight_service = insight_service
        self.usage_service = usage_service
        self.notification_service = notification_service

    async def get_dashboard_overview(self, user_id: UUID) -> dict[str, Any]:
        """
        Pobierz overview dashboardu (4 karty + extensions)

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

        def build_trend(current_value: float | None, previous_value: float | None, *, invert: bool = False) -> dict[str, Any] | None:
            """
            Helper to build trend dictionary.

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

        now = get_utc_now()
        this_week_start = now - timedelta(days=now.weekday())
        this_week_start = this_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        last_week_start = this_week_start - timedelta(days=7)
        last_week_end = this_week_start

        # Count active projects
        active_projects_count = await self.db.scalar(
            select(func.count(Project.id)).where(
                and_(
                    Project.owner_id == user_id,
                    Project.is_active.is_(True),
                    Project.deleted_at.is_(None),
                )
            )
        )

        # Count pending actions
        actions = await self.quick_actions_service.recommend_actions(user_id, limit=10)
        pending_actions_count = len(actions)

        # Count unviewed insights
        insights_ready_count = await self.db.scalar(
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
        trends = await self.metrics_service.get_weekly_trends(user_id)
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
        tti_overall = await self.metrics_service.calculate_time_to_insight(user_id)
        tti_current = await self.metrics_service.calculate_time_to_insight(
            user_id, start_date=this_week_start, end_date=now
        )
        tti_previous = await self.metrics_service.calculate_time_to_insight(
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
        adoption_overall = await self.metrics_service.calculate_adoption_rate(user_id)
        adoption_current = await self.metrics_service.calculate_adoption_rate(
            user_id, start_date=this_week_start, end_date=now
        )
        adoption_previous = await self.metrics_service.calculate_adoption_rate(
            user_id, start_date=last_week_start, end_date=last_week_end
        )
        adoption_trend = build_trend(adoption_current, adoption_previous)

        # Persona coverage
        persona_coverage = await self.metrics_service.calculate_persona_coverage(
            user_id
        )

        # Blockers count
        # Count projects with blockers (health_status != 'on_track')
        blockers_count = 0
        projects_stmt = select(Project).where(
            and_(
                Project.owner_id == user_id,
                Project.is_active.is_(True),
                Project.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(projects_stmt)
        projects = list(result.scalars().all())

        for project in projects:
            health = await self.health_service.assess_project_health(project.id)
            if health["health_status"] != "on_track":
                blockers_count += 1

        previous_metric_stmt = (
            select(DashboardMetric)
            .where(DashboardMetric.user_id == user_id)
            .order_by(DashboardMetric.metric_date.desc())
            .limit(1)
        )
        previous_metric_result = await self.db.execute(previous_metric_stmt)
        previous_metric = previous_metric_result.scalar_one_or_none()

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

        await redis_set_json(cache_key, overview, ttl_seconds=30)
        return overview

    async def get_active_projects(
        self, user_id: UUID
    ) -> list[dict[str, Any]]:
        """
        Pobierz active projects z health status, progress, insights count

        Returns:
            Lista projektów z health, progress stages, insights count
        """
        stmt = (
            select(Project)
            .where(
                and_(
                    Project.owner_id == user_id,
                    Project.is_active.is_(True),
                    Project.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(Project.personas),
                selectinload(Project.focus_groups),
            )
            .order_by(Project.updated_at.desc())
            .limit(10)
        )

        result = await self.db.execute(stmt)
        projects = list(result.scalars().all())

        # Optimize N+1: Get all insights counts in one query with GROUP BY
        project_ids = [p.id for p in projects]

        # Total insights per project
        insights_counts_stmt = (
            select(
                InsightEvidence.project_id,
                func.count(InsightEvidence.id).label("count")
            )
            .where(InsightEvidence.project_id.in_(project_ids))
            .group_by(InsightEvidence.project_id)
        )
        insights_counts_result = await self.db.execute(insights_counts_stmt)
        insights_counts_map = {row.project_id: row.count for row in insights_counts_result}

        # New (unviewed) insights per project
        new_insights_counts_stmt = (
            select(
                InsightEvidence.project_id,
                func.count(InsightEvidence.id).label("count")
            )
            .where(
                and_(
                    InsightEvidence.project_id.in_(project_ids),
                    InsightEvidence.viewed_at.is_(None),
                )
            )
            .group_by(InsightEvidence.project_id)
        )
        new_insights_counts_result = await self.db.execute(new_insights_counts_stmt)
        new_insights_counts_map = {row.project_id: row.count for row in new_insights_counts_result}

        output = []
        for project in projects:
            # Get health
            health = await self.health_service.assess_project_health(project.id)

            # Progress stages (filter soft-deleted)
            has_demographics = bool(project.target_demographics)
            active_personas = [p for p in project.personas if p.deleted_at is None]
            active_focus_groups = [fg for fg in project.focus_groups if fg.deleted_at is None]
            has_personas = bool(active_personas and len(active_personas) > 0)
            has_focus = bool(active_focus_groups and len(active_focus_groups) > 0)

            # Get insights counts from pre-fetched maps (N+1 optimization)
            insights_count = insights_counts_map.get(project.id, 0)
            new_insights_count = new_insights_counts_map.get(project.id, 0)

            # Determine current stage
            if not has_personas:
                current_stage = "demographics"
            elif not has_focus:
                current_stage = "personas"
            elif insights_count == 0:
                current_stage = "focus"
            else:
                current_stage = "analysis"

            # Determine status (use active_focus_groups filtered above)
            if health["health_status"] == "blocked":
                status = "blocked"
            elif any(fg.status == "in_progress" for fg in active_focus_groups):
                status = "running"
            elif active_focus_groups and all(fg.status == "completed" for fg in active_focus_groups):
                status = "completed"
            else:
                status = "paused"

            # CTA
            if health["health_status"] == "blocked":
                cta_label = "Fix Issues"
                cta_url = f"/projects/{project.id}"
            elif not has_personas:
                cta_label = "Generate Personas"
                cta_url = f"/projects/{project.id}/personas/generate"
            elif not has_focus:
                cta_label = "Start Focus Group"
                cta_url = f"/projects/{project.id}/focus-groups/create"
            elif new_insights_count > 0:
                cta_label = "View Insights"
                cta_url = f"/projects/{project.id}/insights"
            else:
                cta_label = "View Project"
                cta_url = f"/projects/{project.id}"

            output.append(
                {
                    "id": str(project.id),
                    "name": project.name,
                    "status": status,
                    "health": {
                        "status": health["health_status"],
                        "score": health["health_score"],
                        "color": (
                            "green"
                            if health["health_status"] == "on_track"
                            else "yellow"
                            if health["health_status"] == "at_risk"
                            else "red"
                        ),
                    },
                    "progress": {
                        "demographics": has_demographics,
                        "personas": has_personas,
                        "focus": has_focus,
                        "analysis": insights_count > 0,
                        "current_stage": current_stage,
                    },
                    "insights_count": insights_count or 0,
                    "new_insights_count": new_insights_count or 0,
                    "last_activity": project.updated_at,
                    "cta_label": cta_label,
                    "cta_url": cta_url,
                }
            )

        return output

    # Delegated methods
    async def get_weekly_completion(
        self, user_id: UUID, weeks: int = 8, project_id: UUID | None = None
    ) -> dict[str, Any]:
        """Deleguj do metrics_aggregator"""
        return await get_weekly_completion(self.db, user_id, weeks, project_id)

    async def get_usage_budget(self, user_id: UUID) -> dict[str, Any]:
        """Deleguj do cost_calculator"""
        return await get_usage_budget(self.db, self.usage_service, user_id)

    async def get_insight_analytics(
        self, user_id: UUID, project_id: UUID | None = None, top_n: int = 10
    ) -> dict[str, Any]:
        """Deleguj do usage_trends"""
        return await get_insight_analytics(self.db, user_id, project_id, top_n)

    # Remaining core methods
    async def get_latest_insights(
        self, user_id: UUID, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Pobierz latest insights (highlights)

        Returns:
            Lista insight highlights
        """
        stmt = (
            select(InsightEvidence)
            .join(Project, InsightEvidence.project_id == Project.id)
            .where(
                and_(
                    Project.owner_id == user_id,
                    Project.deleted_at.is_(None),
                )
            )
            .order_by(InsightEvidence.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        insights = list(result.scalars().all())

        # Get project names
        project_ids = list(set(ins.project_id for ins in insights))
        projects_stmt = select(Project).where(Project.id.in_(project_ids))
        projects_result = await self.db.execute(projects_stmt)
        projects_map = {p.id: p for p in projects_result.scalars().all()}

        output = []
        for insight in insights:
            project = projects_map.get(insight.project_id)
            project_name = project.name if project else "Unknown"

            # Calculate time ago
            delta = get_utc_now() - insight.created_at
            if delta.days > 0:
                time_ago = f"{delta.days} days ago"
            elif delta.seconds > 3600:
                time_ago = f"{delta.seconds // 3600} hours ago"
            else:
                time_ago = f"{delta.seconds // 60} minutes ago"

            output.append(
                {
                    "id": str(insight.id),
                    "project_id": str(insight.project_id),
                    "project_name": project_name,
                    "insight_type": insight.insight_type,
                    "insight_text": insight.insight_text,
                    "confidence_score": insight.confidence_score,
                    "impact_score": insight.impact_score,
                    "time_ago": time_ago,
                    "evidence_count": len(insight.evidence),
                    "is_viewed": insight.viewed_at is not None,
                    "is_adopted": insight.adopted_at is not None,
                }
            )

        return output

    async def get_insight_detail(
        self, insight_id: UUID, user_id: UUID
    ) -> dict[str, Any]:
        """
        Pobierz insight detail z evidence trail

        Args:
            insight_id: UUID insightu
            user_id: UUID użytkownika (security check)

        Returns:
            Insight detail z evidence, provenance
        """
        stmt = (
            select(InsightEvidence)
            .join(Project, InsightEvidence.project_id == Project.id)
            .where(
                and_(
                    InsightEvidence.id == insight_id,
                    Project.owner_id == user_id,
                )
            )
        )

        result = await self.db.execute(stmt)
        insight = result.scalar_one()

        # Get project name
        project_stmt = select(Project).where(Project.id == insight.project_id)
        project_result = await self.db.execute(project_stmt)
        project = project_result.scalar_one()

        # Calculate time ago
        delta = get_utc_now() - insight.created_at
        if delta.days > 0:
            time_ago = f"{delta.days} days ago"
        elif delta.seconds > 3600:
            time_ago = f"{delta.seconds // 3600} hours ago"
        else:
            time_ago = f"{delta.seconds // 60} minutes ago"

        # Mark as viewed (if not already)
        if not insight.viewed_at:
            await self.insight_service.track_insight_adoption(insight_id, "viewed")

        return {
            "id": str(insight.id),
            "project_id": str(insight.project_id),
            "project_name": project.name,
            "insight_type": insight.insight_type,
            "insight_text": insight.insight_text,
            "confidence_score": insight.confidence_score,
            "impact_score": insight.impact_score,
            "time_ago": time_ago,
            "evidence_count": len(insight.evidence),
            "is_viewed": insight.viewed_at is not None,
            "is_adopted": insight.adopted_at is not None,
            "evidence": insight.evidence,
            "concepts": insight.concepts,
            "sentiment": insight.sentiment,
            "provenance": {
                "model_version": insight.model_version,
                "prompt_hash": insight.prompt_hash,
                "sources": insight.sources,
                "created_at": insight.created_at,
            },
        }

    async def get_health_blockers(self, user_id: UUID) -> dict[str, Any]:
        """
        Pobierz health summary + blockers list

        Returns:
            {
                "summary": {"on_track": 5, "at_risk": 2, "blocked": 1},
                "blockers": [...],
            }
        """
        projects_stmt = select(Project).where(
            and_(
                Project.owner_id == user_id,
                Project.is_active.is_(True),
                Project.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(projects_stmt)
        projects = list(result.scalars().all())

        summary = {"on_track": 0, "at_risk": 0, "blocked": 0}
        all_blockers = []

        for project in projects:
            health = await self.health_service.assess_project_health(project.id)
            summary[health["health_status"]] += 1

            # Add blockers with project context
            for blocker in health["blockers"]:
                all_blockers.append(
                    {
                        **blocker,
                        "project_id": str(project.id),
                        "project_name": project.name,
                    }
                )

        return {"summary": summary, "blockers": all_blockers}
