from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db.base import Base


class PersonaEvent(Base):
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
    embedding = Column(Vector(384), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    persona = relationship("Persona", back_populates="events")
    focus_group = relationship("FocusGroup")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<PersonaEvent id={self.id} persona_id={self.persona_id} seq={self.sequence_number}>"
