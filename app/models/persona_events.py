"""
Modele Event Sourcing i Odpowiedzi Person

Ten moduł zawiera modele do śledzenia historii interakcji person (event sourcing)
oraz przechowywania odpowiedzi w grupach fokusowych.
"""
from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db.base import Base
from app.core.config import get_settings

settings = get_settings()


class PersonaEvent(Base):
    """
    Model zdarzenia persony (Event Sourcing)

    Event sourcing to wzorzec architektoniczny gdzie każda zmiana stanu jest zapisywana
    jako niemodyfikowalny event. To pozwala na:
    - Pełną historię interakcji każdej persony
    - Odtworzenie stanu persony w dowolnym momencie
    - Semantic search po historii (dzięki embeddingom)

    Attributes:
        id: UUID eventu (klucz główny)
        persona_id: UUID persony której dotyczy event
        focus_group_id: UUID grupy fokusowej (opcjonalne, SET NULL przy usunięciu grupy)
        event_type: Typ eventu (np. "response_given", "question_asked")
        event_data: Dane eventu jako JSON (np. {"question": "...", "response": "..."})
        sequence_number: Numer sekwencyjny (1, 2, 3...) dla tej persony
        embedding: Wektor semantyczny (768 wymiarów) dla semantic search
        timestamp: Czas utworzenia eventu

    Constraints:
        - UNIQUE(persona_id, sequence_number) - każda persona ma unikalną sekwencję

    Relations:
        persona: Persona do której należy event
        focus_group: Grupa fokusowa w której event powstał (opcjonalne)
    """
    __tablename__ = "persona_events"
    __table_args__ = (
        UniqueConstraint("persona_id", "sequence_number", name="uq_persona_event_sequence"),
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(
        PGUUID(as_uuid=True), ForeignKey("personas.id", ondelete="CASCADE"), nullable=False
    )
    focus_group_id = Column(
        PGUUID(as_uuid=True), ForeignKey("focus_groups.id", ondelete="SET NULL"), nullable=True
    )
    event_type = Column(String(100), nullable=False)  # "response_given", "question_asked", etc.
    event_data = Column(JSON, nullable=False)  # {"question": "...", "response": "..."}
    sequence_number = Column(Integer, nullable=False)  # 1, 2, 3, ... (per persona)
    embedding = Column(Vector(settings.EMBEDDING_DIMENSION), nullable=True)  # Wektor semantyczny Google Gemini
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relacje
    persona = relationship("Persona", back_populates="events")
    focus_group = relationship("FocusGroup")

    def __repr__(self) -> str:
        return f"<PersonaEvent id={self.id} persona_id={self.persona_id} seq={self.sequence_number}>"


class PersonaResponse(Base):
    """
    Model odpowiedzi persony w grupie fokusowej

    Uproszczona tabela przechowująca odpowiedzi person na pytania.
    Duplikuje część informacji z PersonaEvent ale ułatwia zapytania
    o konkretne odpowiedzi w grupach fokusowych.

    Attributes:
        id: UUID odpowiedzi (klucz główny)
        persona_id: UUID persony która odpowiedziała
        focus_group_id: UUID grupy fokusowej
        question_text: Treść pytania
        response_text: Treść odpowiedzi persony
        response_time_ms: Czas generowania odpowiedzi w milisekundach
        created_at: Czas utworzenia odpowiedzi

    Relations:
        persona: Persona która udzieliła odpowiedzi
        focus_group: Grupa fokusowa w której udzielono odpowiedzi
    """
    __tablename__ = "persona_responses"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(
        PGUUID(as_uuid=True), ForeignKey("personas.id", ondelete="CASCADE"), nullable=False
    )
    focus_group_id = Column(
        PGUUID(as_uuid=True), ForeignKey("focus_groups.id", ondelete="CASCADE"), nullable=False
    )
    question_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    response_time_ms = Column(Integer, nullable=True)  # Czas wykonania w ms (metryki wydajności)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relacje
    persona = relationship("Persona", back_populates="responses")
    focus_group = relationship("FocusGroup", back_populates="responses")

    def __repr__(self) -> str:
        return f"<PersonaResponse id={self.id} persona_id={self.persona_id}>"
