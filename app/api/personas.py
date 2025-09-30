from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
import json

from app.db import get_db
from app.models import Project, Persona
from app.schemas.persona import PersonaResponse, PersonaGenerateRequest
from app.services.persona_generator_langchain import PersonaGeneratorLangChain, DemographicDistribution

router = APIRouter()


@router.post("/projects/{project_id}/personas/generate", status_code=202)
async def generate_personas(
    project_id: UUID,
    request: PersonaGenerateRequest,
    background_tasks: BackgroundTasks,
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

    # Schedule background task for persona generation
    background_tasks.add_task(
        _generate_personas_task,
        db,
        project_id,
        request.num_personas,
        request.adversarial_mode,
    )

    return {
        "message": "Persona generation started",
        "project_id": str(project_id),
        "num_personas": request.num_personas,
        "adversarial_mode": request.adversarial_mode,
    }


async def _generate_personas_task(
    db: AsyncSession,
    project_id: UUID,
    num_personas: int,
    adversarial_mode: bool,
):
    """Background task to generate personas"""
    from app.services import AdversarialService

    generator = PersonaGeneratorLangChain()

    # Load project
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one()

    # Create distribution from target demographics
    distribution = DemographicDistribution(
        age_groups=project.target_demographics.get("age_group", {}),
        genders=project.target_demographics.get("gender", {}),
        education_levels=project.target_demographics.get("education_level", {}),
        income_brackets=project.target_demographics.get("income_bracket", {}),
        locations=project.target_demographics.get("location", {}),
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
        for _ in range(num_personas):
            demographic = generator.sample_demographic_profile(distribution)[0]
            psychological = generator.sample_big_five_traits()
            cultural = generator.sample_cultural_dimensions()
            psychological.update(cultural)

            prompt, personality = await generator.generate_persona_personality(
                demographic, psychological
            )

            # Extract age from age group
            age_group = demographic.get("age_group", "25-34")
            if "-" in age_group:
                age_parts = age_group.split("-")
                age = (int(age_parts[0]) + int(age_parts[1])) // 2
            else:
                age = 35

            personas_data.append(
                {
                    "project_id": str(project_id),
                    "age": age,
                    "gender": demographic.get("gender"),
                    "location": demographic.get("location"),
                    "education_level": demographic.get("education_level"),
                    "income_bracket": demographic.get("income_bracket"),
                    "occupation": personality.get("occupation", "N/A"),
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
                    "values": personality.get("values", []),
                    "interests": personality.get("interests", []),
                    "background_story": personality.get("background_story", ""),
                    "personality_prompt": prompt,
                }
            )

    # Save personas to database
    for persona_data in personas_data:
        persona = Persona(**persona_data)
        db.add(persona)

    await db.commit()

    # Validate distribution if not adversarial
    if not adversarial_mode:
        validation = generator.validate_distribution(
            [{"age_group": f"{p['age']}-{p['age']}", "gender": p["gender"],
              "education_level": p["education_level"], "income_bracket": p["income_bracket"],
              "location": p["location"]} for p in personas_data],
            distribution,
        )

        # Update project validation results
        project.chi_square_statistic = {k: v["chi_square_statistic"] for k, v in validation.items() if k != "overall_valid"}
        project.p_values = {k: v["p_value"] for k, v in validation.items() if k != "overall_valid"}
        project.is_statistically_valid = validation["overall_valid"]
        from datetime import datetime
        project.validation_date = datetime.utcnow()

        await db.commit()


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
        .where(Persona.project_id == project_id, Persona.is_active == True)
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
