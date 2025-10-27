"""
Background Tasks Module

Scheduled jobs dla dashboardu:
- calculate_daily_metrics: Oblicz metryki KPI (daily)
- update_health_scores: Health projekty (hourly)
- generate_budget_alerts: Alerty budżetowe (daily)
- cleanup_expired_notifications: Cleanup (daily)
"""

from .dashboard_metrics import (
    calculate_daily_metrics_job,
    cleanup_expired_notifications_job,
    generate_budget_alerts_job,
    update_health_scores_job,
)

__all__ = [
    "calculate_daily_metrics_job",
    "update_health_scores_job",
    "generate_budget_alerts_job",
    "cleanup_expired_notifications_job",
]
