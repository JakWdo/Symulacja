"""
Cleanup Job - Scheduled Background Task

Daily cleanup job that removes soft-deleted entities older than retention period.
Runs daily at 2:00 AM UTC via APScheduler.
"""

import logging
from app.db import get_db
from app.services.maintenance.cleanup_service import CleanupService


logger = logging.getLogger(__name__)


async def run_cleanup_job(retention_days: int = 7):
    """
    Scheduled cleanup job - uruchamiany codziennie o 2:00 AM UTC.

    Usuwa (hard delete) soft-deleted entities starsze niż retention_days:
    - Projects (CASCADE usuwa personas, focus_groups, surveys)
    - Personas (orphaned)
    - Focus Groups (orphaned)
    - Surveys (orphaned)

    Args:
        retention_days: Number of days to retain soft-deleted entities (default: 7)

    Raises:
        Exception: Re-raises any exception after logging (for scheduler to track failures)
    """
    logger.info("⏰ Cleanup job started (scheduled)")

    try:
        # Get DB session from dependency
        async for db in get_db():
            try:
                service = CleanupService(retention_days=retention_days)
                stats = await service.cleanup_old_deleted_entities(db)

                logger.info(
                    f"✅ Cleanup job completed successfully: {stats['total_deleted']} entities deleted",
                    extra={
                        "job": "cleanup_deleted_entities",
                        "stats": stats,
                        "retention_days": retention_days,
                    }
                )
            finally:
                # DB session cleanup handled by get_db() context manager
                pass
            break  # Exit after first (and only) iteration

    except Exception as exc:
        logger.error(
            f"❌ Cleanup job failed: {exc}",
            extra={
                "job": "cleanup_deleted_entities",
                "error": str(exc),
            },
            exc_info=True,
        )
        raise  # Re-raise for scheduler to track failures
