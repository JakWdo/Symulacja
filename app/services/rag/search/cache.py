"""Redis cache dla hybrid search queries.

Moduł odpowiada za:
- Generowanie cache keys dla hybrid search
- Get/Set operations z 7-day TTL
- Serializacja/deserializacja Document objects
"""

import hashlib
import json
import logging
from typing import Optional

import redis.asyncio as redis
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# Cache TTL (7 days - same as GraphRAGService)
CACHE_TTL_SECONDS = 7 * 24 * 60 * 60  # 604800 seconds


def get_hybrid_search_cache_key(query: str, top_k: int) -> str:
    """Generate cache key for hybrid search.

    Args:
        query: Search query text
        top_k: Number of results

    Returns:
        Cache key string (format: "hybrid_search:query_hash:topk")
    """
    # Hash query for shorter cache key (MD5 sufficient for caching)
    query_normalized = query.lower().strip()
    query_hash = hashlib.md5(query_normalized.encode()).hexdigest()[:12]

    return f"hybrid_search:{query_hash}:{top_k}"


async def get_hybrid_cache(
    redis_client: Optional[redis.Redis],
    cache_key: str
) -> Optional[list[Document]]:
    """Get cached hybrid search results from Redis.

    Args:
        redis_client: Redis client instance (or None if disabled)
        cache_key: Redis key

    Returns:
        Cached documents (list of Document) or None if cache miss
    """
    if not redis_client:
        return None

    try:
        cached = await redis_client.get(cache_key)
        if cached:
            logger.info(f"✅ Hybrid search cache HIT for {cache_key}")
            # Deserialize JSON back to Document objects
            docs_data = json.loads(cached)
            documents = [
                Document(
                    page_content=doc_data["page_content"],
                    metadata=doc_data.get("metadata", {})
                )
                for doc_data in docs_data
            ]
            return documents
        else:
            logger.info(f"❌ Hybrid search cache MISS for {cache_key}")
            return None
    except Exception as exc:
        logger.warning(f"⚠️ Redis get failed: {exc}")
        return None


async def set_hybrid_cache(
    redis_client: Optional[redis.Redis],
    cache_key: str,
    documents: list[Document]
) -> None:
    """Store hybrid search results in Redis cache.

    Args:
        redis_client: Redis client instance (or None if disabled)
        cache_key: Redis key
        documents: List of Document objects
    """
    if not redis_client:
        return

    try:
        # Serialize Document objects to JSON
        docs_data = [
            {
                "page_content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in documents
        ]

        await redis_client.setex(
            cache_key,
            CACHE_TTL_SECONDS,
            json.dumps(docs_data, ensure_ascii=False)
        )
        logger.info(
            f"💾 Cached hybrid search: {cache_key} "
            f"({len(documents)} docs, TTL 7 days)"
        )
    except Exception as exc:
        logger.warning(f"⚠️ Redis set failed: {exc}")
