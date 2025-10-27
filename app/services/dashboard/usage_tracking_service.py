"""
Usage Tracking Service - Token usage & cost tracking

Tracking kosztów LLM operations:
- Token usage (input, output, total)
- Cost calculation based on model pricing
- Budget forecasting
- Budget alerts (>90% usage)
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UsageMetric

# Model pricing (USD per 1M tokens) - Gemini 2.5 pricing
MODEL_PRICING = {
    "gemini-2.5-flash": {
        "input_price_per_million": 0.075,  # $0.075 per 1M input tokens
        "output_price_per_million": 0.30,  # $0.30 per 1M output tokens
    },
    "gemini-2.5-pro": {
        "input_price_per_million": 1.25,  # $1.25 per 1M input tokens
        "output_price_per_million": 5.00,  # $5.00 per 1M output tokens
    },
}


class UsageTrackingService:
    """Serwis do trackingu usage tokenów i kosztów LLM"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def track_token_usage(
        self,
        user_id: UUID,
        operation_type: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        project_id: UUID | None = None,
        operation_id: UUID | None = None,
    ) -> UsageMetric:
        """
        Zapisz token usage dla operacji LLM

        Args:
            user_id: UUID użytkownika
            operation_type: Typ operacji ('persona_generation', 'focus_group', etc.)
            model_name: Nazwa modelu ('gemini-2.5-flash')
            input_tokens: Liczba tokenów wejściowych
            output_tokens: Liczba tokenów wyjściowych
            project_id: UUID projektu (optional)
            operation_id: UUID konkretnej operacji (optional)

        Returns:
            UsageMetric: Zapisana metryka
        """
        total_tokens = input_tokens + output_tokens

        # Calculate costs based on model pricing
        pricing = MODEL_PRICING.get(
            model_name, MODEL_PRICING["gemini-2.5-flash"]
        )  # fallback to Flash

        input_cost = (input_tokens / 1_000_000) * pricing["input_price_per_million"]
        output_cost = (output_tokens / 1_000_000) * pricing["output_price_per_million"]
        total_cost = input_cost + output_cost

        metric = UsageMetric(
            user_id=user_id,
            project_id=project_id,
            operation_type=operation_type,
            operation_id=operation_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            model_name=model_name,
        )

        self.db.add(metric)
        await self.db.commit()
        await self.db.refresh(metric)

        return metric

    async def calculate_costs(
        self,
        user_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Oblicz łączne koszty dla użytkownika

        Args:
            user_id: UUID użytkownika
            start_date: Data początkowa (optional)
            end_date: Data końcowa (optional)

        Returns:
            {
                "total_tokens": int,
                "total_cost": float,
                "by_operation": {...},
                "by_model": {...},
            }
        """
        # Base query
        query = select(
            func.sum(UsageMetric.total_tokens).label("total_tokens"),
            func.sum(UsageMetric.total_cost).label("total_cost"),
        ).where(UsageMetric.user_id == user_id)

        if start_date:
            query = query.where(UsageMetric.operation_timestamp >= start_date)
        if end_date:
            query = query.where(UsageMetric.operation_timestamp <= end_date)

        result = await self.db.execute(query)
        row = result.first()

        # By operation type
        by_operation_query = (
            select(
                UsageMetric.operation_type,
                func.sum(UsageMetric.total_tokens).label("tokens"),
                func.sum(UsageMetric.total_cost).label("cost"),
            )
            .where(UsageMetric.user_id == user_id)
            .group_by(UsageMetric.operation_type)
        )

        if start_date:
            by_operation_query = by_operation_query.where(
                UsageMetric.operation_timestamp >= start_date
            )
        if end_date:
            by_operation_query = by_operation_query.where(
                UsageMetric.operation_timestamp <= end_date
            )

        by_operation_result = await self.db.execute(by_operation_query)
        by_operation = {
            row.operation_type: {"tokens": row.tokens, "cost": float(row.cost)}
            for row in by_operation_result
        }

        # By model
        by_model_query = (
            select(
                UsageMetric.model_name,
                func.sum(UsageMetric.total_tokens).label("tokens"),
                func.sum(UsageMetric.total_cost).label("cost"),
            )
            .where(UsageMetric.user_id == user_id)
            .group_by(UsageMetric.model_name)
        )

        if start_date:
            by_model_query = by_model_query.where(
                UsageMetric.operation_timestamp >= start_date
            )
        if end_date:
            by_model_query = by_model_query.where(
                UsageMetric.operation_timestamp <= end_date
            )

        by_model_result = await self.db.execute(by_model_query)
        by_model = {
            row.model_name: {"tokens": row.tokens, "cost": float(row.cost)}
            for row in by_model_result
        }

        return {
            "total_tokens": int(row.total_tokens or 0),
            "total_cost": float(row.total_cost or 0.0),
            "by_operation": by_operation,
            "by_model": by_model,
        }

    async def forecast_budget(
        self, user_id: UUID, budget_limit: float | None = None
    ) -> dict[str, Any]:
        """
        Prognoza kosztów na koniec miesiąca

        Args:
            user_id: UUID użytkownika
            budget_limit: Limit budżetu (USD, optional)

        Returns:
            {
                "current_month_cost": float,
                "forecast_month_end": float,
                "budget_limit": float | None,
                "budget_used_percent": float,
                "days_remaining": int,
            }
        """
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Calculate current month cost
        current_costs = await self.calculate_costs(
            user_id, start_date=month_start, end_date=now
        )
        current_month_cost = current_costs["total_cost"]

        # Calculate days elapsed and days remaining
        days_in_month = (month_start.replace(month=month_start.month + 1) - month_start).days if month_start.month < 12 else 31
        days_elapsed = (now - month_start).days + 1
        days_remaining = days_in_month - days_elapsed

        # Forecast based on daily average
        if days_elapsed > 0:
            daily_avg = current_month_cost / days_elapsed
            forecast_month_end = current_month_cost + (daily_avg * days_remaining)
        else:
            forecast_month_end = current_month_cost

        # Budget used percent
        budget_used_percent = (
            (current_month_cost / budget_limit * 100) if budget_limit else None
        )

        return {
            "current_month_cost": current_month_cost,
            "forecast_month_end": forecast_month_end,
            "budget_limit": budget_limit,
            "budget_used_percent": budget_used_percent,
            "days_remaining": days_remaining,
        }

    async def check_budget_alerts(
        self, user_id: UUID, budget_limit: float
    ) -> list[dict[str, Any]]:
        """
        Sprawdź czy przekroczono progi budżetu

        Args:
            user_id: UUID użytkownika
            budget_limit: Limit budżetu (USD)

        Returns:
            Lista alertów
        """
        forecast = await self.forecast_budget(user_id, budget_limit)
        alerts = []

        if forecast["budget_used_percent"]:
            if forecast["budget_used_percent"] >= 100:
                alerts.append(
                    {
                        "alert_type": "exceeded",
                        "message": f"Budget exceeded: ${forecast['current_month_cost']:.2f} / ${budget_limit:.2f}",
                        "threshold": 1.0,
                        "current": forecast["budget_used_percent"] / 100,
                    }
                )
            elif forecast["budget_used_percent"] >= 90:
                alerts.append(
                    {
                        "alert_type": "warning",
                        "message": f"Budget warning: {forecast['budget_used_percent']:.1f}% used (${forecast['current_month_cost']:.2f} / ${budget_limit:.2f})",
                        "threshold": 0.9,
                        "current": forecast["budget_used_percent"] / 100,
                    }
                )

        return alerts
