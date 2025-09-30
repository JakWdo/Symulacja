from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_demographics = Column(JSON, nullable=False)
    target_sample_size = Column(Integer, nullable=False)
    chi_square_statistic = Column(JSON, nullable=True)
    p_values = Column(JSON, nullable=True)
    is_statistically_valid = Column(Boolean, nullable=False, default=False)
    validation_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    is_active = Column(Boolean, nullable=False, default=True)

    personas = relationship(
        "Persona", back_populates="project", cascade="all, delete-orphan", passive_deletes=True
    )
    focus_groups = relationship(
        "FocusGroup",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Project id={self.id} name={self.name!r}>"
