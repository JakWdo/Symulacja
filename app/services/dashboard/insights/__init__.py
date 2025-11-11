"""
Dashboard Insights - Serwisy insightów i quick actions.

Moduły:
- insight_traceability_service.py - Śledzenie pochodzenia insightów
- quick_actions_service.py - Serwis quick actions (rekomendacje następnych kroków)
"""

from .insight_traceability_service import InsightTraceabilityService
from .quick_actions_service import QuickActionsService

__all__ = [
    "InsightTraceabilityService",
    "QuickActionsService",
]
