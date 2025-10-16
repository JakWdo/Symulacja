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
import re
import time
import unicodedata
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from app.db import AsyncSessionLocal
from app.models import Persona
from app.services.persona_audit_service import PersonaAuditService
from app.services.persona_needs_service import PersonaNeedsService
from app.core.redis import redis_get_json, redis_set_json, redis_delete
from app.schemas.persona_details import PersonaDetailsResponse, PersonaAuditEntry

logger = logging.getLogger(__name__)


def _gender_label_for_persona(gender: Optional[str]) -> str:
    if not gender:
        return "Osoby"
    lowered = gender.strip().lower()
    if lowered.startswith("k"):
        return "Kobiety"
    if lowered.startswith("m"):
        return "Mężczyźni"
    return "Osoby"


def _slugify_segment_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
    return ascii_text


def _sanitize_context_text(text: Optional[str], max_length: int = 900) -> Optional[str]:
    if not text:
        return None
    cleaned = re.sub(r"[`*_#>\[\]]+", "", str(text))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return None
    if max_length and len(cleaned) > max_length:
        truncated = cleaned[:max_length].rsplit(" ", 1)[0]
        return f"{truncated}..."
    return cleaned


def _build_segment_name_from_persona(persona: Persona) -> str:
    gender_label = _gender_label_for_persona(persona.gender)
    parts: List[str] = [gender_label]

    if persona.age:
        parts.append(f"{persona.age} lat")
    if persona.education_level:
        parts.append(persona.education_level)
    if persona.location and persona.location.lower() not in {"polska", "kraj"}:
        parts.append(persona.location)

    name = " ".join(part for part in parts if part).strip()
    if not name:
        name = "Segment demograficzny"
    if len(name) > 60:
        name = name[:57].rstrip() + "..."
    return name


def _build_segment_description_from_persona(persona: Persona, segment_name: str) -> str:
    gender_label = _gender_label_for_persona(persona.gender)
    if persona.age:
        subject = f"{gender_label.lower()} w wieku około {persona.age} lat"
    else:
        subject = gender_label.lower()

    sentences = [f"{segment_name} obejmuje {subject}."]

    details: List[str] = []
    if persona.education_level:
        details.append(f"z wykształceniem {persona.education_level}")
    if persona.income_bracket:
        details.append(f"osiągające dochody około {persona.income_bracket}")
    if persona.location:
        if persona.location.lower() in {"polska", "kraj"}:
            details.append("rozproszone w całej Polsce")
        else:
            details.append(f"mieszkające w {persona.location}")

    if details:
        sentences.append(f"W tej grupie dominują osoby {', '.join(details)}.")

    return " ".join(sentences)


def _build_segment_social_context(persona: Persona, details: Dict[str, Any], fallback_description: str) -> str:
    for key in (
        "segment_social_context",
        "graph_context",
        "context_preview",
        "overall_context",
    ):
        sanitized = _sanitize_context_text(details.get(key))
        if sanitized:
            return sanitized

    if persona.background_story:
        story_sanitized = _sanitize_context_text(persona.background_story, max_length=700)
        if story_sanitized:
            return story_sanitized

    return fallback_description


