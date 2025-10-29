"""
Dashboard Orchestrator - Główny serwis agregujący dane dashboardu

Orkiestruje wszystkie serwisy dashboard:
- Metrics, Health, QuickActions, Insights, Usage, Notifications
- Caching wyników w Redis (30s TTL)
- Formatowanie odpowiedzi API
"""

import json
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, func

from app.models import DashboardMetric, InsightEvidence, Project
from app.services.dashboard.health_service import ProjectHealthService
from app.services.dashboard.insight_traceability_service import InsightTraceabilityService
from app.services.dashboard.metrics_service import DashboardMetricsService
from app.services.dashboard.notification_service import NotificationService
from app.services.dashboard.quick_actions_service import QuickActionsService
from app.services.dashboard.usage_tracking_service import UsageTrackingService
from app.core.redis import redis_get_json, redis_set_json


class DashboardOrchestrator:
    """
    Orchestrator agregujący wszystkie serwisy dashboard

    Odpowiedzialny za:
    - Agregację danych z wielu serwisów
    - Caching w Redis
    - Formatowanie odpowiedzi API
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

        now = datetime.utcnow()
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
        tti_p90_minutes = (
            (tti_overall["p90_seconds"] / 60) if tti_overall["p90_seconds"] else None
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

    async def get_weekly_completion(
        self, user_id: UUID, weeks: int = 8, project_id: UUID | None = None
    ) -> dict[str, Any]:
        """
        Pobierz weekly completion chart data

        Cached: Redis 30s

        Args:
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

        # Import models
        from app.models import FocusGroup, Persona, Survey

        now = datetime.utcnow()
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
            personas_count = await self.db.scalar(
                select(func.count(Persona.id))
                .join(Project, Persona.project_id == Project.id)
                .where(and_(*personas_filters))
            )
            personas_data.append(personas_count or 0)

            # Count focus groups
            focus_groups_count = await self.db.scalar(
                select(func.count(FocusGroup.id))
                .join(Project, FocusGroup.project_id == Project.id)
                .where(and_(*focus_groups_filters))
            )
            focus_groups_data.append(focus_groups_count or 0)

            # Count surveys
            surveys_count = await self.db.scalar(
                select(func.count(Survey.id))
                .join(Project, Survey.project_id == Project.id)
                .where(and_(*surveys_filters))
            )
            surveys_data.append(surveys_count or 0)

            # Count insights
            insights_count = await self.db.scalar(
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
            delta = datetime.utcnow() - insight.created_at
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
        delta = datetime.utcnow() - insight.created_at
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

    async def get_usage_budget(self, user_id: UUID) -> dict[str, Any]:
        """
        Pobierz token usage, costs, forecast, alerts

        Cached: Redis 60s

        Returns:
            Usage & budget data
        """
        # Check Redis cache (60s TTL - usage changes less frequently)
        cache_key = f"dashboard:usage:{user_id}"
        cached = await redis_get_json(cache_key)
        if cached is not None:
            return cached

        # Calculate current month costs
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        costs = await self.usage_service.calculate_costs(
            user_id, start_date=month_start
        )

        # Get user to determine budget limit based on plan
        from app.models import User

        user_stmt = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        # Determine budget limit: user custom limit > plan-based limit > fallback
        if user and user.budget_limit is not None:
            # User has set custom budget limit in Settings
            budget_limit = user.budget_limit
        elif user and user.plan:
            # Fallback to plan-based budget limits
            budget_map = {
                "free": 50.0,
                "pro": 100.0,
                "enterprise": 500.0,
            }
            budget_limit = budget_map.get(user.plan, 100.0)  # default to pro if unknown plan
        else:
            budget_limit = 100.0  # fallback

        forecast = await self.usage_service.forecast_budget(user_id, budget_limit)

        # Alerts
        alerts = await self.usage_service.check_budget_alerts(user_id, budget_limit)

        # History (last 30 days)
        history = []
        for i in range(29, -1, -1):
            day = now - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            day_costs = await self.usage_service.calculate_costs(
                user_id, start_date=day_start, end_date=day_end
            )

            history.append(
                {
                    "date": day_start.strftime("%Y-%m-%d"),
                    "total_tokens": day_costs["total_tokens"],
                    "total_cost": day_costs["total_cost"],
                }
            )

        result = {
            "total_tokens": costs["total_tokens"],
            "total_cost": costs["total_cost"],
            "forecast_month_end": forecast["forecast_month_end"],
            "budget_limit": budget_limit,
            "alerts": alerts,
            "history": history,
            "alert_thresholds": {
                "warning": user.warning_threshold if user and user.warning_threshold is not None else 80,
                "critical": user.critical_threshold if user and user.critical_threshold is not None else 90,
            },
        }

        # Store in Redis cache (60s TTL)
        await redis_set_json(cache_key, result, ttl_seconds=60)
        return result

    async def get_insight_analytics(
        self, user_id: UUID, project_id: UUID | None = None, top_n: int = 10
    ) -> dict[str, Any]:
        """
        Pobierz insight analytics (top concepts, sentiment, patterns)

        Cached: Redis 30s

        Args:
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

        result = await self.db.execute(stmt)
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
        keyword_patterns = {
            "Price sensitivity": ["price", "pricing", "cost", "expensive", "cheap"],
            "Product quality": ["quality", "durable", "reliable", "defect", "faulty"],
            "Customer experience": ["experience", "journey", "onboarding", "support", "service"],
            "Feature requests": ["feature", "missing", "lack", "add", "improve"],
            "Performance issues": ["slow", "lag", "performance", "crash", "bug"],
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
