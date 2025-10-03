from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class FocusGroup(Base):
    __tablename__ = "focus_groups"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    project_context = Column(Text, nullable=True)
    persona_ids = Column(ARRAY(PGUUID(as_uuid=True)), nullable=False)
    questions = Column(ARRAY(Text), nullable=False)
    mode = Column(String(50), nullable=False, default="normal")
    status = Column(String(50), nullable=False, default="pending")
    total_execution_time_ms = Column(Integer, nullable=True)
    avg_response_time_ms = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="focus_groups")
    responses = relationship(
        "PersonaResponse",
        back_populates="focus_group",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def meets_performance_requirements(self) -> bool:
        """Evaluate whether performance metrics satisfy requirements."""
        thresholds = {
            "total_execution_time_ms": 30_000,
            "avg_response_time_ms": 3_000.0,
        }

        total_time = self.total_execution_time_ms
        if total_time is not None and total_time > thresholds["total_execution_time_ms"]:
            return False

        avg_time = self.avg_response_time_ms
        if avg_time is not None and avg_time > thresholds["avg_response_time_ms"]:
            return False

        return True

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<FocusGroup id={self.id} project_id={self.project_id}>"
