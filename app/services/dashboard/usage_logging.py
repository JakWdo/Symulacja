"""Utility helpers for logging LLM token usage to UsageMetric."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, replace
from typing import Any
from uuid import UUID

from app.db.session import AsyncSessionLocal
from app.services.dashboard.usage_tracking_service import UsageTrackingService

logger = logging.getLogger(__name__)


@dataclass
class UsageLogContext:
    """Context information describing a single LLM operation."""

    user_id: UUID | None
    operation_type: str
    project_id: UUID | None = None
    operation_id: UUID | None = None
    model_name: str | None = None
    metadata: dict[str, Any] | None = None


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        # Allow floats/strings convertible to int
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _extract_usage_counts(usage_meta: dict[str, Any]) -> tuple[int | None, int | None]:
    """Extract input/output token counts from Gemini/LLM metadata."""
    candidates = [
        "input_token_count",
        "prompt_token_count",
        "promptTokenCount",  # Gemini camelCase
        "inputTokens",
        "promptTokens",
        "prompt_tokens",
    ]
    output_candidates = [
        "output_token_count",
        "candidates_token_count",
        "candidatesTokenCount",  # Gemini camelCase
        "outputTokens",
        "completionTokens",
        "completion_tokens",
    ]

    input_tokens = None
    output_tokens = None

    for key in candidates:
        if key in usage_meta:
            input_tokens = _coerce_int(usage_meta.get(key))
            if input_tokens is not None:
                break

    for key in output_candidates:
        if key in usage_meta:
            output_tokens = _coerce_int(usage_meta.get(key))
            if output_tokens is not None:
                break

    # Some payloads use nested objects like {"token_usage": {"total_tokens": ...}}
    if input_tokens is None:
        token_usage = usage_meta.get("token_usage")
        if isinstance(token_usage, dict):
            input_tokens = _coerce_int(token_usage.get("prompt_tokens"))
            if input_tokens is None:
                input_tokens = _coerce_int(token_usage.get("input_tokens"))

    if output_tokens is None:
        token_usage = usage_meta.get("token_usage")
        if isinstance(token_usage, dict):
            output_tokens = _coerce_int(token_usage.get("completion_tokens"))
            if output_tokens is None:
                output_tokens = _coerce_int(token_usage.get("output_tokens"))

    return input_tokens, output_tokens


async def log_usage_from_metadata(
    context: UsageLogContext,
    usage_metadata: dict[str, Any] | None,
) -> None:
    """Persist usage metrics using extracted metadata."""
    if usage_metadata is None:
        logger.debug("Usage metadata missing for %s", context.operation_type)
        return

    input_tokens, output_tokens = _extract_usage_counts(usage_metadata)

    if input_tokens is None and output_tokens is None:
        logger.debug(
            "Token counts missing in usage metadata for %s: %s",
            context.operation_type,
            usage_metadata,
        )
        return

    await log_usage(
        context,
        input_tokens or 0,
        output_tokens or 0,
    )


async def log_usage(
    context: UsageLogContext,
    input_tokens: int,
    output_tokens: int,
) -> None:
    """Store token usage in the UsageMetric table."""
    if not context.user_id:
        logger.debug("Missing user_id for usage logging; skipping")
        return

    # Skip no-op logging to avoid noise
    if (input_tokens or 0) == 0 and (output_tokens or 0) == 0:
        return

    try:
        async with AsyncSessionLocal() as session:
            service = UsageTrackingService(session)
            await service.track_token_usage(
                user_id=context.user_id,
                operation_type=context.operation_type,
                model_name=context.model_name or "unknown",
                input_tokens=int(input_tokens or 0),
                output_tokens=int(output_tokens or 0),
                project_id=context.project_id,
                operation_id=context.operation_id,
            )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Failed to log LLM usage: %s", exc)


def context_with_model(context: UsageLogContext, model_name: str | None) -> UsageLogContext:
    """Return a copy of context with model name filled in."""
    if context.model_name == model_name:
        return context
    return replace(context, model_name=model_name)


def schedule_usage_logging(
    context: UsageLogContext,
    usage_metadata: dict[str, Any] | None,
) -> None:
    """Fire-and-forget helper to log usage without blocking the main flow."""

    async def _runner() -> None:
        try:
            await log_usage_from_metadata(context, usage_metadata)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Background usage logging failed: %s", exc)

    if usage_metadata is None:
        # Nothing to log, bail early.
        return

    try:
        task = asyncio.create_task(_runner())
        task.add_done_callback(_usage_task_done)
    except RuntimeError:
        # No running loop (e.g. synchronous context); fallback to direct call
        asyncio.run(_runner())


def _usage_task_done(task: asyncio.Task) -> None:
    if task.cancelled():  # pragma: no cover - nothing to log
        return
    exc = task.exception()
    if exc:  # pragma: no cover - defensive logging
        logger.exception("Background usage logging raised: %s", exc)
