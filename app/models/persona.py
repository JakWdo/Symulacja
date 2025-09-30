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
from sqlalchemy.sql import func

from app.db.base import Base


class Persona(Base):
    __tablename__ = "personas"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    age = Column(Integer, nullable=False)
    gender = Column(String(50), nullable=False)
    location = Column(String(255), nullable=True)
    education_level = Column(String(255), nullable=True)
    income_bracket = Column(String(255), nullable=True)
    occupation = Column(String(255), nullable=True)
    openness = Column(Float, nullable=True)
    conscientiousness = Column(Float, nullable=True)
    extraversion = Column(Float, nullable=True)
    agreeableness = Column(Float, nullable=True)
    neuroticism = Column(Float, nullable=True)
    power_distance = Column(Float, nullable=True)
    individualism = Column(Float, nullable=True)
    masculinity = Column(Float, nullable=True)
    uncertainty_avoidance = Column(Float, nullable=True)
    long_term_orientation = Column(Float, nullable=True)
    indulgence = Column(Float, nullable=True)
    values = Column(ARRAY(String()), nullable=True)
    interests = Column(ARRAY(String()), nullable=True)
    background_story = Column(Text, nullable=True)
    personality_prompt = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    is_active = Column(Boolean, nullable=False, default=True)

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
