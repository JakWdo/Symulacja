"""
Background Tasks Module

Note: Previously contained dashboard_metrics and scheduler modules.
These were removed as they were unused and contained broken code (get_async_session).

Active background tasks are now handled in app/main.py via APScheduler:
- cleanup_job: Daily cleanup of old data (runs at 2:00 AM UTC)
"""

__all__ = []
