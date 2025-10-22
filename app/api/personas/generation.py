"""
API Endpoints - Persona Generation

POST /projects/{project_id}/personas/generate - generuje persony w tle z AI

Główny workflow generowania person:
1. Weryfikuje projekt i parametry
2. Uruchamia asynchroniczne zadanie w tle (asyncio.create_task)
3. Zadanie w tle (1) orchestration (Gemini 2.5 Pro), (2) generation (parallel LLM calls), (3) validation
4. Zapisuje w bazie danych w batch-ach
5. Endpoint zwraca natychmiast 202 Accepted

Czas generowania: ~1.5-3s per persona, ~30-60s dla 20 person
"""

import asyncio
import json
import logging
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from fastapi import APIRouter, Depends, BackgroundTasks, Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal, get_db
from app.models import Project, Persona, User
from app.services.personas import (
    PersonaOrchestrationService,
    PersonaValidator,
)
from app.services import DemographicDistribution
from app.api.dependencies import get_current_user, get_project_for_user
from app.schemas.persona import PersonaGenerateRequest
from app.core.constants import (
    DEFAULT_AGE_GROUPS,
    DEFAULT_GENDERS,
    POLISH_EDUCATION_LEVELS,
    POLISH_INCOME_BRACKETS,
    POLISH_LOCATIONS,
    POLISH_VALUES,
    POLISH_INTERESTS,
)

# Import utility functions
from .utils import (
    _get_persona_generator,
    _calculate_concurrency_limit,
    _normalize_distribution,
    _build_segment_metadata,
    _polishify_gender,
    _polishify_education,
    _polishify_income,
    _ensure_polish_location,
    _looks_polish_phrase,
    _infer_full_name,
    _fallback_full_name,
    _extract_age_from_story,
    _get_consistent_occupation,
    _compose_headline,
    _fallback_polish_list,
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)

