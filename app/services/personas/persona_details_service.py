"""
PersonaDetailsService - Orchestrator dla Persona Detail View

Główny orchestrator dla szczegółowego widoku persony:
- Fetch base persona data
- Parallel fetch needs (with RAG context) and audit log (asyncio.gather)
- Merge data into comprehensive response
- Cache full response (Redis, TTL 1h)
- Handle graceful degradation (jeśli część danych nie jest dostępna)

Performance Optimizations (2025-10):
- Smart cache invalidation: Include persona.updated_at in cache key
- Performance logging: Track duration for each fetch operation
- Longer cache TTL: 5min → 1h for stable data
- RAG context integration for needs analysis (consistency with segments)
- Target latency: <50ms (cached), <3s (fresh with parallel fetch)

Performance:
- Cache hit: < 50ms (Redis)
- Cache miss (optimized): < 3s (parallel fetch + structured output + RAG context)
- Graceful degradation: jeśli część danych failuje, zwróć partial response
"""

import asyncio
import logging
import time
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from app.models import Persona
from app.services.personas.persona_audit_service import PersonaAuditService
from app.core.redis import redis_get_json, redis_set_json
from app.schemas.persona_details import PersonaDetailsResponse

# Import funkcji z nowych modułów
from .details_enrichment import (
    ensure_segment_metadata,
    fetch_needs_and_pains,
    fetch_segment_brief,
)
from .details_crud import (
    fetch_audit_log,
    log_view_event,
    persist_persona_field,
)

logger = logging.getLogger(__name__)


