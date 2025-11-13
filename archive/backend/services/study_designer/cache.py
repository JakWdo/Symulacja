"""
Study Designer Response Caching

Cache'uje LLM responses aby zredukować redundantne wywołania API.

Strategy:
- Cache key = hash(conversation_history + user_message)
- TTL = 1 hour (3600s)
- Storage = Redis
- Hit rate expected: 20-30% (users często pytają o podobne rzeczy)

Benefits:
- <10ms response dla cached (vs 3-5s LLM call)
- -30% LLM costs
- Better UX (instant responses)

Usage:
    from app.services.study_designer.cache import StudyDesignerCache

    cache = StudyDesignerCache(redis_client)

    # Check cache first
    cached = await cache.get_extraction(conversation_history, user_message)
    if cached:
        return cached

    # LLM call
    result = await call_llm(...)

    # Cache result
    await cache.set_extraction(conversation_history, user_message, result)
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class StudyDesignerCache:
    """
    Response cache dla Study Designer LLM calls.

    Attributes:
        redis: Async Redis client
        ttl: Time-to-live dla cached entries (seconds)
        key_prefix: Prefix dla Redis keys
    """

    def __init__(self, redis: Redis, ttl: int = 3600):
        """
        Inicjalizuje cache.

        Args:
            redis: Async Redis client
            ttl: Time-to-live w sekundach (default 1h)
        """
        self.redis = redis
        self.ttl = ttl
        self.key_prefix = "study_designer:cache"

        logger.debug(
            f"[Study Designer Cache] Initialized with TTL={ttl}s",
            extra={"ttl": ttl, "prefix": self.key_prefix}
        )

    def _make_cache_key(self, conversation: list[dict], user_message: str) -> str:
        """
        Tworzy deterministic cache key z conversation history + user message.

        Args:
            conversation: Lista message dicts [{role, content}, ...]
            user_message: Najnowsza wiadomość użytkownika

        Returns:
            Redis key (string)

        Example:
            "study_designer:cache:abc123def456..."
        """
        # Serialize conversation + message to JSON
        cache_input = {
            "conversation": conversation,
            "user_message": user_message
        }

        json_str = json.dumps(cache_input, sort_keys=True, ensure_ascii=False)

        # SHA256 hash for fixed-length key
        hash_digest = hashlib.sha256(json_str.encode("utf-8")).hexdigest()

        # Prefix + hash
        key = f"{self.key_prefix}:{hash_digest}"

        return key

    async def get_extraction(
        self, conversation: list[dict], user_message: str
    ) -> dict[str, Any] | None:
        """
        Pobiera cached extraction result.

        Args:
            conversation: Message history (bez ostatniej user message)
            user_message: Latest user message

        Returns:
            Cached extraction dict lub None jeśli cache miss
        """
        key = self._make_cache_key(conversation, user_message)

        try:
            cached_json = await self.redis.get(key)

            if cached_json:
                # Cache hit
                logger.info(
                    "[Study Designer Cache] ✅ Cache HIT",
                    extra={"key": key[:50] + "..."}
                )

                result = json.loads(cached_json)
                return result
            else:
                # Cache miss
                logger.debug(
                    "[Study Designer Cache] ❌ Cache MISS",
                    extra={"key": key[:50] + "..."}
                )
                return None

        except Exception as e:
            # Redis error - log but don't fail
            logger.warning(
                f"[Study Designer Cache] Redis GET failed: {e}",
                exc_info=True,
                extra={"key": key[:50] + "..."}
            )
            return None

    async def set_extraction(
        self, conversation: list[dict], user_message: str, result: dict[str, Any]
    ) -> bool:
        """
        Zapisuje extraction result do cache.

        Args:
            conversation: Message history
            user_message: User message
            result: Extraction result dict (JSON-serializable)

        Returns:
            True jeśli sukces, False jeśli failed
        """
        key = self._make_cache_key(conversation, user_message)

        try:
            # Serialize result
            result_json = json.dumps(result, ensure_ascii=False)

            # Set with TTL
            await self.redis.setex(key, self.ttl, result_json)

            logger.debug(
                f"[Study Designer Cache] Cached result (TTL={self.ttl}s)",
                extra={"key": key[:50] + "...", "size_bytes": len(result_json)}
            )

            return True

        except Exception as e:
            # Redis error - log but don't fail
            logger.warning(
                f"[Study Designer Cache] Redis SET failed: {e}",
                exc_info=True,
                extra={"key": key[:50] + "..."}
            )
            return False

    async def invalidate_session(self, session_id: str) -> int:
        """
        Inwaliduje cache entries dla danej sesji.

        NOTE: Obecnie używamy hash-based keys bez session_id,
        więc to nie jest możliwe. Implementacja opcjonalna dla przyszłości.

        Args:
            session_id: UUID sesji

        Returns:
            Liczba usuniętych keys (zawsze 0 w current implementation)
        """
        # Not implemented - hash-based keys nie zawierają session_id
        logger.warning(
            f"[Study Designer Cache] Session invalidation not implemented (hash-based keys)"
        )
        return 0

    async def clear_all(self) -> int:
        """
        Czyści WSZYSTKIE cached entries dla Study Designer.

        UWAGA: Use with caution - usuwa cały cache!

        Returns:
            Liczba usuniętych keys
        """
        try:
            # Find all keys matching prefix
            pattern = f"{self.key_prefix}:*"
            keys = []

            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                # Delete all matching keys
                deleted = await self.redis.delete(*keys)
                logger.warning(
                    f"[Study Designer Cache] Cleared {deleted} cache entries",
                    extra={"deleted_count": deleted}
                )
                return deleted
            else:
                logger.info("[Study Designer Cache] No keys to clear")
                return 0

        except Exception as e:
            logger.error(
                f"[Study Designer Cache] Clear all failed: {e}",
                exc_info=True
            )
            return 0
