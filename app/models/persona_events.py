"""Persona events and responses models - event sourcing and consistency tracking."""
from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db.base import Base


class PersonaEvent(Base):
    """Event sourcing for persona interactions - immutable log."""
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
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSON, nullable=False)
    sequence_number = Column(Integer, nullable=False)
    embedding = Column(Vector(768), nullable=True)  # Google Generative AI Embeddings dimension
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    persona = relationship("Persona", back_populates="events")
    focus_group = relationship("FocusGroup")

    def __repr__(self) -> str:
        return f"<PersonaEvent id={self.id} persona_id={self.persona_id} seq={self.sequence_number}>"


class PersonaResponse(Base):
    """Persona responses to questions with consistency tracking."""
    __tablename__ = "persona_responses"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(
        PGUUID(as_uuid=True), ForeignKey("personas.id", ondelete="CASCADE"), nullable=False
    )
    focus_group_id = Column(
        PGUUID(as_uuid=True), ForeignKey("focus_groups.id", ondelete="CASCADE"), nullable=False
    )
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    retrieved_context = Column(JSON, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    llm_provider = Column(String(50), nullable=True)
    llm_model = Column(String(255), nullable=True)
    temperature = Column(Float, nullable=True)
    consistency_score = Column(Float, nullable=True)
    contradicts_events = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    persona = relationship("Persona", back_populates="responses")
    focus_group = relationship("FocusGroup", back_populates="responses")

    def __repr__(self) -> str:
        return f"<PersonaResponse id={self.id} persona_id={self.persona_id}>"
