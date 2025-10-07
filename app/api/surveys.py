"""
API Endpoints dla Ankiet Syntetycznych (Surveys)

Ten moduł zawiera endpoints do zarządzania ankietami syntetycznymi:
- POST /projects/{id}/surveys - Utworzenie ankiety
- POST /surveys/{id}/run - Uruchomienie zbierania odpowiedzi (background task)
- GET /projects/{id}/surveys - Lista ankiet projektu
- GET /surveys/{id} - Szczegóły ankiety
- GET /surveys/{id}/results - Wyniki ankiety z analizą statystyczną

Ankiety działają asynchronicznie - tworzenie jest natychmiastowe,
ale wykonanie (run) działa w tle i może trwać kilkadziesiąt sekund.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
from typing import List
from uuid import UUID

from app.db import AsyncSessionLocal, get_db
from app.models import Survey, Project
from app.schemas.survey import (
    SurveyCreate,
    SurveyResponse,
    SurveyResultsResponse,
)

router = APIRouter()

# Śledź uruchomione zadania aby zapobiec garbage collection
_running_tasks = set()


@router.post("/projects/{project_id}/surveys", response_model=SurveyResponse, status_code=201)
async def create_survey(
    project_id: UUID,
    survey: SurveyCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Utwórz nową ankietę dla projektu

    Args:
        project_id: UUID projektu
        survey: Dane ankiety (title, description, questions, target_responses)
        db: Sesja bazy danych

    Returns:
        SurveyResponse: Utworzona ankieta

    Raises:
        404: Projekt nie istnieje
    """
    # Verify project exists
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.is_active == True)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Konwertuj pytania z Pydantic do dict
    questions_dict = [q.model_dump() for q in survey.questions]

    db_survey = Survey(
        project_id=project_id,
        title=survey.title,
        description=survey.description,
        questions=questions_dict,
        target_responses=survey.target_responses,
        status="draft",
    )

    db.add(db_survey)
    await db.commit()
    await db.refresh(db_survey)

    return db_survey


@router.get("/projects/{project_id}/surveys", response_model=List[SurveyResponse])
async def get_project_surveys(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Pobierz wszystkie ankiety projektu

    Args:
        project_id: UUID projektu
        db: Sesja bazy danych

    Returns:
        List[SurveyResponse]: Lista ankiet

    Raises:
        404: Projekt nie istnieje
    """
    # Verify project exists
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.is_active == True)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all surveys for project
    result = await db.execute(
        select(Survey)
        .where(Survey.project_id == project_id, Survey.is_active == True)
        .order_by(Survey.created_at.desc())
    )
    surveys = result.scalars().all()

    return surveys


@router.get("/surveys/{survey_id}", response_model=SurveyResponse)
async def get_survey(
    survey_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Pobierz szczegóły ankiety

    Args:
        survey_id: UUID ankiety
        db: Sesja bazy danych

    Returns:
        SurveyResponse: Dane ankiety

    Raises:
        404: Ankieta nie istnieje
    """
    result = await db.execute(
        select(Survey).where(Survey.id == survey_id, Survey.is_active == True)
    )
    survey = result.scalar_one_or_none()

    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    return survey


@router.post("/surveys/{survey_id}/run", status_code=202)
async def run_survey(
    survey_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Uruchom zbieranie odpowiedzi od person projektu

    Ten endpoint uruchamia background task, który:
    1. Pobiera wszystkie persony projektu
    2. Dla każdej persony i każdego pytania generuje odpowiedź używając AI
    3. Zapisuje odpowiedzi w bazie danych
    4. Aktualizuje status ankiety

    Args:
        survey_id: UUID ankiety
        background_tasks: FastAPI BackgroundTasks
        db: Sesja bazy danych

    Returns:
        dict: Informacja o rozpoczęciu zadania

    Raises:
        404: Ankieta nie istnieje
        400: Ankieta już jest uruchomiona
    """
    import logging
    logger = logging.getLogger(__name__)

    # Verify survey exists
    result = await db.execute(
        select(Survey).where(Survey.id == survey_id, Survey.is_active == True)
    )
    survey = result.scalar_one_or_none()

    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    if survey.status == "running":
        raise HTTPException(status_code=400, detail="Survey is already running")

    if survey.status == "completed":
        raise HTTPException(status_code=400, detail="Survey is already completed")

    # Schedule background task and keep reference
    logger.info(f"📊 Scheduling survey task: {survey_id}")
    task = asyncio.create_task(_run_survey_task(survey_id))

    # Keep task reference to prevent garbage collection
    _running_tasks.add(task)
    task.add_done_callback(_running_tasks.discard)

    logger.info(f"📝 Survey task created and added to running tasks")

    return {
        "message": "Survey execution started",
        "survey_id": str(survey_id),
    }


async def _run_survey_task(survey_id: UUID):
    """
    Background task do uruchomienia ankiety

    Ten task:
    1. Zmienia status na 'running'
    2. Wywołuje SurveyResponseGenerator service
    3. Zmienia status na 'completed' lub 'failed'
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"🎯 Background task started for survey {survey_id}")

    try:
        async with AsyncSessionLocal() as db:
            # Import service (lazy loading aby uniknąć circular imports)
            from app.services.survey_response_generator import SurveyResponseGenerator

            service = SurveyResponseGenerator()
            logger.info(f"📦 Service created, calling generate_responses...")
            result = await service.generate_responses(db, str(survey_id))
            logger.info(f"✅ Survey completed: {result.get('status')}")
    except Exception as e:
        logger.error(f"❌ Error in survey background task: {e}", exc_info=True)

        # Mark survey as failed
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Survey).where(Survey.id == survey_id)
                )
                survey = result.scalar_one_or_none()
                if survey:
                    survey.status = "failed"
                    await db.commit()
        except Exception as commit_error:
            logger.error(f"❌ Error marking survey as failed: {commit_error}")


