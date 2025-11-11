"""
Dashboard Cost Calculator - Kalkulacja kosztów i budżetu

Odpowiedzialny za:
- Kalkulację kosztów użycia API
- Tracking budżetu użytkownika
- Alerty budżetowe
- Historia kosztów (30 dni)
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User
from app.services.dashboard.usage_tracking_service import UsageTrackingService
from app.core.redis import redis_get_json, redis_set_json


async def get_usage_budget(
    db: AsyncSession,
    usage_service: UsageTrackingService,
    user_id: UUID,
) -> dict[str, Any]:
    """
    Pobierz token usage, costs, forecast, alerts

    Cached: Redis 60s

    Args:
        db: Database session
        usage_service: UsageTrackingService instance
        user_id: UUID użytkownika

    Returns:
        Usage & budget data
    """
    # Check Redis cache (60s TTL - usage changes less frequently)
    cache_key = f"dashboard:usage:{user_id}"
    cached = await redis_get_json(cache_key)
    if cached is not None:
        return cached

    # Calculate current month costs
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    costs = await usage_service.calculate_costs(
        user_id, start_date=month_start
    )

    # Get user to determine budget limit based on plan
    user_stmt = select(User).where(User.id == user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    # Determine budget limit: user custom limit > plan-based limit > fallback
    if user and user.budget_limit is not None:
        # User has set custom budget limit in Settings
        budget_limit = user.budget_limit
    elif user and user.plan:
        # Fallback to plan-based budget limits
        budget_map = {
            "free": 50.0,
            "pro": 100.0,
            "enterprise": 500.0,
        }
        budget_limit = budget_map.get(user.plan, 100.0)  # default to pro if unknown plan
    else:
        budget_limit = 100.0  # fallback

    forecast = await usage_service.forecast_budget(user_id, budget_limit)

    # Alerts
    alerts = await usage_service.check_budget_alerts(user_id, budget_limit)

    # History (last 30 days)
    history = []
    for i in range(29, -1, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        day_costs = await usage_service.calculate_costs(
            user_id, start_date=day_start, end_date=day_end
        )

        history.append(
            {
                "date": day_start.strftime("%Y-%m-%d"),
                "total_tokens": day_costs["total_tokens"],
                "total_cost": day_costs["total_cost"],
            }
        )

    result = {
        "total_tokens": costs["total_tokens"],
        "total_cost": costs["total_cost"],
        "forecast_month_end": forecast["forecast_month_end"],
        "budget_limit": budget_limit,
        "alerts": alerts,
        "history": history,
        "alert_thresholds": {
            "warning": user.warning_threshold if user and user.warning_threshold is not None else 80,
            "critical": user.critical_threshold if user and user.critical_threshold is not None else 90,
        },
    }

    # Store in Redis cache (60s TTL)
    await redis_set_json(cache_key, result, ttl_seconds=60)
    return result
