"""
Asynchronous Redis client helper.

Provides a shared Redis connection pool used across the backend for caching persona
details, segment cache, undo windows and other low-latency features.

Optimizations for Upstash Redis (TLS, connection pooling, retry logic):
- ConnectionPool z SSL/TLS support (rediss:// schema)
- Health check (ping) before returning client
- Retry logic z exponential backoff dla transient failures
- Socket keepalive dla long-lived connections
- Graceful degradation - cache failures don't crash aplikacji
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import TypeVar, Callable
from collections.abc import Awaitable

from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import ConnectionError, TimeoutError, RedisError

from config import app
from app.types import JSONValue

T = TypeVar('T')

logger = logging.getLogger(__name__)

_redis_pool: ConnectionPool | None = None
_last_health_check: float = 0


def _create_connection_pool() -> ConnectionPool:
    """
    Tworzy ConnectionPool z SSL/TLS support i Upstash-optimized settings.

    Kluczowe ustawienia dla Upstash Redis:
    - SSL/TLS (rediss:// schema) - WYMAGANE dla Upstash
    - socket_keepalive=True - zapobiega "Connection closed by server" errors
    - socket_timeout=5s - timeout dla pojedynczej operacji
    - retry_on_timeout=True - automatyczny retry przy timeout
    - health_check_interval=30s - ping Redis co 30s (Upstash idle timeout ~60s)

    Returns:
        ConnectionPool: Configured connection pool dla Redis
    """
    # Parsuj REDIS_URL dla SSL detection
    # rediss:// (z dwoma 's') = SSL enabled
    # redis:// (jedno 's') = no SSL
    is_ssl = app.redis.url.startswith("rediss://")

    logger.info(
        f"Creating Redis ConnectionPool: SSL={is_ssl}, "
        f"max_connections={app.redis.max_connections}, "
        f"socket_keepalive={app.redis.socket_keepalive}"
    )

    pool = ConnectionPool.from_url(
        app.redis.url,
        # Connection pool settings
        max_connections=app.redis.max_connections,
        # Socket settings (Upstash optimization)
        socket_timeout=app.redis.socket_timeout,
        socket_keepalive=app.redis.socket_keepalive,
        socket_keepalive_options={},  # Use OS defaults
        # Retry settings
        retry_on_timeout=app.redis.retry_on_timeout,
        # Health check interval (ping co N sekund)
        health_check_interval=app.redis.health_check_interval,
        # Encoding
        encoding="utf-8",
        decode_responses=True,
        # SSL/TLS (automatycznie z rediss://)
        # ConnectionPool.from_url() automatycznie wykrywa rediss:// i dodaje ssl=True
    )

    return pool


async def get_redis_client() -> Redis:
    """
    Zwraca Redis client z connection pool.

    Connection pool jest tworzony lazily (singleton pattern).
    Przed zwróceniem clienta wykonywany jest health check (ping).

    Returns:
        Redis: Async Redis client z connection pool

    Raises:
        ConnectionError: Jeśli health check failuje (Redis unavailable)
    """
    global _redis_pool, _last_health_check

    # Lazy initialization - utwórz pool przy pierwszym wywołaniu
    if _redis_pool is None:
        _redis_pool = _create_connection_pool()

    client = Redis(connection_pool=_redis_pool)

    # Health check co REDIS_HEALTH_CHECK_INTERVAL sekund
    # Nie pingujemy przy każdym request (overhead), tylko co N sekund
    current_time = time.time()
    if current_time - _last_health_check > app.redis.health_check_interval:
        try:
            await client.ping()
            _last_health_check = current_time
            logger.debug("Redis health check: OK")
        except Exception as exc:
            logger.warning(f"Redis health check failed: {exc}")
            # NIE raise - graceful degradation, spróbujemy użyć client anyway
            # Jeśli connection dead, redis_get_json/set_json zwróci None

    return client


async def _retry_with_backoff(
    operation: Callable[..., Awaitable[T]],
    *args,
    max_retries: int = 3,
    backoff: float = 0.5,
    **kwargs
) -> T:
    """
    Wykonuje operację Redis z retry logic i exponential backoff.

    Retry dla transient failures:
    - ConnectionError (server closed connection)
    - TimeoutError (operation timeout)

    Args:
        operation: Async funkcja do wykonania (np. client.get, client.set)
        *args: Argumenty dla operacji
        max_retries: Maksymalna liczba retry attempts
        backoff: Początkowy backoff (sekundy), rosnący exponentially
        **kwargs: Keyword argumenty dla operacji

    Returns:
        Wynik operacji lub None przy failure

    Raises:
        Exception: Jeśli wszystkie retry attempts failują
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            return await operation(*args, **kwargs)
        except (ConnectionError, TimeoutError) as exc:
            last_exception = exc
            if attempt < max_retries - 1:
                # Exponential backoff: 0.5s, 1s, 2s
                wait_time = backoff * (2 ** attempt)
                logger.warning(
                    f"Redis operation failed (attempt {attempt + 1}/{max_retries}): {exc}. "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    f"Redis operation failed after {max_retries} attempts: {exc}",
                    exc_info=exc
                )
                raise
        except Exception as exc:
            # Non-transient error - nie retry
            logger.error(f"Redis operation failed (non-retryable): {exc}", exc_info=exc)
            raise

    # Shouldn't reach here, but for type safety
    if last_exception:
        raise last_exception


async def redis_get_json(key: str) -> JSONValue | None:
    """Fetch JSON data from Redis and decode it.

    Graceful degradation:
    - Connection errors → return None (cache miss)
    - JSON decode errors → delete corrupted key, return None
    - Timeout errors → retry z exponential backoff, potem return None

    Returns None on any failure - cache failures don't break the application.

    Args:
        key: Redis key

    Returns:
        Decoded JSON value lub None jeśli key nie istnieje lub error
    """
    try:
        client = await get_redis_client()

        # Retry z exponential backoff dla transient failures
        raw = await _retry_with_backoff(
            client.get,
            key,
            max_retries=app.redis.max_retries,
            backoff=app.redis.retry_backoff,
        )

        if raw is None:
            return None

        try:
            return json.loads(raw)
        except json.JSONDecodeError as json_exc:
            logger.warning(f"Redis JSON decode error for key '{key}': {json_exc}")
            # Clean up corrupted data (fire and forget)
            try:
                await client.delete(key)
            except Exception:
                pass  # Ignore cleanup errors
            return None

    except (ConnectionError, TimeoutError, RedisError) as exc:
        logger.warning(f"Redis GET failed for key '{key}': {exc}")
        return None  # Graceful fallback - treat as cache miss

    except Exception as exc:
        # Unexpected error - log z backtrace
        logger.error(f"Unexpected error in redis_get_json for key '{key}': {exc}", exc_info=exc)
        return None


async def redis_set_json(key: str, value: JSONValue, ttl_seconds: int | None = None) -> bool:
    """Store JSON-serialisable value in Redis with optional TTL.

    Graceful degradation:
    - Connection errors → silent failure, return False
    - Timeout errors → retry z exponential backoff, potem silent failure

    Cache write failures don't break the application.

    Args:
        key: Redis key
        value: JSON-serialisable value
        ttl_seconds: Optional TTL (time-to-live) w sekundach

    Returns:
        True jeśli set successful, False przy failure
    """
    try:
        client = await get_redis_client()
        payload = json.dumps(value)

        # Retry z exponential backoff dla transient failures
        if ttl_seconds is not None:
            await _retry_with_backoff(
                client.set,
                key,
                payload,
                ex=ttl_seconds,
                max_retries=app.redis.max_retries,
                backoff=app.redis.retry_backoff,
            )
        else:
            await _retry_with_backoff(
                client.set,
                key,
                payload,
                max_retries=app.redis.max_retries,
                backoff=app.redis.retry_backoff,
            )

        return True

    except (ConnectionError, TimeoutError, RedisError) as exc:
        logger.warning(f"Redis SET failed for key '{key}': {exc}")
        return False  # Silent failure - cache write is not critical

    except Exception as exc:
        # Unexpected error - log z backtrace
        logger.error(f"Unexpected error in redis_set_json for key '{key}': {exc}", exc_info=exc)
        return False


async def redis_delete(key: str) -> bool:
    """Remove a key from Redis.

    Graceful degradation - cache delete failures don't break the application.

    Args:
        key: Redis key to delete

    Returns:
        True jeśli delete successful, False przy failure
    """
    try:
        client = await get_redis_client()

        # Retry z exponential backoff dla transient failures
        await _retry_with_backoff(
            client.delete,
            key,
            max_retries=app.redis.max_retries,
            backoff=app.redis.retry_backoff,
        )

        return True

    except (ConnectionError, TimeoutError, RedisError) as exc:
        logger.warning(f"Redis DELETE failed for key '{key}': {exc}")
        return False  # Silent failure - cache invalidation is not critical

    except Exception as exc:
        # Unexpected error - log z backtrace
        logger.error(f"Unexpected error in redis_delete for key '{key}': {exc}", exc_info=exc)
        return False


async def redis_delete_pattern(pattern: str) -> int:
    """Delete all keys matching a pattern using SCAN (safe for production).

    Uses SCAN cursor to avoid blocking Redis with KEYS command.
    Graceful degradation - cache delete failures don't break the application.

    Args:
        pattern: Redis key pattern (e.g., "dashboard:weekly:user123:*")

    Returns:
        Number of keys deleted, or 0 on failure
    """
    try:
        client = await get_redis_client()

        deleted_count = 0
        cursor = 0

        # Use SCAN instead of KEYS (production-safe)
        while True:
            cursor, keys = await _retry_with_backoff(
                client.scan,
                cursor=cursor,
                match=pattern,
                count=100,  # Scan 100 keys per iteration
                max_retries=app.redis.max_retries,
                backoff=app.redis.retry_backoff,
            )

            if keys:
                # Delete keys in batch
                await _retry_with_backoff(
                    client.delete,
                    *keys,
                    max_retries=app.redis.max_retries,
                    backoff=app.redis.retry_backoff,
                )
                deleted_count += len(keys)

            # SCAN cursor = 0 means iteration complete
            if cursor == 0:
                break

        if deleted_count > 0:
            logger.debug(f"Deleted {deleted_count} keys matching pattern '{pattern}'")

        return deleted_count

    except (ConnectionError, TimeoutError, RedisError) as exc:
        logger.warning(f"Redis DELETE_PATTERN failed for pattern '{pattern}': {exc}")
        return 0  # Silent failure - cache invalidation is not critical

    except Exception as exc:
        # Unexpected error - log z backtrace
        logger.error(f"Unexpected error in redis_delete_pattern for pattern '{pattern}': {exc}", exc_info=exc)
        return 0
