"""
APScheduler Setup and Management

Centralized scheduler configuration for background jobs.
Currently schedules:
- Daily cleanup job (2:00 AM UTC) - removes old soft-deleted entities
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.tasks.cleanup_job import run_cleanup_job


logger = logging.getLogger(__name__)


# Global scheduler instance
_scheduler: AsyncIOScheduler | None = None


def init_scheduler() -> AsyncIOScheduler | None:
    """
    Initialize and start APScheduler with configured jobs.

    Jobs:
    - cleanup_deleted_entities: Daily at 2:00 AM UTC (removes entities deleted >7 days ago)

    Returns:
        AsyncIOScheduler instance or None if initialization failed

    Note:
        This function is idempotent - calling it multiple times won't create duplicate schedulers.
    """
    global _scheduler

    if _scheduler is not None:
        logger.warning("Scheduler already initialized, skipping")
        return _scheduler

    try:
        scheduler = AsyncIOScheduler(timezone='UTC')

        # Schedule cleanup job (daily at 2 AM UTC)
        scheduler.add_job(
            run_cleanup_job,
            trigger='cron',
            hour=2,
            minute=0,
            timezone='UTC',
            id='cleanup_deleted_entities',
            name='Cleanup Old Deleted Entities',
            replace_existing=True,
            max_instances=1,  # Prevent overlapping executions
            kwargs={'retention_days': 7},  # Keep deleted entities for 7 days
        )

        scheduler.start()
        logger.info("✓ APScheduler started - cleanup job scheduled daily at 2:00 AM UTC")

        _scheduler = scheduler
        return scheduler

    except Exception as exc:
        logger.error(f"❌ Failed to start APScheduler: {exc}", exc_info=True)
        # Don't fail startup if scheduler fails - app can run without it
        return None


def shutdown_scheduler(wait: bool = True):
    """
    Shutdown APScheduler gracefully.

    Args:
        wait: If True, wait for running jobs to complete before shutting down

    Note:
        This is safe to call even if scheduler was never initialized.
    """
    global _scheduler

    if _scheduler is None:
        logger.debug("Scheduler not initialized, skipping shutdown")
        return

    try:
        _scheduler.shutdown(wait=wait)
        logger.info("✓ APScheduler stopped gracefully")
        _scheduler = None
    except Exception as exc:
        logger.error(f"❌ Error stopping scheduler: {exc}", exc_info=True)


def get_scheduler() -> AsyncIOScheduler | None:
    """
    Get the global scheduler instance.

    Returns:
        AsyncIOScheduler instance or None if not initialized
    """
    return _scheduler