class PersonaDetailsService:
    """
    Orchestrator dla Persona Detail View

    Responsibilities:
    - Fetch base persona data
    - Parallel fetch needs (with RAG context) and audit log (asyncio.gather)
    - Merge data into comprehensive response
    - Cache full response (Redis, TTL 5min)
    - Handle graceful degradation (jeśli część danych nie jest dostępna)

    Performance:
    - Cache hit: < 50ms (Redis)
    - Cache miss: < 3s (parallel fetch with LLM call for needs)

    Examples:
        >>> details_service = PersonaDetailsService(db)
        >>> details = await details_service.get_persona_details(persona_id, user)
        >>> print(details.needs_and_pains)  # JTBD + pain points
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_service = PersonaAuditService()

    async def get_persona_details(
        self,
        persona_id: UUID,
        user_id: UUID,
        force_refresh: bool = False,
    ) -> PersonaDetailsResponse:
        """
        Pobierz pełny detail view persony

        Optimizations:
        - Smart cache key: Include persona.updated_at for auto-invalidation
        - Longer TTL: 5min → 1h (invalidates on persona update via updated_at)
        - Performance logging: Track each operation duration

        Args:
            persona_id: UUID persony
            user_id: UUID użytkownika (dla audit log)
            force_refresh: Czy wymusić recalculation (bypass cache)

        Returns:
            PersonaDetailsResponse z pełnymi danymi Detail View

        Raises:
            ValueError: Persona nie istnieje lub is_active=False

        Performance:
            - Cache hit: < 50ms (Redis)
            - Cache miss (optimized): < 3s (parallel fetch with structured output)
            - Graceful degradation: jeśli część danych failuje, zwróć partial response
        """
        start_time = time.time()

        # === FETCH BASE PERSONA (needed for cache key) ===
        fetch_start = time.time()
        result = await self.db.execute(
            select(Persona).where(Persona.id == persona_id, Persona.is_active.is_(True))
        )
        persona = result.scalars().first()

        if not persona:
            raise ValueError(f"Persona {persona_id} not found or inactive")

        fetch_elapsed_ms = int((time.time() - fetch_start) * 1000)

        # Smart cache key: Include updated_at timestamp for auto-invalidation
        cache_key = f"persona_details:{persona_id}:{int(persona.updated_at.timestamp())}"

        if not force_refresh:
            cached = await redis_get_json(cache_key)
            if cached:
                try:
                    cached_response = PersonaDetailsResponse.model_validate(cached)
                    asyncio.create_task(log_view_event(persona_id, user_id))

                    total_elapsed_ms = int((time.time() - start_time) * 1000)
                    logger.info(
                        "persona_details_served_from_cache",
                        extra={
                            "persona_id": str(persona_id),
                            "total_duration_ms": total_elapsed_ms,
                            "db_fetch_ms": fetch_elapsed_ms,
                        }
                    )
                    return cached_response
                except ValidationError as e:
                    logger.warning("Invalid cached data for persona %s: %s", persona_id, e)

        # === PARALLEL FETCH COMPUTED DATA ===
        # Używamy asyncio.gather dla równoległego fetchowania (non-blocking)
        # Jeśli któraś operacja failuje, catch exception i zwróć None (graceful degradation)

        parallel_start = time.time()
        needs_and_pains, audit_log, segment_brief_data = await asyncio.gather(
            fetch_needs_and_pains(self.db, persona, force_refresh=force_refresh),
            fetch_audit_log(persona_id, self.db, self.audit_service),
            fetch_segment_brief(self.db, persona, force_refresh=force_refresh),
            return_exceptions=True,  # Nie failuj całego requesta jeśli 1 operacja failuje
        )
        parallel_elapsed_ms = int((time.time() - parallel_start) * 1000)

        # Handle exceptions from parallel fetch (graceful degradation)
        if isinstance(needs_and_pains, Exception):
            logger.warning(
                "Failed to fetch needs for persona %s: %s",
                persona_id,
                needs_and_pains,
                exc_info=needs_and_pains,
            )
            needs_and_pains = persona.needs_and_pains

        if isinstance(audit_log, Exception):
            logger.warning(
                f"Failed to fetch audit log for persona {persona_id}: {audit_log}",
                exc_info=audit_log,
            )
            audit_log = []

        if isinstance(segment_brief_data, Exception):
            logger.warning(
                "Failed to fetch segment brief for persona %s: %s",
                persona_id,
                segment_brief_data,
                exc_info=segment_brief_data,
            )
            segment_brief_data = None

        # Enrich RAG details with segment brief data
        enriched_rag_details = ensure_segment_metadata(persona)
        if segment_brief_data and enriched_rag_details:
            # Merge segment brief into orchestration_reasoning
            orchestration = enriched_rag_details.get("orchestration_reasoning") or {}
            orchestration["segment_brief"] = segment_brief_data.get("segment_brief")
            orchestration["persona_uniqueness"] = segment_brief_data.get("persona_uniqueness")
            enriched_rag_details["orchestration_reasoning"] = orchestration

        segment_id = persona.segment_id or (enriched_rag_details.get("segment_id") if enriched_rag_details else None)
        segment_name = persona.segment_name or (enriched_rag_details.get("segment_name") if enriched_rag_details else None)

        # === MERGE DATA ===
        response = PersonaDetailsResponse(
            # Base persona data
            id=persona.id,
            project_id=persona.project_id,
            full_name=persona.full_name,
            persona_title=persona.persona_title,
            headline=persona.headline,
            age=persona.age,
            gender=persona.gender,
            location=persona.location,
            education_level=persona.education_level,
            income_bracket=persona.income_bracket,
            occupation=persona.occupation,
            # Psychographics
            big_five={
                "openness": persona.openness,
                "conscientiousness": persona.conscientiousness,
                "extraversion": persona.extraversion,
                "agreeableness": persona.agreeableness,
                "neuroticism": persona.neuroticism,
            },
            hofstede={
                "power_distance": persona.power_distance,
                "individualism": persona.individualism,
                "masculinity": persona.masculinity,
                "uncertainty_avoidance": persona.uncertainty_avoidance,
                "long_term_orientation": persona.long_term_orientation,
                "indulgence": persona.indulgence,
            },
            values=persona.values or [],
            interests=persona.interests or [],
            background_story=persona.background_story,
            # Computed/JSONB fields
            needs_and_pains=needs_and_pains,
            # RAG data
            rag_context_used=persona.rag_context_used,
            rag_citations=persona.rag_citations,
            rag_context_details=enriched_rag_details,
            # Audit log
            audit_log=audit_log if isinstance(audit_log, list) else [],
            # Metadata
            segment_id=segment_id,
            segment_name=segment_name,
            created_at=persona.created_at,
            updated_at=persona.updated_at,
            is_active=persona.is_active,
        )

        # Cache for 1 hour (vs. 5min) - invalidates automatically via updated_at in cache key
        await redis_set_json(cache_key, response.model_dump(mode="json"), ttl_seconds=3600)

        # === LOG VIEW EVENT ===
        # Async non-blocking (używamy create_task aby nie czekać na commit)
        asyncio.create_task(log_view_event(persona_id, user_id))

        # === PERSIST NEEDS IF FRESHLY GENERATED ===
        # Jeśli needs_and_pains zostały wygenerowane, zapisz asynchronicznie
        if needs_and_pains and needs_and_pains != persona.needs_and_pains:
            asyncio.create_task(persist_persona_field(persona.id, "needs_and_pains", needs_and_pains))

        total_elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "persona_details_fetched_successfully",
            extra={
                "persona_id": str(persona_id),
                "total_duration_ms": total_elapsed_ms,
                "db_fetch_ms": fetch_elapsed_ms,
                "parallel_fetch_ms": parallel_elapsed_ms,
                "needs_available": needs_and_pains is not None and not isinstance(needs_and_pains, Exception),
                "force_refresh": force_refresh,
            }
        )

        return response
