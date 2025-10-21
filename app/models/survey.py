"""
Modele ankiet wykorzystywane do funkcjonalności syntetycznych badań.

Umożliwia tworzenie ankiet i zbieranie odpowiedzi od syntetycznych person.
"""

import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Survey(Base):
    """
    Model reprezentujący syntetyczną ankietę.

    Survey pozwala na stworzenie zestawu pytań, które zostaną zadane
    syntetycznym personom projektu. AI generuje odpowiedzi bazując na
    profilach psychologicznych i demograficznych person.
    """
    __tablename__ = "surveys"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    # Podstawowe informacje
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Pytania ankietowe zapisane jako tablica JSON obiektów pytania
    # Format: [{"id": "q1", "type": "single-choice", "title": "...", "options": [...], ...}, ...]
    questions = Column(JSON, nullable=False)

    # Status ankiety
    status = Column(
        String(50),
        default="draft",
        nullable=False,
        index=True
    )  # draft, running, completed, failed

    # Statystyki odpowiedzi
    target_responses = Column(Integer, default=1000, nullable=False)
    actual_responses = Column(Integer, default=0, nullable=False)

    # Znacznik czasus
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Metryki wykonania (podobnie jak w FocusGroup)
    total_execution_time_ms = Column(Integer, nullable=True)
    avg_response_time_ms = Column(Integer, nullable=True)

    # Miękkie usunięcie
    is_active = Column(Boolean, default=True, nullable=False)

    # Relacje
    project = relationship("Project", back_populates="surveys")
    responses = relationship("SurveyResponse", back_populates="survey", cascade="all, delete-orphan")


class SurveyResponse(Base):
    """
    Model reprezentujący odpowiedź persony na ankietę.

    Każda persona w projekcie może odpowiedzieć na ankietę.
    Odpowiedzi są generowane przez AI na podstawie profilu persony.
    """
    __tablename__ = "survey_responses"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id = Column(PGUUID(as_uuid=True), ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False, index=True)
    persona_id = Column(PGUUID(as_uuid=True), ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True)

    # Odpowiedzi na pytania
    # Format: {"question_id": "answer_value", ...}
    # Dla single-choice: {"q1": "Option 1"}
    # Dla multiple-choice: {"q1": ["Option 1", "Option 2"]}
    # Dla rating-scale: {"q1": 4}
    # Dla open-text: {"q1": "Free text response..."}
    answers = Column(JSON, nullable=False)

    # Znacznik czasu
    completed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Metryki wykonania
    response_time_ms = Column(Integer, nullable=True)

    # Relacje
    survey = relationship("Survey", back_populates="responses")
    persona = relationship("Persona")
