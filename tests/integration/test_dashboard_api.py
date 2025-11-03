"""
Dashboard API Smoke Tests

Minimalne testy sprawdzające czy dashboard API działa poprawnie.
Testujemy głównie happy path - 200 OK i podstawową strukturę odpowiedzi.

Coverage: Smoke tests only (nie comprehensive).
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Project


@pytest.mark.asyncio
async def test_dashboard_overview_returns_200(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
):
    """
    Smoke test: GET /dashboard/overview zwraca 200 OK

    Sprawdza że endpoint działa i zwraca podstawową strukturę danych.
    """
    response = await async_client.get(
        "/api/v1/dashboard/overview",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Verify structure: 8 metric cards
    assert "active_research" in data
    assert "pending_actions" in data
    assert "insights_ready" in data
    assert "this_week_activity" in data
    assert "time_to_insight" in data
    assert "insight_adoption_rate" in data
    assert "persona_coverage" in data
    assert "blockers_count" in data

    # Verify metric card structure
    metric = data["active_research"]
    assert "label" in metric
    assert "value" in metric
    assert "raw_value" in metric
    # trend and tooltip are optional


@pytest.mark.asyncio
async def test_quick_actions_returns_list(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
):
    """
    Smoke test: GET /dashboard/quick-actions zwraca listę akcji
    """
    response = await async_client.get(
        "/api/v1/dashboard/quick-actions?limit=4",
        headers=auth_headers,
    )

    assert response.status_code == 200
    actions = response.json()

    assert isinstance(actions, list)
    # Lista może być pusta jeśli nie ma pending actions
    # Jeśli nie jest pusta, sprawdź strukturę
    if actions:
        action = actions[0]
        assert "action_id" in action
        assert "action_type" in action
        assert "priority" in action
        assert "title" in action
        assert "description" in action
        assert "cta_label" in action
        assert "cta_url" in action


@pytest.mark.asyncio
async def test_active_projects_returns_list(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    """
    Smoke test: GET /dashboard/projects/active zwraca listę projektów
    """
    # Create a test project
    project = Project(
        name="Test Dashboard Project",
        description="Test project for dashboard smoke test",
        owner_id=test_user.id,
        is_active=True,
        target_demographics={
            "age_range": [25, 45],
            "gender": "all",
            "location": "PL",
        }
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    response = await async_client.get(
        "/api/v1/dashboard/projects/active",
        headers=auth_headers,
    )

    assert response.status_code == 200
    projects = response.json()

    assert isinstance(projects, list)
    assert len(projects) > 0

    # Verify project structure
    proj = projects[0]
    assert "id" in proj
    assert "name" in proj
    assert "status" in proj
    assert "health" in proj
    assert "progress" in proj
    assert "insights_count" in proj
    assert "cta_label" in proj
    assert "cta_url" in proj

    # Verify health structure
    assert proj["health"]["status"] in ["on_track", "at_risk", "blocked"]
    assert isinstance(proj["health"]["score"], int)

    # Verify progress structure
    assert "demographics" in proj["progress"]
    assert "personas" in proj["progress"]
    assert "focus" in proj["progress"]
    assert "analysis" in proj["progress"]


@pytest.mark.asyncio
async def test_weekly_completion_returns_chart_data(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
):
    """
    Smoke test: GET /dashboard/analytics/weekly zwraca dane dla wykresów
    """
    response = await async_client.get(
        "/api/v1/dashboard/analytics/weekly?weeks=8",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Verify structure
    assert "weeks" in data
    assert "personas" in data
    assert "focus_groups" in data
    assert "insights" in data

    # Verify arrays
    assert isinstance(data["weeks"], list)
    assert isinstance(data["personas"], list)
    assert isinstance(data["focus_groups"], list)
    assert isinstance(data["insights"], list)

    # All arrays should have same length
    assert len(data["weeks"]) == len(data["personas"])
    assert len(data["weeks"]) == len(data["focus_groups"])
    assert len(data["weeks"]) == len(data["insights"])


@pytest.mark.asyncio
async def test_notifications_returns_list(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
):
    """
    Smoke test: GET /dashboard/notifications zwraca listę powiadomień
    """
    response = await async_client.get(
        "/api/v1/dashboard/notifications?limit=20",
        headers=auth_headers,
    )

    assert response.status_code == 200
    notifications = response.json()

    assert isinstance(notifications, list)
    # Lista może być pusta jeśli nie ma notifications
    # Jeśli nie jest pusta, sprawdź strukturę
    if notifications:
        notif = notifications[0]
        assert "id" in notif
        assert "notification_type" in notif
        assert "priority" in notif
        assert "title" in notif
        assert "message" in notif
        assert "time_ago" in notif
        assert "is_read" in notif
        assert "is_done" in notif


@pytest.mark.asyncio
async def test_health_blockers_returns_summary(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
):
    """
    Smoke test: GET /dashboard/health/blockers zwraca health summary
    """
    response = await async_client.get(
        "/api/v1/dashboard/health/blockers",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Verify structure
    assert "summary" in data
    assert "blockers" in data

    # Verify summary
    summary = data["summary"]
    assert "on_track" in summary
    assert "at_risk" in summary
    assert "blocked" in summary
    assert isinstance(summary["on_track"], int)
    assert isinstance(summary["at_risk"], int)
    assert isinstance(summary["blocked"], int)

    # Blockers is a list (może być pusta)
    assert isinstance(data["blockers"], list)


@pytest.mark.asyncio
async def test_usage_budget_returns_data(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
):
    """
    Smoke test: GET /dashboard/usage zwraca usage & budget data
    """
    response = await async_client.get(
        "/api/v1/dashboard/usage",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Verify structure
    assert "total_tokens" in data
    assert "total_cost" in data
    assert "forecast_month_end" in data
    assert "alerts" in data
    assert "history" in data

    # Verify types
    assert isinstance(data["total_tokens"], int)
    assert isinstance(data["total_cost"], (int, float))
    assert isinstance(data["forecast_month_end"], (int, float))
    assert isinstance(data["alerts"], list)
    assert isinstance(data["history"], list)


@pytest.mark.asyncio
async def test_insight_analytics_returns_data(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
):
    """
    Smoke test: GET /dashboard/analytics/insights zwraca analytics data
    """
    response = await async_client.get(
        "/api/v1/dashboard/analytics/insights",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Verify structure
    assert "top_concepts" in data
    assert "sentiment_distribution" in data
    assert "response_patterns" in data

    # Verify types
    assert isinstance(data["top_concepts"], list)
    assert isinstance(data["sentiment_distribution"], dict)
    assert isinstance(data["response_patterns"], list)

    # Verify sentiment keys
    sentiment = data["sentiment_distribution"]
    assert "positive" in sentiment
    assert "negative" in sentiment
    assert "neutral" in sentiment
    assert "mixed" in sentiment


@pytest.mark.asyncio
async def test_latest_insights_returns_list(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
):
    """
    Smoke test: GET /dashboard/insights/latest zwraca listę insights
    """
    response = await async_client.get(
        "/api/v1/dashboard/insights/latest?limit=10",
        headers=auth_headers,
    )

    assert response.status_code == 200
    insights = response.json()

    assert isinstance(insights, list)
    # Lista może być pusta jeśli nie ma insights
    # Jeśli nie jest pusta, sprawdź strukturę
    if insights:
        insight = insights[0]
        assert "id" in insight
        assert "project_id" in insight
        assert "project_name" in insight
        assert "insight_type" in insight
        assert "insight_text" in insight
        assert "confidence_score" in insight
        assert "impact_score" in insight
        assert "time_ago" in insight
        assert "evidence_count" in insight


@pytest.mark.asyncio
async def test_dashboard_requires_authentication(
    async_client: AsyncClient,
):
    """
    Smoke test: Dashboard endpoints wymagają autentykacji (401/403 bez tokena)
    """
    response = await async_client.get("/api/v1/dashboard/overview")

    # Should return 401 Unauthorized or 403 Forbidden
    assert response.status_code in [401, 403]


# ============= PHASE 2: New Tests (Figma Make Implementation) =============


@pytest.mark.asyncio
async def test_insight_analytics_includes_insight_types(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
):
    """
    Test: GET /dashboard/analytics/insights zwraca insight_types distribution

    Phase 2 Feature: insight_types (opportunity/risk/trend/pattern)
    """
    response = await async_client.get(
        "/api/v1/dashboard/analytics/insights",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Verify insight_types field exists
    assert "insight_types" in data
    assert isinstance(data["insight_types"], dict)

    # Verify insight types keys
    insight_types = data["insight_types"]
    assert "opportunity" in insight_types
    assert "risk" in insight_types
    assert "trend" in insight_types
    assert "pattern" in insight_types

    # Verify all are integers
    assert isinstance(insight_types["opportunity"], int)
    assert isinstance(insight_types["risk"], int)
    assert isinstance(insight_types["trend"], int)
    assert isinstance(insight_types["pattern"], int)


@pytest.mark.asyncio
async def test_analytics_with_filters(
    async_client: AsyncClient,
    test_user: User,
    test_project: Project,
    auth_headers: dict[str, str],
):
    """
    Test: Analytics endpoints support filter parameters (project_id, top_n)

    Phase 2 Feature: Filter parameters for analytics
    """
    # Test insight analytics with top_n filter
    response = await async_client.get(
        "/api/v1/dashboard/analytics/insights?top_n=5",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "top_concepts" in data
    # Should return max 5 concepts
    assert len(data["top_concepts"]) <= 5

    # Test insight analytics with project_id filter
    response = await async_client.get(
        f"/api/v1/dashboard/analytics/insights?project_id={test_project.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    # Should filter to specific project (may have 0 insights)

    # Test weekly analytics with project_id filter
    response = await async_client.get(
        f"/api/v1/dashboard/analytics/weekly?project_id={test_project.id}&weeks=4",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "weeks" in data
    assert "personas" in data
    assert "focus_groups" in data
    assert "insights" in data


@pytest.mark.asyncio
async def test_budget_limit_based_on_user_plan(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    """
    Test: Budget limit varies based on user plan (free/pro/enterprise)

    Phase 2 Feature: Budget limit from user settings
    """
    # Test with free plan (should be $50)
    test_user.plan = "free"
    await db_session.commit()
    await db_session.refresh(test_user)

    response = await async_client.get(
        "/api/v1/dashboard/usage",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "budget_limit" in data
    assert data["budget_limit"] == 50.0

    # Test with pro plan (should be $100)
    test_user.plan = "pro"
    await db_session.commit()
    await db_session.refresh(test_user)

    response = await async_client.get(
        "/api/v1/dashboard/usage",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["budget_limit"] == 100.0

    # Test with enterprise plan (should be $500)
    test_user.plan = "enterprise"
    await db_session.commit()
    await db_session.refresh(test_user)

    response = await async_client.get(
        "/api/v1/dashboard/usage",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["budget_limit"] == 500.0
