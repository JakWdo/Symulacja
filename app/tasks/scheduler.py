"""Simple asyncio-based scheduler for recurring dashboard jobs."""
from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable

from app.core.config import get_settings
from app.tasks.dashboard_metrics import (
    calculate_daily_metrics_job,
    cleanup_expired_notifications_job,
    generate_budget_alerts_job,
    update_health_scores_job,
)

logger = logging.getLogger(__name__)

JobCallable = Callable[[], Awaitable[None]]


async def _job_loop(name: str, interval: int, job: JobCallable) -> None:
    """Execute the given coroutine periodically with error handling."""
    while True:
        try:
            logger.debug("Running scheduled job '%s'", name)
            await job()
            logger.debug("Completed scheduled job '%s'", name)
        except asyncio.CancelledError:  # pragma: no cover - cooperative cancellation
            logger.info("Cancelled scheduled job '%s'", name)
            raise
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Scheduled job '%s' failed: %s", name, exc)
        await asyncio.sleep(interval)


async def start_dashboard_scheduler() -> list[asyncio.Task]:
    """Start periodic dashboard jobs if scheduling is enabled."""
    settings = get_settings()

    # Skip scheduler entirely in test environment to keep tests deterministic.
    if settings.ENVIRONMENT == "test":
        logger.info("Scheduler disabled in test environment")
        return []

    jobs: list[tuple[str, int, JobCallable]] = [
        ("dashboard.calculate_daily_metrics", 24 * 60 * 60, calculate_daily_metrics_job),
        ("dashboard.update_health_scores", 60 * 60, update_health_scores_job),
        ("dashboard.generate_budget_alerts", 6 * 60 * 60, generate_budget_alerts_job),
        ("dashboard.cleanup_expired_notifications", 12 * 60 * 60, cleanup_expired_notifications_job),
    ]

    tasks = [
        asyncio.create_task(_job_loop(name, interval, job), name=name)
        for name, interval, job in jobs
    ]

    logger.info("Started %d dashboard background jobs", len(tasks))
    return tasks


async def stop_dashboard_scheduler(tasks: list[asyncio.Task]) -> None:
    """Cancel and await running scheduler tasks."""
    if not tasks:
        return

    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Dashboard scheduler stopped")
