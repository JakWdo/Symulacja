"""
Background Jobs - Dashboard Metrics Calculation

Scheduled jobs dla metryk dashboard:
- calculate_daily_metrics: Oblicz TTI, adoption, coverage (daily 00:00 UTC)
- update_health_scores: Oblicz health dla active projects (hourly)
- generate_budget_alerts: Check budget thresholds & create notifications (daily 08:00 UTC)
- cleanup_expired_notifications: Usuń expired notifications (daily 01:00 UTC)

TODO: Setup z Celery lub FastAPI BackgroundTasks
"""

import asyncio
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models import Project, User
from app.services.dashboard import (
    DashboardMetricsService,
    NotificationService,
    ProjectHealthService,
    UsageTrackingService,
)


async def calculate_daily_metrics_job():
    """
    Background job: Calculate dashboard metrics daily (00:00 UTC)

    Oblicza metryki dla:
    - Global metrics (user_id=None)
    - Per-user metrics (wszystkich aktywnych użytkowników)
    """
    async for db in get_async_session():
        metrics_service = DashboardMetricsService(db)

        # Calculate global metrics
        await metrics_service.store_daily_metrics(user_id=None)

        # Calculate per-user metrics
        result = await db.execute(select(User.id).where(User.is_active.is_(True)))
        user_ids = result.scalars().all()

        for user_id in user_ids:
            await metrics_service.store_daily_metrics(user_id=user_id)


async def update_health_scores_job():
    """
    Background job: Update project health scores (hourly)

    Oblicza health status dla wszystkich aktywnych projektów.
    """
    async for db in get_async_session():
        health_service = ProjectHealthService(db)

        # Get all active projects
        result = await db.execute(
            select(Project.id).where(
                and_(Project.is_active.is_(True), Project.deleted_at.is_(None))
            )
        )
        project_ids = result.scalars().all()

        for project_id in project_ids:
            await health_service.log_health_status(project_id)


async def generate_budget_alerts_job():
    """
    Background job: Generate budget alerts (daily 08:00 UTC)

    Sprawdza budżet dla każdego użytkownika i tworzy notyfikacje jeśli >90%.
    """
    async for db in get_async_session():
        usage_service = UsageTrackingService(db)
        notification_service = NotificationService(db)

        # Get all active users
        result = await db.execute(select(User.id).where(User.is_active.is_(True)))
        user_ids = result.scalars().all()

        for user_id in user_ids:
            # Assume budget limit $100 (TODO: get from user settings)
            budget_limit = 100.0
            alerts = await usage_service.check_budget_alerts(user_id, budget_limit)

            for alert in alerts:
                # Create notification
                await notification_service.create_notification(
                    user_id=user_id,
                    notification_type="budget_exceeded"
                    if alert["alert_type"] == "exceeded"
                    else "budget_warning",
                    priority="high",
                    title="Budget Alert",
                    message=alert["message"],
                    action_url="/dashboard/usage",
                    action_label="View Usage",
                )


async def cleanup_expired_notifications_job():
    """
    Background job: Cleanup expired notifications (daily 01:00 UTC)

    Usuwa notyfikacje z expired_at < now.
    """
    async for db in get_async_session():
        notification_service = NotificationService(db)
        count = await notification_service.cleanup_expired()
        print(f"Cleaned up {count} expired notifications")


# Example: Schedule with Celery (not implemented yet)
# from celery import Celery
# celery_app = Celery("sight_tasks")
#
# @celery_app.task
# def scheduled_metrics_calculation():
#     asyncio.run(calculate_daily_metrics_job())
#
# Schedule:
# - calculate_daily_metrics_job: cron(hour=0, minute=0)
# - update_health_scores_job: cron(minute=0)  # Every hour
# - generate_budget_alerts_job: cron(hour=8, minute=0)
# - cleanup_expired_notifications_job: cron(hour=1, minute=0)
