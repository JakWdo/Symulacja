"""
API Endpoints - Zarządzanie Personami

Endpointy do generowania i zarządzania syntetycznymi personami dla badań rynkowych.

Główne funkcjonalności:
- POST /projects/{project_id}/personas/generate - generuje persony z AI (async background task)
- GET /projects/{project_id}/personas - pobiera wszystkie persony projektu
- GET /personas/{persona_id}/details - pobiera pełny detail view persony (MVP)
- DELETE /personas/{persona_id} - usuwa personę (soft delete)

Generowanie person:
1. Parsuje rozkłady demograficzne z target_demographics projektu
2. Uruchamia PersonaGenerator (Google Gemini Flash) w tle
3. Waliduje statystycznie wygenerowane persony (chi-kwadrat)
4. Zapisuje do bazy danych
5. Czas: ~1.5-3s per persona, ~30-60s dla 20 person

Używa background tasks - endpoint zwraca 202 Accepted natychmiast.
"""

import asyncio
import json
import logging
import random
import re
import unicodedata
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, BackgroundTasks, Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal, get_db
from app.models import Project, Persona, User
from app.services.personas.persona_orchestration import PersonaOrchestrationService
from app.api.dependencies import get_current_user, get_project_for_user, get_persona_for_user
from app.schemas.persona import (
    PersonaResponse,
    PersonaGenerateRequest,
    PersonaReasoningResponse,
    GraphInsightResponse,
)
from app.schemas.persona_details import (
    PersonaDetailsResponse,
    PersonaDeleteRequest,
    PersonaDeleteResponse,
    PersonaUndoDeleteResponse,
    PersonasSummaryResponse,
    PersonaBulkDeleteRequest,
    PersonaBulkDeleteResponse,
)
from app.services.personas import (
    PersonaGeneratorLangChain,
    PersonaValidator,
    PersonaDetailsService,
    PersonaAuditService,
)
from app.services.personas.persona_generator_langchain import DemographicDistribution
from app.services.personas.demographics_formatter import DemographicsFormatter
from app.services.personas.distribution_builder import DistributionBuilder
from app.services.personas.segment_constructor import SegmentConstructor
from app.core.config import get_settings
from config import demographics
from app.services.dashboard.cache_invalidation import invalidate_project_cache

# Get settings instance
settings = get_settings()

# Alias dla kompatybilności
PreferredPersonaGenerator = PersonaGeneratorLangChain

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)

# Śledź uruchomione zadania aby zapobiec garbage collection
_running_tasks = set()


def _graph_node_to_insight_response(node: dict[str, Any]) -> GraphInsightResponse | None:
    """Konwertuje surowy węzeł grafu (Neo4j) na GraphInsightResponse."""
    if not node:
        return None

    summary = node.get("summary") or node.get("streszczenie")
    if not summary:
        return None

    magnitude = node.get("magnitude") or node.get("skala")
    confidence_raw = node.get("confidence") or node.get("pewnosc") or node.get("pewność")
    confidence_map = {
        "wysoka": "high",
        "średnia": "medium",
        "srednia": "medium",
        "niska": "low",
    }
    if isinstance(confidence_raw, str):
        confidence = confidence_map.get(confidence_raw.lower(), confidence_raw.lower())
    else:
        confidence = "medium"

    time_period = node.get("time_period") or node.get("okres_czasu")
    source = (
        node.get("source")
        or node.get("document_title")
        or node.get("Źródło")
        or node.get("źródło")
    )

    why_matters = (
        node.get("why_matters")
        or node.get("kluczowe_fakty")
        or node.get("explanation")
        or summary
    )

    try:
        return GraphInsightResponse(
            type=node.get("type", "Insight"),
            summary=summary,
            magnitude=magnitude,
            confidence=confidence or "medium",
            time_period=time_period,
            source=source,
            why_matters=why_matters,
        )
    except Exception as exc:  # pragma: no cover - graceful fallback
        logger.warning("Failed to convert graph node to insight: %s", exc)
        return None


@lru_cache(maxsize=1)
def _get_persona_generator() -> PreferredPersonaGenerator:
    logger.info("Initializing cached persona generator instance")
    return PreferredPersonaGenerator()


