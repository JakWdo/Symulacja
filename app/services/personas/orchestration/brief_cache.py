"""Redis caching dla segment briefs.

Moduł odpowiada za:
- Generowanie cache keys dla segment briefs
- Get/Set operations z konfigurow alnym TTL
- Serializacja/deserializacja SegmentBrief objects
"""

import json
import logging
from typing import Optional

from config import features

from app.schemas.segment_brief import SegmentBrief

logger = logging.getLogger(__name__)

# Cache TTL z config/features.yaml (domyślnie 7 dni)
CACHE_TTL_DAYS = features.segment_cache.ttl_days if hasattr(features, 'segment_cache') else 7
CACHE_TTL_SECONDS = CACHE_TTL_DAYS * 24 * 60 * 60  # Convert days to seconds


def get_cache_key(project_id: str, segment_id: str) -> str:
    """Tworzy klucz Redis dla segment brief.

    Args:
        project_id: UUID projektu
        segment_id: ID segmentu

    Returns:
        Cache key w formacie "segment_brief:{project_id}:{segment_id}"
    """
    return f"segment_brief:{project_id}:{segment_id}"


async def get_from_cache(
    redis_client: Optional[any],
    project_id: str,
    segment_id: str
) -> Optional[SegmentBrief]:
    """Pobiera segment brief z Redis cache.

    Args:
        redis_client: Redis client instance (or None if disabled)
        project_id: UUID projektu
        segment_id: ID segmentu

    Returns:
        SegmentBrief jeśli w cache, None jeśli nie ma
    """
    if not redis_client:
        return None

    cache_key = get_cache_key(project_id, segment_id)

    try:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            # Deserializuj JSON do SegmentBrief
            brief_dict = json.loads(cached_data)
            logger.info(
                "✅ Cache HIT: Segment brief '%s' dla projektu %s",
                segment_id,
                project_id
            )
            return SegmentBrief(**brief_dict)

        logger.info(
            "❌ Cache MISS: Segment brief '%s' dla projektu %s",
            segment_id,
            project_id
        )
        return None

    except Exception as exc:
        logger.warning(
            "⚠️ Błąd odczytu z cache dla %s: %s",
            cache_key,
            exc
        )
        return None


async def save_to_cache(
    redis_client: Optional[any],
    project_id: str,
    segment_id: str,
    brief: SegmentBrief
) -> None:
    """Zapisuje segment brief do Redis cache.

    Args:
        redis_client: Redis client instance (or None if disabled)
        project_id: UUID projektu
        segment_id: ID segmentu
        brief: SegmentBrief do zapisania
    """
    if not redis_client:
        return

    cache_key = get_cache_key(project_id, segment_id)

    try:
        # Serializuj do JSON
        brief_json = brief.model_dump_json()

        # Zapisz z TTL
        await redis_client.setex(
            cache_key,
            CACHE_TTL_SECONDS,
            brief_json
        )

        logger.info(
            "💾 Cache SAVE: Segment brief '%s' dla projektu %s (TTL: %s dni)",
            segment_id,
            project_id,
            CACHE_TTL_DAYS
        )

    except Exception as exc:
        logger.warning(
            "⚠️ Błąd zapisu do cache dla %s: %s",
            cache_key,
            exc
        )


async def get_cache_ttl(
    redis_client: Optional[any],
    project_id: str,
    segment_id: str
) -> Optional[int]:
    """Pobiera TTL dla danego segment brief z cache.

    Args:
        redis_client: Redis client instance
        project_id: UUID projektu
        segment_id: ID segmentu

    Returns:
        TTL w sekundach lub None jeśli brak w cache
    """
    if not redis_client:
        return None

    cache_key = get_cache_key(project_id, segment_id)

    try:
        ttl = await redis_client.ttl(cache_key)
        return ttl if ttl > 0 else None
    except Exception:  # pragma: no cover - best effort cache probe
        return None
