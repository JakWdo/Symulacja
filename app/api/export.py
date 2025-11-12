"""
API endpoints dla eksportu raportów do PDF i DOCX.
"""
import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.persona import Persona
from app.models.focus_group import FocusGroup
from app.models.survey import Survey
from app.services.export import PDFGenerator, DOCXGenerator

router = APIRouter(prefix="/export", tags=["export"])
logger = logging.getLogger(__name__)


@router.get("/personas/{persona_id}/pdf")
async def export_persona_pdf(
    persona_id: int,
    include_reasoning: bool = Query(True, description="Czy dołączyć uzasadnienie generacji"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Eksportuje raport persony do PDF.

    Args:
        persona_id: ID persony
        include_reasoning: Czy dołączyć reasoning/uzasadnienie
        db: Sesja bazodanowa
        current_user: Zalogowany użytkownik

    Returns:
        Response: Plik PDF do pobrania
    """
    # Pobierz personę
    stmt = select(Persona).where(Persona.id == persona_id, Persona.deleted_at.is_(None))
    result = await db.execute(stmt)
    persona = result.scalar_one_or_none()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona nie znaleziona")

    # Sprawdź uprawnienia (persona należy do projektu użytkownika)
    if persona.project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Brak dostępu do tej persony")

    # Przygotuj dane persony
    persona_data = {
        "name": persona.name,
        "age": persona.age,
        "occupation": persona.occupation,
        "education": persona.education,
        "income": persona.income,
        "location": persona.location,
        "values": persona.values or [],
        "interests": persona.interests or [],
        "needs": persona.needs or [],
        "reasoning": persona.reasoning or {},
    }

    # Generuj PDF
    pdf_generator = PDFGenerator()
    user_tier = current_user.subscription_tier or "free"

    try:
        pdf_bytes = await pdf_generator.generate_persona_pdf(
            persona_data=persona_data,
            user_tier=user_tier,
            include_reasoning=include_reasoning,
        )
    except Exception as e:
        logger.error(f"Błąd generowania PDF dla persony {persona_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Błąd generowania PDF: {str(e)}")

    # Zwróć PDF jako plik do pobrania
    filename = f"persona_{persona.name.replace(' ', '_')}_{persona_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/personas/{persona_id}/docx")
async def export_persona_docx(
    persona_id: int,
    include_reasoning: bool = Query(True, description="Czy dołączyć uzasadnienie generacji"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Eksportuje raport persony do DOCX.

    Args:
        persona_id: ID persony
        include_reasoning: Czy dołączyć reasoning
        db: Sesja bazodanowa
        current_user: Zalogowany użytkownik

    Returns:
        Response: Plik DOCX do pobrania
    """
    # Pobierz personę
    stmt = select(Persona).where(Persona.id == persona_id, Persona.deleted_at.is_(None))
    result = await db.execute(stmt)
    persona = result.scalar_one_or_none()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona nie znaleziona")

    if persona.project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Brak dostępu do tej persony")

    # Przygotuj dane
    persona_data = {
        "name": persona.name,
        "age": persona.age,
        "occupation": persona.occupation,
        "education": persona.education,
        "income": persona.income,
        "location": persona.location,
        "values": persona.values or [],
        "interests": persona.interests or [],
        "needs": persona.needs or [],
        "reasoning": persona.reasoning or {},
    }

    # Generuj DOCX
    docx_generator = DOCXGenerator()
    user_tier = current_user.subscription_tier or "free"

    try:
        docx_bytes = await docx_generator.generate_persona_docx(
            persona_data=persona_data,
            user_tier=user_tier,
            include_reasoning=include_reasoning,
        )
    except Exception as e:
        logger.error(f"Błąd generowania DOCX dla persony {persona_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Błąd generowania DOCX: {str(e)}")

    # Zwróć DOCX
    filename = f"persona_{persona.name.replace(' ', '_')}_{persona_id}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/focus-groups/{focus_group_id}/pdf")
async def export_focus_group_pdf(
    focus_group_id: int,
    include_discussion: bool = Query(True, description="Czy dołączyć pełną transkrypcję dyskusji"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Eksportuje raport grupy fokusowej do PDF.

    Args:
        focus_group_id: ID grupy fokusowej
        include_discussion: Czy dołączyć transkrypcję
        db: Sesja bazodanowa
        current_user: Zalogowany użytkownik

    Returns:
        Response: Plik PDF
    """
    # Pobierz grupę
    stmt = select(FocusGroup).where(FocusGroup.id == focus_group_id, FocusGroup.deleted_at.is_(None))
    result = await db.execute(stmt)
    focus_group = result.scalar_one_or_none()

    if not focus_group:
        raise HTTPException(status_code=404, detail="Grupa fokusowa nie znaleziona")

    if focus_group.project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Brak dostępu do tej grupy")

    # Przygotuj dane
    focus_group_data = {
        "name": focus_group.name,
        "personas": [{"name": p.name} for p in focus_group.personas],
        "discussion": focus_group.discussion or [],
        "summary": focus_group.summary or {},
    }

    # Generuj PDF
    pdf_generator = PDFGenerator()
    user_tier = current_user.subscription_tier or "free"

    try:
        pdf_bytes = await pdf_generator.generate_focus_group_pdf(
            focus_group_data=focus_group_data,
            user_tier=user_tier,
            include_discussion=include_discussion,
        )
    except Exception as e:
        logger.error(f"Błąd generowania PDF dla grupy {focus_group_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Błąd generowania PDF: {str(e)}")

    filename = f"focus_group_{focus_group.name.replace(' ', '_')}_{focus_group_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/focus-groups/{focus_group_id}/docx")
async def export_focus_group_docx(
    focus_group_id: int,
    include_discussion: bool = Query(True, description="Czy dołączyć transkrypcję dyskusji"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Eksportuje raport grupy fokusowej do DOCX.
    """
    stmt = select(FocusGroup).where(FocusGroup.id == focus_group_id, FocusGroup.deleted_at.is_(None))
    result = await db.execute(stmt)
    focus_group = result.scalar_one_or_none()

    if not focus_group:
        raise HTTPException(status_code=404, detail="Grupa fokusowa nie znaleziona")

    if focus_group.project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Brak dostępu")

    focus_group_data = {
        "name": focus_group.name,
        "personas": [{"name": p.name} for p in focus_group.personas],
        "discussion": focus_group.discussion or [],
        "summary": focus_group.summary or {},
    }

    docx_generator = DOCXGenerator()
    user_tier = current_user.subscription_tier or "free"

    try:
        docx_bytes = await docx_generator.generate_focus_group_docx(
            focus_group_data=focus_group_data,
            user_tier=user_tier,
            include_discussion=include_discussion,
        )
    except Exception as e:
        logger.error(f"Błąd generowania DOCX dla grupy {focus_group_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Błąd generowania DOCX: {str(e)}")

    filename = f"focus_group_{focus_group.name.replace(' ', '_')}_{focus_group_id}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/surveys/{survey_id}/pdf")
async def export_survey_pdf(
    survey_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Eksportuje raport ankiety do PDF.
    """
    stmt = select(Survey).where(Survey.id == survey_id, Survey.deleted_at.is_(None))
    result = await db.execute(stmt)
    survey = result.scalar_one_or_none()

    if not survey:
        raise HTTPException(status_code=404, detail="Ankieta nie znaleziona")

    if survey.project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Brak dostępu")

    survey_data = {
        "title": survey.title,
        "questions": survey.questions or [],
        "responses": survey.responses or [],
    }

    pdf_generator = PDFGenerator()
    user_tier = current_user.subscription_tier or "free"

    try:
        pdf_bytes = await pdf_generator.generate_survey_pdf(
            survey_data=survey_data,
            user_tier=user_tier,
        )
    except Exception as e:
        logger.error(f"Błąd generowania PDF dla ankiety {survey_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Błąd generowania PDF: {str(e)}")

    filename = f"survey_{survey.title.replace(' ', '_')}_{survey_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/surveys/{survey_id}/docx")
async def export_survey_docx(
    survey_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Eksportuje raport ankiety do DOCX.
    """
    stmt = select(Survey).where(Survey.id == survey_id, Survey.deleted_at.is_(None))
    result = await db.execute(stmt)
    survey = result.scalar_one_or_none()

    if not survey:
        raise HTTPException(status_code=404, detail="Ankieta nie znaleziona")

    if survey.project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Brak dostępu")

    survey_data = {
        "title": survey.title,
        "questions": survey.questions or [],
        "responses": survey.responses or [],
    }

    docx_generator = DOCXGenerator()
    user_tier = current_user.subscription_tier or "free"

    try:
        docx_bytes = await docx_generator.generate_survey_docx(
            survey_data=survey_data,
            user_tier=user_tier,
        )
    except Exception as e:
        logger.error(f"Błąd generowania DOCX dla ankiety {survey_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Błąd generowania DOCX: {str(e)}")

    filename = f"survey_{survey.title.replace(' ', '_')}_{survey_id}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
