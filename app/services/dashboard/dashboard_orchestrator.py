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

from app.models import InsightEvidence, Project
from app.services.dashboard.health_service import ProjectHealthService
from app.services.dashboard.insight_traceability_service import InsightTraceabilityService
from app.services.dashboard.metrics_service import DashboardMetricsService
from app.services.dashboard.notification_service import NotificationService
from app.services.dashboard.quick_actions_service import QuickActionsService
from app.services.dashboard.usage_tracking_service import UsageTrackingService


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
        # TODO: Redis caching (skipped for MVP, add later)
        # cache_key = f"dashboard:overview:{user_id}"

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

        # TTI metrics
        tti = await self.metrics_service.calculate_time_to_insight(user_id)
        tti_median_minutes = (
            (tti["median_seconds"] / 60) if tti["median_seconds"] else None
        )

        # Adoption rate
        adoption_rate = await self.metrics_service.calculate_adoption_rate(user_id)

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

        # Format response
        return {
            "active_research": {
                "label": "Active Research",
                "value": str(active_projects_count or 0),
                "raw_value": active_projects_count or 0,
                "trend": None,  # TODO: Add w/w trend
                "tooltip": "Number of active research projects",
            },
            "pending_actions": {
                "label": "Pending Actions",
                "value": str(pending_actions_count),
                "raw_value": pending_actions_count,
                "trend": None,
                "tooltip": "Recommended actions to take",
            },
            "insights_ready": {
                "label": "Insights Ready",
                "value": str(insights_ready_count or 0),
                "raw_value": insights_ready_count or 0,
                "trend": None,
                "tooltip": "New insights to review",
            },
            "this_week_activity": {
                "label": "This Week",
                "value": str(this_week_total),
                "raw_value": this_week_total,
                "trend": None,
                "tooltip": "Total activity this week (personas + focus groups + insights)",
            },
            "time_to_insight": {
                "label": "Time to Insight",
                "value": (
                    f"{tti_median_minutes:.1f} min"
                    if tti_median_minutes
                    else "No data"
                ),
                "raw_value": tti_median_minutes or 0,
                "trend": None,
                "tooltip": "Median time from project creation to first insight",
            },
            "insight_adoption_rate": {
                "label": "Adoption Rate",
                "value": f"{adoption_rate * 100:.0f}%",
                "raw_value": adoption_rate,
                "trend": None,
                "tooltip": "Percentage of insights acted upon (viewed/shared/exported/adopted)",
            },
            "persona_coverage": {
                "label": "Persona Coverage",
                "value": f"{persona_coverage * 100:.0f}%",
                "raw_value": persona_coverage,
                "trend": None,
                "tooltip": "Average demographic coverage across projects",
            },
            "blockers_count": {
                "label": "Projects with Issues",
                "value": str(blockers_count),
                "raw_value": blockers_count,
                "trend": None,
                "tooltip": "Projects with blockers or at risk",
            },
        }

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

        output = []
        for project in projects:
            # Get health
            health = await self.health_service.assess_project_health(project.id)

            # Progress stages
            has_demographics = bool(project.target_demographics)
            has_personas = bool(project.personas and len(project.personas) > 0)
            has_focus = bool(
                project.focus_groups and len(project.focus_groups) > 0
            )

            # Count insights
            insights_count = await self.db.scalar(
                select(func.count(InsightEvidence.id)).where(
                    InsightEvidence.project_id == project.id
                )
            )

            # Count new (unviewed) insights
            new_insights_count = await self.db.scalar(
                select(func.count(InsightEvidence.id)).where(
                    and_(
                        InsightEvidence.project_id == project.id,
                        InsightEvidence.viewed_at.is_(None),
                    )
                )
            )

            # Determine current stage
            if not has_personas:
                current_stage = "demographics"
            elif not has_focus:
                current_stage = "personas"
            elif insights_count == 0:
                current_stage = "focus"
            else:
                current_stage = "analysis"

            # Determine status
            if health["health_status"] == "blocked":
                status = "blocked"
            elif any(fg.status == "in_progress" for fg in project.focus_groups):
                status = "running"
            elif all(fg.status == "completed" for fg in project.focus_groups):
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
        self, user_id: UUID, weeks: int = 8
    ) -> dict[str, Any]:
        """
        Pobierz weekly completion chart data

        Args:
            user_id: UUID użytkownika
            weeks: Liczba tygodni wstecz

        Returns:
            {
                "weeks": ["2025-W01", "2025-W02", ...],
                "personas": [10, 20, ...],
                "focus_groups": [2, 3, ...],
                "insights": [5, 8, ...],
            }
        """
        # Import models
        from app.models import FocusGroup, Persona

        now = datetime.utcnow()
        weeks_data = []
        personas_data = []
        focus_groups_data = []
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

            # Count personas
            personas_count = await self.db.scalar(
                select(func.count(Persona.id))
                .join(Project, Persona.project_id == Project.id)
                .where(
                    and_(
                        Project.owner_id == user_id,
                        Persona.created_at >= week_start,
                        Persona.created_at < week_end,
                    )
                )
            )
            personas_data.append(personas_count or 0)

            # Count focus groups
            focus_groups_count = await self.db.scalar(
                select(func.count(FocusGroup.id))
                .join(Project, FocusGroup.project_id == Project.id)
                .where(
                    and_(
                        Project.owner_id == user_id,
                        FocusGroup.status == "completed",
                        FocusGroup.updated_at >= week_start,
                        FocusGroup.updated_at < week_end,
                    )
                )
            )
            focus_groups_data.append(focus_groups_count or 0)

            # Count insights
            insights_count = await self.db.scalar(
                select(func.count(InsightEvidence.id))
                .join(Project, InsightEvidence.project_id == Project.id)
                .where(
                    and_(
                        Project.owner_id == user_id,
                        InsightEvidence.created_at >= week_start,
                        InsightEvidence.created_at < week_end,
                    )
                )
            )
            insights_data.append(insights_count or 0)

        return {
            "weeks": weeks_data,
            "personas": personas_data,
            "focus_groups": focus_groups_data,
            "insights": insights_data,
        }

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
            .where(Project.owner_id == user_id)
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

        Returns:
            Usage & budget data
        """
        # Calculate current month costs
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        costs = await self.usage_service.calculate_costs(
            user_id, start_date=month_start
        )

        # Forecast (assume $100 budget limit for MVP)
        budget_limit = 100.0  # TODO: Get from user settings
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

        return {
            "total_tokens": costs["total_tokens"],
            "total_cost": costs["total_cost"],
            "forecast_month_end": forecast["forecast_month_end"],
            "budget_limit": budget_limit,
            "alerts": alerts,
            "history": history,
        }

    async def get_insight_analytics(self, user_id: UUID) -> dict[str, Any]:
        """
        Pobierz insight analytics (top concepts, sentiment, patterns)

        Returns:
            Analytics data
        """
        # Get all insights for user
        stmt = (
            select(InsightEvidence)
            .join(Project, InsightEvidence.project_id == Project.id)
            .where(Project.owner_id == user_id)
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
            )[:10]
        ]

        # Sentiment distribution
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
        for insight in insights:
            sentiment = insight.sentiment or "neutral"
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

        return {
            "top_concepts": top_concepts,
            "sentiment_distribution": sentiment_counts,
            "response_patterns": [],  # TODO: Implement pattern analysis
        }
