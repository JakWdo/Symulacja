from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class PersonaResponse(Base):
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

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<PersonaResponse id={self.id} persona_id={self.persona_id}>"
