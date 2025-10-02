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
from app.services.custom_persona_generator import CustomPersonaGenerator
from app.services.local_persona_generator import LocalPersonaSynthesizer
from app.services.local_persona_generator import LocalPersonaSynthesizer as LegacyPersonaGenerator
from app.services.demographic_consistency import get_consistent_occupation, validate_occupation_consistency
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
    # Usunięto 'db: AsyncSession' z argumentów, ponieważ nie jest tu już potrzebny
):
    """
    Schedules a background task to generate synthetic personas for a project.

    This endpoint initiates a non-blocking background job.
    """
    logger.info(
        "Persona generation request received",
        extra={
            "project_id": str(project_id),
            "num_personas": request.num_personas,
            "adversarial_mode": request.adversarial_mode,
        },
    )

    # --- START POPRAWKI ---
    # Usunięto argument 'db' z wywołania add_task
    advanced_payload = (
        request.advanced_options.model_dump(exclude_none=True)
        if request.advanced_options
        else None
    )

    background_tasks.add_task(
        _generate_personas_task,
        project_id,
        request.num_personas,
        request.adversarial_mode,
        advanced_payload,
    )
    # --- KONIEC POPRAWKI ---

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
# --- KONIEC POPRAWKI ---
    """Background task to generate personas"""
    from app.services import AdversarialService

    # --- START POPRAWKI ---
    # Zadanie w tle tworzy własną, niezależną sesję z bazą danych
    async with AsyncSessionLocal() as db:
    # --- KONIEC POPRAWKI ---
        generator = None
        generator_name = ""

        # Logika wyboru generatora
        for candidate, label in (
            (PreferredPersonaGenerator, "langchain"),
            (LegacyPersonaGenerator, "legacy"),
        ):
            try:
                generator = candidate()
                generator_name = label
                logger.info("Using %s persona generator", label, extra={"project_id": str(project_id)})
                break
            except Exception as exc:
                logger.warning("Persona generator %s unavailable, falling back", label, exc_info=exc, extra={"project_id": str(project_id)})

        if generator is None:
            generator = LocalPersonaSynthesizer()
            generator_name = "local"
            logger.info("Using local persona synthesizer", extra={"project_id": str(project_id)})

        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            return

        target_demographics = project.target_demographics or {}

        age_groups = _normalize_distribution(target_demographics.get("age_group", {}), DEFAULT_AGE_GROUPS)
        genders = _normalize_distribution(target_demographics.get("gender", {}), DEFAULT_GENDERS)
        education_levels = _normalize_distribution(target_demographics.get("education_level", {}), DEFAULT_EDUCATION_LEVELS)
        income_brackets = _normalize_distribution(target_demographics.get("income_bracket", {}), DEFAULT_INCOME_BRACKETS)
        locations = _normalize_distribution(target_demographics.get("location", {}), DEFAULT_LOCATIONS)

        age_min = None
        age_max = None
        required_values: List[str] = []
        excluded_values: List[str] = []
        required_interests: List[str] = []
        excluded_interests: List[str] = []
        preferred_industries: List[str] = []

        if advanced_options:
            age_focus = advanced_options.get('age_focus')
            age_min = advanced_options.get('age_min')
            age_max = advanced_options.get('age_max')

            custom_age = _coerce_distribution(advanced_options.get('custom_age_groups'))
            if custom_age:
                age_groups = custom_age
            age_groups = _apply_age_preferences(age_groups, age_focus, age_min, age_max)

            custom_gender = _coerce_distribution(advanced_options.get('gender_weights'))
            if custom_gender:
                genders = custom_gender
            genders = _apply_gender_preferences(genders, advanced_options.get('gender_balance'))

            custom_locations = _coerce_distribution(advanced_options.get('location_weights'))
            if custom_locations:
                locations = custom_locations
            else:
                locations = _build_location_distribution(locations, advanced_options)

            required_values = list(dict.fromkeys(advanced_options.get('required_values', [])))
            excluded_values = list(dict.fromkeys(advanced_options.get('excluded_values', [])))
            required_interests = list(dict.fromkeys(advanced_options.get('required_interests', [])))
            excluded_interests = list(dict.fromkeys(advanced_options.get('excluded_interests', [])))
            preferred_industries = list(dict.fromkeys(advanced_options.get('industries', [])))

            custom_education = _coerce_distribution(advanced_options.get('education_weights'))
            if custom_education:
                education_levels = custom_education

            custom_income = _coerce_distribution(advanced_options.get('income_weights'))
            if custom_income:
                income_brackets = custom_income

        distribution = DemographicDistribution(
            age_groups=age_groups,
            genders=genders,
            education_levels=education_levels,
            income_brackets=income_brackets,
            locations=locations,
        )

        personas_data = []

        # Extract personality_skew if provided
        personality_skew = None
        if advanced_options:
            personality_skew = advanced_options.get('personality_skew')

        if adversarial_mode:
            adversarial_service = AdversarialService()
            personas_data = await adversarial_service.generate_adversarial_personas(
                db, str(project_id), project.description or "General market research", distribution, num_personas
            )
        else:
            demographic_profiles = [
                generator.sample_demographic_profile(distribution)[0]
                for _ in range(num_personas)
            ]
            psychological_profiles = [
                {**generator.sample_big_five_traits(personality_skew), **generator.sample_cultural_dimensions()}
                for _ in range(num_personas)
            ]

            tasks = []
            for demo, psych in zip(demographic_profiles, psychological_profiles):
                tasks.append(generator.generate_persona_personality(demo, psych))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                demographic = demographic_profiles[i]
                psychological = psychological_profiles[i]

                if isinstance(result, Exception):
                    logger.warning(
                        "Persona personality generation failed; using offline template",
                        exc_info=result,
                        extra={"project_id": str(project_id), "generator": generator_name},
                    )
                    local_generator = LocalPersonaSynthesizer()
                    prompt, personality = await local_generator.generate_persona_personality(demographic, psychological)
                else:
                    prompt, personality = result

                age_group = demographic.get("age_group", "25-34")
                if "-" in age_group:
                    start, end = age_group.split("-", maxsplit=1)
                    try:
                        age = random.randint(int(start), int(end))
                    except ValueError:
                        age = random.randint(25, 44)
                elif age_group.endswith("+"):
                    base = age_group.rstrip("+")
                    try:
                        lower = int(base)
                        age = random.randint(lower, lower + 25)
                    except ValueError:
                        age = random.randint(45, 70)
                else:
                    age = random.randint(25, 44)

                if isinstance(age_min, int):
                    age = max(age, age_min)
                if isinstance(age_max, int):
                    age = min(age, age_max)

                fallback_values = random.sample(DEFAULT_VALUES, k=min(5, len(DEFAULT_VALUES)))
                fallback_interests = random.sample(DEFAULT_INTERESTS, k=min(5, len(DEFAULT_INTERESTS)))

                llm_occupation = personality.get("occupation")
                if llm_occupation:
                    consistency = validate_occupation_consistency(
                        llm_occupation, demographic.get("education_level"), demographic.get("income_bracket"), age
                    )
                    if not all(consistency.values()):
                        logger.warning("LLM occupation inconsistent, replacing", extra={"occupation": llm_occupation, "consistency": consistency, "age": age})
                        occupation = get_consistent_occupation(
                            demographic.get("education_level"), demographic.get("income_bracket"), age, DEFAULT_OCCUPATIONS
                        )
                    else:
                        occupation = llm_occupation
                else:
                    occupation = get_consistent_occupation(
                        demographic.get("education_level"), demographic.get("income_bracket"), age, DEFAULT_OCCUPATIONS
                    )

                if preferred_industries:
                    selected_industry = random.choice(preferred_industries)
                    if not occupation or occupation in DEFAULT_OCCUPATIONS:
                        occupation = f"{selected_industry} Specialist"
                    if not personality.get("persona_title"):
                        personality["persona_title"] = f"{selected_industry} Lead"

                background_story = personality.get("background_story", "")
                background_story = _ensure_story_alignment(background_story, age, occupation)

                inferred_name = _infer_full_name(background_story)
                full_name = (personality.get("full_name") or inferred_name or _fallback_full_name(demographic.get("gender"), age)).strip()

                persona_title = personality.get("persona_title") or occupation
                if persona_title:
                    persona_title = persona_title.strip()

                headline = personality.get("headline")
                if not headline:
                    headline = _compose_headline(full_name, persona_title, occupation, demographic.get("location"))
                if headline:
                    headline = headline.strip()[:255]

                values = personality.get("values") or fallback_values
                values = [value for value in values if value not in excluded_values]
                if required_values:
                    values = values + [val for val in required_values if val not in values]
                if not values:
                    values = fallback_values
                values = list(dict.fromkeys(values))

                interests = personality.get("interests") or fallback_interests
                interests = [interest for interest in interests if interest not in excluded_interests]
                if required_interests:
                    interests = interests + [intr for intr in required_interests if intr not in interests]
                if not interests:
                    interests = fallback_interests
                interests = list(dict.fromkeys(interests))

                personas_data.append(
                    {
                        "project_id": str(project_id),
                        "age": age,
                        "gender": demographic.get("gender"),
                        "location": demographic.get("location"),
                        "education_level": demographic.get("education_level"),
                        "income_bracket": demographic.get("income_bracket"),
                        "occupation": occupation,
                        "full_name": full_name,
                        "persona_title": persona_title,
                        "headline": headline,
                        "openness": psychological.get("openness"),
                        "conscientiousness": psychological.get("conscientiousness"),
                        "extraversion": psychological.get("extraversion"),
                        "agreeableness": psychological.get("agreeableness"),
                        "neuroticism": psychological.get("neuroticism"),
                        "power_distance": psychological.get("power_distance"),
                        "individualism": psychological.get("individualism"),
                        "masculinity": psychological.get("masculinity"),
                        "uncertainty_avoidance": psychological.get("uncertainty_avoidance"),
                        "long_term_orientation": psychological.get("long_term_orientation"),
                        "indulgence": psychological.get("indulgence"),
                        "values": values,
                        "interests": interests,
                        "background_story": background_story,
                        "personality_prompt": prompt,
                    }
                )

        validator = PersonaValidator(similarity_threshold=0.75)
        validation_results = validator.validate_personas(personas_data)

        if not validation_results["is_valid"]:
            logger.warning(
                "Persona validation found issues",
                extra={
                    "project_id": str(project_id),
                    "diversity_score": validation_results["diversity"]["diversity_score"],
                    "duplicates": len(validation_results["uniqueness"]["duplicate_pairs"]),
                    "recommendations": validation_results["recommendations"],
                }
            )

        for persona_data in personas_data:
            persona = Persona(**persona_data)
            db.add(persona)
        await db.commit()

        if not adversarial_mode and personas_data and hasattr(generator, "validate_distribution"):
            try:
                validation = generator.validate_distribution(
                    demographic_profiles,
                    distribution,
                )

                project.chi_square_statistic = {
                    k: v["chi_square_statistic"] for k, v in validation.items() if k != "overall_valid"
                }
                project.p_values = {
                    k: v["p_value"] for k, v in validation.items() if k != "overall_valid"
                }
                project.is_statistically_valid = validation["overall_valid"]

                from datetime import datetime, timezone
                project.validation_date = datetime.now(timezone.utc)
                await db.commit()
            except Exception as exc:
                logger.warning("Validation step failed", exc_info=exc, extra={"project_id": str(project_id)})

        logger.info(
            "Persona generation completed",
            extra={"project_id": str(project_id), "num_personas": len(personas_data), "generator": generator_name, "adversarial": adversarial_mode},
        )


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
