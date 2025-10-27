"""
Dashboard Services - Komplet serwisów dla dashboardu Sight

Zawiera:
- DashboardMetricsService: Obliczanie KPI (TTI, adoption rate, coverage)
- ProjectHealthService: Health scoring & blocker detection
- QuickActionsService: Next Best Action engine
- InsightTraceabilityService: Evidence trail & provenance tracking
- UsageTrackingService: Token usage & cost tracking
- NotificationService: System notifications & alerts
- DashboardOrchestrator: Orkiestracja wszystkich serwisów + caching
"""

from .dashboard_orchestrator import DashboardOrchestrator
from .health_service import ProjectHealthService
from .insight_traceability_service import InsightTraceabilityService
from .metrics_service import DashboardMetricsService
from .notification_service import NotificationService
from .quick_actions_service import QuickActionsService
from .usage_tracking_service import UsageTrackingService

__all__ = [
    "DashboardMetricsService",
    "ProjectHealthService",
    "QuickActionsService",
    "InsightTraceabilityService",
    "UsageTrackingService",
    "NotificationService",
    "DashboardOrchestrator",
]
