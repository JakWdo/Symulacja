"""
Model ORM dla person (syntetycznych uczestników badań)

Tabela `personas` przechowuje kompletny profil wygenerowanych postaci:
dane demograficzne, osobowość, historię fabularną oraz powiązanie z projektem.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, expression

from app.db.base import Base


class Persona(Base):
    """
    Model persony - syntetyczna osoba do badań rynkowych

    Reprezentuje pojedynczą personę wygenerowaną przez AI z pełnym profilem
    demograficznym, psychologicznym i narracyjnym.

    Attributes:
        # === IDENTYFIKATORY ===
        id: UUID persony (klucz główny)
        project_id: UUID projektu do którego należy persona

        # === DANE DEMOGRAFICZNE ===
        age: Wiek w latach
        gender: Płeć (male, female, non-binary)
        location: Lokalizacja geograficzna (miasto, kraj)
        education_level: Poziom edukacji (High school, Bachelor's, etc.)
        income_bracket: Przedział dochodowy (< $25k, $25k-$50k, etc.)
        occupation: Zawód/stanowisko

        # === TOŻSAMOŚĆ PERSONY ===
        full_name: Pełne imię i nazwisko
        persona_title: Krótki tytuł persony (np. "UX Designer", "Retired Teacher")
        headline: Jednoliniowy opis persony
        background_story: Historia życiowa (2-3 zdania)

        # === CECHY OSOBOWOŚCI (BIG FIVE) ===
        # Wszystkie wartości w przedziale [0.0, 1.0]
        openness: Otwartość (ciekawość, kreatywność)
        conscientiousness: Sumienność (organizacja, dyscyplina)
        extraversion: Ekstrawersja (towarzyskość, energia)
        agreeableness: Ugodowość (empatia, współpraca)
        neuroticism: Neurotyzm (emocjonalność, podatność na stres)

        # === WYMIARY KULTUROWE (HOFSTEDE) ===
        # Wszystkie wartości w przedziale [0.0, 1.0]
        power_distance: Akceptacja nierówności władzy
        individualism: Indywidualizm vs kolektywizm
        masculinity: Asertywność vs troska o innych
        uncertainty_avoidance: Unikanie niepewności
        long_term_orientation: Orientacja długo- vs krótkoterminowa
        indulgence: Pobłażliwość vs powściągliwość

        # === WARTOŚCI I ZAINTERESOWANIA ===
        values: Lista wartości życiowych (np. ["Family", "Success", "Creativity"])
        interests: Lista zainteresowań/hobby (np. ["Yoga", "Photography", "Travel"])

        # === METADANE ===
        personality_prompt: Pełny prompt wysłany do LLM (do debugowania)
        created_at: Data utworzenia
        updated_at: Data ostatniej aktualizacji
        is_active: Czy persona jest aktywna (soft delete)

    Relations:
        project: Projekt do którego należy persona
        responses: Lista odpowiedzi persony w grupach fokusowych
        events: Historia eventów persony (event sourcing)
    """
    __tablename__ = "personas"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    # Dane demograficzne
    age = Column(Integer, nullable=False)
    gender = Column(String(50), nullable=False)
    location = Column(String(255), nullable=True)
    education_level = Column(String(255), nullable=True)
    income_bracket = Column(String(255), nullable=True)
    occupation = Column(String(255), nullable=True)

    # Tożsamość
    full_name = Column(String(150), nullable=True)
    persona_title = Column(String(150), nullable=True)
    headline = Column(String(255), nullable=True)

    # Big Five (0.0 - 1.0)
    openness = Column(Float, nullable=True)
    conscientiousness = Column(Float, nullable=True)
    extraversion = Column(Float, nullable=True)
    agreeableness = Column(Float, nullable=True)
    neuroticism = Column(Float, nullable=True)

    # Hofstede (0.0 - 1.0)
    power_distance = Column(Float, nullable=True)
    individualism = Column(Float, nullable=True)
    masculinity = Column(Float, nullable=True)
    uncertainty_avoidance = Column(Float, nullable=True)
    long_term_orientation = Column(Float, nullable=True)
    indulgence = Column(Float, nullable=True)

    # Wartości i zainteresowania
    values = Column(ARRAY(String()), nullable=True)
    interests = Column(ARRAY(String()), nullable=True)
    background_story = Column(Text, nullable=True)

    # Metadane
    personality_prompt = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=expression.true(),
    )

    # Relacje
    project = relationship("Project", back_populates="personas")
    responses = relationship(
        "PersonaResponse",
        back_populates="persona",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    events = relationship(
        "PersonaEvent",
        back_populates="persona",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PersonaEvent.sequence_number",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Persona id={self.id} project_id={self.project_id}>"

    def __init__(self, **kwargs):
        """Wymuś aktywny status jako domyślny bez nadpisywania danych wejściowych."""

        is_active = kwargs.pop("is_active", True)

        super().__init__(**kwargs)

        self.is_active = is_active
