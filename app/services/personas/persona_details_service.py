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
from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from app.db import AsyncSessionLocal
from app.models import Persona
from app.services.personas.persona_audit_service import PersonaAuditService
from app.services.personas.persona_needs_service import PersonaNeedsService
from app.services.personas.persona_narrative_service import PersonaNarrativeService
from app.core.redis import redis_get_json, redis_set_json, redis_delete
from app.schemas.persona_details import (
    PersonaDetailsResponse,
    PersonaAuditEntry,
    PersonaNarratives,
    SegmentRules,
    SimilarPersona,
)

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
        self.narrative_service = PersonaNarrativeService()

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
        needs_and_pains, audit_log, narratives_data, similar_personas_data = await asyncio.gather(
            self._fetch_needs_and_pains(persona, force_refresh=force_refresh),
            self._fetch_audit_log(persona_id),
            self._fetch_narratives(persona_id, force_refresh=force_refresh),
            self._fetch_similar_personas(persona, limit=5),
            return_exceptions=True,  # Nie failuj całego requesta jeśli 1 operacja failuje
        )
        parallel_elapsed_ms = int((time.time() - parallel_start) * 1000)

        # Fetch segment rules (sync operation - quick, no DB call)
        segment_rules_data = self._fetch_segment_rules(persona)

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

        # Extract narratives + status (graceful degradation)
        narratives = None
        narratives_status = "pending"
        if isinstance(narratives_data, Exception):
            logger.warning(
                f"Failed to fetch narratives for persona {persona_id}: {narratives_data}",
                exc_info=narratives_data,
            )
            narratives_status = "offline"
        elif narratives_data:
            narratives, narratives_status = narratives_data
            if narratives:
                # Convert to PersonaNarratives schema
                narratives = PersonaNarratives(**narratives)

        # Handle similar personas (graceful degradation)
        similar_personas = []
        if isinstance(similar_personas_data, Exception):
            logger.warning(
                f"Failed to fetch similar personas for {persona_id}: {similar_personas_data}",
                exc_info=similar_personas_data,
            )
        elif similar_personas_data:
            # Convert to SimilarPersona schema
            similar_personas = [SimilarPersona(**p) for p in similar_personas_data]

        # Convert segment_rules to SegmentRules schema
        segment_rules = None
        if segment_rules_data:
            segment_rules = SegmentRules(**segment_rules_data)

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
            # Narratives (nowe pole)
            narratives=narratives,
            narratives_status=narratives_status,
            # Audit log
            audit_log=audit_log if isinstance(audit_log, list) else [],
            # Segment data (nowe pola)
            segment_rules=segment_rules,
            similar_personas=similar_personas,
            # Metadata
            segment_id=segment_id,
            segment_name=segment_name,
            created_at=persona.created_at,
            updated_at=persona.updated_at,
            data_freshness=persona.updated_at,  # Bazuje na updated_at
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
                "narratives_status": narratives_status,
                "force_refresh": force_refresh,
            }
        )

        return response

    async def _fetch_narratives(
        self,
        persona_id: UUID,
        *,
        force_refresh: bool,
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Fetch narratives from PersonaNarrativeService with timeout.

        Args:
            persona_id: UUID persony
            force_refresh: Whether to bypass cache

        Returns:
            Tuple[narratives_dict, status] lub Exception on failure

        Performance:
            - Cache hit: < 50ms (PersonaNarrativeService cache)
            - Cache miss: < 20s (LLM generation with timeout)
            - Timeout: 15s dla całego flow
        """
        try:
            # Timeout 15s dla narratives (aby nie opóźniać całego detail view)
            narratives, status = await asyncio.wait_for(
                self.narrative_service.get_narratives(
                    persona_id=persona_id,
                    scope='all',
                    force_regenerate=force_refresh
                ),
                timeout=15.0
            )
            return narratives, status
        except asyncio.TimeoutError:
            logger.warning(
                f"Narratives generation timeout for persona {persona_id}",
                extra={"persona_id": str(persona_id)}
            )
            return None, "pending"
        except Exception as e:
            logger.error(
                f"Failed to fetch narratives for persona {persona_id}: {e}",
                exc_info=e,
                extra={"persona_id": str(persona_id)}
            )
            raise  # Propagate dla graceful degradation w get_persona_details

    async def _fetch_needs_and_pains(
        self,
        persona: Persona,
        *,
        force_refresh: bool,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch needs & pains analysis (read-only, no LLM generation).

        Needs are now pre-generated during persona creation.
        If NULL, returns None (no lazy generation to avoid blocking GET requests).

        Args:
            persona: Persona object
            force_refresh: Ignored (kept for backward compatibility)

        Returns:
            Dict with JTBD, desired outcomes, and pain points (or None if not generated)

        Performance:
            - Always < 10ms (read-only, no LLM calls)

        Note:
            force_refresh is deprecated - needs are pre-generated during persona creation.
            For manual regeneration, use POST /personas/{id}/needs/regenerate endpoint.
        """
        if not persona.needs_and_pains:
            logger.warning(
                "Persona %s has NULL needs_and_pains - should be pre-generated during creation",
                persona.id,
                extra={"persona_id": str(persona.id)}
            )
            return None

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

    def _fetch_segment_rules(self, persona: Persona) -> Optional[Dict[str, Any]]:
        """
        Wyciągnij segment rules z orchestration_reasoning lub infer z danych persony.

        Args:
            persona: Persona object

        Returns:
            Dict z polami: age_range, gender_options, location_filters, required_values

        Example:
            {
                "age_range": "30-40",
                "gender_options": ["Kobieta"],
                "location_filters": ["Warszawa", "Kraków"],
                "required_values": ["Niezależność", "Innowacja"]
            }
        """
        try:
            details = persona.rag_context_details or {}
            orchestration = details.get("orchestration_reasoning") or {}

            # Spróbuj wyciągnąć z orchestration (jeśli LLM wygenerował)
            segment_rules = orchestration.get("segment_rules")
            if segment_rules and isinstance(segment_rules, dict):
                return segment_rules

            # Infer z danych persony (fallback)
            age_range = None
            if persona.age:
                # Round to 5-year brackets
                lower_bound = (persona.age // 5) * 5
                upper_bound = lower_bound + 5
                age_range = f"{lower_bound}-{upper_bound}"

            gender_options = [persona.gender] if persona.gender else []

            location_filters = []
            if persona.location and persona.location.lower() not in {"polska", "kraj"}:
                location_filters.append(persona.location)

            # Top 3 values (jeśli dostępne)
            required_values = persona.values[:3] if persona.values else []

            return {
                "age_range": age_range,
                "gender_options": gender_options,
                "location_filters": location_filters,
                "required_values": required_values,
            }
        except Exception as e:
            logger.warning(f"Failed to extract segment rules for persona {persona.id}: {e}")
            return None

    async def _fetch_similar_personas(
        self, persona: Persona, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Znajdź podobne persony (ten sam segment_id).

        Args:
            persona: Persona object
            limit: Max liczba podobnych person

        Returns:
            Lista dict z polami: id, name, distinguishing_trait

        Performance:
            - Query z index na (project_id, segment_id, is_active)
            - Limit 5 osób
        """
        try:
            if not persona.segment_id:
                return []

            query = select(Persona).where(
                Persona.project_id == persona.project_id,
                Persona.segment_id == persona.segment_id,
                Persona.id != persona.id,
                Persona.is_active == True,
                Persona.deleted_at.is_(None),
            ).limit(limit)

            result = await self.db.execute(query)
            similar = result.scalars().all()

            return [
                {
                    "id": str(p.id),
                    "name": self._generate_persona_name(p),
                    "distinguishing_trait": self._get_distinguishing_trait(persona, p),
                }
                for p in similar
            ]
        except Exception as e:
            logger.error(f"Failed to fetch similar personas for {persona.id}: {e}", exc_info=e)
            return []

    def _generate_persona_name(self, persona: Persona) -> str:
        """
        Generuj krótką nazwę persony (dla listy podobnych).

        Args:
            persona: Persona object

        Returns:
            String w formacie: "Occupation, age lat" lub "Kobieta, 32 lata"
        """
        parts = []
        if persona.occupation:
            parts.append(persona.occupation)
        elif persona.gender:
            parts.append(persona.gender)

        if persona.age:
            parts.append(f"{persona.age} lat")

        if not parts:
            return f"Persona #{str(persona.id)[:8]}"

        return ", ".join(parts)

    def _get_distinguishing_trait(self, base_persona: Persona, other_persona: Persona) -> str:
        """
        Generuj krótki opis różnicy między dwiema personami.

        Args:
            base_persona: Persona bazowa (do której porównujemy)
            other_persona: Inna persona (z tego samego segmentu)

        Returns:
            Brief description np. "Młodsza o 5 lat, z Krakowa"

        Example:
            >>> trait = service._get_distinguishing_trait(persona1, persona2)
            >>> print(trait)  # "Starsza o 3 lata, zarabia więcej"
        """
        traits = []

        # Age difference
        if base_persona.age and other_persona.age:
            age_diff = other_persona.age - base_persona.age
            if age_diff > 0:
                traits.append(f"starsza o {age_diff} lat" if other_persona.gender == "Kobieta" else f"starszy o {age_diff} lat")
            elif age_diff < 0:
                traits.append(f"młodsza o {abs(age_diff)} lat" if other_persona.gender == "Kobieta" else f"młodszy o {abs(age_diff)} lat")

        # Location difference
        if base_persona.location != other_persona.location and other_persona.location:
            if other_persona.location.lower() not in {"polska", "kraj"}:
                traits.append(f"z {other_persona.location}")

        # Occupation difference
        if base_persona.occupation != other_persona.occupation and other_persona.occupation:
            traits.append(f"{other_persona.occupation.lower()}")

        # Income difference
        if base_persona.income_bracket != other_persona.income_bracket and other_persona.income_bracket:
            # Parse income brackets to compare (basic comparison)
            if other_persona.income_bracket and base_persona.income_bracket:
                base_income = self._extract_income_value(base_persona.income_bracket)
                other_income = self._extract_income_value(other_persona.income_bracket)
                if base_income and other_income:
                    if other_income > base_income:
                        traits.append("zarabia więcej")
                    elif other_income < base_income:
                        traits.append("zarabia mniej")

        # Default fallback
        if not traits:
            return "podobny profil"

        # Join max 2 traits
        return ", ".join(traits[:2]).capitalize()

    def _extract_income_value(self, income_bracket: str) -> Optional[int]:
        """
        Wyciągnij wartość liczbową z income bracket (dla porównania).

        Args:
            income_bracket: String np. "7500-10000 PLN" lub "5000 PLN"

        Returns:
            Średnia wartość z zakresu lub single value
        """
        import re
        # Extract numbers from string
        numbers = re.findall(r'\d+', income_bracket)
        if not numbers:
            return None
        # Take average if range, otherwise first number
        if len(numbers) >= 2:
            return (int(numbers[0]) + int(numbers[1])) // 2
        return int(numbers[0])
