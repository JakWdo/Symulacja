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
    owner_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    team_id = Column(PGUUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=True, index=True)
    environment_id = Column(PGUUID(as_uuid=True), ForeignKey("environments.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_audience = Column(Text, nullable=True)
    research_objectives = Column(Text, nullable=True)
    additional_notes = Column(Text, nullable=True)
    target_demographics = Column(JSON, nullable=False)  # {"age_group": {...}, "gender": {...}, ...}
    target_sample_size = Column(Integer, nullable=False)
    chi_square_statistic = Column(JSON, nullable=True)  # {"age": 2.34, "gender": 1.12, ...}
    p_values = Column(JSON, nullable=True)              # {"age": 0.67, "gender": 0.89, ...}
    is_statistically_valid = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    validation_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relacje (cascade="all, delete-orphan" = usunięcie projektu usuwa persony i grupy)
    owner = relationship(
        "User",
        foreign_keys=[owner_id],
        back_populates="projects"
    )
    team = relationship(
        "Team",
        back_populates="projects"
    )
    environment = relationship(
        "Environment",
        back_populates="projects"
    )
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
    deleted_by_user = relationship(
        "User",
        foreign_keys=[deleted_by],
        overlaps="projects",  # Prevents SQLAlchemy warnings about overlapping relationships
    )
    health_logs = relationship(
        "ProjectHealthLog",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    snapshots = relationship(
        "ProjectSnapshot",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Project id={self.id} name={self.name!r}>"
