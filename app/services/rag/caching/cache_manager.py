"""Manager cache dla hybrid search - Redis caching z 7-dniowym TTL.

Moduł odpowiada za generowanie kluczy cache, pobieranie i zapisywanie wyników
hybrid search w Redis z automatycznym wygasaniem po 7 dniach.
"""

from typing import Optional, List, Dict
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


def get_cache_key(query: str, k: int, alpha: float = 0.5, include_graph: bool = False) -> str:
    """Generate cache key for hybrid search.

    Args:
        query: Search query text
        k: Number of results
        alpha: RRF alpha parameter (default 0.5 for 50/50 weight)
        include_graph: Whether graph enrichment is enabled

    Returns:
        Cache key string (format: "hybrid_search:query_hash:k:alpha:graph")
    """
    # Hash query for shorter cache key (MD5 sufficient for caching)
    query_normalized = query.lower().strip()
    query_hash = hashlib.md5(query_normalized.encode()).hexdigest()[:12]

    # Include graph flag in cache key (graph enrichment changes results)
    graph_suffix = ":graph" if include_graph else ""

    return f"hybrid_search:{query_hash}:{k}:{alpha}{graph_suffix}"


async def get_cache(cache_key: str, redis_client) -> Optional[List[Dict]]:
    """Get cached hybrid search results from Redis.

    Args:
        cache_key: Redis key
        redis_client: Redis async client instance

    Returns:
        Cached documents (list of dicts with page_content and metadata) or None if cache miss
    """
    if not redis_client:
        return None

    try:
        cached = await redis_client.get(cache_key)
        if cached:
            logger.info(f"✅ Hybrid search cache HIT for {cache_key}")
            # Deserialize JSON back to list of dicts
            docs_data = json.loads(cached)
            return docs_data
        else:
            logger.info(f"❌ Hybrid search cache MISS for {cache_key}")
            return None
    except Exception as exc:
        logger.warning(f"⚠️ Redis get failed: {exc}")
        return None


async def set_cache(
    cache_key: str,
    results: List[Dict],
    redis_client,
    ttl_seconds: int = 604800  # 7 days
) -> None:
    """Store hybrid search results in Redis cache.

    Args:
        cache_key: Redis key
        results: List of document dicts (with page_content and metadata)
        redis_client: Redis async client instance
        ttl_seconds: Time to live in seconds (default 7 days = 604800s)
    """
    if not redis_client:
        return

    try:
        await redis_client.setex(
            cache_key,
            ttl_seconds,
            json.dumps(results, ensure_ascii=False)
        )
        logger.info(
            f"💾 Cached hybrid search: {cache_key} "
            f"({len(results)} docs, TTL {ttl_seconds//86400} days)"
        )
    except Exception as exc:
        logger.warning(f"⚠️ Redis set failed: {exc}")
