"""
Persona API - Generation Logic

Persona generation endpoint and background task.
This is the heaviest module - contains the POST /generate endpoint and
_generate_personas_task background worker (~780 lines).
"""

import asyncio
import json
import logging
import random
import re
import unicodedata
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, BackgroundTasks, Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal, get_db
from app.models import Project, Persona, User
from app.services.personas.persona_orchestration import PersonaOrchestrationService
from app.api.dependencies import get_current_user, get_project_for_user
from app.schemas.persona import PersonaGenerateRequest
from app.services.personas import (
    PersonaGeneratorLangChain,
    PersonaValidator,
)
from app.services.personas.persona_generator_langchain import DemographicDistribution
from app.services.personas.demographics_formatter import DemographicsFormatter
from app.services.personas.distribution_builder import DistributionBuilder
from app.services.personas.segment_constructor import SegmentConstructor
from config import demographics, features
from .helpers import _get_persona_generator, _calculate_concurrency_limit


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

# Śledź uruchomione zadania aby zapobiec garbage collection
_running_tasks = set()


# ===== HELPER FUNCTIONS (used only in generation task) =====

def _infer_full_name(background_story: str | None) -> str | None:
    """
    Próbuje wyekstraktować pełne imię i nazwisko z background story.

    TODO: Implement proper name extraction logic.
    """
    if not background_story:
        return None

    # Simple regex pattern for Polish names (Imię Nazwisko)
    # This is a placeholder - should be replaced with proper NLP
    pattern = r'\b([A-ZŁŚĆŻŹ][a-złśćżźńęą]+)\s+([A-ZŁŚĆŻŹ][a-złśćżźńęą]+)\b'
    match = re.search(pattern, background_story)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return None


def _fallback_full_name(gender: str | None, age: int) -> str:
    """
    Generates a fallback full name based on gender and age.

    TODO: Implement proper Polish name generator with age-appropriate names.
    """
    # Simple placeholder implementation
    if gender and gender.lower() in ["kobieta", "female"]:
        first_names = ["Anna", "Maria", "Katarzyna", "Małgorzata", "Agnieszka"]
        last_names = ["Kowalska", "Nowak", "Wiśniewska", "Wójcik", "Kowalczyk"]
    else:
        first_names = ["Jan", "Piotr", "Krzysztof", "Andrzej", "Tomasz"]
        last_names = ["Kowalski", "Nowak", "Wiśniewski", "Wójcik", "Kowalczyk"]

    return f"{random.choice(first_names)} {random.choice(last_names)}"


def _extract_age_from_story(background_story: str | None) -> int | None:
    """
    Próbuje wyekstraktować wiek z background story.

    WAŻNE: Zwraca tylko wiek jeśli jest jawnie podany (np. "ma 35 lat").
    NIE ekstraktuje liczb z kontekstu "10 lat doświadczenia" → age=10 (to byłby bug!).

    TODO: Implement proper age extraction with context awareness.
    """
    if not background_story:
        return None

    # Pattern for explicit age mentions: "ma X lat", "jest w wieku X lat", "X-letni/a"
    patterns = [
        r'\bma\s+(\d{1,2})\s+lat',
        r'\bw\s+wieku\s+(\d{1,2})\s+lat',
        r'\b(\d{1,2})-letni',
        r'\b(\d{1,2})-letnia',
    ]

    for pattern in patterns:
        match = re.search(pattern, background_story, re.IGNORECASE)
        if match:
            age = int(match.group(1))
            # Sanity check: age should be between 18-100
            if 18 <= age <= 100:
                return age

    return None


def _get_consistent_occupation(
    education_level: str | None,
    income_bracket: str | None,
    age: int,
    personality: dict[str, Any],
    background_story: str,
) -> str:
    """
    Determines a consistent occupation based on education, income, age, and personality.

    TODO: Implement smart occupation matching logic based on Polish job market.
    """
    # Try to extract occupation from personality first
    occupation = personality.get("occupation")
    if occupation and isinstance(occupation, str) and occupation.strip():
        return occupation.strip()

    # Try to extract from background_story
    # Simple pattern matching (placeholder)
    occupation_patterns = [
        r'pracuje jako\s+([a-złśćżźńęą\s]+)',
        r'jest\s+([a-złśćżźńęą]+)em',
        r'zawód:\s+([a-złśćżźńęą\s]+)',
    ]

    for pattern in occupation_patterns:
        match = re.search(pattern, background_story, re.IGNORECASE)
        if match:
            occ = match.group(1).strip()
            if len(occ) > 3 and len(occ) < 50:
                return occ

    # Fallback based on education level
    if education_level:
        if "wyższe" in education_level.lower():
            occupations = ["Specjalista", "Menedżer", "Inżynier", "Konsultant"]
        elif "średnie" in education_level.lower():
            occupations = ["Technik", "Handlowiec", "Pracownik biurowy"]
        else:
            occupations = ["Pracownik fizyczny", "Sprzedawca", "Operator"]
        return random.choice(occupations)

    return "Pracownik"


def _fallback_polish_list(items: list[str] | None, defaults: list[str]) -> list[str]:
    """
    Returns items if valid, otherwise returns random sample from defaults.

    Args:
        items: List of items from LLM (may be None or empty)
        defaults: Default Polish values (e.g., demographics.poland.values)

    Returns:
        Valid list of items (3-5 items)
    """
    if items and isinstance(items, list) and len(items) > 0:
        # Filter out empty/invalid items
        valid_items = [item.strip() for item in items if isinstance(item, str) and item.strip()]
        if valid_items:
            return valid_items[:5]  # Max 5 items

    # Fallback to random sample from defaults
    if defaults and isinstance(defaults, list):
        sample_size = min(4, len(defaults))
        return random.sample(defaults, sample_size)

    return []


# ===== API ENDPOINT =====

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


# ===== BACKGROUND TASK (WARNING: 780+ lines!) =====

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
            # RE-ENABLED with optimizations (see comments in original code)
            orchestration_enabled = features.orchestration.enabled

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
                        demographics_dict = (
                            group.demographics
                            if isinstance(group.demographics, dict)
                            else dict(group.demographics)
                        )
                        segment_metadata = segment_constructor.build_segment_metadata(
                            demographics_dict,
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
                                    "demographics": demographics_dict,
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
                                last_group.segment_characteristics,
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
                    # Enrich persona generation with orchestration context
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
                        "rag_context_details": rag_context_details,
                        **psychological
                    }

                    # === SET SEGMENT_ID and SEGMENT_NAME ===
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
