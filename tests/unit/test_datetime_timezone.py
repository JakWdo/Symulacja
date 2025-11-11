"""
Testy regresyjne dla datetime timezone awareness.

Test suite zapewniający że wszystkie operacje datetime używają timezone-aware datetimes
i unikają błędów "can't subtract offset-naive and offset-aware datetimes".

Pokrycie:
- Dashboard quick actions (24h recently completed check)
- Dashboard overview (time_ago calculation for insights)
- Dashboard health (idle_hours calculation)
- Dashboard notifications (time_ago formatting)
- Metrics service (weekly trends calculation)
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models import FocusGroup, InsightEvidence, Project, User
from app.services.dashboard.insights import QuickActionsService
from app.services.dashboard.dashboard_orchestrator import DashboardOrchestrator
from app.services.dashboard.metrics import ProjectHealthService
from app.services.dashboard.metrics import DashboardMetricsService
from app.utils import get_utc_now


@pytest.mark.asyncio
async def test_get_utc_now_returns_timezone_aware(db_session):
    """Test że get_utc_now() zwraca timezone-aware datetime."""
    now = get_utc_now()

    assert now.tzinfo is not None, "get_utc_now() should return timezone-aware datetime"
    assert str(now.tzinfo) == "UTC", "get_utc_now() should return UTC timezone"


@pytest.mark.asyncio
async def test_quick_actions_recently_completed_check(db_session, test_user):
    """Test że quick actions poprawnie oblicza 'recently completed' z timezone-aware datetimes."""
    # Create project with personas
    project = Project(
        id=uuid4(),
        name="Test Project",
        owner_id=test_user.id,
        research_goal="Test goal",
        is_active=True,
    )
    db_session.add(project)

    # Create focus group completed 12h ago (timezone-aware)
    twelve_hours_ago = get_utc_now() - timedelta(hours=12)
    fg = FocusGroup(
        id=uuid4(),
        project_id=project.id,
        name="Test FG",
        status="completed",
        topic="Test topic",
        created_at=twelve_hours_ago,
        completed_at=twelve_hours_ago,  # Timezone-aware
    )
    db_session.add(fg)
    await db_session.commit()

    # Test service
    service = QuickActionsService(db_session)

    # Should NOT crash with "can't subtract offset-naive and offset-aware datetimes"
    actions = await service.get_quick_actions(test_user.id, limit=10)

    # Verify no action to start focus group (recently completed)
    start_focus_actions = [a for a in actions if a.get("action_type") == "start_focus_group"]
    assert len(start_focus_actions) == 0, "Should not suggest starting FG if completed <24h ago"


@pytest.mark.asyncio
async def test_dashboard_overview_time_ago_calculation(db_session, test_user):
    """Test że dashboard overview poprawnie oblicza time_ago dla insights."""
    # Create project
    project = Project(
        id=uuid4(),
        name="Test Project",
        owner_id=test_user.id,
        research_goal="Test goal",
        is_active=True,
    )
    db_session.add(project)

    # Create insight 2 days ago (timezone-aware)
    two_days_ago = get_utc_now() - timedelta(days=2)
    insight = InsightEvidence(
        id=uuid4(),
        project_id=project.id,
        insight_type="pain_point",
        content="Test insight",
        confidence=0.8,
        created_at=two_days_ago,  # Timezone-aware
    )
    db_session.add(insight)
    await db_session.commit()

    # Test orchestrator
    orchestrator = DashboardOrchestrator(db_session)

    # Should NOT crash with "can't subtract offset-naive and offset-aware datetimes"
    result = await orchestrator.get_latest_insights(
        user_id=test_user.id,
        limit=5,
        insight_types=None
    )

    # Verify time_ago is calculated
    assert len(result) == 1
    assert "time_ago" in result[0]
    assert "2 days ago" in result[0]["time_ago"]


@pytest.mark.asyncio
async def test_health_service_idle_hours_calculation(db_session, test_user):
    """Test że health service poprawnie oblicza idle_hours dla focus groups."""
    # Create project
    project = Project(
        id=uuid4(),
        name="Test Project",
        owner_id=test_user.id,
        research_goal="Test goal",
        is_active=True,
    )
    db_session.add(project)

    # Create in_progress focus group idle for 50h (timezone-aware)
    fifty_hours_ago = get_utc_now() - timedelta(hours=50)
    fg = FocusGroup(
        id=uuid4(),
        project_id=project.id,
        name="Test FG",
        status="in_progress",
        topic="Test topic",
        created_at=fifty_hours_ago,
        started_at=fifty_hours_ago,
        updated_at=fifty_hours_ago,  # Last activity
    )
    db_session.add(fg)
    await db_session.commit()

    # Test health service
    service = ProjectHealthService(db_session)

    # Should NOT crash with "can't subtract offset-naive and offset-aware datetimes"
    blockers = await service.get_project_blockers(project_id=project.id, user_id=test_user.id)

    # Verify idle blocker is detected
    idle_blockers = [b for b in blockers if b.get("type") == "idle_focus_group"]
    assert len(idle_blockers) > 0, "Should detect idle focus group (>48h)"
    assert "50" in idle_blockers[0]["message"] or "5" in idle_blockers[0]["message"]


@pytest.mark.asyncio
async def test_metrics_service_weekly_trends(db_session, test_user):
    """Test że metrics service poprawnie oblicza weekly trends z timezone-aware datetimes."""
    # Create project
    project = Project(
        id=uuid4(),
        name="Test Project",
        owner_id=test_user.id,
        research_goal="Test goal",
        is_active=True,
    )
    db_session.add(project)

    # Create focus groups in this week and last week (timezone-aware)
    now = get_utc_now()
    this_week_start = now - timedelta(days=now.weekday())
    this_week_start = this_week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    # This week focus group
    fg_this_week = FocusGroup(
        id=uuid4(),
        project_id=project.id,
        name="This Week FG",
        status="completed",
        topic="Test topic",
        created_at=this_week_start + timedelta(days=1),
    )
    db_session.add(fg_this_week)

    # Last week focus group
    last_week_start = this_week_start - timedelta(days=7)
    fg_last_week = FocusGroup(
        id=uuid4(),
        project_id=project.id,
        name="Last Week FG",
        status="completed",
        topic="Test topic",
        created_at=last_week_start + timedelta(days=1),
    )
    db_session.add(fg_last_week)
    await db_session.commit()

    # Test metrics service
    service = DashboardMetricsService(db_session)

    # Should NOT crash with "can't subtract offset-naive and offset-aware datetimes"
    trends = await service.get_weekly_trends(user_id=test_user.id)

    # Verify trends are calculated
    assert "this_week" in trends
    assert "last_week" in trends
    assert trends["this_week"]["focus_groups"] >= 1
    assert trends["last_week"]["focus_groups"] >= 1


@pytest.mark.asyncio
async def test_all_model_timestamps_are_timezone_aware(db_session, test_user):
    """Test że wszystkie modele używają timezone-aware timestamps."""
    # Test User model
    assert test_user.created_at.tzinfo is not None, "User.created_at should be timezone-aware"
    assert test_user.updated_at.tzinfo is not None, "User.updated_at should be timezone-aware"

    # Test Project model
    project = Project(
        id=uuid4(),
        name="Test Project",
        owner_id=test_user.id,
        research_goal="Test goal",
        is_active=True,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    assert project.created_at.tzinfo is not None, "Project.created_at should be timezone-aware"
    assert project.updated_at.tzinfo is not None, "Project.updated_at should be timezone-aware"

    # Test FocusGroup model
    fg = FocusGroup(
        id=uuid4(),
        project_id=project.id,
        name="Test FG",
        status="draft",
        topic="Test topic",
    )
    db_session.add(fg)
    await db_session.commit()
    await db_session.refresh(fg)

    assert fg.created_at.tzinfo is not None, "FocusGroup.created_at should be timezone-aware"
    assert fg.updated_at.tzinfo is not None, "FocusGroup.updated_at should be timezone-aware"

    # Test InsightEvidence model
    insight = InsightEvidence(
        id=uuid4(),
        project_id=project.id,
        insight_type="pain_point",
        content="Test insight",
        confidence=0.8,
    )
    db_session.add(insight)
    await db_session.commit()
    await db_session.refresh(insight)

    assert insight.created_at.tzinfo is not None, "InsightEvidence.created_at should be timezone-aware"


@pytest.mark.asyncio
async def test_datetime_subtraction_with_db_timestamps(db_session, test_user):
    """Test że możemy odejmować get_utc_now() od DB timestamps bez błędów."""
    # Create project
    project = Project(
        id=uuid4(),
        name="Test Project",
        owner_id=test_user.id,
        research_goal="Test goal",
        is_active=True,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Should NOT raise: "can't subtract offset-naive and offset-aware datetimes"
    now = get_utc_now()
    time_diff = now - project.created_at

    assert time_diff.total_seconds() >= 0, "Time difference should be non-negative"
    assert isinstance(time_diff, timedelta), "Should return timedelta object"


@pytest.mark.asyncio
async def test_datetime_comparison_with_db_timestamps(db_session, test_user):
    """Test że możemy porównywać get_utc_now() z DB timestamps bez błędów."""
    # Create project
    project = Project(
        id=uuid4(),
        name="Test Project",
        owner_id=test_user.id,
        research_goal="Test goal",
        is_active=True,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Should NOT raise: "can't compare offset-naive and offset-aware datetimes"
    now = get_utc_now()

    assert project.created_at < now, "Project should be created before now"
    assert project.created_at <= now, "Project should be created before or at now"
    assert now > project.created_at, "Now should be after project creation"
    assert now >= project.created_at, "Now should be after or at project creation"
