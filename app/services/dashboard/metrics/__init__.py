"""
Dashboard Metrics - Serwisy metryk i zdrowia projektu.

Moduły:
- metrics_service.py - Główny serwis metryk dashboardu
- metrics_aggregator.py - Agregacja metryk (weekly completion, etc.)
- health_service.py - Serwis zdrowia projektu (health scores, recommendations)
"""

from .metrics_service import DashboardMetricsService
from .metrics_aggregator import get_weekly_completion
from .health_service import ProjectHealthService

__all__ = [
    "DashboardMetricsService",
    "get_weekly_completion",
    "ProjectHealthService",
]
