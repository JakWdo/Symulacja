"""
API Endpoints - Zarządzanie Personami

Endpointy do generowania i zarządzania syntetycznymi personami dla badań rynkowych.

Główne funkcjonalności:
- POST /projects/{project_id}/personas/generate - generuje persony z AI (async background task)
- GET /projects/{project_id}/personas - pobiera wszystkie persony projektu
- GET /personas/{persona_id} - pobiera szczegóły pojedynczej persony
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
from functools import lru_cache
import json
import logging
import random
import re
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID
from functools import lru_cache

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal, get_db
from app.models import Project, Persona, User
from app.api.dependencies import get_current_user, get_project_for_user, get_persona_for_user
from app.schemas.persona import (
    PersonaResponse,
    PersonaGenerateRequest,
)
from app.services import DemographicDistribution
from app.services.persona_generator_langchain import PersonaGeneratorLangChain as PreferredPersonaGenerator
from app.services.persona_validator import PersonaValidator
from app.core.constants import (
    DEFAULT_AGE_GROUPS,
    DEFAULT_GENDERS,
    DEFAULT_EDUCATION_LEVELS,
    DEFAULT_INCOME_BRACKETS,
    DEFAULT_LOCATIONS,
    DEFAULT_OCCUPATIONS,
    DEFAULT_VALUES,
    DEFAULT_INTERESTS,
    # Polskie stałe (preferowane jako fallback)
    POLISH_LOCATIONS,
    POLISH_INCOME_BRACKETS,
    POLISH_EDUCATION_LEVELS,
)

router = APIRouter()

logger = logging.getLogger(__name__)

# Śledź uruchomione zadania aby zapobiec garbage collection
_running_tasks = set()


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


_NAME_FROM_STORY_PATTERN = re.compile(
    r"^(?P<name>[A-Z][a-z]+(?: [A-Z][a-z]+){0,2})\s+is\s+(?:an|a)\s",
)
_AGE_IN_STORY_PATTERN = re.compile(r"(?P<age>\d{1,3})-year-old")
# Wzorce do ekstrakcji wieku z polskiego tekstu
_POLISH_AGE_PATTERNS = [
    re.compile(r"(?:ma|mam)\s+(?P<age>\d{1,2})\s+lat", re.IGNORECASE),  # "ma 32 lata"
    re.compile(r"(?P<age>\d{1,2})-letni[aey]?", re.IGNORECASE),  # "32-letnia"
    re.compile(r"(?P<age>\d{1,2})\s+lat", re.IGNORECASE),  # "32 lat"
]


def _infer_full_name(background_story: Optional[str]) -> Optional[str]:
    if not background_story:
        return None
    match = _NAME_FROM_STORY_PATTERN.match(background_story.strip())
    if match:
        return match.group('name')
    return None


def _extract_age_from_story(background_story: Optional[str]) -> Optional[int]:
    """
    Ekstraktuj wiek z background_story (wspiera polski i angielski tekst)

    Args:
        background_story: Historia życiowa persony

    Returns:
        Wyekstraktowany wiek lub None jeśli nie znaleziono
    """
    if not background_story:
        return None

    # Spróbuj angielski wzorzec "32-year-old"
    match = _AGE_IN_STORY_PATTERN.search(background_story)
    if match:
        try:
            return int(match.group('age'))
        except (ValueError, AttributeError):
            pass

    # Spróbuj polskie wzorce
    for pattern in _POLISH_AGE_PATTERNS:
        match = pattern.search(background_story)
        if match:
            try:
                age = int(match.group('age'))
                if 10 <= age <= 100:  # Sanity check
                    return age
            except (ValueError, AttributeError):
                continue

    return None


def _fallback_full_name(gender: Optional[str], age: int) -> str:
    gender_label = (gender or "Persona").split()[0].capitalize()
    return f"{gender_label} {age}"


def _compose_headline(
    full_name: str,
    persona_title: Optional[str],
    occupation: Optional[str],
    location: Optional[str],
) -> str:
    primary_role = persona_title or occupation
    name_root = full_name.split()[0]
    if primary_role and location:
        return f"{primary_role} based in {location}"
    if primary_role:
        return primary_role
    if location:
        return f"{name_root} from {location}"
    return f"{name_root}'s persona profile"


def _get_consistent_occupation(
    education_level: Optional[str],
    income_bracket: Optional[str],
    age: int,
    occupations_list: List[str]
) -> str:
    """Prosta wersja get_consistent_occupation - wybiera losowy zawód z listy"""
    if not occupations_list:
        return "Professional"
    return random.choice(occupations_list)


def _ensure_story_alignment(
    story: Optional[str],
    age: int,
    occupation: Optional[str],
) -> Optional[str]:
    if not story:
        return story
    text = story.strip()
    match = _AGE_IN_STORY_PATTERN.search(text)
    if match and match.group('age') != str(age):
        text = _AGE_IN_STORY_PATTERN.sub(f"{age}-year-old", text, count=1)
    return text


def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(value for value in weights.values() if value > 0)
    if total <= 0:
        return weights
    return {key: value / total for key, value in weights.items() if value > 0}


def _coerce_distribution(raw: Optional[Dict[str, Any]]) -> Optional[Dict[str, float]]:
    if not raw:
        return None
    cleaned: Dict[str, float] = {}
    for key, value in raw.items():
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if numeric > 0:
            cleaned[str(key)] = numeric
    return _normalize_weights(cleaned) if cleaned else None


def _age_group_bounds(label: str) -> Tuple[int, Optional[int]]:
    if '-' in label:
        start, end = label.split('-', maxsplit=1)
        try:
            return int(start), int(end)
        except ValueError:
            return 0, None
    if label.endswith('+'):
        try:
            base = int(label.rstrip('+'))
            return base, None
        except ValueError:
            return 0, None
    try:
        value = int(label)
        return value, value
    except ValueError:
        return 0, None


def _age_group_overlaps(label: str, min_age: Optional[int], max_age: Optional[int]) -> bool:
    group_min, group_max = _age_group_bounds(label)
    if min_age is not None and group_max is not None and group_max < min_age:
        return False
    if max_age is not None and group_min is not None and group_min > max_age:
        return False
    return True


def _apply_age_preferences(
    age_groups: Dict[str, float],
    focus: Optional[str],
    min_age: Optional[int],
    max_age: Optional[int],
) -> Dict[str, float]:
    adjusted = {
        label: weight
        for label, weight in age_groups.items()
        if _age_group_overlaps(label, min_age, max_age)
    }
    if not adjusted:
        adjusted = dict(age_groups)

    if focus == 'young_adults':
        for label in adjusted:
            lower, upper = _age_group_bounds(label)
            upper_value = upper if upper is not None else lower + 5
            if upper_value <= 35:
                adjusted[label] *= 1.8
            else:
                adjusted[label] *= 0.6
    elif focus == 'experienced_leaders':
        for label in adjusted:
            lower, _ = _age_group_bounds(label)
            if lower >= 35:
                adjusted[label] *= 1.8
            else:
                adjusted[label] *= 0.6

    normalized = _normalize_weights(adjusted)
    return normalized if normalized else dict(age_groups)


def _apply_gender_preferences(genders: Dict[str, float], balance: Optional[str]) -> Dict[str, float]:
    if balance == 'female_skew':
        return _normalize_weights({
            'female': 0.65,
            'male': 0.3,
            'non-binary': 0.05,
        })
    if balance == 'male_skew':
        return _normalize_weights({
            'male': 0.65,
            'female': 0.3,
            'non-binary': 0.05,
        })
    return genders


def _build_location_distribution(
    base_locations: Dict[str, float],
    advanced_options: Optional[Dict[str, Any]],
) -> Dict[str, float]:
    if not advanced_options:
        return base_locations

    cities = advanced_options.get('target_cities') or []
    countries = advanced_options.get('target_countries') or []

    if cities:
        city_weights = {city: 1 / len(cities) for city in cities}
        return _normalize_weights(city_weights)

    if countries:
        labels = [f"{country} - Urban hub" for country in countries]
        return _normalize_weights({label: 1 / len(labels) for label in labels})

    urbanicity = advanced_options.get('urbanicity')
    if urbanicity == 'urban':
        return base_locations
    if urbanicity == 'suburban':
        return _normalize_weights({
            'Suburban Midwest, USA': 0.25,
            'Suburban Northeast, USA': 0.25,
            'Sunbelt Suburb, USA': 0.2,
            'Other': 0.3,
        })
    if urbanicity == 'rural':
        return _normalize_weights({
            'Rural Midwest, USA': 0.35,
            'Rural South, USA': 0.25,
            'Mountain Town, USA': 0.2,
            'Other Rural Area': 0.2,
        })

    return base_locations

def _normalize_distribution(
    distribution: Dict[str, float], fallback: Dict[str, float]
) -> Dict[str, float]:
    """Normalize distribution to sum to 1.0, or use fallback if invalid."""
    if not distribution:
        return fallback
    total = sum(distribution.values())
    if total <= 0:
        return fallback
    return {key: value / total for key, value in distribution.items()}


@router.post(
    "/projects/{project_id}/personas/generate",
    status_code=202,
    summary="Start persona generation job",
)
async def generate_personas(
    project_id: UUID,
    request: PersonaGenerateRequest,
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
            "num_personas": request.num_personas,
            "adversarial_mode": request.adversarial_mode,
        },
    )

    # Przygotuj advanced options (konwertuj None fields)
    advanced_payload = (
        request.advanced_options.model_dump(exclude_none=True)
        if request.advanced_options
        else None
    )

    # Utwórz zadanie asynchroniczne
    logger.info(f"Creating async task for persona generation (project={project_id}, personas={request.num_personas}, use_rag={request.use_rag})")
    task = asyncio.create_task(_generate_personas_task(
        project_id,
        request.num_personas,
        request.adversarial_mode,
        advanced_payload,
        request.use_rag,
    ))

    # Zachowujemy referencję do zadania, aby GC go nie usunął
    _running_tasks.add(task)
    task.add_done_callback(_running_tasks.discard)

    # Zwróć natychmiast (nie czekaj na zakończenie generowania)
    return {
        "message": "Persona generation started in background",
        "project_id": str(project_id),
        "num_personas": request.num_personas,
        "adversarial_mode": request.adversarial_mode,
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

            # Kontrolowana współbieżność pozwala przyspieszyć generowanie bez przeciążania modelu
            logger.info(f"Generating demographic and psychological profiles for {num_personas} personas")
            concurrency_limit = _calculate_concurrency_limit(num_personas, adversarial_mode)
            semaphore = asyncio.Semaphore(concurrency_limit)
            demographic_profiles = [generator.sample_demographic_profile(distribution)[0] for _ in range(num_personas)]
            psychological_profiles = [{**generator.sample_big_five_traits(), **generator.sample_cultural_dimensions()} for _ in range(num_personas)]

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
                    result = await generator.generate_persona_personality(demo_profile, psych_profile, use_rag, advanced_options)
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

                    occupation = _get_consistent_occupation(
                        demographic.get("education_level"),
                        demographic.get("income_bracket"),
                        age,
                        DEFAULT_OCCUPATIONS
                    )

                    # Sprytne wartości domyślne dla brakujących pól
                    full_name = personality.get("full_name")
                    if not full_name or full_name == "N/A":
                        inferred_name = _infer_full_name(personality.get("background_story"))
                        full_name = inferred_name or _fallback_full_name(demographic.get("gender"), age)
                        logger.warning(
                            f"Missing full_name for persona {idx}, using fallback: {full_name}",
                            extra={"project_id": str(project_id), "index": idx}
                        )

                    persona_title = personality.get("persona_title")
                    if not persona_title or persona_title == "N/A":
                        persona_title = occupation or f"{demographic.get('gender', 'Person')} {age}"
                        logger.warning(
                            f"Missing persona_title for persona {idx}, using fallback: {persona_title}",
                            extra={"project_id": str(project_id), "index": idx}
                        )

                    headline = personality.get("headline")
                    if not headline or headline == "N/A":
                        headline = _compose_headline(
                            full_name, persona_title, occupation, demographic.get("location")
                        )
                        logger.warning(
                            f"Missing headline for persona {idx}, using generated: {headline}",
                            extra={"project_id": str(project_id), "index": idx}
                        )

                    background_story = personality.get("background_story", "")
                    if not background_story:
                        logger.warning(
                            f"Missing background_story for persona {idx}",
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
                                if not (min_age <= extracted_age <= max_age):
                                    logger.warning(
                                        f"Age mismatch for persona {idx}: story says {extracted_age}, "
                                        f"but age_group is {age_group_str}. Using story age.",
                                        extra={"project_id": str(project_id), "index": idx}
                                    )
                                # Używaj wieku z opisu jeśli jest dostępny (bardziej spójne)
                                age = extracted_age
                            except ValueError:
                                pass
                        elif "+" in age_group_str:
                            try:
                                min_age = int(age_group_str.replace("+", ""))
                                if extracted_age >= min_age:
                                    age = extracted_age
                            except ValueError:
                                pass
                        else:
                            # Brak przedziału - użyj extracted_age
                            age = extracted_age

                    values = personality.get("values", [])
                    if not values:
                        values = random.sample(DEFAULT_VALUES, k=min(5, len(DEFAULT_VALUES)))
                        logger.warning(
                            f"Missing values for persona {idx}, using defaults",
                            extra={"project_id": str(project_id), "index": idx}
                        )

                    interests = personality.get("interests", [])
                    if not interests:
                        interests = random.sample(DEFAULT_INTERESTS, k=min(5, len(DEFAULT_INTERESTS)))
                        logger.warning(
                            f"Missing interests for persona {idx}, using defaults",
                            extra={"project_id": str(project_id), "index": idx}
                        )

                    # Ekstrakcja RAG citations (jeśli były używane)
                    rag_citations = personality.get("_rag_citations")
                    rag_context_used = bool(rag_citations)

                    persona_payload = {
                        "project_id": project_id,
                        "full_name": full_name,
                        "persona_title": persona_title,
                        "headline": headline,
                        "age": age,
                        "gender": demographic.get("gender"),
                        "location": demographic.get("location"),
                        "education_level": demographic.get("education_level"),
                        "income_bracket": demographic.get("income_bracket"),
                        "occupation": occupation,
                        "background_story": background_story,
                        "values": values,
                        "interests": interests,
                        "personality_prompt": prompt,
                        "rag_context_used": rag_context_used,
                        "rag_citations": rag_citations,
                        **psychological
                    }

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


@router.get("/projects/{project_id}/personas", response_model=List[PersonaResponse])
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
        .where(Persona.project_id == project_id, Persona.is_active.is_(True))
        .offset(skip)
        .limit(limit)
    )
    personas = result.scalars().all()
    return personas


@router.get("/personas/{persona_id}", response_model=PersonaResponse)
async def get_persona(
    persona_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific persona"""
    persona = await get_persona_for_user(persona_id, current_user, db)
    return persona


@router.delete("/personas/{persona_id}", status_code=204)
async def delete_persona(
    persona_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft delete a persona"""
    persona = await get_persona_for_user(persona_id, current_user, db)

    # Miękkie usunięcie rekordu
    persona.is_active = False
    await db.commit()

    return None
