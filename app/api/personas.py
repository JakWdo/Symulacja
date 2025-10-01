import asyncio
import logging
import random
from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal, get_db
from app.models import Project, Persona
from app.schemas.persona import PersonaResponse, PersonaGenerateRequest
from app.services import DemographicDistribution, PersonaGenerator
from app.services.persona_generator_langchain import PersonaGeneratorLangChain as PreferredPersonaGenerator
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


@router.post("/projects/{project_id}/personas/generate", status_code=202)
async def generate_personas(
    project_id: UUID,
    request: PersonaGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate synthetic personas for a project"""

    # Check project exists
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(
            _generate_personas_task(
                project_id,
                request.num_personas,
                request.adversarial_mode,
            )
        )
        logger.info(
            "Scheduled persona generation",
            extra={
                "project_id": str(project_id),
                "num_personas": request.num_personas,
                "adversarial_mode": request.adversarial_mode,
            },
        )
    except RuntimeError as exc:  # pragma: no cover - defensive fallback
        logger.exception("Failed to schedule persona generation", exc_info=exc)
        raise HTTPException(
            status_code=500,
            detail="Unable to schedule persona generation task.",
        ) from exc

    return {
        "message": "Persona generation started",
        "project_id": str(project_id),
        "num_personas": request.num_personas,
        "adversarial_mode": request.adversarial_mode,
    }
async def _generate_personas_task(
    project_id: UUID,
    num_personas: int,
    adversarial_mode: bool,
):
    """Background task to generate personas"""
    from app.services import AdversarialService

    async with AsyncSessionLocal() as db:
        generator = None
        generator_name = ""

        for candidate, label in (
            (PreferredPersonaGenerator, "langchain"),
            (LegacyPersonaGenerator, "legacy"),
        ):
            try:
                generator = candidate()
                generator_name = label
                logger.info(
                    "Using %s persona generator",
                    label,
                    extra={"project_id": str(project_id)},
                )
                break
            except Exception as exc:
                logger.warning(
                    "Persona generator %s unavailable, falling back",
                    label,
                    exc_info=exc,
                    extra={"project_id": str(project_id)},
                )

        if generator is None:
            generator = LocalPersonaSynthesizer()
            generator_name = "local"
            logger.info(
                "Using local persona synthesizer",
                extra={"project_id": str(project_id)},
            )

        # Load project
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            return

        target_demographics = project.target_demographics or {}

        # Create distribution from target demographics with sensible fallbacks
        distribution = DemographicDistribution(
            age_groups=_normalize_distribution(
                target_demographics.get("age_group", {}), DEFAULT_AGE_GROUPS
            ),
            genders=_normalize_distribution(
                target_demographics.get("gender", {}), DEFAULT_GENDERS
            ),
            education_levels=_normalize_distribution(
                target_demographics.get("education_level", {}),
                DEFAULT_EDUCATION_LEVELS,
            ),
            income_brackets=_normalize_distribution(
                target_demographics.get("income_bracket", {}),
                DEFAULT_INCOME_BRACKETS,
            ),
            locations=_normalize_distribution(
                target_demographics.get("location", {}), DEFAULT_LOCATIONS
            ),
        )

        if adversarial_mode:
            # Use adversarial service
            adversarial_service = AdversarialService()
            personas_data = await adversarial_service.generate_adversarial_personas(
                db,
                str(project_id),
                project.description or "General market research",
                distribution,
                num_personas,
            )
        else:
            # Generate normal personas
            personas_data = []
            validation_samples = []
            for _ in range(num_personas):
                try:
                    demographic = generator.sample_demographic_profile(distribution)[0]
                except Exception as exc:
                    logger.exception(
                        "Demographic sampling failed, using local fallback",
                        exc_info=exc,
                        extra={"project_id": str(project_id)},
                    )
                    demographic = LocalPersonaSynthesizer().sample_demographic_profile(
                        distribution
                    )[0]

                psychological = generator.sample_big_five_traits()
                cultural = generator.sample_cultural_dimensions()
                psychological.update(cultural)

                validation_samples.append(
                    {
                        "age_group": demographic.get("age_group"),
                        "gender": demographic.get("gender"),
                        "education_level": demographic.get("education_level"),
                        "income_bracket": demographic.get("income_bracket"),
                        "location": demographic.get("location"),
                    }
                )

                try:
                    prompt, personality = await generator.generate_persona_personality(
                        demographic, psychological
                    )
                except Exception as exc:
                    logger.warning(
                        "Persona personality generation failed; using offline template",
                        exc_info=exc,
                        extra={
                            "project_id": str(project_id),
                            "generator": generator_name,
                        },
                    )
                    local_generator = LocalPersonaSynthesizer()
                    prompt, personality = await local_generator.generate_persona_personality(
                        demographic, psychological
                    )

                # Extract age from age group
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

                fallback_values = random.sample(DEFAULT_VALUES, k=min(5, len(DEFAULT_VALUES)))
                fallback_interests = random.sample(
                    DEFAULT_INTERESTS, k=min(5, len(DEFAULT_INTERESTS))
                )

                # Get occupation from LLM or use demographic-consistent fallback
                llm_occupation = personality.get("occupation")
                if llm_occupation:
                    # Validate LLM-generated occupation
                    consistency = validate_occupation_consistency(
                        llm_occupation,
                        demographic.get("education_level"),
                        demographic.get("income_bracket"),
                        age
                    )
                    # If not consistent, get a better one
                    if not all(consistency.values()):
                        logger.warning(
                            "LLM occupation inconsistent, replacing",
                            extra={
                                "occupation": llm_occupation,
                                "consistency": consistency,
                                "age": age,
                            }
                        )
                        occupation = get_consistent_occupation(
                            demographic.get("education_level"),
                            demographic.get("income_bracket"),
                            age,
                            DEFAULT_OCCUPATIONS
                        )
                    else:
                        occupation = llm_occupation
                else:
                    # No occupation from LLM, generate consistent one
                    occupation = get_consistent_occupation(
                        demographic.get("education_level"),
                        demographic.get("income_bracket"),
                        age,
                        DEFAULT_OCCUPATIONS
                    )

                personas_data.append(
                    {
                        "project_id": str(project_id),
                        "age": age,
                        "gender": demographic.get("gender"),
                        "location": demographic.get("location"),
                        "education_level": demographic.get("education_level"),
                        "income_bracket": demographic.get("income_bracket"),
                        "occupation": occupation,
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
                        "values": personality.get("values") or fallback_values,
                        "interests": personality.get("interests") or fallback_interests,
                        "background_story": personality.get("background_story", ""),
                        "personality_prompt": prompt,
                    }
                )

        # Validate persona quality before saving
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

        # Save personas to database
        for persona_data in personas_data:
            persona = Persona(**persona_data)
            db.add(persona)

        await db.commit()

        # Validate distribution if not adversarial
        if (
            not adversarial_mode
            and personas_data
            and hasattr(generator, "validate_distribution")
        ):
            try:
                validation = generator.validate_distribution(
                    validation_samples,
                    distribution,
                )

                project.chi_square_statistic = {
                    k: v["chi_square_statistic"]
                    for k, v in validation.items()
                    if k != "overall_valid"
                }
                project.p_values = {
                    k: v["p_value"]
                    for k, v in validation.items()
                    if k != "overall_valid"
                }
                project.is_statistically_valid = validation["overall_valid"]

                from datetime import datetime, timezone

                project.validation_date = datetime.now(timezone.utc)

                await db.commit()
            except Exception as exc:
                logger.warning(
                    "Validation step failed",
                    exc_info=exc,
                    extra={"project_id": str(project_id)},
                )

        logger.info(
            "Persona generation completed",
            extra={
                "project_id": str(project_id),
                "num_personas": len(personas_data),
                "generator": generator_name,
                "adversarial": adversarial_mode,
            },
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
