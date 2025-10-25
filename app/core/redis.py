"""
Asynchronous Redis client helper.

Provides a shared Redis connection used across the backend for caching persona
details, undo windows and other low-latency features.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from redis.asyncio import Redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_redis_client: Redis | None = None


def get_redis_client() -> Redis:
    """
    Return a singleton Redis client configured from settings.

    The connection is created lazily and re-used for subsequent calls.
    """
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def redis_get_json(key: str) -> Any | None:
    """Fetch JSON data from Redis and decode it.

    Returns None on any failure (connection error, JSON decode error).
    Graceful degradation - cache failures don't break the application.
    """
    try:
        client = get_redis_client()
        raw = await client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as json_exc:
            logger.warning(f"Redis JSON decode error for key '{key}': {json_exc}")
            await client.delete(key)  # Clean up corrupted data
            return None
    except Exception as exc:
        logger.warning(f"Redis GET failed for key '{key}': {exc}")
        return None  # Graceful fallback - treat as cache miss


async def redis_set_json(key: str, value: Any, ttl_seconds: int | None = None) -> None:
    """Store JSON-serialisable value in Redis with optional TTL.

    Fails silently on connection errors - cache write failures don't break the application.
    """
    try:
        client = get_redis_client()
        payload = json.dumps(value)
        if ttl_seconds is not None:
            await client.set(key, payload, ex=ttl_seconds)
        else:
            await client.set(key, payload)
    except Exception as exc:
        logger.warning(f"Redis SET failed for key '{key}': {exc}")
        # Silent failure - cache write is not critical


async def redis_delete(key: str) -> None:
    """Remove a key from Redis.

    Fails silently on connection errors - cache delete failures don't break the application.
    """
    try:
        client = get_redis_client()
        await client.delete(key)
    except Exception as exc:
        logger.warning(f"Redis DELETE failed for key '{key}': {exc}")
        # Silent failure - cache invalidation is not critical
