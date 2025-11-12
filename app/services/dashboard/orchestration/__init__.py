"""Dashboard Orchestration Modules - Split dashboard logic into smaller modules."""

from .overview_builder import get_dashboard_overview, build_trend
from .projects_builder import get_active_projects
from .insights_builder import get_latest_insights, get_insight_detail, get_health_blockers

__all__ = [
    "get_dashboard_overview",
    "build_trend",
    "get_active_projects",
    "get_latest_insights",
    "get_insight_detail",
    "get_health_blockers",
]
