"""
Model ORM dla projektów badawczych

Tabela `projects` opisuje główny kontener danych użytkownika:
cele badawcze, założenia demograficzne oraz powiązane persony i grupy fokusowe.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from app.db.base import Base


class Project(Base):
    """
    Model projektu badawczego

    Reprezentuje pojedynczy projekt badań rynkowych, który zawiera:
    - Cel badawczy i opis grupy docelowej
    - Wygenerowane persony
    - Przeprowadzone grupy fokusowe

    Attributes:
        id: UUID projektu (klucz główny)
        name: Nazwa projektu
        description: Opis projektu
        target_audience: Opis grupy docelowej
        research_objectives: Cele badawcze
        target_sample_size: Docelowa liczba person do wygenerowania
        created_at: Data utworzenia
        updated_at: Data ostatniej aktualizacji
        is_active: Czy projekt jest aktywny (soft delete)

    Relations:
        personas: Lista person należących do projektu
        focus_groups: Lista grup fokusowych należących do projektu
        surveys: Lista ankiet należących do projektu

    Note: Demographics są teraz generowane przez RAG + segment-based allocation,
          nie przez hardcoded target_demographics.
    """
    __tablename__ = "projects"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_audience = Column(Text, nullable=True)
    research_objectives = Column(Text, nullable=True)
    additional_notes = Column(Text, nullable=True)
    target_sample_size = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"))

    # Relacje (cascade="all, delete-orphan" = usunięcie projektu usuwa persony i grupy)
    owner = relationship("User", back_populates="projects")
    personas = relationship(
        "Persona", back_populates="project", cascade="all, delete-orphan", passive_deletes=True
    )
    focus_groups = relationship(
        "FocusGroup",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    surveys = relationship(
        "Survey",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Project id={self.id} name={self.name!r}>"
