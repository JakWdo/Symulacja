from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime
import uuid

from app.db.base import Base


class PersonaEvent(Base):
    """Event sourcing for persona interactions - immutable log"""
    __tablename__ = "persona_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id"), nullable=False)
    focus_group_id = Column(UUID(as_uuid=True), ForeignKey("focus_groups.id"), nullable=True)

    # Event Details
    event_type = Column(String(100), nullable=False)  # question_asked, response_given, context_updated
    event_data = Column(JSON, nullable=False)
    sequence_number = Column(Integer, nullable=False)  # For ordering events

    # Vector embedding for semantic search
    embedding = Column(Vector(768))

    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    persona = relationship("Persona", back_populates="events")
    focus_group = relationship("FocusGroup", back_populates="events")

    def __repr__(self):
        return f"<PersonaEvent {self.event_type} for {self.persona_id}>"


class PersonaResponse(Base):
    """Persona responses to questions with consistency tracking"""
    __tablename__ = "persona_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id"), nullable=False)
    focus_group_id = Column(UUID(as_uuid=True), ForeignKey("focus_groups.id"), nullable=False)

    # Question & Response
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=False)

    # Context from memory
    retrieved_context = Column(JSON)  # List of relevant past events
    context_embedding = Column(Vector(1536))

    # Response metadata
    response_time_ms = Column(Integer)
    llm_provider = Column(String(50))
    llm_model = Column(String(100))
    temperature = Column(Float)

    # Consistency validation
    consistency_score = Column(Float)  # 0-1, based on contradiction detection
    contradicts_events = Column(JSON)  # List of event IDs if contradictions found

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    persona = relationship("Persona", back_populates="responses")
    focus_group = relationship("FocusGroup", back_populates="responses")