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
from .metrics import ProjectHealthService, DashboardMetricsService
from .insights import InsightTraceabilityService, QuickActionsService
from .usage import UsageTrackingService
from .notification_service import NotificationService

__all__ = [
    "DashboardMetricsService",
    "ProjectHealthService",
    "QuickActionsService",
    "InsightTraceabilityService",
    "UsageTrackingService",
    "NotificationService",
    "DashboardOrchestrator",
]