def _calculate_concurrency_limit(num_personas: int, adversarial_mode: bool) -> int:
    base_limit = max(3, min(12, (num_personas // 3) + 3))
    if adversarial_mode:
        base_limit = max(2, base_limit - 2)
    if num_personas > 0:
        base_limit = min(base_limit, num_personas)
    return base_limit




@router.post(
    "/projects/{project_id}/personas/generate",
    status_code=202,
    summary="Start persona generation job",
)
@limiter.limit("10/hour")  # Security: Limit expensive LLM operations
async def generate_personas(
    request: Request,  # Required by slowapi limiter
    project_id: UUID,
    generate_request: PersonaGenerateRequest,
    _background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),  # Potrzebne do weryfikacji projektu przed uruchomieniem zadania
    current_user: User = Depends(get_current_user),
):
    """
    Rozpocznij generowanie syntetycznych person dla projektu (w tle)

    Endpoint ten:
    1. Weryfikuje czy projekt istnieje
    2. Loguje request
    3. Uruchamia zadanie w tle przy użyciu asyncio.create_task (odpowiedź HTTP wraca od razu)
    4. Zwraca natychmiast potwierdzenie

    Faktyczne generowanie odbywa się asynchronicznie w _generate_personas_task().

    Args:
        project_id: UUID projektu
        request: Parametry generowania (num_personas, adversarial_mode, advanced_options)
        _background_tasks: FastAPI BackgroundTasks do uruchomienia zadania w tle (obecnie niewykorzystane)
        db: Sesja bazy (tylko do weryfikacji projektu)

    Returns:
        {
            "message": "Persona generation started in background",
            "project_id": str,
            "num_personas": int,
            "adversarial_mode": bool
        }

    Raises:
        HTTPException 404: Jeśli projekt nie istnieje
    """
    # Weryfikacja czy projekt istnieje (przed dodaniem do kolejki)
    await get_project_for_user(project_id, current_user, db)

    logger.info(
        "Persona generation request received",
        extra={
            "project_id": str(project_id),
            "num_personas": generate_request.num_personas,
            "adversarial_mode": generate_request.adversarial_mode,
        },
    )

    # Przygotuj advanced options (konwertuj None fields)
    advanced_payload = (
        generate_request.advanced_options.model_dump(exclude_none=True)
        if generate_request.advanced_options
        else None
    )

    # Utwórz zadanie asynchroniczne
    logger.info(f"Creating async task for persona generation (project={project_id}, personas={generate_request.num_personas}, use_rag={generate_request.use_rag})")
    task = asyncio.create_task(_generate_personas_task(
        project_id,
        generate_request.num_personas,
        generate_request.adversarial_mode,
        advanced_payload,
        generate_request.use_rag,
    ))

    # Zachowujemy referencję do zadania, aby GC go nie usunął
    _running_tasks.add(task)
    task.add_done_callback(_running_tasks.discard)

    # Zwróć natychmiast (nie czekaj na zakończenie generowania)
    return {
        "message": "Persona generation started in background",
        "project_id": str(project_id),
        "num_personas": generate_request.num_personas,
        "adversarial_mode": generate_request.adversarial_mode,
    }


async def _generate_personas_task(
    project_id: UUID,
    num_personas: int,
    adversarial_mode: bool,
    advanced_options: dict[str, Any] | None = None,
    use_rag: bool = True,
):
    """
    Asynchroniczne zadanie w tle do generowania person

    To zadanie wykonuje się poza cyklem request-response HTTP:
    1. Tworzy własną sesję DB (AsyncSessionLocal)
    2. Ładuje projekt i jego target_demographics
    3. Generuje persony używając PersonaGeneratorLangChain
    4. Waliduje różnorodność person
    5. Zapisuje w bazie danych
    6. Aktualizuje statystyki projektu

    WAŻNE: To zadanie NIE może używać sesji DB z HTTP requesta!
    Musi stworzyć własną sesję przez AsyncSessionLocal().

    Args:
        project_id: UUID projektu
        num_personas: Liczba person do wygenerowania
        adversarial_mode: Czy użyć adversarial prompting (dla edge cases)
        advanced_options: Opcjonalne zaawansowane opcje (custom distributions, etc.)
    """
    logger.info(f"Starting persona generation task for project {project_id}, num_personas={num_personas}")

    try:
        # Utwórz własną sesję DB (niezależną od HTTP requesta)
        async with AsyncSessionLocal() as db:
            # Generator trzymamy w cache, żeby uniknąć kosztownej inicjalizacji przy każdym zadaniu
            generator = _get_persona_generator()
            generator_name = getattr(generator, "__class__", type(generator)).__name__
            logger.info("Using %s persona generator", generator_name, extra={"project_id": str(project_id)})

            # Initialize utility classes
            formatter = DemographicsFormatter()
            distribution_builder = DistributionBuilder()
            segment_constructor = SegmentConstructor()

            project = await db.get(Project, project_id)
            if not project:
                logger.error("Project not found in background task.", extra={"project_id": str(project_id)})
                return

            target_demographics = project.target_demographics or {}
            distribution = DemographicDistribution(
                age_groups=distribution_builder.normalize_distribution(target_demographics.get("age_group", {}), demographics.common.age_groups),
                genders=distribution_builder.normalize_distribution(target_demographics.get("gender", {}), demographics.common.genders),
                # Używaj POLSKICH wartości domyślnych dla lepszej realistyczności
                education_levels=distribution_builder.normalize_distribution(target_demographics.get("education_level", {}), demographics.poland.education_levels),
                income_brackets=distribution_builder.normalize_distribution(target_demographics.get("income_bracket", {}), demographics.poland.income_brackets),
                locations=distribution_builder.normalize_distribution(target_demographics.get("location", {}), demographics.poland.locations),
            )

            # === ADVANCED OPTIONS PROCESSING (AI Wizard kafle) ===
            # Extract fields from advanced_options (now properly defined in Pydantic schema)
            target_audience_desc = None
            focus_area = None
            demographic_preset = None

            if advanced_options:
                target_audience_desc = advanced_options.get("target_audience_description")
                focus_area = advanced_options.get("focus_area")
                demographic_preset = advanced_options.get("demographic_preset")

            # PHASE 2.1: Apply demographic preset (modifies distribution)
            if demographic_preset:
                logger.info(f"📊 Applying demographic preset: {demographic_preset}")
                distribution = distribution_builder.apply_demographic_preset(distribution, demographic_preset)

            # PHASE 2.2: Extract cities from target_audience_description
            if target_audience_desc:
                extracted_cities = distribution_builder.extract_polish_cities_from_description(target_audience_desc)
                if extracted_cities:
                    # Override location distribution with extracted cities (equal weights)
                    city_weights = {city: 1.0 / len(extracted_cities) for city in extracted_cities}
                    distribution.locations = distribution_builder.normalize_weights(city_weights)
                    logger.info(f"📍 Overrode locations with extracted cities: {extracted_cities}")

            # PHASE 2.3: Map focus_area to industries (if not already specified)
            if focus_area and not (advanced_options and advanced_options.get("industries")):
                industries = distribution_builder.map_focus_area_to_industries(focus_area)
                if industries:
                    # Add industries to advanced_options for generator
                    if not advanced_options:
                        advanced_options = {}
                    advanced_options["industries"] = industries
                    logger.info(f"🏢 Auto-set industries from focus_area: {industries}")

            # === ORCHESTRATION STEP (GEMINI 2.5 PRO) ===
            # RE-ENABLED with optimizations:
            #   - Redis caching (7-day TTL) for Graph RAG queries → 300-400x speedup on cache hits
            #   - Connection pooling for Neo4j → prevents connection exhaustion
            #   - Reduced parallel queries: 8+ → 4 consolidated → 50% latency reduction
            #   - Optimized Cypher queries with CALL subqueries + TEXT indexes → 30-50% faster
            # Expected performance:
            #   - Cache HIT: ~5-10s total (4 queries × 50ms = 200ms Graph RAG + 5-8s LLM)
            #   - Cache MISS: ~15-25s total (4 queries × 2-3s = 8-12s Graph RAG + 5-8s LLM)
            #   - Timeout: 90s (safety margin, orchestration should complete in <30s)
            # Rollback: Set ORCHESTRATION_ENABLED=false in .env or config.py

            # Check feature flag
            orchestration_enabled = settings.ORCHESTRATION_ENABLED

            allocation_plan = None
            persona_group_mapping = {}

            if orchestration_enabled:
                # Instancja orchestration service
                orchestration_service = PersonaOrchestrationService()
                logger.info("🎯 Creating orchestration plan with Gemini 2.5 Pro...")
                try:
                    # Pobierz advanced options (target_audience, focus_area, demographic_preset)
                    target_audience_desc = None
                    focus_area = None
                    demographic_preset = None

                    if advanced_options:
                        target_audience_desc = advanced_options.get("target_audience_description")
                        focus_area = advanced_options.get("focus_area")
                        demographic_preset = advanced_options.get("demographic_preset")

                    # Komponuj additional_context z wszystkich dostępnych pól
                    additional_context_parts = []

                    if target_audience_desc:
                        additional_context_parts.append(f"Grupa docelowa: {target_audience_desc}")

                    if focus_area:
                        # Mapuj focus_area na ludzki opis
                        focus_area_labels = {
                            "tech": "Branża technologiczna (IT, software, hardware)",
                            "healthcare": "Branża zdrowotna (medycyna, opieka zdrowotna, farmacja)",
                            "finance": "Branża finansowa (bankowość, fintech, inwestycje)",
                            "education": "Branża edukacyjna (nauczanie, szkolenia, e-learning)",
                            "retail": "Branża detaliczna (handel, e-commerce, FMCG)",
                            "manufacturing": "Branża produkcyjna (przemysł, logistyka)",
                            "services": "Branża usługowa (consulting, usługi B2B/B2C)",
                            "other": "Inna branża"
                        }
                        focus_label = focus_area_labels.get(focus_area, focus_area)
                        additional_context_parts.append(f"Obszar zainteresowań: {focus_label}")

                    if demographic_preset:
                        # Mapuj demographic_preset na rozkłady demograficzne (hints dla orchestration)
                        preset_labels = {
                            "gen_z": "Generacja Z (18-27 lat) - digitalni natywni, wartości: autentyczność, różnorodność, ekologia",
                            "millennials": "Millennialsi (28-43 lata) - work-life balance, kariera, technologia, przedsiębiorczość",
                            "gen_x": "Generacja X (44-59 lat) - stabilność, rodzina, doświadczenie zawodowe",
                            "boomers": "Baby Boomers (60+ lat) - tradycyjne wartości, bezpieczeństwo, dziedzictwo",
                            "urban_professionals": "Profesjonaliści miejscy - duże miasta, wyższe wykształcenie, kariera korporacyjna",
                            "suburban_families": "Rodziny podmiejskie - przedmieścia, średnie dochody, stabilność",
                            "rural_communities": "Społeczności wiejskie - mniejsze miejscowości, lokalne społeczności"
                        }
                        preset_label = preset_labels.get(demographic_preset, demographic_preset)
                        additional_context_parts.append(f"Preset demograficzny: {preset_label}")

                    additional_context = "\n".join(additional_context_parts) if additional_context_parts else None

                    if additional_context:
                        logger.info(
                            f"📋 Additional context for orchestration:\n{additional_context}"
                        )

                    # Tworzymy plan alokacji (długie briefe dla każdej grupy)
                    allocation_plan = await orchestration_service.create_persona_allocation_plan(
                        target_demographics=target_demographics,
                        num_personas=num_personas,
                        project_description=project.description,
                        additional_context=additional_context,
                    )
    
                    logger.info(
                        f"✅ Orchestration plan created: {len(allocation_plan.groups)} demographic groups, "
                        f"overall_context={len(allocation_plan.overall_context)} chars"
                    )
    
                    # Mapuj briefe do każdej persony
                    # Strategia: Każda grupa ma `count` person, więc przydzielamy briefe sekwencyjnie
                    persona_index = 0
                    group_metadata: list[dict[str, str | None]] = []
                    for group_index, group in enumerate(allocation_plan.groups):
                        demographics = (
                            group.demographics
                            if isinstance(group.demographics, dict)
                            else dict(group.demographics)
                        )
                        segment_metadata = segment_constructor.build_segment_metadata(
                            demographics,
                            group.brief,
                            group.allocation_reasoning,
                            group_index,
                            group.segment_characteristics,  # Pass catchy name from orchestration
                        )
                        group_metadata.append(segment_metadata)
                        group_count = group.count
                        for _ in range(group_count):
                            if persona_index < num_personas:
                                persona_group_mapping[persona_index] = {
                                    "brief": group.brief,
                                    "graph_insights": [insight.model_dump() for insight in group.graph_insights],
                                    "allocation_reasoning": group.allocation_reasoning,
                                    "demographics": demographics,
                                    "segment_characteristics": group.segment_characteristics,
                                    **segment_metadata,
                                }
                                persona_index += 1
    
                    # KOREKCJA: Jeśli LLM alokował za mało, dolicz brakujące do ostatniej grupy
                    # To naprawia off-by-one error gdzie LLM czasami zwraca sum(group.count) < num_personas
                    total_allocated = sum(group.count for group in allocation_plan.groups)
                    if total_allocated < num_personas and allocation_plan.groups:
                        shortage = num_personas - total_allocated
                        logger.info(
                            f"🔧 Correcting allocation shortage: adding {shortage} personas to last group "
                            f"(LLM allocated {total_allocated}/{num_personas})"
                        )
    
                        # Zwiększ count ostatniej grupy
                        allocation_plan.groups[-1].count += shortage
    
                        # Dodaj brakujące persony do mapping (używając briefa ostatniej grupy)
                        last_group = allocation_plan.groups[-1]
                        if group_metadata:
                            last_metadata = group_metadata[-1]
                        else:
                            last_demographics = (
                                last_group.demographics
                                if isinstance(last_group.demographics, dict)
                                else dict(last_group.demographics)
                            )
                            last_metadata = segment_constructor.build_segment_metadata(
                                last_demographics,
                                last_group.brief,
                                last_group.allocation_reasoning,
                                len(allocation_plan.groups) - 1,
                                last_group.segment_characteristics,  # Pass catchy name from orchestration
                            )
                        for i in range(persona_index, num_personas):
                            persona_group_mapping[i] = {
                                "brief": last_group.brief,
                                "graph_insights": [insight.model_dump() for insight in last_group.graph_insights],
                                "allocation_reasoning": last_group.allocation_reasoning,
                                "demographics": last_group.demographics
                                if isinstance(last_group.demographics, dict)
                                else dict(last_group.demographics),
                                "segment_characteristics": last_group.segment_characteristics,
                                **last_metadata,
                            }
                            persona_index += 1
    
                    # WALIDACJA: Sprawdź czy wszystkie persony dostały briefe
                    total_allocated = sum(group.count for group in allocation_plan.groups)
                    if total_allocated != num_personas:
                        logger.warning(
                            f"⚠️ Allocation plan gap: expected {num_personas} personas, "
                            f"but allocation plan covers {total_allocated}. "
                            f"{num_personas - total_allocated} personas won't have orchestration briefs."
                        )
                    elif persona_index < num_personas:
                        logger.warning(
                            f"⚠️ Brief mapping incomplete: mapped {persona_index}/{num_personas} personas. "
                            f"Last {num_personas - persona_index} personas won't have orchestration briefs."
                        )
    
                    logger.info(f"📋 Mapped briefs to {len(persona_group_mapping)} personas")
    
                except Exception as orch_error:
                    # GRACEFUL DEGRADATION: Orchestration failure doesn't block persona generation
                    logger.error(
                        f"❌ Orchestration failed: {orch_error}. Falling back to basic generation...",
                        exc_info=orch_error
                    )
                    allocation_plan = None
                    persona_group_mapping = {}

            else:
                # Orchestration disabled via feature flag
                logger.info(
                    "🚫 ORCHESTRATION DISABLED (ORCHESTRATION_ENABLED=false) - using basic generation mode"
                )
                logger.info(
                    "   Personas will be generated without detailed reasoning/briefs."
                )
                logger.info(
                    "   To enable: Set ORCHESTRATION_ENABLED=true in .env or config.py"
                )

            # Kontrolowana współbieżność pozwala przyspieszyć generowanie bez przeciążania modelu
            logger.info(f"Generating demographic and psychological profiles for {num_personas} personas")
            concurrency_limit = _calculate_concurrency_limit(num_personas, adversarial_mode)
            semaphore = asyncio.Semaphore(concurrency_limit)
            demographic_profiles = [generator.sample_demographic_profile(distribution)[0] for _ in range(num_personas)]
            psychological_profiles = [{**generator.sample_big_five_traits(), **generator.sample_cultural_dimensions()} for _ in range(num_personas)]

            # === OVERRIDE DEMOGRAPHICS FROM ORCHESTRATION (if available) ===
            # When orchestration is enabled and successful, override sampled demographics
            # with orchestration-allocated values for targeted generation
            if persona_group_mapping:
                logger.info(
                    f"Overriding demographics for {len(persona_group_mapping)} personas "
                    f"based on orchestration allocation"
                )
                for idx, group_data in persona_group_mapping.items():
                    if idx < len(demographic_profiles):
                        orch_demographics = group_data["demographics"]
                        demographic_profiles[idx].update({
                            "age_group": orch_demographics.get("age", demographic_profiles[idx]["age_group"]),
                            "gender": orch_demographics.get("gender", demographic_profiles[idx]["gender"]),
                            "education_level": orch_demographics.get("education", demographic_profiles[idx]["education_level"]),
                            "location": orch_demographics.get("location", demographic_profiles[idx]["location"]),
                        })
                        logger.debug(
                            f"✅ Persona {idx}: demographics overridden with orchestration "
                            f"(age={orch_demographics.get('age')}, gender={orch_demographics.get('gender')})"
                        )

            logger.info(
                f"Starting LLM generation for {num_personas} personas with concurrency={concurrency_limit}",
                extra={"project_id": str(project_id), "concurrency_limit": concurrency_limit},
            )

            personas_data: list[dict[str, Any]] = []
            batch_payloads: list[dict[str, Any]] = []
            saved_count = 0
            # Mniejsze batch-e oznaczają szybszą widoczność danych w UI i niższe zużycie pamięci
            batch_size = max(1, min(10, num_personas // 4 or 1))

            async def persist_batch() -> None:
                """Zapisz aktualny batch person do bazy – komentarz po polsku, zgodnie z prośbą."""
                nonlocal saved_count
                if not batch_payloads:
                    return
                try:
                    db.add_all([Persona(**data) for data in batch_payloads])
                    await db.commit()
                    saved_count += len(batch_payloads)
                    logger.info(
                        "Persisted persona batch",
                        extra={
                            "project_id": str(project_id),
                            "batch_size": len(batch_payloads),
                            "saved_total": saved_count,
                            "target": num_personas,
                        },
                    )
                except Exception as commit_error:  # pragma: no cover - zabezpieczenie awaryjne
                    await db.rollback()
                    logger.error(
                        "Database commit FAILED for persona batch",
                        exc_info=True,
                        extra={
                            "project_id": str(project_id),
                            "batch_size": len(batch_payloads),
                            "saved_count": saved_count,
                            "target_personas": num_personas,
                            "error_type": type(commit_error).__name__,
                        },
                    )
                    raise
                finally:
                    batch_payloads.clear()

            async def create_single_persona(idx: int, demo_profile: dict[str, Any], psych_profile: dict[str, Any]):
                async with semaphore:
                    # === INJECT ORCHESTRATION BRIEF (if available) ===
                    # Enrich persona generation with orchestration context:
                    #   - orchestration_brief: 900-1200 char educational context
                    #   - orchestration_insights: Graph RAG insights (3-5 per group)
                    #   - segment_characteristics: 4-6 key traits
                    enhanced_options = advanced_options.copy() if advanced_options else {}

                    if persona_group_mapping and idx in persona_group_mapping:
                        group_data = persona_group_mapping[idx]
                        enhanced_options["orchestration_brief"] = group_data["brief"]
                        enhanced_options["orchestration_insights"] = group_data["graph_insights"]
                        enhanced_options["segment_characteristics"] = group_data["segment_characteristics"]

                        logger.debug(
                            f"✅ Persona {idx}: injecting orchestration brief "
                            f"({len(group_data['brief'])} chars, {len(group_data['graph_insights'])} insights)"
                        )

                    result = await generator.generate_persona_personality(demo_profile, psych_profile, use_rag, enhanced_options)
                    if (idx + 1) % max(1, batch_size) == 0 or idx == num_personas - 1:
                        logger.info(
                            "Generated personas chunk",
                            extra={"project_id": str(project_id), "generated": idx + 1, "target": num_personas},
                        )
                    return idx, result

            tasks = [
                asyncio.create_task(create_single_persona(i, demo, psych))
                for i, (demo, psych) in enumerate(zip(demographic_profiles, psychological_profiles))
            ]

            try:
                for future in asyncio.as_completed(tasks):
                    try:
                        idx, result = await future
                    except Exception as gen_error:  # pragma: no cover - logowanie błędów zadań
                        from app.middleware.request_id import get_request_id
                        logger.error(
                            "Persona generation coroutine FAILED",
                            exc_info=True,
                            extra={
                                "project_id": str(project_id),
                                "request_id": get_request_id(),
                                "num_personas": num_personas,
                                "personas_generated_so_far": len(personas_data),
                                "error_type": type(gen_error).__name__,
                            },
                        )
                        continue

                    prompt, personality_json = result

                    # Odporne parsowanie JSON-a z mechanizmem awaryjnym
                    personality: dict[str, Any] = {}
                    try:
                        if isinstance(personality_json, str):
                            cleaned = personality_json.strip()
                            if cleaned.startswith("```json"):
                                cleaned = cleaned[7:]
                            if cleaned.startswith("```"):
                                cleaned = cleaned[3:]
                            if cleaned.endswith("```"):
                                cleaned = cleaned[:-3]
                            cleaned = cleaned.strip()
                            personality = json.loads(cleaned)
                        elif isinstance(personality_json, dict):
                            personality = personality_json
                        else:
                            logger.warning(
                                f"Unexpected personality_json type: {type(personality_json)}",
                                extra={"project_id": str(project_id), "index": idx}
                            )
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.error(
                            f"Failed to parse personality JSON for persona {idx}: {str(e)[:200]}",
                            extra={
                                "project_id": str(project_id),
                                "index": idx,
                                "raw_json": str(personality_json)[:500],
                            }
                        )
                        personality = {}

                    demographic = demographic_profiles[idx]
                    psychological = psychological_profiles[idx]

                    background_story = (personality.get("background_story") or "").strip()
                    if not background_story:
                        logger.warning(
                            f"Missing background_story for persona {idx}",
                            extra={"project_id": str(project_id), "index": idx},
                        )

                    # Wyliczamy wiek na podstawie przedziału wiekowego
                    age_group = demographic.get("age_group", "25-34")
                    age = random.randint(25, 34)
                    if "-" in age_group:
                        try:
                            start, end = map(int, age_group.split("-"))
                            age = random.randint(start, end)
                        except ValueError:
                            pass
                    elif "+" in age_group:
                        try:
                            start = int(age_group.replace("+", ""))
                            age = random.randint(start, start + 15)
                        except ValueError:
                            pass

                    full_name = personality.get("full_name")
                    if not full_name or full_name == "N/A":
                        inferred_name = _infer_full_name(personality.get("background_story"))
                        full_name = inferred_name or _fallback_full_name(demographic.get("gender"), age)
                        logger.warning(
                            f"Missing full_name for persona {idx}, using fallback: {full_name}",
                            extra={"project_id": str(project_id), "index": idx}
                        )

                    # WALIDACJA WIEKU: Spróbuj wyekstraktować wiek z opisu i porównaj z demografią
                    # KRYTYCZNE: Używaj extracted_age TYLKO jeśli mieści się w zakresie demograficznym
                    # To naprawia bug gdzie "10 lat doświadczenia" → age=10 dla persony 35-44
                    extracted_age = _extract_age_from_story(background_story)
                    if extracted_age:
                        # Sprawdź czy extracted_age mieści się w age_group
                        age_group_str = demographic.get("age_group", "")
                        if "-" in age_group_str:
                            try:
                                min_age, max_age = map(int, age_group_str.split("-"))
                                if min_age <= extracted_age <= max_age:
                                    # ✅ OK - extracted_age jest w zakresie, użyj go
                                    age = extracted_age
                                    logger.debug(
                                        f"Using extracted age {extracted_age} (within range {age_group_str})",
                                        extra={"project_id": str(project_id), "index": idx}
                                    )
                                else:
                                    # ❌ Poza zakresem - IGNORUJ extracted_age, zostaw losowy wiek
                                    logger.warning(
                                        f"Age mismatch for persona {idx}: story says {extracted_age}, "
                                        f"but age_group is {age_group_str}. IGNORING extracted age, using random age {age}.",
                                        extra={"project_id": str(project_id), "index": idx}
                                    )
                                    # NIE ustawiaj age = extracted_age!
                            except ValueError:
                                pass
                        elif "+" in age_group_str:
                            try:
                                min_age = int(age_group_str.replace("+", ""))
                                if extracted_age >= min_age:
                                    # ✅ OK - extracted_age jest >= min_age, użyj go
                                    age = extracted_age
                                else:
                                    # ❌ Poniżej minimum - IGNORUJ
                                    logger.warning(
                                        f"Age mismatch for persona {idx}: story says {extracted_age}, "
                                        f"but age_group is {age_group_str}. IGNORING extracted age.",
                                        extra={"project_id": str(project_id), "index": idx}
                                    )
                            except ValueError:
                                pass
                        else:
                            # Brak przedziału - użyj extracted_age (ale z sanity check)
                            if 18 <= extracted_age <= 100:
                                age = extracted_age

                    occupation = _get_consistent_occupation(
                        demographic.get("education_level"),
                        demographic.get("income_bracket"),
                        age,
                        personality,
                        background_story,
                    )

                    persona_title = personality.get("persona_title")
                    if persona_title:
                        persona_title = persona_title.strip()
                    if not persona_title or persona_title == "N/A" or not formatter.looks_polish_phrase(persona_title):
                        persona_title = occupation or f"Persona {age}"
                        logger.info(
                            "Persona title zaktualizowany na polski zawód",
                            extra={"project_id": str(project_id), "index": idx},
                        )

                    gender_value = formatter.polishify_gender(demographic.get("gender"))
                    education_value = formatter.polishify_education(demographic.get("education_level"))
                    income_value = formatter.polishify_income(demographic.get("income_bracket"))
                    location_value = formatter.ensure_polish_location(demographic.get("location"), background_story)

                    headline = personality.get("headline")
                    if not headline or headline == "N/A":
                        headline = formatter.compose_headline(
                            full_name, persona_title, occupation, location_value
                        )
                        logger.warning(
                            f"Missing headline for persona {idx}, using generated: {headline}",
                            extra={"project_id": str(project_id), "index": idx}
                        )

                    values = _fallback_polish_list(personality.get("values"), demographics.poland.values)
                    if not personality.get("values"):
                        logger.warning(
                            f"Missing values for persona {idx}, using Polish defaults",
                            extra={"project_id": str(project_id), "index": idx},
                        )

                    interests = _fallback_polish_list(personality.get("interests"), demographics.poland.interests)
                    if not personality.get("interests"):
                        logger.warning(
                            f"Missing interests for persona {idx}, using Polish defaults",
                            extra={"project_id": str(project_id), "index": idx},
                        )

                    # Ekstrakcja RAG citations i details (jeśli były używane)
                    rag_citations_raw = personality.get("_rag_citations") or []
                    rag_citations = rag_citations_raw or None
                    rag_context_details = personality.get("_rag_context_details") or {}
                    if (
                        "graph_nodes_count" not in rag_context_details
                        and rag_context_details.get("graph_nodes")
                    ):
                        rag_context_details["graph_nodes_count"] = len(
                            rag_context_details.get("graph_nodes", [])
                        )
                    rag_context_used = bool(
                        rag_citations_raw
                        or rag_context_details.get("graph_nodes")
                        or rag_context_details.get("graph_context")
                        or rag_context_details.get("context_preview")
                    )

                    # === INJECT ORCHESTRATION REASONING into rag_context_details (if available) ===
                    # This powers the /personas/{id}/reasoning endpoint
                    # Contains: brief, graph_insights, allocation_reasoning, demographics, etc.
                    if persona_group_mapping and idx in persona_group_mapping:
                        group_data = persona_group_mapping[idx]

                        rag_context_details["orchestration_reasoning"] = {
                            "brief": group_data["brief"],
                            "graph_insights": group_data["graph_insights"],
                            "allocation_reasoning": group_data["allocation_reasoning"],
                            "demographics": group_data["demographics"],
                            "segment_characteristics": group_data["segment_characteristics"],
                            "segment_name": group_data.get("segment_name"),
                            "segment_id": group_data.get("segment_id"),
                            "segment_description": group_data.get("segment_description"),
                            "segment_social_context": group_data.get("segment_social_context"),
                        }

                        logger.debug(f"✅ Persona {idx}: orchestration reasoning injected into rag_context_details")

                    persona_payload = {
                        "project_id": project_id,
                        "full_name": full_name,
                        "persona_title": persona_title,
                        "headline": headline,
                        "age": age,
                        "gender": gender_value,
                        "location": location_value,
                        "education_level": education_value,
                        "income_bracket": income_value,
                        "occupation": occupation,
                        "background_story": background_story,
                        "values": values,
                        "interests": interests,
                        "personality_prompt": prompt,
                        "rag_context_used": rag_context_used,
                        "rag_citations": rag_citations,
                        "rag_context_details": rag_context_details,  # NOWE POLE
                        **psychological
                    }

                    # === SET SEGMENT_ID and SEGMENT_NAME ===
                    # Priority:
                    #   1. Orchestration data (if available) - most authoritative
                    #   2. catchy_segment_name from LLM response (fallback)

                    # First, try orchestration data
                    if persona_group_mapping and idx in persona_group_mapping:
                        group_data = persona_group_mapping[idx]
                        if group_data.get("segment_id"):
                            persona_payload["segment_id"] = group_data["segment_id"]
                        if group_data.get("segment_name"):
                            persona_payload["segment_name"] = group_data["segment_name"]
                            logger.debug(
                                f"✅ Persona {idx}: Using orchestration segment_name: '{group_data['segment_name']}'"
                            )

                    # Fallback to catchy_segment_name from LLM if orchestration didn't provide segment_name
                    if "segment_name" not in persona_payload:
                        # OVERRIDE segment_name with catchy_segment_name from LLM if available
                        # This replaces long technical names like "Kobiety 35-44 wyższe wykształcenie"
                        # with catchy marketing names like "Pasywni Liberałowie", "Młodzi Prekariusze"
                        catchy_segment_name = personality.get("catchy_segment_name")
                        if catchy_segment_name and isinstance(catchy_segment_name, str):
                            catchy_segment_name = catchy_segment_name.strip()
                            # Validate length (2-4 words = roughly 10-60 chars)
                            if 5 <= len(catchy_segment_name) <= 60:
                                persona_payload["segment_name"] = catchy_segment_name
                                if isinstance(rag_context_details, dict):
                                    rag_context_details["segment_name"] = catchy_segment_name
                                    # Also update orchestration_reasoning if it exists
                                    if "orchestration_reasoning" in rag_context_details:
                                        rag_context_details["orchestration_reasoning"]["segment_name"] = catchy_segment_name
                                logger.info(
                                    f"Using catchy segment name: '{catchy_segment_name}' (persona {idx})",
                                    extra={"project_id": str(project_id), "index": idx}
                                )
                            else:
                                logger.warning(
                                    f"Catchy segment name too short/long: '{catchy_segment_name}' ({len(catchy_segment_name)} chars), keeping original",
                                    extra={"project_id": str(project_id), "index": idx}
                                )

                    # === VALIDATION: SPRAWDŹ SPÓJNOŚĆ DEMOGRAPHICS ===
                    # Validate że generated persona pasuje do orchestration demographics
                    if idx in persona_group_mapping:
                        orch_demo = persona_group_mapping[idx]["demographics"]
                        mismatches = []

                        # Check gender
                        expected_gender = formatter.polishify_gender(orch_demo.get("gender", ""))
                        if expected_gender and persona_payload["gender"] != expected_gender:
                            mismatches.append(
                                f"gender: got '{persona_payload['gender']}', expected '{expected_gender}'"
                            )

                        # Check age range
                        expected_age_range = orch_demo.get("age", "")
                        if expected_age_range and "-" in expected_age_range:
                            try:
                                min_age, max_age = map(int, expected_age_range.split("-"))
                                if not (min_age <= persona_payload["age"] <= max_age):
                                    mismatches.append(
                                        f"age: {persona_payload['age']} not in range {expected_age_range}"
                                    )
                            except ValueError:
                                pass

                        # Check education (basic comparison - might have different formats)
                        expected_education = orch_demo.get("education", "")
                        if expected_education:
                            # Normalize for comparison
                            norm_expected_ed = formatter.polishify_education(expected_education)
                            if persona_payload["education_level"] != norm_expected_ed:
                                mismatches.append(
                                    f"education: got '{persona_payload['education_level']}', "
                                    f"expected '{norm_expected_ed}'"
                                )

                        # Log mismatches jeśli znaleziono
                        if mismatches:
                            logger.warning(
                                f"⚠️  Demographics mismatch for persona {idx} ('{full_name}'): "
                                f"{'; '.join(mismatches)}",
                                extra={
                                    "project_id": str(project_id),
                                    "persona_index": idx,
                                    "full_name": full_name,
                                    "mismatches": mismatches,
                                }
                            )

                    personas_data.append(persona_payload)
                    batch_payloads.append(persona_payload)

                    if len(batch_payloads) >= batch_size:
                        await persist_batch()
            finally:
                for task in tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)

            # Finalne opróżnienie bufora
            await persist_batch()

            if not personas_data:
                logger.warning("No personas were generated successfully.", extra={"project_id": str(project_id)})
                return

            # Walidacja jakości wygenerowanych person
            validator = PersonaValidator()
            validation_results = validator.validate_personas(personas_data)
            if not validation_results["is_valid"]:
                logger.warning("Persona validation found issues.", extra=validation_results)

            if not adversarial_mode and hasattr(generator, "validate_distribution"):
                try:
                    validation = generator.validate_distribution(demographic_profiles, distribution)
                    project = await db.get(Project, project_id)  # Ponowne pobranie po commitach batchy
                    if project:
                        project.is_statistically_valid = validation.get("overall_valid", False)
                        project.chi_square_statistic = {k: v.get("chi_square_statistic") for k, v in validation.items() if k != "overall_valid"}
                        project.p_values = {k: v.get("p_value") for k, v in validation.items() if k != "overall_valid"}
                        await db.commit()
                except Exception as e:
                    logger.error("Statistical validation failed.", exc_info=e)

            logger.info("Persona generation task completed.", extra={"project_id": str(project_id), "count": len(personas_data)})
    except Exception as e:
        from app.middleware.request_id import get_request_id
        logger.error(
            "CRITICAL ERROR in persona generation task",
            exc_info=True,
            extra={
                "project_id": str(project_id),
                "request_id": get_request_id(),
                "num_personas": num_personas,
                "personas_generated": len(personas_data) if 'personas_data' in locals() else 0,
                "use_rag": use_rag,
                "adversarial_mode": adversarial_mode,
                "error_type": type(e).__name__,
                "error_message": str(e)[:500],
            },
        )


def _normalize_rag_citations(citations: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
    """
    Normalizuje RAG citations do aktualnego schematu RAGCitation.

    Stary format (przed refactorem):
    {
        "text": str,
        "score": float,
        "metadata": {"title": str, ...}
    }

    Nowy format (RAGCitation schema):
    {
        "document_title": str,
        "chunk_text": str,
        "relevance_score": float
    }

    Args:
        citations: Lista citations (może być None lub pusta)

    Returns:
        Lista citations w nowym formacie lub None jeśli input był None
    """
    if not citations:
        return citations

    normalized = []
    for citation in citations:
        if not isinstance(citation, dict):
            logger.warning(f"Invalid citation type: {type(citation)}, skipping")
            continue

        # Sprawdź czy to stary format (ma 'text' zamiast 'chunk_text')
        if 'text' in citation and 'chunk_text' not in citation:
            # Stary format - przekształć
            normalized_citation = {
                "document_title": citation.get("metadata", {}).get("title", "Unknown Document"),
                "chunk_text": citation.get("text", ""),
                "relevance_score": abs(float(citation.get("score", 0.0)))  # abs() bo stare scores były ujemne
            }
            normalized.append(normalized_citation)
        elif 'chunk_text' in citation:
            # Nowy format - użyj bez zmian
            normalized.append(citation)
        else:
            # Nieprawidłowy format - spróbuj wyekstraktować co się da
            logger.warning(f"Unknown citation format: {list(citation.keys())}")
            normalized_citation = {
                "document_title": citation.get("document_title") or citation.get("metadata", {}).get("title", "Unknown Document"),
                "chunk_text": citation.get("chunk_text") or citation.get("text", ""),
                "relevance_score": abs(float(citation.get("relevance_score") or citation.get("score", 0.0)))
            }
            normalized.append(normalized_citation)

    return normalized if normalized else None


@router.get("/projects/{project_id}/personas/summary", response_model=PersonasSummaryResponse)
async def get_personas_summary(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Zwróć podsumowanie person projektu (liczebność, segmenty)."""
    await get_project_for_user(project_id, current_user, db)

    totals_row = await db.execute(
        select(
            func.count().label("total"),
            func.sum(case((Persona.is_active.is_(True), 1), else_=0)).label("active"),
            func.sum(case((Persona.is_active.is_(False), 1), else_=0)).label("archived"),
        ).where(Persona.project_id == project_id)
    )
    totals = totals_row.first()
    total_personas = int(totals.total or 0) if totals else 0
    active_personas = int(totals.active or 0) if totals else 0
    archived_personas = int(totals.archived or 0) if totals else 0

    segments_result = await db.execute(
        select(
            Persona.segment_id,
            Persona.segment_name,
            func.sum(case((Persona.is_active.is_(True), 1), else_=0)).label("active"),
            func.sum(case((Persona.is_active.is_(False), 1), else_=0)).label("archived"),
        )
        .where(Persona.project_id == project_id)
        .group_by(Persona.segment_id, Persona.segment_name)
    )

    segment_rows = segments_result.all()
    segments = [
        {
            "segment_id": row.segment_id,
            "segment_name": row.segment_name,
            "active_personas": int(row.active or 0),
            "archived_personas": int(row.archived or 0),
        }
        for row in segment_rows
    ]

    return PersonasSummaryResponse(
        project_id=project_id,
        total_personas=total_personas,
        active_personas=active_personas,
        archived_personas=archived_personas,
        segments=segments,
    )


@router.get("/projects/{project_id}/personas", response_model=list[PersonaResponse])
async def list_personas(
    project_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List personas for a project"""
    await get_project_for_user(project_id, current_user, db)
    result = await db.execute(
        select(Persona)
        .where(
            Persona.project_id == project_id,
            Persona.is_active.is_(True),
            Persona.deleted_at.is_(None),
        )
        .offset(skip)
        .limit(limit)
    )
    personas = result.scalars().all()

    # Normalizuj rag_citations dla każdej persony (backward compatibility)
    for persona in personas:
        if persona.rag_citations:
            persona.rag_citations = _normalize_rag_citations(persona.rag_citations)

    return personas


@router.delete("/personas/{persona_id}", response_model=PersonaDeleteResponse)
async def delete_persona(
    persona_id: UUID,
    delete_request: PersonaDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete persona z audit logging

    Args:
        persona_id: UUID persony do usunięcia
        delete_request: Powód usunięcia (reason + optional reason_detail)
        db: DB session
        current_user: Authenticated user

    Returns:
        PersonaDeleteResponse

    RBAC:
        - MVP: Wszyscy zalogowani użytkownicy mogą usuwać własne persony
        - Production: Tylko Admin może usuwać (TODO: add RBAC check)

    Audit:
        - Loguje delete action z reason w persona_audit_log
    """
    persona = await get_persona_for_user(persona_id, current_user, db)

    if persona.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Persona already deleted",
        )

    deleted_at = datetime.utcnow()
    undo_deadline = deleted_at + timedelta(days=7)
    permanent_delete_at = deleted_at + timedelta(days=7)

    # Miękkie usunięcie rekordu
    persona.is_active = False
    persona.deleted_at = deleted_at
    persona.deleted_by = current_user.id

    # Log delete action (audit trail)
    audit_service = PersonaAuditService()
    await audit_service.log_action(
        persona_id=persona_id,
        user_id=current_user.id,
        action="delete",
        details={
            "reason": delete_request.reason,
            "reason_detail": delete_request.reason_detail,
        },
        db=db,
    )

    await db.commit()

    # Invalidate dashboard cache
    await invalidate_project_cache(current_user.id, persona.project_id)

    return PersonaDeleteResponse(
        persona_id=persona_id,
        full_name=persona.full_name,
        status="deleted",
        deleted_at=deleted_at,
        deleted_by=current_user.id,
        undo_available_until=undo_deadline,
        permanent_deletion_scheduled_at=permanent_delete_at,
        message="Persona deleted successfully. You can undo this action within 7 days.",
    )


@router.post("/personas/{persona_id}/undo-delete", response_model=PersonaUndoDeleteResponse)
async def undo_delete_persona(
    persona_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Przywróć personę jeśli okno undo (7 dni) nie wygasło."""
    persona = await get_persona_for_user(
        persona_id,
        current_user,
        db,
        include_inactive=True,
    )

    if persona.deleted_at is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona is not deleted")

    undo_deadline = persona.deleted_at + timedelta(days=7)
    now = datetime.utcnow()
    if now > undo_deadline:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Restore window expired (7 days passed). Persona will be permanently deleted.",
            headers={
                "X-Undo-Deadline": undo_deadline.isoformat(),
                "X-Deleted-At": persona.deleted_at.isoformat(),
            },
        )

    persona.is_active = True
    persona.deleted_at = None
    persona.deleted_by = None

    audit_service = PersonaAuditService()
    await audit_service.log_action(
        persona_id=persona_id,
        user_id=current_user.id,
        action="undo_delete",
        details={"source": "undo"},
        db=db,
    )

    await db.commit()

    # Invalidate dashboard cache
    await invalidate_project_cache(current_user.id, persona.project_id)

    return PersonaUndoDeleteResponse(
        persona_id=persona_id,
        full_name=persona.full_name,
        status="active",
        restored_at=now,
        restored_by=current_user.id,
        message="Persona restored successfully",
    )


@router.post("/personas/bulk-delete", response_model=PersonaBulkDeleteResponse)
async def bulk_delete_personas(
    bulk_request: PersonaBulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Usuń wiele person jednocześnie (bulk soft delete z audit logging)

    Args:
        bulk_request: PersonaBulkDeleteRequest z listą persona_ids i powodem
        db: DB session
        current_user: Authenticated user

    Returns:
        PersonaBulkDeleteResponse ze statystykami (deleted_count, failed_count, failed_ids)

    Flow:
        1. Loop przez wszystkie persona_ids
        2. Dla każdej persony: weryfikuj ownership, soft delete, log w audit
        3. Zbieraj statystyki (successes vs failures)
        4. Zwróć response z undo_available_until (7 dni)

    RBAC:
        - MVP: Wszyscy zalogowani użytkownicy mogą usuwać własne persony
        - Production: Tylko Admin może usuwać (TODO: add RBAC check)

    Audit:
        - Loguje delete action dla każdej persony z reason w persona_audit_log
    """
    deleted_at = datetime.utcnow()
    undo_deadline = deleted_at + timedelta(days=7)

    deleted_count = 0
    failed_count = 0
    failed_ids: list[UUID] = []

    audit_service = PersonaAuditService()

    # Loop przez wszystkie persona_ids
    for persona_id in bulk_request.persona_ids:
        try:
            # Pobierz personę i weryfikuj ownership
            persona = await get_persona_for_user(persona_id, current_user, db)

            # Sprawdź czy już usunięta
            if persona.deleted_at is not None:
                failed_count += 1
                failed_ids.append(persona_id)
                continue

            # Soft delete
            persona.is_active = False
            persona.deleted_at = deleted_at
            persona.deleted_by = current_user.id

            # Log delete action (audit trail)
            await audit_service.log_action(
                persona_id=persona_id,
                user_id=current_user.id,
                action="delete",
                details={
                    "reason": bulk_request.reason,
                    "reason_detail": bulk_request.reason_detail,
                    "bulk_operation": True,
                },
                db=db,
            )

            deleted_count += 1

        except HTTPException:
            # Persona nie znaleziona lub brak dostępu
            failed_count += 1
            failed_ids.append(persona_id)
        except Exception as e:
            # Niespodziewany błąd
            logger.error(f"Error deleting persona {persona_id}: {str(e)}")
            failed_count += 1
            failed_ids.append(persona_id)

    # Commit wszystkich zmian naraz
    await db.commit()

    # Invalidate dashboard cache if any personas were deleted
    if deleted_count > 0:
        from app.services.dashboard.cache_invalidation import invalidate_dashboard_cache
        await invalidate_dashboard_cache(current_user.id)

    # Przygotuj komunikat
    if deleted_count == len(bulk_request.persona_ids):
        message = f"Successfully deleted {deleted_count} persona(s). You can undo this action within 7 days."
    elif deleted_count > 0:
        message = f"Deleted {deleted_count} persona(s), {failed_count} failed. Check failed_ids for details."
    else:
        message = f"Failed to delete all personas. Check failed_ids for details."

    return PersonaBulkDeleteResponse(
        deleted_count=deleted_count,
        failed_count=failed_count,
        failed_ids=failed_ids,
        undo_available_until=undo_deadline,
        message=message,
    )


@router.get("/personas/{persona_id}/reasoning", response_model=PersonaReasoningResponse)
async def get_persona_reasoning(
    persona_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pobierz szczegółowe reasoning persony (dla zakładki 'Uzasadnienie' w UI)

    Zwraca:
    - orchestration_brief: Zwięzły (900-1200 znaków) edukacyjny brief od Gemini 2.5 Pro
    - graph_insights: Lista wskaźników z Graph RAG z wyjaśnieniami "dlaczego to ważne"
    - allocation_reasoning: Dlaczego tyle person w tej grupie demograficznej
    - demographics: Docelowa demografia tej grupy
    - overall_context: Ogólny kontekst społeczny Polski

    Output style: Edukacyjny, konwersacyjny, wyjaśniający, production-ready

    Raises:
        HTTPException 404: Jeśli persona nie istnieje lub nie ma reasoning data
    """
    # Pobierz personę (weryfikacja uprawnień)
    persona = await get_persona_for_user(persona_id, current_user, db)

    # Graceful handling: zwróć pustą response jeśli brak orchestration data
    # (zamiast 404 - lepsze UX)
    rag_details: dict[str, Any] = persona.rag_context_details or {}
    if not rag_details:
        logger.warning(
            "Persona %s nie ma rag_context_details - zwracam pustą response", persona_id
        )
        return PersonaReasoningResponse(
            orchestration_brief=None,
            graph_insights=[],
            allocation_reasoning=None,
            demographics=None,
            overall_context=None,
        )

    orch_reasoning: dict[str, Any] = rag_details.get("orchestration_reasoning") or {}
    if not orch_reasoning:
        logger.warning(
            "Persona %s nie ma orchestration_reasoning - korzystam tylko z danych RAG",
            persona_id,
        )

    # Parsuj graph insights z orchestration lub fallbacku
    graph_insights: list[GraphInsightResponse] = []
    raw_graph_insights = orch_reasoning.get("graph_insights") or rag_details.get(
        "graph_insights", []
    )
    for insight_dict in raw_graph_insights or []:
        try:
            graph_insights.append(GraphInsightResponse(**insight_dict))
        except Exception as exc:
            logger.warning(
                "Failed to parse graph insight: %s, insight=%s", exc, insight_dict
            )

    # Fallback: konwertuj surowe węzły grafu na insights
    if not graph_insights and rag_details.get("graph_nodes"):
        for node in rag_details["graph_nodes"]:
            converted = _graph_node_to_insight_response(node)
            if converted:
                graph_insights.append(converted)

    # Wyprowadź pola segmentowe i kontekstowe
    segment_name = orch_reasoning.get("segment_name") or rag_details.get("segment_name")
    segment_description = orch_reasoning.get("segment_description") or rag_details.get(
        "segment_description"
    )
    segment_social_context = (
        orch_reasoning.get("segment_social_context")
        or rag_details.get("segment_social_context")
        or rag_details.get("segment_context")
    )
    raw_characteristics = (
        orch_reasoning.get("segment_characteristics")
        or rag_details.get("segment_characteristics")
        or []
    )
    segment_characteristics = [str(item).strip() for item in raw_characteristics if str(item).strip()]

    orchestration_brief = orch_reasoning.get("brief") or rag_details.get("brief")
    allocation_reasoning = orch_reasoning.get("allocation_reasoning") or rag_details.get(
        "allocation_reasoning"
    )
    demographics = orch_reasoning.get("demographics") or rag_details.get("demographics")
    overall_context = (
        orch_reasoning.get("overall_context")
        or rag_details.get("overall_context")
        or rag_details.get("graph_context")
    )

    # Fallback demografia (używana również do budowania opisów segmentu)
    fallback_demographics = demographics or {
        "age": str(persona.age) if persona.age else None,
        "gender": persona.gender,
        "education": persona.education_level,
        "income": persona.income_bracket,
        "location": persona.location,
    }
    if not isinstance(fallback_demographics, dict):
        try:
            fallback_demographics = dict(fallback_demographics)
        except Exception:
            fallback_demographics = {
                "age": str(persona.age) if persona.age else None,
                "gender": persona.gender,
                "education": persona.education_level,
                "income": persona.income_bracket,
                "location": persona.location,
            }

    # Preferuj catchy segment name zapisany przy personie
    if persona.segment_name:
        segment_name = persona.segment_name
    if persona.segment_id:
        segment_id_value = persona.segment_id
    else:
        segment_id_value = orch_reasoning.get("segment_id") or rag_details.get("segment_id")

    if not segment_name:
        segment_name = segment_constructor.build_segment_metadata(
            fallback_demographics,
            orchestration_brief,
            allocation_reasoning,
            0,
        ).get("segment_name")

    if not segment_description and segment_name:
        segment_description = segment_constructor.compose_segment_description(fallback_demographics, segment_name)

    if not segment_social_context:
        characteristic_summary = ""
        if segment_characteristics:
            characteristic_summary = (
                " Kluczowe wyróżniki: "
                + ", ".join(segment_characteristics[:4])
                + "."
            )
        demographic_sentence = segment_constructor.compose_segment_description(
            fallback_demographics,
            segment_name or "Ten segment",
        )
        brief_snippet = segment_constructor.sanitize_brief_text(orchestration_brief, max_length=280)
        segment_social_context = (
            f"{demographic_sentence}{characteristic_summary} "
            f"{brief_snippet}" if brief_snippet else f"{demographic_sentence}{characteristic_summary}"
        ).strip()

    segment_social_context = segment_constructor.sanitize_brief_text(segment_social_context)

    response = PersonaReasoningResponse(
        orchestration_brief=orchestration_brief,
        graph_insights=graph_insights,
        allocation_reasoning=allocation_reasoning,
        demographics=demographics,
        overall_context=overall_context,
        segment_name=segment_name,
        segment_id=segment_id_value,
        segment_description=segment_description,
        segment_social_context=segment_social_context,
        segment_characteristics=segment_characteristics,
    )

    return response


@router.get("/personas/{persona_id}/details", response_model=PersonaDetailsResponse)
async def get_persona_details(
    persona_id: UUID,
    force_refresh: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pobierz pełny detail view persony (MVP)

    Pełny widok szczegółowy persony z:
    - Base persona data (demographics, psychographics)
    - Needs and pains (JTBD, desired outcomes, pain points - opcjonalne)
    - RAG insights (z rag_context_details)
    - Audit log (last 20 actions)

    Note: KPI snapshot i customer journey zostały usunięte z modelu.
    Dla KPI metrics użyj PersonaKPIService, dla journey - PersonaJourneyService.

    Args:
        persona_id: UUID persony
        force_refresh: Wymuś recalculation (bypass cache)
        db: DB session
        current_user: Authenticated user

    Returns:
        PersonaDetailsResponse z pełnym detail view

    RBAC:
        - MVP: Wszyscy zalogowani użytkownicy mogą przeglądać persony
        - Production: Role-based permissions (Viewer+)

    Performance:
        - Cache hit: < 50ms (Redis cache with TTL 1h, auto-invalidation on update)
        - Cache miss: < 500ms (parallel fetch + 1 DB query)

    Audit:
        - Loguje "view" action w persona_audit_log (async, non-blocking)
    """
    # Verify access
    await get_persona_for_user(persona_id, current_user, db)

    # Fetch details (orchestration service)
    details_service = PersonaDetailsService(db)
    try:
        details = await details_service.get_persona_details(
            persona_id=persona_id,
            user_id=current_user.id,
            force_refresh=force_refresh,
        )
        return details
    except ValueError as e:
        # Persona not found
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Unexpected error
        logger.error(f"Failed to fetch persona details: {e}", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch persona details. Please try again later.",
        )


@router.get("/personas/archived", response_model=list[PersonaResponse])
async def get_archived_personas(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pobierz listę usuniętych person (archiwum) z ostatnich 7 dni

    Zwraca persony które zostały soft-deleted i nadal mogą być przywrócone
    (restore window: 7 dni od deleted_at).

    Args:
        db: DB session
        current_user: Authenticated user

    Returns:
        List[PersonaResponse]: Lista usuniętych person (ordered by deleted_at DESC)

    Query:
        - is_active = False
        - deleted_at IS NOT NULL
        - deleted_at > now() - 7 days (restore window)
        - User ma dostęp poprzez project ownership

    RBAC:
        - Użytkownik widzi tylko persony z własnych projektów
    """
    # Calculate restore window cutoff (7 days ago)
    restore_window_start = datetime.utcnow() - timedelta(days=7)

    # Query: pobierz usunięte persony z ostatnich 7 dni
    result = await db.execute(
        select(Persona)
        .join(Project, Persona.project_id == Project.id)
        .where(
            Persona.is_active.is_(False),
            Persona.deleted_at.isnot(None),
            Persona.deleted_at > restore_window_start,
            Project.owner_id == current_user.id,
        )
        .order_by(Persona.deleted_at.desc())
    )
    personas = result.scalars().all()

    # Convert to PersonaResponse
    return [
        PersonaResponse(
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
            created_at=persona.created_at,
        )
        for persona in personas
    ]
