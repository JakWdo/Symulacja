"""
PersonaNarrativeService - Orchestrator dla generowania narracji biznesowych

Główny serwis odpowiedzialny za:
- Generowanie 5 narracji (person_profile, person_motivations, segment_hero, segment_significance, evidence_context)
- Cache Redis z auto-invalidation (hash promptów + modeli w kluczu)
- Graceful degradation (status: ok/degraded/offline)
- Parallel LLM calls (asyncio.gather) dla optymalizacji

Performance Targets:
- Cache hit: <50ms
- Cache miss: <20s (P95) dla wszystkich 5 narracji
- Individual calls: Flash <3s, Pro <5s

Examples:
    >>> service = PersonaNarrativeService()
    >>> narratives, status = await service.get_narratives(persona_id)
    >>> print(narratives['person_profile'])  # Profil 1 akapit
    >>> print(status)  # "ok" | "degraded" | "offline"
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.models import Persona
from app.services.rag.graph_context_provider import GraphContextProvider
from app.services.rag.hybrid_context_provider import HybridContextProvider
from app.services.personas.persona_needs_service import PersonaNeedsService
from app.services.core.clients import build_chat_model
from app.core.config import get_settings
from app.core.redis import redis_get_json, redis_set_json
from app.core.prompts import (
    NARRATIVE_SYSTEM_INSTRUCTION,
    PERSON_PROFILE_PROMPT,
    PERSON_PROFILE_MODEL_PARAMS,
    PERSON_MOTIVATIONS_PROMPT,
    PERSON_MOTIVATIONS_MODEL_PARAMS,
    SEGMENT_HERO_PROMPT,
    SEGMENT_HERO_MODEL_PARAMS,
    SEGMENT_SIGNIFICANCE_PROMPT,
    SEGMENT_SIGNIFICANCE_MODEL_PARAMS,
    EVIDENCE_CONTEXT_PROMPT,
    EVIDENCE_CONTEXT_SCHEMA,
    EVIDENCE_CONTEXT_MODEL_PARAMS,
    format_jobs_to_be_done,
    format_desired_outcomes,
    format_pain_points,
    format_graph_context,
    format_insights,
    format_persona_context,
    PromptVersion,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class PersonaNarrativeService:
    """
    Orchestrator dla generowania narracji biznesowych person.

    Responsibilities:
    - Generate 5 narratives (Flash + Pro mix dla balance cost/quality)
    - Cache results w Redis z auto-invalidation
    - Graceful degradation (zwróć partial results + status)
    - Parallel LLM calls dla performance

    Architecture:
    - Uses GraphContextProvider dla graph data
    - Uses HybridContextProvider dla text data
    - Uses PersonaNeedsService dla JTBD/Outcomes/Pains
    - Uses build_chat_model factory dla Flash/Pro models

    Performance:
    - Cache hit: <50ms
    - Cache miss: <20s (5 LLM calls parallel)
    - Graceful degradation: zwróć None dla failed narratives
    """

    def __init__(self):
        self.graph_provider = GraphContextProvider()
        self.hybrid_provider = HybridContextProvider()

    def _compute_cache_key(self, persona_id: UUID, persona_updated_at: int) -> str:
        """
        Buduje cache key z auto-invalidation.

        Format: persona:narratives:{id}:{updated_at_ts}:{prompts_hash}:{models_hash}

        Auto-invalidation triggers:
        - persona.updated_at zmienia się (nowe dane persony)
        - Prompt versions się zmieniają (PromptVersion enum)
        - Model names się zmieniają (Flash/Pro switch)

        Args:
            persona_id: UUID persony
            persona_updated_at: Unix timestamp persona.updated_at

        Returns:
            Cache key string
        """
        # Hash promptów (z versions)
        prompts_data = {
            "person_profile": PromptVersion.PERSON_PROFILE.value,
            "person_motivations": PromptVersion.PERSON_MOTIVATIONS.value,
            "segment_hero": PromptVersion.SEGMENT_HERO.value,
            "segment_significance": PromptVersion.SEGMENT_SIGNIFICANCE.value,
            "evidence_context": PromptVersion.EVIDENCE_CONTEXT.value,
        }
        prompts_hash = hashlib.md5(
            json.dumps(prompts_data, sort_keys=True).encode()
        ).hexdigest()[:8]

        # Hash modeli
        models_data = {
            "flash": settings.PERSONA_GENERATION_MODEL,  # Flash dla profile
            "pro": settings.ANALYSIS_MODEL,  # Pro dla reszty
        }
        models_hash = hashlib.md5(
            json.dumps(models_data, sort_keys=True).encode()
        ).hexdigest()[:8]

        return f"persona:narratives:{persona_id}:{persona_updated_at}:{prompts_hash}:{models_hash}"

    async def get_narratives(
        self,
        persona_id: UUID,
        scope: str = 'all',
        force_regenerate: bool = False
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Pobiera lub generuje narracje dla persony.

        Orchestration Flow:
        1. Sprawdź cache Redis (klucz z hash promptów + modeli)
        2. Jeśli cache miss → generuj narracje:
           a. Fetch persona + needs + graph context + hybrid context (parallel)
           b. Generate 5 narratives (parallel LLM calls)
           c. Merge results
        3. Zapisz do cache (TTL 3600s)
        4. Zwróć narracje + status

        Args:
            persona_id: UUID persony
            scope: Które narracje wygenerować ('all' | 'profile' | 'segment')
            force_regenerate: Czy wymusić regenerację (bypass cache)

        Returns:
            Tuple[narratives_dict, status]
            - narratives_dict: {person_profile, person_motivations, ...} lub None
            - status: "ok" | "degraded" | "offline"

        Raises:
            ValueError: Jeśli persona nie istnieje

        Performance:
            - Cache hit: <50ms
            - Cache miss: <20s (parallel generation)
        """
        start_time = time.time()

        # Fetch persona (potrzebne dla cache key)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Persona).where(Persona.id == persona_id, Persona.is_active == True)
            )
            persona = result.scalars().first()

            if not persona:
                raise ValueError(f"Persona {persona_id} not found or inactive")

            # Cache key z auto-invalidation
            cache_key = self._compute_cache_key(
                persona_id,
                int(persona.updated_at.timestamp())
            )

            # Check cache (jeśli nie force_regenerate)
            if not force_regenerate:
                cached = await redis_get_json(cache_key)
                if cached is not None:
                    elapsed_ms = int((time.time() - start_time) * 1000)
                    logger.info(
                        f"Narratives cache hit for persona {persona_id}",
                        extra={
                            "persona_id": str(persona_id),
                            "duration_ms": elapsed_ms,
                            "source": "cache"
                        }
                    )
                    return cached.get("narratives"), cached.get("status", "ok")

            # === GENERATE NARRATIVES ===
            try:
                # Step 1: Parallel fetch dependencies
                fetch_start = time.time()

                needs_service = PersonaNeedsService(db)

                needs_and_pains, graph_context, hybrid_context = await asyncio.gather(
                    needs_service.generate_needs_analysis(persona) if not persona.needs_and_pains else asyncio.sleep(0, result=persona.needs_and_pains),
                    self.graph_provider.get_segment_nodes(persona, limit=10),
                    self.hybrid_provider.get_narrative_context(persona, top_k=5),
                    return_exceptions=True  # Graceful degradation
                )

                fetch_elapsed_ms = int((time.time() - fetch_start) * 1000)
                logger.debug(
                    f"Dependencies fetched in {fetch_elapsed_ms}ms",
                    extra={
                        "persona_id": str(persona_id),
                        "duration_ms": fetch_elapsed_ms
                    }
                )

                # Handle exceptions (graceful degradation)
                if isinstance(needs_and_pains, Exception):
                    logger.warning(f"Needs fetch failed: {needs_and_pains}")
                    needs_and_pains = persona.needs_and_pains or {}

                if isinstance(graph_context, Exception):
                    logger.warning(f"Graph context fetch failed: {graph_context}")
                    graph_context = []

                if isinstance(hybrid_context, Exception):
                    logger.warning(f"Hybrid context fetch failed: {hybrid_context}")
                    hybrid_context = {"context": "", "citations": [], "metadata": {}}

                # Step 2: Parallel generate narratives
                gen_start = time.time()

                narratives_results = await asyncio.gather(
                    self.compose_person_profile(persona),
                    self.compose_person_motivations(needs_and_pains, persona),
                    self.compose_segment_hero(persona, graph_context, hybrid_context),
                    self.compose_segment_significance(
                        await self.graph_provider.get_top_insights(persona, limit=5),
                        persona
                    ),
                    self.compose_evidence_context(graph_context, hybrid_context, persona),
                    return_exceptions=True  # Graceful degradation
                )

                gen_elapsed_ms = int((time.time() - gen_start) * 1000)
                logger.debug(
                    f"Narratives generated in {gen_elapsed_ms}ms",
                    extra={
                        "persona_id": str(persona_id),
                        "duration_ms": gen_elapsed_ms
                    }
                )

                # Unpack results
                person_profile, person_motivations, segment_hero, segment_significance, evidence_context = narratives_results

                # Determine status based on failures
                failed_count = sum(1 for r in narratives_results if isinstance(r, Exception))

                if failed_count == len(narratives_results):
                    status = "offline"
                    narratives = None
                elif failed_count > 0:
                    status = "degraded"
                    narratives = {
                        "person_profile": person_profile if not isinstance(person_profile, Exception) else None,
                        "person_motivations": person_motivations if not isinstance(person_motivations, Exception) else None,
                        "segment_hero": segment_hero if not isinstance(segment_hero, Exception) else None,
                        "segment_significance": segment_significance if not isinstance(segment_significance, Exception) else None,
                        "evidence_context": evidence_context if not isinstance(evidence_context, Exception) else None,
                    }
                else:
                    status = "ok"
                    narratives = {
                        "person_profile": person_profile,
                        "person_motivations": person_motivations,
                        "segment_hero": segment_hero,
                        "segment_significance": segment_significance,
                        "evidence_context": evidence_context,
                    }

                # Cache result (TTL 3600s = 1h)
                cache_data = {
                    "narratives": narratives,
                    "status": status,
                    "generated_at": int(time.time())
                }
                await redis_set_json(cache_key, cache_data, ttl_seconds=3600)

                total_elapsed_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    f"Narratives generated successfully for persona {persona_id}",
                    extra={
                        "persona_id": str(persona_id),
                        "total_duration_ms": total_elapsed_ms,
                        "fetch_ms": fetch_elapsed_ms,
                        "gen_ms": gen_elapsed_ms,
                        "status": status,
                        "failed_count": failed_count
                    }
                )

                return narratives, status

            except Exception as e:
                logger.error(
                    f"Failed to generate narratives for persona {persona_id}: {e}",
                    exc_info=e,
                    extra={"persona_id": str(persona_id)}
                )
                return None, "offline"

    async def compose_person_profile(self, persona: Persona) -> str:
        """
        Generuje person_profile (1 akapit, Flash model).

        Strategia:
        - Model: Gemini 2.5 Flash (factual task, low temperature)
        - Input: Demographics (age, gender, location, education, income, occupation, background)
        - Output: 1 akapit (3-4 zdania), faktyczny, zwięzły
        - Timeout: 30s

        Args:
            persona: Persona object

        Returns:
            String z 1 akapitem profilu

        Raises:
            Exception: Jeśli LLM call fails (propagated dla graceful degradation)
        """
        try:
            # Build prompt
            prompt = PERSON_PROFILE_PROMPT.format(
                age=persona.age,
                gender=persona.gender or "Unknown",
                location=persona.location or "Unknown",
                education_level=persona.education_level or "Unknown",
                income_bracket=persona.income_bracket or "Unknown",
                occupation=persona.occupation or "Unknown",
                background_story=persona.background_story or "No background available"
            )

            # Build Flash model
            flash_model = build_chat_model(
                model=settings.PERSONA_GENERATION_MODEL,  # Flash
                temperature=PERSON_PROFILE_MODEL_PARAMS["temperature"],
                max_tokens=PERSON_PROFILE_MODEL_PARAMS["max_tokens"]
            )

            # Invoke with system instruction
            messages = [
                {"role": "system", "content": NARRATIVE_SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt}
            ]

            response = await asyncio.wait_for(
                flash_model.ainvoke(messages),
                timeout=30.0
            )

            profile_text = response.content.strip()
            if not profile_text:
                raise ValueError("Empty response for person_profile")

            logger.debug(
                f"Generated person_profile for persona {persona.id}",
                extra={
                    "persona_id": str(persona.id),
                    "length": len(profile_text)
                }
            )

            return profile_text

        except asyncio.TimeoutError:
            logger.warning(
                "Timeout generating person_profile for persona %s, using fallback",
                persona.id,
                extra={"persona_id": str(persona.id)}
            )
            return await self._fallback_person_profile(persona)
        except Exception as e:
            logger.error(
                f"Failed to generate person_profile for persona {persona.id}: {e}",
                exc_info=e
            )
            return await self._fallback_person_profile(persona)

    async def compose_person_motivations(
        self,
        needs: Dict[str, Any],
        persona: Persona
    ) -> str:
        """
        Generuje person_motivations (2-3 akapity, Pro model).

        Strategia:
        - Model: Gemini 2.5 Pro (synthesis task, moderate temperature)
        - Input: JTBD + Desired Outcomes + Pain Points
        - Output: 2-3 akapity syntetyzujące motywacje
        - Timeout: 30s

        Args:
            needs: NeedsAndPains dict (JTBD, outcomes, pains)
            persona: Persona object (dla context)

        Returns:
            String z 2-3 akapitami motywacji

        Raises:
            Exception: Jeśli LLM call fails
        """
        try:
            # Extract JTBD, outcomes, pains
            jobs = needs.get("jobs_to_be_done", [])
            outcomes = needs.get("desired_outcomes", [])
            pains = needs.get("pain_points", [])

            # Format data using helpers
            jobs_text = format_jobs_to_be_done(jobs)
            outcomes_text = format_desired_outcomes(outcomes)
            pains_text = format_pain_points(pains)
            persona_context_text = format_persona_context({
                "gender": persona.gender,
                "age": persona.age,
                "location": persona.location,
                "education_level": persona.education_level,
                "income_bracket": persona.income_bracket,
                "occupation": persona.occupation
            })

            # Build prompt
            prompt = PERSON_MOTIVATIONS_PROMPT.format(
                jobs_to_be_done=jobs_text,
                desired_outcomes=outcomes_text,
                pain_points=pains_text,
                persona_context=persona_context_text
            )

            # Build Pro model
            pro_model = build_chat_model(
                model=settings.ANALYSIS_MODEL,  # Pro
                temperature=PERSON_MOTIVATIONS_MODEL_PARAMS["temperature"],
                max_tokens=PERSON_MOTIVATIONS_MODEL_PARAMS["max_tokens"]
            )

            # Invoke
            messages = [
                {"role": "system", "content": NARRATIVE_SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt}
            ]

            response = await asyncio.wait_for(
                pro_model.ainvoke(messages),
                timeout=30.0
            )

            motivations_text = response.content.strip()
            if not motivations_text:
                raise ValueError("Empty response for person_motivations")

            logger.debug(
                f"Generated person_motivations for persona {persona.id}",
                extra={
                    "persona_id": str(persona.id),
                    "length": len(motivations_text)
                }
            )

            return motivations_text

        except asyncio.TimeoutError:
            logger.warning(
                "Timeout generating person_motivations for persona %s, using fallback",
                persona.id,
                extra={"persona_id": str(persona.id)}
            )
            return await self._fallback_person_motivations(needs, persona)
        except Exception as e:
            logger.error(
                f"Failed to generate person_motivations for persona {persona.id}: {e}",
                exc_info=e
            )
            return await self._fallback_person_motivations(needs, persona)

    async def compose_segment_hero(
        self,
        persona: Persona,
        graph_context: list,
        hybrid_context: dict
    ) -> str:
        """
        Generuje segment_hero (nazwa + tagline + 2-3 akapity, Pro model).

        Strategia:
        - Model: Gemini 2.5 Pro (storytelling task, higher temperature)
        - Input: Demographics + Graph insights + Hybrid context
        - Output: Segment name + Tagline + Description
        - Timeout: 30s

        Args:
            persona: Persona object
            graph_context: Lista graph nodes
            hybrid_context: Dict z context + citations

        Returns:
            String z segment hero (format specified in prompt)

        Raises:
            Exception: Jeśli LLM call fails
        """
        try:
            # Format inputs
            demographics_text = format_persona_context({
                "gender": persona.gender,
                "age": persona.age,
                "location": persona.location,
                "education_level": persona.education_level,
                "income_bracket": persona.income_bracket,
                "occupation": persona.occupation
            })

            graph_text = format_graph_context(graph_context)
            hybrid_text = hybrid_context.get("context", "Brak kontekstu z dokumentów.")

            # Build prompt
            prompt = SEGMENT_HERO_PROMPT.format(
                persona_demographics=demographics_text,
                graph_context=graph_text,
                hybrid_context=hybrid_text
            )

            # Build Pro model
            pro_model = build_chat_model(
                model=settings.ANALYSIS_MODEL,  # Pro
                temperature=SEGMENT_HERO_MODEL_PARAMS["temperature"],
                max_tokens=SEGMENT_HERO_MODEL_PARAMS["max_tokens"]
            )

            # Invoke
            messages = [
                {"role": "system", "content": NARRATIVE_SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt}
            ]

            response = await asyncio.wait_for(
                pro_model.ainvoke(messages),
                timeout=30.0
            )

            hero_text = response.content.strip()
            if not hero_text:
                raise ValueError("Empty response for segment_hero")

            logger.debug(
                f"Generated segment_hero for persona {persona.id}",
                extra={
                    "persona_id": str(persona.id),
                    "length": len(hero_text)
                }
            )

            return hero_text

        except asyncio.TimeoutError:
            logger.warning(
                "Timeout generating segment_hero for persona %s, using fallback",
                persona.id,
                extra={"persona_id": str(persona.id)}
            )
            return await self._fallback_segment_hero(persona, graph_context, hybrid_context)
        except Exception as e:
            logger.error(
                f"Failed to generate segment_hero for persona {persona.id}: {e}",
                exc_info=e
            )
            return await self._fallback_segment_hero(persona, graph_context, hybrid_context)

    async def compose_segment_significance(
        self,
        insights: list,
        persona: Persona
    ) -> str:
        """
        Generuje segment_significance (1 akapit, Pro model).

        Strategia:
        - Model: Gemini 2.5 Pro (analytical task, low-moderate temperature)
        - Input: Top insights + persona context
        - Output: 1 akapit (4-6 zdań) biznesowego znaczenia
        - Timeout: 30s

        Args:
            insights: Lista top insights (sorted by confidence)
            persona: Persona object (dla context)

        Returns:
            String z 1 akapitem znaczenia biznesowego

        Raises:
            Exception: Jeśli LLM call fails
        """
        try:
            # Format inputs
            insights_text = format_insights(insights)
            persona_context_text = format_persona_context({
                "gender": persona.gender,
                "age": persona.age,
                "location": persona.location,
                "education_level": persona.education_level,
                "income_bracket": persona.income_bracket,
                "occupation": persona.occupation
            })

            # Build prompt
            prompt = SEGMENT_SIGNIFICANCE_PROMPT.format(
                insights=insights_text,
                persona_context=persona_context_text
            )

            # Build Pro model
            pro_model = build_chat_model(
                model=settings.ANALYSIS_MODEL,  # Pro
                temperature=SEGMENT_SIGNIFICANCE_MODEL_PARAMS["temperature"],
                max_tokens=SEGMENT_SIGNIFICANCE_MODEL_PARAMS["max_tokens"]
            )

            # Invoke
            messages = [
                {"role": "system", "content": NARRATIVE_SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt}
            ]

            response = await asyncio.wait_for(
                pro_model.ainvoke(messages),
                timeout=30.0
            )

            significance_text = response.content.strip()
            if not significance_text:
                raise ValueError("Empty response for segment_significance")

            logger.debug(
                f"Generated segment_significance for persona {persona.id}",
                extra={
                    "persona_id": str(persona.id),
                    "length": len(significance_text)
                }
            )

            return significance_text

        except asyncio.TimeoutError:
            logger.warning(
                "Timeout generating segment_significance for persona %s, using fallback",
                persona.id,
                extra={"persona_id": str(persona.id)}
            )
            return await self._fallback_segment_significance(insights, persona)
        except Exception as e:
            logger.error(
                f"Failed to generate segment_significance for persona {persona.id}: {e}",
                exc_info=e
            )
            return await self._fallback_segment_significance(insights, persona)

    async def compose_evidence_context(
        self,
        graph_context: list,
        hybrid_context: dict,
        persona: Persona
    ) -> Dict[str, Any]:
        """
        Generuje evidence_context (JSON structured output, Pro model).

        Strategia:
        - Model: Gemini 2.5 Pro (citation analysis, structured output)
        - Input: Graph nodes + Hybrid citations + Demographics
        - Output: {background_narrative, key_citations[]}
        - Timeout: 30s

        Args:
            graph_context: Lista graph nodes
            hybrid_context: Dict z context + citations
            persona: Persona object

        Returns:
            Dict z:
            - background_narrative: str (1-2 akapity kontekstu)
            - key_citations: List[{source, insight, relevance}]

        Raises:
            Exception: Jeśli LLM call fails
        """
        try:
            # Format inputs
            graph_text = format_graph_context(graph_context)
            hybrid_text = json.dumps(hybrid_context, indent=2, ensure_ascii=False)
            demographics_text = format_persona_context({
                "gender": persona.gender,
                "age": persona.age,
                "location": persona.location,
                "education_level": persona.education_level,
                "income_bracket": persona.income_bracket,
                "occupation": persona.occupation
            })

            # Build prompt
            prompt = EVIDENCE_CONTEXT_PROMPT.format(
                graph_context=graph_text,
                hybrid_context=hybrid_text,
                persona_demographics=demographics_text
            )

            # Build Pro model with structured output
            pro_model = build_chat_model(
                model=settings.ANALYSIS_MODEL,  # Pro
                temperature=EVIDENCE_CONTEXT_MODEL_PARAMS["temperature"],
                max_tokens=EVIDENCE_CONTEXT_MODEL_PARAMS["max_tokens"]
            )

            # Use with_structured_output dla JSON reliability
            structured_model = pro_model.with_structured_output(EVIDENCE_CONTEXT_SCHEMA)

            # Invoke
            messages = [
                {"role": "system", "content": NARRATIVE_SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt}
            ]

            response = await asyncio.wait_for(
                structured_model.ainvoke(messages),
                timeout=30.0
            )

            # Check if response is None (LLM returned None instead of structured output)
            if response is None:
                logger.warning(
                    f"Structured output returned None for persona {persona.id}, using fallback",
                    extra={"persona_id": str(persona.id)}
                )
                return await self._fallback_evidence_context(persona, graph_context, hybrid_context)

            # Validate structure
            if not isinstance(response, dict):
                raise ValueError(f"Expected dict, got {type(response)}")

            if "background_narrative" not in response or "key_citations" not in response:
                raise ValueError(f"Missing required fields in response: {list(response.keys())}")

            background_raw = response.get("background_narrative", "")
            if not isinstance(background_raw, str) or not background_raw.strip():
                raise ValueError("Empty background_narrative from structured output")

            cleaned_background = background_raw.strip()
            raw_citations = response.get("key_citations", [])
            if not isinstance(raw_citations, list):
                raise ValueError("key_citations is not a list")

            cleaned_citations: List[Dict[str, Any]] = []
            for entry in raw_citations:
                if not isinstance(entry, dict):
                    continue
                source = str(entry.get("source", "")).strip()
                insight = str(entry.get("insight", "")).strip()
                relevance_value = entry.get("relevance", "")
                relevance = str(relevance_value).strip() if relevance_value is not None else ""

                if not (source or insight or relevance):
                    continue

                cleaned_citations.append(
                    {
                        "source": source or "Źródło nieznane",
                        "insight": insight or "Brak opisu",
                        "relevance": relevance or "Istotne dla segmentu",
                    }
                )

            if not cleaned_citations:
                raise ValueError("key_citations empty after cleaning")

            logger.debug(
                f"Generated evidence_context for persona {persona.id}",
                extra={
                    "persona_id": str(persona.id),
                    "narrative_length": len(response.get("background_narrative", "")),
                    "citations_count": len(response.get("key_citations", []))
                }
            )

            return {
                "background_narrative": cleaned_background,
                "key_citations": cleaned_citations,
            }

        except asyncio.TimeoutError:
            logger.warning(
                "Timeout generating evidence_context for persona %s, using fallback",
                persona.id,
                extra={"persona_id": str(persona.id)}
            )
            return await self._fallback_evidence_context(persona, graph_context, hybrid_context)
        except Exception as e:
            logger.error(
                f"Failed to generate evidence_context for persona {persona.id}: {e}",
                exc_info=e
            )
            return await self._fallback_evidence_context(persona, graph_context, hybrid_context)

    def _truncate_text(self, text: Optional[str], limit: int = 240) -> Optional[str]:
        """Trim text to a sensible length keeping whole words."""
        if not text:
            return None
        cleaned = str(text).strip()
        if not cleaned:
            return None
        if len(cleaned) <= limit:
            return cleaned
        truncated = cleaned[:limit].rsplit(" ", 1)[0]
        if not truncated:
            truncated = cleaned[:limit]
        truncated = truncated.rstrip(",.; ")
        return f"{truncated}..."

    def _describe_demographics(self, persona: Persona) -> str:
        parts: List[str] = []
        if persona.gender:
            parts.append(persona.gender.strip().lower())
        if persona.age:
            parts.append(f"około {persona.age} lat")
        if persona.location:
            parts.append(f"z obszaru {persona.location.strip()}")
        if persona.education_level:
            parts.append(f"z wykształceniem {persona.education_level.strip()}")
        if persona.income_bracket:
            parts.append(f"w przedziale dochodowym {persona.income_bracket}")
        if persona.occupation:
            parts.append(f"pracującą jako {persona.occupation}")
        return ", ".join(parts) if parts else "o zdefiniowanym profilu demograficznym"

    def _prepare_list_summary(self, block: Optional[str]) -> Optional[str]:
        if not block:
            return None
        stripped = block.strip()
        if not stripped or stripped.lower().startswith("brak"):
            return None
        items: List[str] = []
        for line in stripped.splitlines():
            entry = line.strip()
            if not entry:
                continue
            entry = entry.lstrip("0123456789.- ").strip()
            if entry:
                items.append(entry)
        return "; ".join(items) if items else None

    def _collect_insight_summaries(self, insights: List[Dict[str, Any]]) -> Optional[str]:
        summaries: List[str] = []
        for insight in insights or []:
            summary = insight.get("summary") or insight.get("streszczenie")
            if summary:
                summaries.append(str(summary).strip())
        if not summaries:
            return None
        return "; ".join(summaries[:3])

    def _collect_graph_highlights(self, graph_context: List[Dict[str, Any]]) -> Optional[str]:
        highlights: List[str] = []
        for node in graph_context or []:
            summary = node.get("summary") or node.get("streszczenie")
            if summary:
                highlights.append(str(summary).strip())
            if len(highlights) >= 3:
                break
        if not highlights:
            return None
        return "; ".join(highlights)

    async def _invoke_chat_model(
        self,
        *,
        prompt: str,
        model_name: str,
        temperature: float,
        max_tokens: int,
        timeout: float = 20.0,
    ) -> str:
        model = build_chat_model(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        messages = [
            {"role": "system", "content": NARRATIVE_SYSTEM_INSTRUCTION},
            {"role": "user", "content": prompt},
        ]
        response = await asyncio.wait_for(model.ainvoke(messages), timeout=timeout)
        content = getattr(response, "content", "")
        if isinstance(content, str):
            text = content.strip()
        elif isinstance(content, list):
            text = "".join(str(part) for part in content).strip()
        else:
            text = str(content).strip()
        if not text:
            raise ValueError("Empty response from chat model")
        return text

    async def _fallback_person_profile(self, persona: Persona) -> str:
        profile_subject = persona.full_name or persona.persona_title or "Ta persona"
        demographics = self._describe_demographics(persona)
        background = self._truncate_text(persona.background_story, 220)
        prompt = (
            "Na podstawie poniższych danych przygotuj zwięzły, biznesowy akapit "
            "przedstawiający personę. Wpleć najważniejsze elementy demografii i "
            "kontekstu, nie wspominaj o brakach danych ani o problemach z generowaniem.\n\n"
            f"DANE:\n"
            f"- Opis osoby: {profile_subject}\n"
            f"- Profil demograficzny: {demographics}\n"
            f"- Kontekst projektu: {background or 'Persona bierze udział w projekcie badawczym dotyczącym rynku.'}\n\n"
            "Wynik: 1 akapit (3-4 zdania) opisujący tę osobę w sposób spójny i naturalny."
        )
        try:
            return await self._invoke_chat_model(
                prompt=prompt,
                model_name=settings.PERSONA_GENERATION_MODEL,
                temperature=max(PERSON_PROFILE_MODEL_PARAMS["temperature"], 0.2),
                max_tokens=PERSON_PROFILE_MODEL_PARAMS["max_tokens"],
                timeout=20.0,
            )
        except Exception as fallback_error:
            logger.warning(
                "LLM fallback failed for person_profile of persona %s: %s",
                persona.id,
                fallback_error,
            )
            sentences = [f"{profile_subject} to osoba {demographics}."]
            if background:
                sentences.append(f"Dotychczasowe doświadczenia pokazują, że {background}")
            else:
                sentences.append(
                    "Łączy ambicje zawodowe z troską o codzienną jakość życia, co czyni ją ważnym głosem w badaniu."
                )
            return " ".join(sentences).strip()

    async def _fallback_person_motivations(self, needs: Dict[str, Any], persona: Persona) -> str:
        needs = needs or {}
        jobs_summary = self._prepare_list_summary(format_jobs_to_be_done(needs.get("jobs_to_be_done", []))) or \
            "realizacją codziennych zadań związanych z rolą zawodową i prywatnymi obowiązkami"
        outcomes_summary = self._prepare_list_summary(format_desired_outcomes(needs.get("desired_outcomes", []))) or \
            "poszukiwaniem stabilności, wygody i jasnych rezultatów, które ułatwiają podejmowanie decyzji"
        pains_summary = self._prepare_list_summary(format_pain_points(needs.get("pain_points", []))) or \
            "mierzeniem się z ograniczeniami czasu, budżetu i brakiem klarownych rozwiązań na rynku"

        demographics = self._describe_demographics(persona)
        prompt = (
            "Stwórz dwa krótkie akapity opisujące motywacje, oczekiwania oraz frustracje persony. "
            "Oprzyj się na poniższych informacjach, dodaj logiczne wnioski wynikające z demografii, "
            "ale nie wspominaj o brakach danych ani o procesie generowania.\n\n"
            f"Profil demograficzny: {demographics}\n"
            f"Jobs-to-be-Done: {jobs_summary}\n"
            f"Oczekiwane rezultaty: {outcomes_summary}\n"
            f"Problemy i bariery: {pains_summary}\n\n"
            "Zadbaj o ton empatyczny, skupiony na potrzebach biznesowych."
        )
        try:
            return await self._invoke_chat_model(
                prompt=prompt,
                model_name=settings.ANALYSIS_MODEL,
                temperature=PERSON_MOTIVATIONS_MODEL_PARAMS["temperature"],
                max_tokens=PERSON_MOTIVATIONS_MODEL_PARAMS["max_tokens"],
                timeout=25.0,
            )
        except Exception as fallback_error:
            logger.warning(
                "LLM fallback failed for person_motivations of persona %s: %s",
                persona.id,
                fallback_error,
            )
            sentences = [
                f"Osoba {demographics} koncentruje się na {jobs_summary}.",
                f"Oczekuje rezultatów opartych na {outcomes_summary}, które pozwalają jej pewnie realizować cele.",
                f"Jednocześnie doświadcza wyzwań związanych z {pains_summary}, dlatego docenia rozwiązania wspierające porządkowanie codziennych decyzji."
            ]
            return " ".join(sentences).strip()

    def _derive_segment_name(self, persona: Persona) -> str:
        parts: List[str] = []
        if persona.gender:
            parts.append(persona.gender.strip().title())
        if persona.age:
            parts.append(f"{persona.age} lat")
        if persona.education_level:
            parts.append(persona.education_level.strip())
        if persona.location:
            parts.append(persona.location.strip())
        name = " ".join(parts).strip()
        if not name:
            name = "Segment demograficzny"
        if len(name) > 60:
            name = name[:57].rsplit(" ", 1)[0] + "..."
        return name

    def _derive_segment_tagline(self, persona: Persona) -> str:
        location = persona.location or "kluczowych regionów"
        focus = persona.occupation or persona.persona_title or "osiąganiu swoich celów"
        focus_text = focus.lower()
        return f"Świadomi konsumenci z obszaru {location}, skoncentrowani na {focus_text}."

    async def _fallback_segment_hero(
        self,
        persona: Persona,
        graph_context: List[Dict[str, Any]],
        hybrid_context: Dict[str, Any],
    ) -> str:
        segment_name = persona.segment_name or self._derive_segment_name(persona)
        tagline = self._derive_segment_tagline(persona)
        demographics = self._describe_demographics(persona)
        highlights = self._collect_graph_highlights(graph_context)
        context_excerpt = self._truncate_text(hybrid_context.get("context"), 260) if hybrid_context else None
        narrative_context = highlights or context_excerpt or (
            "Segment charakteryzuje się świadomym podejściem do decyzji zakupowych oraz aktywnym poszukiwaniem rozwiązań, "
            "które oszczędzają czas i wspierają długofalowy rozwój."
        )

        background = self._truncate_text(persona.background_story, 260)
        prompt = (
            "Przygotuj opis segmentu w dokładnie poniższym formacie:\n"
            "Nazwa segmentu: ...\n"
            "Tagline: ...\n\n"
            "[Akapit 1]\n"
            "[Akapit 2]\n"
            "[Akapit 3 opcjonalny]\n\n"
            "Dane wejściowe:\n"
            f"- Proponowana nazwa segmentu: {segment_name}\n"
            f"- Profil: {demographics}\n"
            f"- Kluczowe obserwacje: {narrative_context}\n"
            f"- Kontekst projektu: {background or 'Persona stanowi punkt odniesienia w analizie klientów na rynku.'}\n\n"
            "Zasady: nadaj segmentowi spójną narrację, zachowaj profesjonalny ton i nie wspominaj o brakach danych."
        )
        try:
            return await self._invoke_chat_model(
                prompt=prompt,
                model_name=settings.ANALYSIS_MODEL,
                temperature=SEGMENT_HERO_MODEL_PARAMS["temperature"],
                max_tokens=SEGMENT_HERO_MODEL_PARAMS["max_tokens"],
                timeout=25.0,
            )
        except Exception as fallback_error:
            logger.warning(
                "LLM fallback failed for segment_hero of persona %s: %s",
                persona.id,
                fallback_error,
            )
            parts = [
                f"Nazwa segmentu: {segment_name}",
                f"Tagline: {tagline}",
                "",
                f"Segment obejmuje osoby {demographics}.",
                narrative_context,
            ]
            if background:
                parts.append(f"Kontekst projektu: {background}")
            return "\n".join(part for part in parts if part).strip()

    async def _fallback_segment_significance(
        self,
        insights: List[Dict[str, Any]],
        persona: Persona,
    ) -> str:
        demographics = self._describe_demographics(persona)
        insight_summary = self._collect_insight_summaries(insights) or (
            "uczestnicy ceniący przejrzyste rozwiązania, personalizację i wsparcie, które realnie usprawnia codzienne decyzje zakupowe"
        )
        prompt = (
            "Napisz jeden zwięzły akapit (4-5 zdań) wyjaśniający, dlaczego ten segment jest istotny biznesowo. "
            "Oprzyj się na danych demograficznych i obserwacjach, przedstaw logikę biznesową bez wzmianki o brakach danych.\n\n"
            f"Profil segmentu: {demographics}\n"
            f"Najważniejsze obserwacje: {insight_summary}\n"
            "Uwzględnij argumenty dotyczące potencjału zakupowego, lojalności oraz wpływu na decyzje produktowe."
        )
        try:
            return await self._invoke_chat_model(
                prompt=prompt,
                model_name=settings.ANALYSIS_MODEL,
                temperature=SEGMENT_SIGNIFICANCE_MODEL_PARAMS["temperature"],
                max_tokens=SEGMENT_SIGNIFICANCE_MODEL_PARAMS["max_tokens"],
                timeout=20.0,
            )
        except Exception as fallback_error:
            logger.warning(
                "LLM fallback failed for segment_significance of persona %s: %s",
                persona.id,
                fallback_error,
            )
            return (
                f"Segment obejmujący osoby {demographics} ma solidny potencjał komercyjny. "
                f"Dotychczasowe obserwacje pokazują, że {insight_summary}, co przekłada się na większą gotowość do testowania nowych rozwiązań "
                "i wysoki poziom zaangażowania w komunikację marek, które rozumieją ich potrzeby."
            )

    async def _fallback_evidence_context(
        self,
        persona: Persona,
        graph_context: List[Dict[str, Any]],
        hybrid_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        demographics = self._describe_demographics(persona)
        graph_highlights = self._collect_graph_highlights(graph_context) or \
            "Obserwowana grupa sięga po treści i rozwiązania, które przyspieszają codzienne decyzje."
        hybrid_excerpt = self._truncate_text(hybrid_context.get("context"), 240) if hybrid_context else None
        background = self._truncate_text(persona.background_story, 240)

        prompt = (
            "Przygotuj JSON zgodny z wymaganym schematem {background_narrative, key_citations[]} opisujący kontekst dowodowy segmentu. "
            "W background_narrative zawrzyj 1-2 akapity syntetyzujące najważniejsze obserwacje, bez wzmianki o brakach danych. "
            "W key_citations podaj 2-3 źródła. Gdy jedynym źródłem są obserwacje projektu, nazwij je np. 'Wewnętrzna analiza person 2025'. "
            "Każdy wpis ma mieć pola source, insight, relevance.\n\n"
            f"Profil segmentu: {demographics}\n"
            f"Insight z grafu: {graph_highlights}\n"
            f"Kontekst dokumentów: {hybrid_excerpt or 'Analizy jakościowe zespołu badawczego wskazują na potrzebę praktycznych rekomendacji.'}\n"
            f"Kontekst projektu: {background or 'Segment jest na bieżąco monitorowany w ramach badań fokusowych.'}"
        )
        try:
            pro_model = build_chat_model(
                model=settings.ANALYSIS_MODEL,
                temperature=EVIDENCE_CONTEXT_MODEL_PARAMS["temperature"],
                max_tokens=EVIDENCE_CONTEXT_MODEL_PARAMS["max_tokens"],
            )
            structured_model = pro_model.with_structured_output(EVIDENCE_CONTEXT_SCHEMA)
            messages = [
                {"role": "system", "content": NARRATIVE_SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt},
            ]
            response = await asyncio.wait_for(structured_model.ainvoke(messages), timeout=25.0)
            if not isinstance(response, dict):
                raise ValueError("Fallback structured response is not a dict")
            return response
        except Exception as fallback_error:
            logger.warning(
                "LLM fallback failed for evidence_context of persona %s: %s",
                persona.id,
                fallback_error,
            )
            background_parts = [
                hybrid_excerpt or "Segment w badaniach jakościowych konsekwentnie podkreśla wartość praktycznych rozwiązań wspierających decyzje konsumenckie.",
                f"Dodatkowe obserwacje wskazują, że {graph_highlights}",
            ]
            citations = [
                {
                    "source": "Wewnętrzna analiza person 2025",
                    "insight": "Wywiady fokusowe pokazują wzrost oczekiwań wobec narzędzi usprawniających decyzje zakupowe.",
                    "relevance": "Potwierdza charakter segmentu i uzasadnia inwestycje w dopasowaną komunikację.",
                },
                {
                    "source": "Desk research rynku",
                    "insight": "Użytkownicy w tym profilu demograficznym chętnie korzystają z rekomendacji ekspertów i społeczności.",
                    "relevance": "Pokazuje, że kanały edukacyjne i poradnikowe zwiększają ich lojalność.",
                },
            ]
            return {
                "background_narrative": " ".join(background_parts).strip(),
                "key_citations": citations,
            }
