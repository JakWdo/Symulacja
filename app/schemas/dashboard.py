"""
Dashboard Schemas - Pydantic models dla API responses

Zawiera wszystkie schematy dla dashboard API:
- Overview: MetricCard, TrendData
- Quick Actions: QuickAction, ActionExecutionResult
- Active Projects: ProjectWithHealth, HealthStatus, ProgressStages
- Analytics: WeeklyCompletionData, InsightAnalyticsData
- Insights: InsightHighlight, InsightDetail, InsightEvidence
- Health & Blockers: Blocker, BlockerWithFix, HealthBlockersResponse
- Usage & Budget: UsageBudgetResponse, UsageHistory, BudgetAlert
- Notifications: Notification
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


# ============= OVERVIEW =============

class TrendData(BaseModel):
    """Dane trendu (w/w lub m/m)"""
    value: float
    change_percent: float  # % change
    direction: Literal["up", "down", "stable"]


class MetricCard(BaseModel):
    """Karta metryki dla dashboardu"""
    label: str
    value: str  # Formatted value (e.g., "2.5 min", "87%", "12")
    raw_value: float | int
    trend: TrendData | None = None
    tooltip: str | None = None


class OverviewResponse(BaseModel):
    """Overview dashboardu - 4 główne karty + extensions"""
    # 4 main cards
    active_research: MetricCard
    pending_actions: MetricCard
    insights_ready: MetricCard
    this_week_activity: MetricCard

    # Extensions
    time_to_insight: MetricCard
    insight_adoption_rate: MetricCard
    persona_coverage: MetricCard
    blockers_count: MetricCard


# ============= QUICK ACTIONS =============

class ActionContext(BaseModel):
    """Kontekst akcji"""
    project_id: UUID | None = None
    project_name: str | None = None
    blocker_count: int | None = None
    blockers: list[dict[str, Any]] | None = None
    target_count: int | None = None
    persona_count: int | None = None
    insight_count: int | None = None


class QuickAction(BaseModel):
    """Recommended action"""
    action_id: str
    action_type: str
    priority: Literal["high", "medium", "low"]
    title: str
    description: str
    icon: str  # Lucide icon name
    context: ActionContext
    cta_label: str
    cta_url: str


class ActionExecutionResult(BaseModel):
    """Wynik wykonania akcji"""
    status: Literal["success", "redirect", "error"]
    message: str
    redirect_url: str | None = None


# ============= ACTIVE PROJECTS =============

class HealthStatus(BaseModel):
    """Health status projektu"""
    status: Literal["on_track", "at_risk", "blocked"]
    score: int  # 0-100
    color: str  # CSS color ('green', 'yellow', 'red')


class ProgressStages(BaseModel):
    """Etapy postępu projektu"""
    demographics: bool
    personas: bool
    focus: bool
    analysis: bool
    current_stage: str  # 'demographics', 'personas', 'focus', 'analysis'


class Blocker(BaseModel):
    """Bloker projektu"""
    type: str
    severity: Literal["critical", "high", "medium", "low"]
    message: str
    fix_action: str
    fix_url: str | None = None
    focus_group_id: str | None = None


class ProjectWithHealth(BaseModel):
    """Projekt z health status i progress"""
    id: str
    name: str
    status: Literal["running", "paused", "completed", "blocked"]
    health: HealthStatus
    progress: ProgressStages
    insights_count: int
    new_insights_count: int
    last_activity: datetime
    cta_label: str
    cta_url: str


# ============= ANALYTICS =============

class WeeklyCompletionData(BaseModel):
    """Dane weekly completion chart"""
    weeks: list[str]  # ["2025-W01", "2025-W02", ...]
    personas: list[int]
    focus_groups: list[int]
    insights: list[int]


class ConceptData(BaseModel):
    """Top concept"""
    concept: str
    count: int


class SentimentData(BaseModel):
    """Sentiment distribution"""
    positive: int
    negative: int
    neutral: int
    mixed: int


class InsightAnalyticsData(BaseModel):
    """Analytics insightów"""
    top_concepts: list[ConceptData]
    sentiment_distribution: SentimentData
    response_patterns: list[dict[str, Any]]


# ============= INSIGHTS =============

class InsightEvidenceItem(BaseModel):
    """Evidence dla insightu"""
    type: Literal["quote", "snippet", "concept"]
    text: str
    source: str
    source_id: UUID | None = None


class InsightProvenance(BaseModel):
    """Provenance insightu (traceability)"""
    model_version: str
    prompt_hash: str
    sources: list[dict[str, Any]]
    created_at: datetime


class InsightHighlight(BaseModel):
    """Insight highlight (lista)"""
    id: str
    project_id: str
    project_name: str
    insight_type: Literal["opportunity", "risk", "trend", "pattern"]
    insight_text: str
    confidence_score: float
    impact_score: int
    time_ago: str  # "2 hours ago"
    evidence_count: int
    is_viewed: bool
    is_adopted: bool


class InsightDetail(InsightHighlight):
    """Insight detail (pełny)"""
    evidence: list[InsightEvidenceItem]
    provenance: InsightProvenance
    concepts: list[str]
    sentiment: str


# ============= HEALTH & BLOCKERS =============

class BlockerWithFix(Blocker):
    """Bloker z kontekstem projektu"""
    project_id: str
    project_name: str


class HealthBlockersResponse(BaseModel):
    """Health summary + blockers"""
    summary: dict[str, int]  # {"on_track": 5, "at_risk": 2, "blocked": 1}
    blockers: list[BlockerWithFix]


# ============= USAGE & BUDGET =============

class UsageHistory(BaseModel):
    """Historia usage (dzień)"""
    date: str  # "2025-10-27"
    total_tokens: int
    total_cost: float


class BudgetAlert(BaseModel):
    """Alert budżetowy"""
    alert_type: Literal["warning", "exceeded"]
    message: str
    threshold: float  # 0.9 or 1.0
    current: float  # 0-1


class UsageBudgetResponse(BaseModel):
    """Usage & budget data"""
    total_tokens: int
    total_cost: float
    forecast_month_end: float
    budget_limit: float | None
    alerts: list[BudgetAlert]
    history: list[UsageHistory]


# ============= NOTIFICATIONS =============

class Notification(BaseModel):
    """Notyfikacja użytkownika"""
    id: str
    notification_type: str
    priority: Literal["high", "medium", "low"]
    title: str
    message: str
    time_ago: str  # "2 hours ago"
    is_read: bool
    is_done: bool
    action_label: str | None = None
    action_url: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
