import asyncio
import json
import logging
import random
import re
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal, get_db
from app.models import Project, Persona
from app.schemas.persona import (
    PersonaResponse,
    PersonaGenerateRequest,
)
from app.services import DemographicDistribution, PersonaGenerator
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
)

router = APIRouter()

logger = logging.getLogger(__name__)


_NAME_FROM_STORY_PATTERN = re.compile(
    r"^(?P<name>[A-Z][a-z]+(?: [A-Z][a-z]+){0,2})\s+is\s+(?:an|a)\s",
)
_AGE_IN_STORY_PATTERN = re.compile(r"(?P<age>\d{1,3})-year-old")


def _infer_full_name(background_story: Optional[str]) -> Optional[str]:
    if not background_story:
        return None
    match = _NAME_FROM_STORY_PATTERN.match(background_story.strip())
    if match:
        return match.group('name')
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
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db), # Ten argument jest potrzebny do weryfikacji projektu
):
    """
    Schedules a background task to generate synthetic personas for a project.
    """
    # Weryfikacja, czy projekt istnieje
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    logger.info(
        "Persona generation request received",
        extra={
            "project_id": str(project_id),
            "num_personas": request.num_personas,
            "adversarial_mode": request.adversarial_mode,
        },
    )

    advanced_payload = (
        request.advanced_options.model_dump(exclude_none=True)
        if request.advanced_options
        else None
    )
    
    # POPRAWKA: Usunięto argument 'db' z wywołania zadania w tle
    background_tasks.add_task(
        _generate_personas_task,
        project_id,
        request.num_personas,
        request.adversarial_mode,
        advanced_payload,
    )

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
):
    """Asynchroniczne zadanie w tle do generowania person z kontrolą współbieżności."""
    # POPRAWKA: Zadanie w tle tworzy własną, niezależną sesję z bazą danych
    async with AsyncSessionLocal() as db:
        # Użyj PersonaGeneratorLangChain (główny generator)
        generator = PreferredPersonaGenerator()
        generator_name = "langchain"
        logger.info("Using %s persona generator", generator_name, extra={"project_id": str(project_id)})

        project = await db.get(Project, project_id)
        if not project:
            logger.error("Project not found in background task.", extra={"project_id": str(project_id)})
            return
            
        target_demographics = project.target_demographics or {}
        distribution = DemographicDistribution(
            age_groups=_normalize_distribution(target_demographics.get("age_group", {}), DEFAULT_AGE_GROUPS),
            genders=_normalize_distribution(target_demographics.get("gender", {}), DEFAULT_GENDERS),
            education_levels=_normalize_distribution(target_demographics.get("education_level", {}), DEFAULT_EDUCATION_LEVELS),
            income_brackets=_normalize_distribution(target_demographics.get("income_bracket", {}), DEFAULT_INCOME_BRACKETS),
            locations=_normalize_distribution(target_demographics.get("location", {}), DEFAULT_LOCATIONS),
        )

        # POPRAWKA WYDAJNOŚCI: Użycie semafora do kontrolowanej współbieżności
        concurrency_limit = 15
        semaphore = asyncio.Semaphore(concurrency_limit)
        demographic_profiles = [generator.sample_demographic_profile(distribution)[0] for _ in range(num_personas)]
        psychological_profiles = [{**generator.sample_big_five_traits(), **generator.sample_cultural_dimensions()} for _ in range(num_personas)]

        async def create_single_persona(demo_profile, psych_profile):
            async with semaphore:
                return await generator.generate_persona_personality(demo_profile, psych_profile, advanced_options)

        tasks = [create_single_persona(demo, psych) for demo, psych in zip(demographic_profiles, psychological_profiles)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        personas_data = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Failed to process persona generation result.", exc_info=result)
                continue

            prompt, personality_json = result

            # Robust JSON parsing with fallback
            personality = {}
            try:
                if isinstance(personality_json, str):
                    # Strip markdown code blocks if present
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
                        extra={"project_id": str(project_id), "index": i}
                    )
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(
                    f"Failed to parse personality JSON for persona {i}: {str(e)[:200]}",
                    extra={
                        "project_id": str(project_id),
                        "index": i,
                        "raw_json": str(personality_json)[:500],
                    }
                )
                personality = {}

            demographic = demographic_profiles[i]
            psychological = psychological_profiles[i]

            # Parse age from age_group
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

            # Smart fallbacks for missing fields
            full_name = personality.get("full_name")
            if not full_name or full_name == "N/A":
                # Try to infer from background_story
                inferred_name = _infer_full_name(personality.get("background_story"))
                full_name = inferred_name or _fallback_full_name(demographic.get("gender"), age)
                logger.warning(
                    f"Missing full_name for persona {i}, using fallback: {full_name}",
                    extra={"project_id": str(project_id), "index": i}
                )

            persona_title = personality.get("persona_title")
            if not persona_title or persona_title == "N/A":
                persona_title = occupation or f"{demographic.get('gender', 'Person')} {age}"
                logger.warning(
                    f"Missing persona_title for persona {i}, using fallback: {persona_title}",
                    extra={"project_id": str(project_id), "index": i}
                )

            headline = personality.get("headline")
            if not headline or headline == "N/A":
                headline = _compose_headline(
                    full_name, persona_title, occupation, demographic.get("location")
                )
                logger.warning(
                    f"Missing headline for persona {i}, using generated: {headline}",
                    extra={"project_id": str(project_id), "index": i}
                )

            background_story = personality.get("background_story", "")
            if not background_story:
                logger.warning(
                    f"Missing background_story for persona {i}",
                    extra={"project_id": str(project_id), "index": i}
                )

            values = personality.get("values", [])
            if not values:
                values = random.sample(DEFAULT_VALUES, k=min(5, len(DEFAULT_VALUES)))
                logger.warning(
                    f"Missing values for persona {i}, using defaults",
                    extra={"project_id": str(project_id), "index": i}
                )

            interests = personality.get("interests", [])
            if not interests:
                interests = random.sample(DEFAULT_INTERESTS, k=min(5, len(DEFAULT_INTERESTS)))
                logger.warning(
                    f"Missing interests for persona {i}, using defaults",
                    extra={"project_id": str(project_id), "index": i}
                )

            personas_data.append({
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
                **psychological
            })

        # Logika walidacji i zapisu do bazy (bez zmian)
        validator = PersonaValidator()
        validation_results = validator.validate_personas(personas_data)
        if not validation_results["is_valid"]:
            logger.warning("Persona validation found issues.", extra=validation_results)

        db.add_all([Persona(**data) for data in personas_data])
        await db.commit()

        if not adversarial_mode and hasattr(generator, "validate_distribution"):
            try:
                validation = generator.validate_distribution(demographic_profiles, distribution)
                project.is_statistically_valid = validation.get("overall_valid", False)
                project.chi_square_statistic = {k: v.get("chi_square_statistic") for k, v in validation.items() if k != "overall_valid"}
                project.p_values = {k: v.get("p_value") for k, v in validation.items() if k != "overall_valid"}
                await db.commit()
            except Exception as e:
                logger.error("Statistical validation failed.", exc_info=e)

        logger.info("Persona generation task completed.", extra={"project_id": str(project_id), "count": len(personas_data)})


@router.get("/projects/{project_id}/personas", response_model=List[PersonaResponse])
async def list_personas(
    project_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List personas for a project"""
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
):
    """Get a specific persona"""
    result = await db.execute(
        select(Persona).where(Persona.id == persona_id)
    )
    persona = result.scalar_one_or_none()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    return persona


@router.delete("/personas/{persona_id}", status_code=204)
async def delete_persona(
    persona_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a persona"""
    result = await db.execute(
        select(Persona).where(Persona.id == persona_id)
    )
    persona = result.scalar_one_or_none()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Soft delete
    persona.is_active = False
    await db.commit()

    return None
