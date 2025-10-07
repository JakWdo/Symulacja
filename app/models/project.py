from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Project(Base):
    """
    Model projektu badawczego

    Reprezentuje pojedynczy projekt badań rynkowych, który zawiera:
    - Definicję docelowej grupy demograficznej
    - Wygenerowane persony
    - Przeprowadzone grupy fokusowe
    - Wyniki walidacji statystycznej

    Attributes:
        id: UUID projektu (klucz główny)
        name: Nazwa projektu
        description: Opis projektu
        target_demographics: JSON z rozkładami demograficznymi (age_group, gender, education_level, etc.)
        target_sample_size: Docelowa liczba person do wygenerowania
        chi_square_statistic: JSON z wartościami chi-kwadrat dla każdej kategorii demograficznej
        p_values: JSON z p-wartościami testów statystycznych
        is_statistically_valid: Czy rozkład person przeszedł walidację (wszystkie p > 0.05)
        validation_date: Data ostatniej walidacji statystycznej
        created_at: Data utworzenia
        updated_at: Data ostatniej aktualizacji
        is_active: Czy projekt jest aktywny (soft delete)

    Relations:
        personas: Lista person należących do projektu
        focus_groups: Lista grup fokusowych należących do projektu
    """
    __tablename__ = "projects"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_demographics = Column(JSON, nullable=False)  # {"age_group": {...}, "gender": {...}, ...}
    target_sample_size = Column(Integer, nullable=False)
    chi_square_statistic = Column(JSON, nullable=True)  # {"age": 2.34, "gender": 1.12, ...}
    p_values = Column(JSON, nullable=True)              # {"age": 0.67, "gender": 0.89, ...}
    is_statistically_valid = Column(Boolean, nullable=False, default=False)
    validation_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    is_active = Column(Boolean, nullable=False, default=True)

    # Relacje (cascade="all, delete-orphan" = usunięcie projektu usuwa persony i grupy)
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
