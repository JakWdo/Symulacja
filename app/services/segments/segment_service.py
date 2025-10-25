"""
SegmentService - Segment cache manager dla segment-first architecture.

Ten serwis zarządza cache'owaniem kontekstu RAG + segment brief na poziomie segmentu
demograficznego zamiast per-persona. To kluczowa optymalizacja Fazy 2.

Korzyści:
- 3x szybsze generowanie person (8 RAG calls zamiast 16-24)
- 60% mniej tokenów (RAG context reused w segmencie)
- Lepsza spójność (persony w segmencie dzielą kontekst)

Cache strategy:
- Redis-only (no DB model) - łatwiejszy rollback
- TTL: 7 days (configurable)
- Cache key: segment:{project_id}:{demo_hash}
- Graceful degradation: cache failures nie crashują serwisu

Performance:
- Cache hit: < 50ms
- Cache miss (generation): 3-5s (RAG + brief generation)
- Cache hit rate target: > 70%
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.redis import redis_get_json, redis_set_json
from app.services.retrieval.retrieval_service import RetrievalService
from app.services.personas.segment_brief_service import SegmentBriefService

settings = get_settings()
logger = logging.getLogger(__name__)


class SegmentService:
    """Manages segment-level cache for RAG + brief."""

    def __init__(self, db: AsyncSession):
        """Inicjalizuje segment service z retrieval i brief services.

        Args:
            db: AsyncSession dla SegmentBriefService
        """
        self.db = db
        self.retrieval_service = RetrievalService()
        self.brief_service = SegmentBriefService(db=db)

        # Cache TTL (7 dni, configurable)
        self.cache_ttl_seconds = getattr(
            settings, "SEGMENT_CACHE_TTL_DAYS", 7
        ) * 24 * 60 * 60

        logger.info(
            f"SegmentService zainicjalizowany (cache TTL: {self.cache_ttl_seconds}s = "
            f"{self.cache_ttl_seconds // 86400} dni)"
        )

    async def get_or_create_segment_cache(
        self,
        project_id: int | str,  # Accept int, UUID string, or str
        demographics: dict[str, Any],
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """Pobiera lub tworzy cache dla segmentu demograficznego.

        Cache key: f"segment:{project_id}:{demo_hash}"
        TTL: 7 days (604800 seconds)

        Graceful degradation: Jeśli Redis failure, zwraca freshly generated context
        (bez cache'owania - ale nie crashuje serwisu).

        Args:
            project_id: ID projektu (int, UUID, lub str)
            demographics: Dict z age_group, gender, education, location
            force_refresh: Wymuś regenerację cache (default: False)

        Returns:
            Dict z kluczami:
            - rag_context: str (RAG context ≤1500 chars)
            - segment_brief: str (segment brief 900-1200 chars)
            - graph_context: dict (graph insights ≤5 nodes)
            - characteristics: list[str] (segment characteristics 4-6 items)
            - created_at: str (ISO timestamp)
            - cache_hit: bool (czy z cache czy fresh)

        Raises:
            ValueError: Jeśli demographics niepełne (brak wymaganych pól)
        """
        # Validate demographics
        required_fields = ["age", "gender", "education", "location"]
        # Alternatywne nazwy (age vs age_group, education vs education_level)
        actual_fields = {
            "age": demographics.get("age") or demographics.get("age_group"),
            "gender": demographics.get("gender"),
            "education": demographics.get("education") or demographics.get("education_level"),
            "location": demographics.get("location"),
        }

        missing = [k for k, v in actual_fields.items() if not v]
        if missing:
            raise ValueError(
                f"Demographics niepełne - brakuje pól: {missing}. "
                f"Wymagane: age/age_group, gender, education/education_level, location"
            )

        # Generate cache key
        demo_hash = self.retrieval_service.generate_segment_hash(
            age_group=actual_fields["age"],
            gender=actual_fields["gender"],
            education=actual_fields["education"],
            location=actual_fields["location"],
        )
        # Convert project_id to string (handles UUID, int, str)
        proj_id_str = str(project_id)
        cache_key = f"segment:{proj_id_str}:{demo_hash}"

        logger.info(
            f"🔍 SegmentService.get_or_create_segment_cache: project={proj_id_str}, "
            f"demo_hash={demo_hash}, force_refresh={force_refresh}"
        )

        # Try cache first (unless force_refresh)
        if not force_refresh:
            cached = await redis_get_json(cache_key)
            if cached:
                logger.info(f"✅ Cache HIT: {cache_key}")
                cached["cache_hit"] = True
                return cached

        logger.info(f"⚠️ Cache MISS: {cache_key} - generuję nowy kontekst")

        # Cache miss or force_refresh - generate fresh context
        segment_context = await self._generate_segment_context(
            project_id=project_id,
            demographics=demographics,
            demo_hash=demo_hash,
        )

        # Try to cache (graceful failure - nie crashuje jeśli Redis down)
        await redis_set_json(cache_key, segment_context, ttl_seconds=self.cache_ttl_seconds)

        segment_context["cache_hit"] = False
        return segment_context

    async def _generate_segment_context(
        self,
        project_id: int | str,
        demographics: dict[str, Any],
        demo_hash: str,
    ) -> dict[str, Any]:
        """Generuje fresh segment context (RAG + brief).

        Args:
            project_id: ID projektu
            demographics: Demografia segmentu
            demo_hash: Hash demografii (dla logowania)

        Returns:
            Dict z segment context (bez cache_hit flag)
        """
        logger.info(
            f"🔨 Generating fresh segment context: project={project_id}, demo_hash={demo_hash}"
        )

        # Normalize field names
        age_group = demographics.get("age") or demographics.get("age_group")
        gender = demographics.get("gender")
        education = demographics.get("education") or demographics.get("education_level")
        location = demographics.get("location")

        # 1. Get RAG context from RetrievalService (vector-first, ≤1500 chars)
        rag_result = await self.retrieval_service.get_segment_context(
            age_group=age_group,
            gender=gender,
            education=education,
            location=location,
        )

        # 2. Get segment brief from SegmentBriefService (900-1200 chars)
        # Note: SegmentBriefService ma własny cache (segment_brief:{project_id}:{segment_id})
        # który jest niezależny od naszego segment cache. To OK - double cache doesn't hurt.
        brief_result = await self.brief_service.get_or_generate_segment_brief(
            project_id=str(project_id),
            demographics=demographics,
            force_refresh=False,  # Use brief service's own cache
        )

        # 3. Combine into segment context
        segment_context = {
            "rag_context": rag_result.get("context", ""),
            "segment_brief": brief_result.brief if hasattr(brief_result, "brief") else str(brief_result),
            "graph_context": {
                "insights": rag_result.get("graph_insights", []),
                "query": rag_result.get("query", ""),
                "search_type": rag_result.get("search_type", "unknown"),
            },
            "characteristics": self._extract_characteristics(brief_result),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "demographics": {
                "age_group": age_group,
                "gender": gender,
                "education": education,
                "location": location,
            },
        }

        logger.info(
            f"✅ Generated segment context: {len(segment_context['rag_context'])} chars RAG, "
            f"{len(segment_context['segment_brief'])} chars brief, "
            f"{len(segment_context['characteristics'])} characteristics"
        )

        return segment_context

    def _extract_characteristics(self, brief_result: Any) -> list[str]:
        """Ekstraktuje characteristics z segment brief.

        Args:
            brief_result: SegmentBrief object lub dict

        Returns:
            Lista characteristics (4-6 items)
        """
        # Try to extract characteristics from brief_result
        if hasattr(brief_result, "characteristics"):
            chars = brief_result.characteristics
            if isinstance(chars, list):
                return chars
            elif isinstance(chars, str):
                # Parse if JSON string
                try:
                    return json.loads(chars)
                except (json.JSONDecodeError, TypeError):
                    return [chars]

        # Fallback: extract from brief text (if available)
        if hasattr(brief_result, "brief"):
            brief_text = brief_result.brief
        elif isinstance(brief_result, dict):
            brief_text = brief_result.get("brief", "")
        else:
            brief_text = str(brief_result)

        # Extract first sentence as characteristic (fallback)
        if brief_text:
            sentences = brief_text.split(".")
            return [s.strip() for s in sentences[:4] if s.strip()]

        return []

    async def invalidate_segment_cache(
        self,
        project_id: int | str,
        demographics: dict[str, Any],
    ) -> bool:
        """Invalidate cache for specific segment.

        Args:
            project_id: ID projektu
            demographics: Demografia segmentu

        Returns:
            True if cache was invalidated, False if not found or error
        """
        # Generate cache key
        age_group = demographics.get("age") or demographics.get("age_group")
        gender = demographics.get("gender")
        education = demographics.get("education") or demographics.get("education_level")
        location = demographics.get("location")

        if not all([age_group, gender, education, location]):
            logger.warning(
                "Cannot invalidate cache - demographics niepełne: %s", demographics
            )
            return False

        demo_hash = self.retrieval_service.generate_segment_hash(
            age_group=age_group,
            gender=gender,
            education=education,
            location=location,
        )
        proj_id_str = str(project_id)
        cache_key = f"segment:{proj_id_str}:{demo_hash}"

        try:
            from app.core.redis import redis_delete
            await redis_delete(cache_key)
            logger.info(f"✅ Invalidated segment cache: {cache_key}")
            return True
        except Exception as exc:
            logger.warning(f"⚠️ Failed to invalidate segment cache: {exc}")
            return False

    async def get_cache_stats(self, project_id: int | str) -> dict[str, Any]:
        """Get cache statistics for project (debug/monitoring).

        Args:
            project_id: ID projektu

        Returns:
            Dict with cache stats (liczba cached segments, etc.)
        """
        # TODO: Implement if needed for monitoring
        # Would require scanning Redis keys with pattern: segment:{project_id}:*
        return {
            "project_id": project_id,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "message": "Cache stats not yet implemented",
        }
