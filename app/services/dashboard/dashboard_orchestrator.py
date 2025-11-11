"""
Dashboard Orchestrator - Backward compatibility wrapper

Ten plik został podzielony na moduły (Prompt 5):
- dashboard_core.py: Główna klasa DashboardOrchestrator
- metrics_aggregator.py: Agregacja metryk tygodniowych
- cost_calculator.py: Kalkulacja kosztów i budżetu
- usage_trends.py: Analityka insightów i wzorców

Ten wrapper zachowuje backward compatibility dla istniejących importów.
"""

from app.services.dashboard.dashboard_core import DashboardOrchestrator

__all__ = ["DashboardOrchestrator"]
