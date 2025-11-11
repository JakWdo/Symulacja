"""
Dashboard API Endpoints

Wszystkie endpointy dla dashboardu Sight:
- GET /dashboard/overview - Overview cards (8 metryk)
- GET /dashboard/quick-actions - Recommended actions (Next Best Action)
- GET /dashboard/projects/active - Active projects z health & progress
- GET /dashboard/analytics/weekly - Weekly completion chart data
- GET /dashboard/analytics/insights - Insight analytics (concepts, sentiment)
- GET /dashboard/insights/latest - Latest insights (highlights)
- GET /dashboard/insights/{id} - Insight detail z evidence trail
- GET /dashboard/health/blockers - Health summary + blockers list
- GET /dashboard/usage - Token usage & budget forecast
- GET /dashboard/notifications - Notifications (unread + tasks)
- POST /dashboard/actions/{action_id}/execute - Execute recommended action
- POST /dashboard/notifications/{id}/read - Mark notification as read
- POST /dashboard/notifications/{id}/done - Mark notification as done
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db import get_db
from app.models import User
from app.schemas.dashboard import (
    ActionExecutionResult,
    HealthBlockersResponse,
    InsightAnalyticsData,
    InsightDetail,
    InsightHighlight,
    Notification,
    OverviewResponse,
    ProjectWithHealth,
    QuickAction,
    UsageBudgetResponse,
    UsageBreakdownResponse,
    WeeklyCompletionData,
)
from app.utils import get_utc_now
from app.services.dashboard import (
    DashboardMetricsService,
    DashboardOrchestrator,
    InsightTraceabilityService,
    NotificationService,
    ProjectHealthService,
    QuickActionsService,
    UsageTrackingService,
)

router = APIRouter()


# Dependency: Orchestrator factory
def get_dashboard_orchestrator(
    db: AsyncSession = Depends(get_db),
) -> DashboardOrchestrator:
    """Factory do tworzenia Dashboard Orchestrator z wszystkimi zależnościami"""
    metrics_service = DashboardMetricsService(db)
    health_service = ProjectHealthService(db)
    quick_actions_service = QuickActionsService(db, health_service)
    insight_service = InsightTraceabilityService(db)
    usage_service = UsageTrackingService(db)
    notification_service = NotificationService(db)

    return DashboardOrchestrator(
        db=db,
        metrics_service=metrics_service,
        health_service=health_service,
        quick_actions_service=quick_actions_service,
        insight_service=insight_service,
        usage_service=usage_service,
        notification_service=notification_service,
    )


@router.get("/dashboard/overview", response_model=OverviewResponse)
async def get_overview(
    current_user: User = Depends(get_current_user),
    orchestrator: DashboardOrchestrator = Depends(get_dashboard_orchestrator),
):
    """
    Pobierz overview dashboardu (8 kart metryk)

    Cached: Redis 30s (TODO: implement caching)
    """
    return await orchestrator.get_dashboard_overview(current_user.id)


@router.get("/dashboard/quick-actions", response_model=list[QuickAction])
async def get_quick_actions(
    limit: int = 4,
    current_user: User = Depends(get_current_user),
    orchestrator: DashboardOrchestrator = Depends(get_dashboard_orchestrator),
):
    """Pobierz top N recommended actions (Next Best Action)"""
    return await orchestrator.quick_actions_service.recommend_actions(
        user_id=current_user.id, limit=limit
    )


@router.get("/dashboard/projects/active", response_model=list[ProjectWithHealth])
async def get_active_projects(
    current_user: User = Depends(get_current_user),
    orchestrator: DashboardOrchestrator = Depends(get_dashboard_orchestrator),
):
    """Pobierz active projects z health status, progress, insights count"""
    return await orchestrator.get_active_projects(current_user.id)


@router.get("/dashboard/analytics/weekly", response_model=WeeklyCompletionData)
async def get_weekly_completion(
    weeks: int = 8,
    project_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    orchestrator: DashboardOrchestrator = Depends(get_dashboard_orchestrator),
):
    """
    Pobierz weekly completion chart data

    Args:
        weeks: Liczba tygodni wstecz (default: 8)
        project_id: Opcjonalnie filtruj dla konkretnego projektu
    """
    return await orchestrator.get_weekly_completion(current_user.id, weeks, project_id)


@router.get("/dashboard/analytics/insights", response_model=InsightAnalyticsData)
async def get_insight_analytics(
    project_id: UUID | None = None,
    top_n: int = 10,
    current_user: User = Depends(get_current_user),
    orchestrator: DashboardOrchestrator = Depends(get_dashboard_orchestrator),
):
    """
    Pobierz insight analytics (top concepts, sentiment, patterns)

    Args:
        project_id: Opcjonalnie filtruj dla konkretnego projektu
        top_n: Liczba top concepts do zwrócenia (default: 10, max: 20)
    """
    # Validate top_n
    if top_n < 1 or top_n > 20:
        raise HTTPException(status_code=400, detail="top_n must be between 1 and 20")

    return await orchestrator.get_insight_analytics(current_user.id, project_id, top_n)


@router.get("/dashboard/insights/latest", response_model=list[InsightHighlight])
async def get_latest_insights(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    orchestrator: DashboardOrchestrator = Depends(get_dashboard_orchestrator),
):
    """Pobierz latest insights (highlights)"""
    return await orchestrator.get_latest_insights(current_user.id, limit)


@router.get("/dashboard/insights/{insight_id}", response_model=InsightDetail)
async def get_insight_detail(
    insight_id: UUID,
    current_user: User = Depends(get_current_user),
    orchestrator: DashboardOrchestrator = Depends(get_dashboard_orchestrator),
):
    """Pobierz insight detail z evidence trail (traceability)"""
    try:
        return await orchestrator.get_insight_detail(insight_id, current_user.id)
    except Exception:
        raise HTTPException(status_code=404, detail="Insight not found")


@router.get("/dashboard/health/blockers", response_model=HealthBlockersResponse)
async def get_health_blockers(
    current_user: User = Depends(get_current_user),
    orchestrator: DashboardOrchestrator = Depends(get_dashboard_orchestrator),
):
    """Pobierz health summary + blockers list"""
    return await orchestrator.get_health_blockers(current_user.id)


@router.get("/dashboard/usage", response_model=UsageBudgetResponse)
async def get_usage_budget(
    current_user: User = Depends(get_current_user),
    orchestrator: DashboardOrchestrator = Depends(get_dashboard_orchestrator),
):
    """Pobierz token usage, costs, forecast, alerts"""
    return await orchestrator.get_usage_budget(current_user.id)


@router.get("/dashboard/usage-breakdown", response_model=UsageBreakdownResponse)
async def get_usage_breakdown(
    current_user: User = Depends(get_current_user),
    orchestrator: DashboardOrchestrator = Depends(get_dashboard_orchestrator),
):
    """Pobierz breakdown usage po kategoriach (persona gen, focus groups, RAG, other)"""
    return await orchestrator.usage_service.calculate_breakdown_by_operation_type(current_user.id)


@router.get("/dashboard/notifications", response_model=list[Notification])
async def get_notifications(
    unread_only: bool = False,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    orchestrator: DashboardOrchestrator = Depends(get_dashboard_orchestrator),
):
    """Pobierz notifications (unread + tasks)"""
    notifications = await orchestrator.notification_service.get_notifications(
        user_id=current_user.id, unread_only=unread_only, limit=limit
    )

    # Format time_ago
    output = []
    for notif in notifications:
        delta = get_utc_now() - notif.created_at
        if delta.days > 0:
            time_ago = f"{delta.days} days ago"
        elif delta.seconds > 3600:
            time_ago = f"{delta.seconds // 3600} hours ago"
        else:
            time_ago = f"{delta.seconds // 60} minutes ago"

        output.append(
            Notification(
                id=str(notif.id),
                notification_type=notif.notification_type,
                priority=notif.priority,
                title=notif.title,
                message=notif.message,
                time_ago=time_ago,
                is_read=notif.is_read,
                is_done=notif.is_done,
                action_label=notif.action_label,
                action_url=notif.action_url,
                created_at=notif.created_at,
            )
        )

    return output


@router.post("/dashboard/actions/{action_id}/execute", response_model=ActionExecutionResult)
async def execute_action(
    action_id: str,
    current_user: User = Depends(get_current_user),
    orchestrator: DashboardOrchestrator = Depends(get_dashboard_orchestrator),
):
    """Execute recommended action (trigger orchestration)"""
    return await orchestrator.quick_actions_service.execute_action(
        action_id=action_id, user_id=current_user.id
    )


@router.post("/dashboard/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    orchestrator: DashboardOrchestrator = Depends(get_dashboard_orchestrator),
):
    """Mark notification as read"""
    await orchestrator.notification_service.mark_as_read(
        notification_id=notification_id, user_id=current_user.id
    )
    return {"status": "success"}


@router.post("/dashboard/notifications/{notification_id}/done")
async def mark_notification_done(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    orchestrator: DashboardOrchestrator = Depends(get_dashboard_orchestrator),
):
    """Mark notification as done"""
    await orchestrator.notification_service.mark_as_done(
        notification_id=notification_id, user_id=current_user.id
    )
    return {"status": "success"}