@router.get("/surveys/{survey_id}/results", response_model=SurveyResultsResponse)
async def get_survey_results(
    survey_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Pobierz wyniki ankiety z analizą statystyczną

    Ten endpoint zwraca:
    - Podstawowe informacje o ankiecie
    - Agregowane wyniki dla każdego pytania
    - Analizę demograficzną odpowiedzi
    - Statystyki wykonania

    Args:
        survey_id: UUID ankiety
        db: Sesja bazy danych

    Returns:
        SurveyResultsResponse: Wyniki z analizą

    Raises:
        404: Ankieta nie istnieje
        400: Ankieta nie została jeszcze uruchomiona
    """
    from app.services.survey_response_generator import SurveyResponseGenerator

    result = await db.execute(
        select(Survey).where(Survey.id == survey_id, Survey.is_active == True)
    )
    survey = result.scalar_one_or_none()

    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    if survey.status == "draft":
        raise HTTPException(
            status_code=400,
            detail="Survey has not been run yet. Use POST /surveys/{id}/run to execute it."
        )

    # Generate analytics using service
    service = SurveyResponseGenerator()
    analytics = await service.get_survey_analytics(db, str(survey_id))

    return {
        "id": survey.id,
        "project_id": survey.project_id,
        "title": survey.title,
        "description": survey.description,
        "questions": survey.questions,
        "status": survey.status,
        "target_responses": survey.target_responses,
        "actual_responses": survey.actual_responses,
        "total_execution_time_ms": survey.total_execution_time_ms,
        "avg_response_time_ms": survey.avg_response_time_ms,
        "created_at": survey.created_at,
        "started_at": survey.started_at,
        "completed_at": survey.completed_at,
        **analytics,  # question_analytics, demographic_breakdown, completion_rate, average_response_time_ms
    }


@router.delete("/surveys/{survey_id}", status_code=204)
async def delete_survey(
    survey_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Usuń ankietę (soft delete)

    Args:
        survey_id: UUID ankiety
        db: Sesja bazy danych

    Raises:
        404: Ankieta nie istnieje
    """
    result = await db.execute(
        select(Survey).where(Survey.id == survey_id, Survey.is_active == True)
    )
    survey = result.scalar_one_or_none()

    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    # Soft delete
    survey.is_active = False
    await db.commit()

    return None
