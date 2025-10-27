"""
Dashboard Metrics Service - Obliczanie KPI dla dashboardu

Oblicza kluczowe metryki:
- Time-to-Insight (TTI): Mediana + P90 czasu od utworzenia projektu do pierwszego insightu
- Insight Adoption Rate: % insightów adopted/exported/shared
- Persona Coverage: Średnie % demographic coverage (is_statistically_valid)
- Weekly Trends: m/m, w/w changes dla personas/focus groups/insights

Metryki obliczane są asynchronicznie (background jobs) i cache'owane w Redis.
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DashboardMetric, InsightEvidence, Project


class DashboardMetricsService:
    """
    Serwis do obliczania metryk KPI dla dashboardu

    Umożliwia:
    - Obliczenie Time-to-Insight (mediana + P90)
    - Obliczenie Insight Adoption Rate
    - Obliczenie Persona Coverage
    - Obliczenie weekly trends (w/w changes)
    - Zapisywanie metryk dziennych (background job)
    """

    def __init__(self, db: AsyncSession):
        """
        Inicjalizuj serwis

        Args:
            db: Async SQLAlchemy session
        """
        self.db = db

    async def calculate_time_to_insight(
        self,
        user_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Oblicz Time-to-Insight (TTI) dla projektów użytkownika

        TTI = czas od project.created_at do pierwszego InsightEvidence.created_at

        Args:
            user_id: UUID użytkownika
            start_date: Data początkowa filtrowania (optional)
            end_date: Data końcowa filtrowania (optional)

        Returns:
            {
                "median_seconds": float,
                "p90_seconds": float,
                "count": int,  # liczba projektów w sample
            }
        """
        # SQL query:
        # SELECT
        #   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY time_diff) as median,
        #   PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY time_diff) as p90,
        #   COUNT(*) as count
        # FROM (
        #   SELECT EXTRACT(EPOCH FROM (MIN(ie.created_at) - p.created_at)) as time_diff
        #   FROM projects p
        #   JOIN insight_evidences ie ON p.id = ie.project_id
        #   WHERE p.owner_id = :user_id
        #     AND p.deleted_at IS NULL
        #     [AND ie.created_at BETWEEN :start_date AND :end_date]
        #   GROUP BY p.id
        # ) AS subq

        # Subquery: time diff per project
        time_diff_expr = func.extract(
            "epoch",
            func.min(InsightEvidence.created_at) - Project.created_at,
        ).label("time_diff")

        subq = (
            select(time_diff_expr)
            .select_from(Project)
            .join(InsightEvidence, Project.id == InsightEvidence.project_id)
            .where(
                and_(
                    Project.owner_id == user_id,
                    Project.deleted_at.is_(None),
                )
            )
        )

        # Add date filters if provided
        if start_date:
            subq = subq.where(InsightEvidence.created_at >= start_date)
        if end_date:
            subq = subq.where(InsightEvidence.created_at <= end_date)

        subq = subq.group_by(Project.id).subquery()

        # Main query: calculate percentiles
        median_expr = func.percentile_cont(0.5).within_group(subq.c.time_diff).label("median")
        p90_expr = func.percentile_cont(0.9).within_group(subq.c.time_diff).label("p90")
        count_expr = func.count().label("count")

        query = select(median_expr, p90_expr, count_expr).select_from(subq)

        result = await self.db.execute(query)
        row = result.first()

        if not row or row.count == 0:
            return {
                "median_seconds": None,
                "p90_seconds": None,
                "count": 0,
            }

        return {
            "median_seconds": float(row.median) if row.median else None,
            "p90_seconds": float(row.p90) if row.p90 else None,
            "count": int(row.count),
        }

    async def calculate_adoption_rate(
        self,
        user_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> float:
        """
        Oblicz Insight Adoption Rate

        Adoption = insight ma adopted_at LUB exported_at LUB shared_at

        Args:
            user_id: UUID użytkownika
            start_date: Data początkowa filtrowania (optional)
            end_date: Data końcowa filtrowania (optional)

        Returns:
            float (0-1): % adopted insights
        """
        # Count total insights
        total_query = (
            select(func.count(InsightEvidence.id))
            .select_from(InsightEvidence)
            .join(Project, InsightEvidence.project_id == Project.id)
            .where(
                and_(
                    Project.owner_id == user_id,
                    Project.deleted_at.is_(None),
                )
            )
        )

        if start_date:
            total_query = total_query.where(InsightEvidence.created_at >= start_date)
        if end_date:
            total_query = total_query.where(InsightEvidence.created_at <= end_date)

        total_result = await self.db.execute(total_query)
        total_count = total_result.scalar_one()

        if total_count == 0:
            return 0.0

        # Count adopted insights (adopted_at OR exported_at OR shared_at IS NOT NULL)
        adopted_query = (
            select(func.count(InsightEvidence.id))
            .select_from(InsightEvidence)
            .join(Project, InsightEvidence.project_id == Project.id)
            .where(
                and_(
                    Project.owner_id == user_id,
                    Project.deleted_at.is_(None),
                    (
                        InsightEvidence.adopted_at.isnot(None)
                        | InsightEvidence.exported_at.isnot(None)
                        | InsightEvidence.shared_at.isnot(None)
                    ),
                )
            )
        )

        if start_date:
            adopted_query = adopted_query.where(InsightEvidence.created_at >= start_date)
        if end_date:
            adopted_query = adopted_query.where(InsightEvidence.created_at <= end_date)

        adopted_result = await self.db.execute(adopted_query)
        adopted_count = adopted_result.scalar_one()

        return float(adopted_count) / float(total_count)

    async def calculate_persona_coverage(
        self, user_id: UUID, project_id: UUID | None = None
    ) -> float:
        """
        Oblicz średnią persona coverage dla projektów użytkownika

        Coverage = is_statistically_valid = True → 1.0, False → 0.0

        Args:
            user_id: UUID użytkownika
            project_id: UUID konkretnego projektu (optional - jeśli podany, oblicz tylko dla tego projektu)

        Returns:
            float (0-1): Average coverage
        """
        # SQL: AVG(CASE WHEN is_statistically_valid THEN 1.0 ELSE 0.0 END)
        query = (
            select(
                func.avg(
                    func.case(
                        (Project.is_statistically_valid, 1.0),
                        else_=0.0,
                    )
                )
            )
            .where(
                and_(
                    Project.owner_id == user_id,
                    Project.deleted_at.is_(None),
                )
            )
        )

        if project_id:
            query = query.where(Project.id == project_id)

        result = await self.db.execute(query)
        avg_coverage = result.scalar_one()

        return float(avg_coverage) if avg_coverage is not None else 0.0

    async def get_weekly_trends(self, user_id: UUID) -> dict[str, Any]:
        """
        Oblicz weekly trends (w/w, m/m changes)

        Returns:
            {
                "this_week": {
                    "personas_generated": int,
                    "focus_groups_completed": int,
                    "insights_extracted": int,
                },
                "last_week": {...},
                "week_over_week_change": {
                    "personas": float,  # % change
                    "focus_groups": float,
                    "insights": float,
                },
            }
        """
        now = datetime.utcnow()

        # Calculate week boundaries (Monday to Sunday)
        # This week: start of current week (Monday 00:00) to now
        this_week_start = now - timedelta(days=now.weekday())
        this_week_start = this_week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        # Last week: 7 days before this_week_start
        last_week_start = this_week_start - timedelta(days=7)
        last_week_end = this_week_start

        # Import models (avoid circular imports)
        from app.models import FocusGroup, Persona

        # Count this week
        this_week_personas = await self.db.scalar(
            select(func.count(Persona.id))
            .join(Project, Persona.project_id == Project.id)
            .where(
                and_(
                    Project.owner_id == user_id,
                    Persona.created_at >= this_week_start,
                )
            )
        )

        this_week_focus_groups = await self.db.scalar(
            select(func.count(FocusGroup.id))
            .join(Project, FocusGroup.project_id == Project.id)
            .where(
                and_(
                    Project.owner_id == user_id,
                    FocusGroup.status == "completed",
                    FocusGroup.updated_at >= this_week_start,
                )
            )
        )

        this_week_insights = await self.db.scalar(
            select(func.count(InsightEvidence.id))
            .join(Project, InsightEvidence.project_id == Project.id)
            .where(
                and_(
                    Project.owner_id == user_id,
                    InsightEvidence.created_at >= this_week_start,
                )
            )
        )

        # Count last week
        last_week_personas = await self.db.scalar(
            select(func.count(Persona.id))
            .join(Project, Persona.project_id == Project.id)
            .where(
                and_(
                    Project.owner_id == user_id,
                    Persona.created_at >= last_week_start,
                    Persona.created_at < last_week_end,
                )
            )
        )

        last_week_focus_groups = await self.db.scalar(
            select(func.count(FocusGroup.id))
            .join(Project, FocusGroup.project_id == Project.id)
            .where(
                and_(
                    Project.owner_id == user_id,
                    FocusGroup.status == "completed",
                    FocusGroup.updated_at >= last_week_start,
                    FocusGroup.updated_at < last_week_end,
                )
            )
        )

        last_week_insights = await self.db.scalar(
            select(func.count(InsightEvidence.id))
            .join(Project, InsightEvidence.project_id == Project.id)
            .where(
                and_(
                    Project.owner_id == user_id,
                    InsightEvidence.created_at >= last_week_start,
                    InsightEvidence.created_at < last_week_end,
                )
            )
        )

        # Calculate % changes
        def percent_change(current: int, previous: int) -> float:
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return ((current - previous) / previous) * 100.0

        return {
            "this_week": {
                "personas_generated": this_week_personas or 0,
                "focus_groups_completed": this_week_focus_groups or 0,
                "insights_extracted": this_week_insights or 0,
            },
            "last_week": {
                "personas_generated": last_week_personas or 0,
                "focus_groups_completed": last_week_focus_groups or 0,
                "insights_extracted": last_week_insights or 0,
            },
            "week_over_week_change": {
                "personas": percent_change(
                    this_week_personas or 0, last_week_personas or 0
                ),
                "focus_groups": percent_change(
                    this_week_focus_groups or 0, last_week_focus_groups or 0
                ),
                "insights": percent_change(
                    this_week_insights or 0, last_week_insights or 0
                ),
            },
        }

    async def store_daily_metrics(self, user_id: UUID | None = None) -> DashboardMetric:
        """
        Oblicz i zapisz dzienne metryki (background job)

        Args:
            user_id: UUID użytkownika (jeśli None, oblicz global metrics)

        Returns:
            DashboardMetric: Zapisana metryka
        """
        tti = await self.calculate_time_to_insight(user_id) if user_id else {"median_seconds": None, "p90_seconds": None, "count": 0}
        adoption = await self.calculate_adoption_rate(user_id) if user_id else 0.0
        coverage = await self.calculate_persona_coverage(user_id) if user_id else 0.0
        trends = await self.get_weekly_trends(user_id) if user_id else {
            "this_week": {"personas_generated": 0, "focus_groups_completed": 0, "insights_extracted": 0},
            "last_week": {"personas_generated": 0, "focus_groups_completed": 0, "insights_extracted": 0},
            "week_over_week_change": {"personas": 0.0, "focus_groups": 0.0, "insights": 0.0},
        }

        # Count active/blocked projects
        from app.models import ProjectHealthLog

        active_count = 0
        blocked_count = 0

        if user_id:
            # Count based on latest health log per project
            latest_health_logs_subq = (
                select(
                    ProjectHealthLog.project_id,
                    func.max(ProjectHealthLog.checked_at).label("max_checked_at"),
                )
                .join(Project, ProjectHealthLog.project_id == Project.id)
                .where(
                    and_(
                        Project.owner_id == user_id,
                        Project.deleted_at.is_(None),
                        Project.is_active.is_(True),
                    )
                )
                .group_by(ProjectHealthLog.project_id)
                .subquery()
            )

            latest_health_logs = (
                select(ProjectHealthLog)
                .join(
                    latest_health_logs_subq,
                    and_(
                        ProjectHealthLog.project_id == latest_health_logs_subq.c.project_id,
                        ProjectHealthLog.checked_at == latest_health_logs_subq.c.max_checked_at,
                    ),
                )
            )

            result = await self.db.execute(latest_health_logs)
            health_logs = result.scalars().all()

            for log in health_logs:
                if log.health_status == "blocked":
                    blocked_count += 1
                else:
                    active_count += 1

        metric = DashboardMetric(
            user_id=user_id,
            metric_date=datetime.utcnow().date(),
            time_to_insight_median=tti["median_seconds"],
            time_to_insight_p90=tti["p90_seconds"],
            insight_adoption_rate=adoption,
            active_projects_count=active_count,
            blocked_projects_count=blocked_count,
            persona_coverage_avg=coverage,
            weekly_personas_generated=trends["this_week"]["personas_generated"],
            weekly_focus_groups_completed=trends["this_week"]["focus_groups_completed"],
            weekly_insights_extracted=trends["this_week"]["insights_extracted"],
        )

        self.db.add(metric)
        await self.db.commit()
        await self.db.refresh(metric)

        return metric