# Śledź uruchomione zadania aby zapobiec garbage collection
_running_tasks: Set[asyncio.Task] = set()


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
    advanced_options: Optional[Dict[str, Any]] = None,
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

            project = await db.get(Project, project_id)
            if not project:
                logger.error("Project not found in background task.", extra={"project_id": str(project_id)})
                return

            target_demographics = project.target_demographics or {}
            distribution = DemographicDistribution(
                age_groups=_normalize_distribution(target_demographics.get("age_group", {}), DEFAULT_AGE_GROUPS),
                genders=_normalize_distribution(target_demographics.get("gender", {}), DEFAULT_GENDERS),
                # Używaj POLSKICH wartości domyślnych dla lepszej realistyczności
                education_levels=_normalize_distribution(target_demographics.get("education_level", {}), POLISH_EDUCATION_LEVELS),
                income_brackets=_normalize_distribution(target_demographics.get("income_bracket", {}), POLISH_INCOME_BRACKETS),
                locations=_normalize_distribution(target_demographics.get("location", {}), POLISH_LOCATIONS),
            )

            # === ORCHESTRATION STEP (GEMINI 2.5 PRO) ===
            # Tworzymy szczegółowy plan alokacji używając orchestration agent
            orchestration_service = PersonaOrchestrationService()
            allocation_plan = None
            persona_group_mapping = {}  # Mapuje persona index -> brief

            logger.info("🎯 Creating orchestration plan with Gemini 2.5 Pro...")
            try:
                # Pobierz dodatkowy opis grupy docelowej jeśli istnieje
                target_audience_desc = None
                if advanced_options and "target_audience_description" in advanced_options:
                    target_audience_desc = advanced_options["target_audience_description"]

                # Tworzymy plan alokacji (długie briefe dla każdej grupy)
                allocation_plan = await orchestration_service.create_persona_allocation_plan(
                    target_demographics=target_demographics,
                    num_personas=num_personas,
                    project_description=project.description,
                    additional_context=target_audience_desc,
                )

                logger.info(
                    f"✅ Orchestration plan created: {len(allocation_plan.groups)} demographic groups, "
                    f"overall_context={len(allocation_plan.overall_context)} chars"
                )

                # Mapuj briefe do każdej persony
                # Strategia: Każda grupa ma `count` person, więc przydzielamy briefe sekwencyjnie
                persona_index = 0
                group_metadata: List[Dict[str, Optional[str]]] = []
                for group_index, group in enumerate(allocation_plan.groups):
                    demographics = (
                        group.demographics
                        if isinstance(group.demographics, dict)
                        else dict(group.demographics)
                    )
                    segment_metadata = _build_segment_metadata(
                        demographics,
                        group.brief,
                        group.allocation_reasoning,
                        group_index,
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
                        last_metadata = _build_segment_metadata(
                            last_demographics,
                            last_group.brief,
                            last_group.allocation_reasoning,
                            len(allocation_plan.groups) - 1,
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
                # Jeśli orchestration failuje, logujemy ale kontynuujemy (fallback do basic generation)
                logger.error(
                    f"❌ Orchestration failed: {orch_error}. Continuing with basic generation...",
                    exc_info=orch_error
                )
                allocation_plan = None
                persona_group_mapping = {}

            # Kontrolowana współbieżność pozwala przyspieszyć generowanie bez przeciążania modelu
            logger.info(f"Generating demographic and psychological profiles for {num_personas} personas")
            concurrency_limit = _calculate_concurrency_limit(num_personas, adversarial_mode)
            semaphore = asyncio.Semaphore(concurrency_limit)
            demographic_profiles = [generator.sample_demographic_profile(distribution)[0] for _ in range(num_personas)]
            psychological_profiles = [{**generator.sample_big_five_traits(), **generator.sample_cultural_dimensions()} for _ in range(num_personas)]

            # === OVERRIDE DEMOGRAPHICS Z ORCHESTRATION ===
            # Orchestration plan ma AUTORYTATYWNE demographics (z Gemini 2.5 Pro analysis)
            # Override sampled demographics aby zapewnić spójność z briefami
            if allocation_plan and persona_group_mapping:
                logger.info("🔒 Overriding sampled demographics with orchestration demographics...")
                override_count = 0

                for idx, profile in enumerate(demographic_profiles):
                    if idx in persona_group_mapping:
                        orch_demo = persona_group_mapping[idx]["demographics"]

                        # Override sampled values (orchestration jest bardziej autorytatywny)
                        if "age" in orch_demo and orch_demo["age"]:
                            profile["age_group"] = orch_demo["age"]
                            override_count += 1

                        if "gender" in orch_demo and orch_demo["gender"]:
                            profile["gender"] = orch_demo["gender"]

                        if "education" in orch_demo and orch_demo["education"]:
                            profile["education_level"] = orch_demo["education"]

                        if "income" in orch_demo and orch_demo["income"]:
                            profile["income_bracket"] = orch_demo["income"]

                        logger.debug(
                            f"Persona {idx}: enforced demographics from orchestration "
                            f"(age={orch_demo.get('age')}, gender={orch_demo.get('gender')})",
                            extra={"project_id": str(project_id), "index": idx}
                        )

                logger.info(
                    f"✅ Demographics override completed: {override_count}/{num_personas} personas enforced",
                    extra={"project_id": str(project_id)}
                )

            logger.info(
                f"Starting LLM generation for {num_personas} personas with concurrency={concurrency_limit}",
                extra={"project_id": str(project_id), "concurrency_limit": concurrency_limit},
            )

            personas_data: List[Dict[str, Any]] = []
            batch_payloads: List[Dict[str, Any]] = []
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
                        "Nie udało się zapisać partii wygenerowanych person.",
                        exc_info=commit_error,
                        extra={"project_id": str(project_id), "batch_size": len(batch_payloads)},
                    )
                    raise
                finally:
                    batch_payloads.clear()

            async def create_single_persona(idx: int, demo_profile: Dict[str, Any], psych_profile: Dict[str, Any]):
                async with semaphore:
                    # Dodaj orchestration brief do advanced_options jeśli istnieje
                    enhanced_options = advanced_options.copy() if advanced_options else {}
                    if idx in persona_group_mapping:
                        enhanced_options["orchestration_brief"] = persona_group_mapping[idx]["brief"]
                        enhanced_options["graph_insights"] = persona_group_mapping[idx]["graph_insights"]
                        enhanced_options["allocation_reasoning"] = persona_group_mapping[idx]["allocation_reasoning"]

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
                        logger.error(
                            "Persona generation coroutine failed.",
                            exc_info=gen_error,
                            extra={"project_id": str(project_id)},
                        )
                        continue

                    prompt, personality_json = result

                    # Odporne parsowanie JSON-a z mechanizmem awaryjnym
                    personality: Dict[str, Any] = {}
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
                    if not persona_title or persona_title == "N/A" or not _looks_polish_phrase(persona_title):
                        persona_title = occupation or f"Persona {age}"
                        logger.info(
                            "Persona title zaktualizowany na polski zawód",
                            extra={"project_id": str(project_id), "index": idx},
                        )

                    gender_value = _polishify_gender(demographic.get("gender"))
                    education_value = _polishify_education(demographic.get("education_level"))
                    income_value = _polishify_income(demographic.get("income_bracket"))
                    location_value = _ensure_polish_location(demographic.get("location"), background_story)

                    headline = personality.get("headline")
                    if not headline or headline == "N/A":
                        headline = _compose_headline(
                            full_name, persona_title, occupation, location_value
                        )
                        logger.warning(
                            f"Missing headline for persona {idx}, using generated: {headline}",
                            extra={"project_id": str(project_id), "index": idx}
                        )

                    values = _fallback_polish_list(personality.get("values"), POLISH_VALUES)
                    if not personality.get("values"):
                        logger.warning(
                            f"Missing values for persona {idx}, using Polish defaults",
                            extra={"project_id": str(project_id), "index": idx},
                        )

                    interests = _fallback_polish_list(personality.get("interests"), POLISH_INTERESTS)
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

                    # Dodaj orchestration reasoning do rag_context_details (jeśli istnieje)
                    if idx in persona_group_mapping:
                        mapping_entry = persona_group_mapping[idx]
                        segment_name_meta = mapping_entry.get("segment_name")
                        segment_id_meta = mapping_entry.get("segment_id")
                        segment_description_meta = mapping_entry.get("segment_description")
                        segment_context_meta = mapping_entry.get("segment_social_context")

                        rag_context_details["orchestration_reasoning"] = {
                            "brief": mapping_entry["brief"],
                            "graph_insights": mapping_entry["graph_insights"],
                            "allocation_reasoning": mapping_entry["allocation_reasoning"],
                            "demographics": mapping_entry["demographics"],
                            "segment_characteristics": mapping_entry["segment_characteristics"],
                            "overall_context": allocation_plan.overall_context if allocation_plan else None,
                            "segment_name": segment_name_meta,
                            "segment_id": segment_id_meta,
                            "segment_description": segment_description_meta,
                            "segment_social_context": segment_context_meta,
                        }

                        if segment_name_meta and "segment_name" not in rag_context_details:
                            rag_context_details["segment_name"] = segment_name_meta
                        if segment_id_meta and "segment_id" not in rag_context_details:
                            rag_context_details["segment_id"] = segment_id_meta
                        if segment_description_meta and "segment_description" not in rag_context_details:
                            rag_context_details["segment_description"] = segment_description_meta
                        if segment_context_meta and "segment_social_context" not in rag_context_details:
                            rag_context_details["segment_social_context"] = segment_context_meta
                        if mapping_entry["segment_characteristics"] and "segment_characteristics" not in rag_context_details:
                            rag_context_details["segment_characteristics"] = mapping_entry["segment_characteristics"]

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

                    if idx in persona_group_mapping:
                        mapping_entry = persona_group_mapping[idx]
                        if mapping_entry.get("segment_id"):
                            persona_payload["segment_id"] = mapping_entry["segment_id"]
                        if mapping_entry.get("segment_name"):
                            persona_payload["segment_name"] = mapping_entry["segment_name"]

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
                                orchestration_info = rag_context_details.get("orchestration_reasoning")
                                if isinstance(orchestration_info, dict):
                                    orchestration_info["segment_name"] = catchy_segment_name
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
                        expected_gender = _polishify_gender(orch_demo.get("gender", ""))
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
                            norm_expected_ed = _polishify_education(expected_education)
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
        logger.error(f"CRITICAL ERROR in persona generation task", exc_info=e)
