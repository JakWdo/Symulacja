"""
Dashboard Core - Główna klasa orkiestracji dashboardu

Orkiestruje wszystkie serwisy dashboard:
- Metrics, Health, QuickActions, Insights, Usage, Notifications
- Caching wyników w Redis (30s TTL)
- Formatowanie odpowiedzi API
- Delegacja do orchestration modules (overview_builder, projects_builder, insights_builder)

**Architecture**: Thin orchestrator delegating to specialized modules.
"""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.dashboard.metrics import ProjectHealthService, DashboardMetricsService
from app.services.dashboard.insights import InsightTraceabilityService, QuickActionsService
from app.services.dashboard.usage import UsageTrackingService, get_insight_analytics
from app.services.dashboard.costs import get_usage_budget
from app.services.dashboard.notification_service import NotificationService
from app.services.dashboard.orchestration import (
    get_dashboard_overview,
    get_active_projects,
    get_latest_insights,
    get_insight_detail,
    get_health_blockers,
)
from app.services.dashboard.metrics import get_weekly_completion


class DashboardOrchestrator:
    """
    Orchestrator agregujący wszystkie serwisy dashboard

    Odpowiedzialny za:
    - Agregację danych z wielu serwisów
    - Caching w Redis
    - Formatowanie odpowiedzi API
    - Delegację do wyspecjalizowanych modułów (orchestration/)

    **Architecture:**
    - overview_builder: Dashboard overview + 8 metric cards
    - projects_builder: Active projects + health + progress
    - insights_builder: Latest insights + detail + blockers
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

    # === Delegated to orchestration/ modules ===

    async def get_dashboard_overview(self, user_id: UUID) -> dict[str, Any]:
        """
        Pobierz overview dashboardu (8 metric cards)

        Cached: Redis 30s

        Deleguje do: orchestration.overview_builder.get_dashboard_overview

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
        return await get_dashboard_overview(
            db=self.db,
            user_id=user_id,
            metrics_service=self.metrics_service,
            health_service=self.health_service,
            quick_actions_service=self.quick_actions_service,
        )

    async def get_active_projects(
        self, user_id: UUID
    ) -> list[dict[str, Any]]:
        """
        Pobierz active projects z health status, progress, insights count

        Deleguje do: orchestration.projects_builder.get_active_projects

        Returns:
            Lista projektów z health, progress stages, insights count
        """
        return await get_active_projects(
            db=self.db,
            user_id=user_id,
            health_service=self.health_service,
        )

    async def get_latest_insights(
        self, user_id: UUID, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Pobierz latest insights (highlights)

        Deleguje do: orchestration.insights_builder.get_latest_insights

        Returns:
            Lista insight highlights
        """
        return await get_latest_insights(
            db=self.db,
            user_id=user_id,
            limit=limit
        )

    async def get_insight_detail(
        self, insight_id: UUID, user_id: UUID
    ) -> dict[str, Any]:
        """
        Pobierz insight detail z evidence trail

        Deleguje do: orchestration.insights_builder.get_insight_detail

        Args:
            insight_id: UUID insightu
            user_id: UUID użytkownika (security check)

        Returns:
            Insight detail z evidence, provenance
        """
        return await get_insight_detail(
            db=self.db,
            insight_id=insight_id,
            user_id=user_id,
            insight_service=self.insight_service,
        )

    async def get_health_blockers(self, user_id: UUID) -> dict[str, Any]:
        """
        Pobierz health summary + blockers list

        Deleguje do: orchestration.insights_builder.get_health_blockers

        Returns:
            {
                "summary": {"on_track": 5, "at_risk": 2, "blocked": 1},
                "blockers": [...],
            }
        """
        return await get_health_blockers(
            db=self.db,
            user_id=user_id,
            health_service=self.health_service,
        )

    # === Delegated to utility modules (already thin) ===

    async def get_weekly_completion(
        self, user_id: UUID, weeks: int = 8, project_id: UUID | None = None
    ) -> dict[str, Any]:
        """Deleguj do metrics_aggregator.get_weekly_completion"""
        return await get_weekly_completion(self.db, user_id, weeks, project_id)

    async def get_usage_budget(self, user_id: UUID) -> dict[str, Any]:
        """Deleguj do costs.get_usage_budget"""
        return await get_usage_budget(self.db, self.usage_service, user_id)

    async def get_insight_analytics(
        self, user_id: UUID, project_id: UUID | None = None, top_n: int = 10
    ) -> dict[str, Any]:
        """Deleguj do usage.get_insight_analytics"""
        return await get_insight_analytics(self.db, user_id, project_id, top_n)