def _ensure_segment_metadata(persona: Persona) -> Optional[Dict[str, Any]]:
    details = persona.rag_context_details or {}
    if not isinstance(details, dict):
        return details

    details_copy: Dict[str, Any] = dict(details)
    orchestration = dict(details_copy.get("orchestration_reasoning") or {})
    mutated = False

    segment_name = (
        orchestration.get("segment_name")
        or details_copy.get("segment_name")
        or persona.segment_name
    )
    if not segment_name:
        segment_name = _build_segment_name_from_persona(persona)
        mutated = True

    segment_id = (
        orchestration.get("segment_id")
        or details_copy.get("segment_id")
        or persona.segment_id
    )
    if not segment_id and segment_name:
        slug = _slugify_segment_name(segment_name)
        segment_id = slug or f"segment-{persona.id}"
        mutated = True

    segment_description = (
        orchestration.get("segment_description")
        or details_copy.get("segment_description")
    )
    if not segment_description and segment_name:
        segment_description = _build_segment_description_from_persona(persona, segment_name)
        mutated = True

    segment_social_context = (
        orchestration.get("segment_social_context")
        or details_copy.get("segment_social_context")
    )
    if not segment_social_context:
        segment_social_context = _build_segment_social_context(persona, details_copy, segment_description or "")
        mutated = True

    if mutated:
        if segment_name:
            orchestration.setdefault("segment_name", segment_name)
            details_copy.setdefault("segment_name", segment_name)
        if segment_id:
            orchestration.setdefault("segment_id", segment_id)
            details_copy.setdefault("segment_id", segment_id)
        if segment_description:
            orchestration.setdefault("segment_description", segment_description)
            details_copy.setdefault("segment_description", segment_description)
        if segment_social_context:
            orchestration.setdefault("segment_social_context", segment_social_context)
            details_copy.setdefault("segment_social_context", segment_social_context)

    details_copy["orchestration_reasoning"] = orchestration
    return details_copy


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
            select(Persona).where(Persona.id == persona_id, Persona.is_active == True)
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
                    asyncio.create_task(self._log_view_event(persona_id, user_id))

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
                    await redis_delete(cache_key)

        # === PARALLEL FETCH COMPUTED DATA ===
        # Używamy asyncio.gather dla równoległego fetchowania (non-blocking)
        # Jeśli któraś operacja failuje, catch exception i zwróć None (graceful degradation)

        parallel_start = time.time()
        needs_and_pains, audit_log = await asyncio.gather(
            self._fetch_needs_and_pains(persona, force_refresh=force_refresh),
            self._fetch_audit_log(persona_id),
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

        enriched_rag_details = _ensure_segment_metadata(persona)
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
        asyncio.create_task(
            self._log_view_event(persona_id, user_id)
        )

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

    async def _fetch_needs_and_pains(
        self,
        persona: Persona,
        *,
        force_refresh: bool,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch needs & pains analysis from cache or generate via LLM with RAG context.

        Args:
            persona: Persona object
            force_refresh: Whether to bypass cache

        Returns:
            Dict with JTBD, desired outcomes, and pain points

        Performance:
            - Cache hit: < 10ms (return persona.needs_and_pains)
            - Cache miss: < 2s (LLM with structured output + RAG context)
        """
        service = PersonaNeedsService(self.db)
        try:
            if persona.needs_and_pains and not force_refresh:
                return persona.needs_and_pains

            # Extract RAG context for consistency with segment data
            rag_context = self._extract_rag_context(persona)

            # Generate needs with RAG context
            needs_data = await service.generate_needs_analysis(persona, rag_context=rag_context)
            persona.needs_and_pains = needs_data
            asyncio.create_task(self._persist_persona_field(persona.id, "needs_and_pains", needs_data))
            return needs_data
        except Exception as exc:
            logger.error("Failed to generate needs for persona %s: %s", persona.id, exc, exc_info=True)
            return persona.needs_and_pains

    async def _fetch_audit_log(self, persona_id: UUID) -> List[PersonaAuditEntry]:
        """
        Fetch audit log (last 20 actions)

        Args:
            persona_id: UUID persony

        Returns:
            Lista PersonaAuditEntry (last 20 actions)

        Performance:
            - Index na (persona_id, timestamp DESC)
            - Limit 20 entries
        """
        try:
            logs = await self.audit_service.get_audit_log(persona_id, self.db, limit=20)
            return [
                PersonaAuditEntry(
                    id=log.id,
                    action=log.action,
                    details=log.details,
                    user_id=log.user_id,
                    timestamp=log.timestamp,
                )
                for log in logs
            ]
        except Exception as e:
            logger.error(
                f"Failed to fetch audit log for persona {persona_id}: {e}", exc_info=e
            )
            return []

    async def _log_view_event(self, persona_id: UUID, user_id: UUID):
        """
        Log view event (async, non-blocking)

        Args:
            persona_id: UUID persony
            user_id: UUID użytkownika

        Note:
            To jest async task (create_task) - nie blokuje HTTP response
            Jeśli failuje, logujemy warning ale nie propagujemy exception
        """
        try:
            async with AsyncSessionLocal() as audit_db:
                await self.audit_service.log_action(
                    persona_id=persona_id,
                    user_id=user_id,
                    action="view",
                    details={"source": "detail_view", "device": "web"},
                    db=audit_db,
                )
        except Exception as e:
            logger.warning("Failed to log view event: %s", e)

    async def _persist_persona_field(self, persona_id: UUID, field_name: str, value: Dict[str, Any]) -> None:
        """Persist a JSONB field on Persona in a dedicated transaction."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(Persona).where(Persona.id == persona_id))
                persona = result.scalars().first()
                if not persona:
                    logger.warning("Persona %s not found when persisting %s", persona_id, field_name)
                    return

                setattr(persona, field_name, value)
                await session.commit()
                logger.debug("Persisted %s for persona %s", field_name, persona_id)
                await redis_delete(f"persona_details:{persona_id}")
        except Exception as exc:
            logger.warning("Failed to persist %s for persona %s: %s", field_name, persona_id, exc)

    def _extract_rag_context(self, persona: Persona) -> Optional[str]:
        details = persona.rag_context_details or {}
        reasoning = details.get("orchestration_reasoning") or {}
        context_candidates = [
            reasoning.get("segment_social_context"),
            reasoning.get("overall_context"),
            details.get("graph_context"),
        ]
        for candidate in context_candidates:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        return None
