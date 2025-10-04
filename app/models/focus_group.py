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
    """
    Model grupy fokusowej

    Reprezentuje symulowaną grupę fokusową, w której wybrane persony
    odpowiadają na serię pytań. System śledzi wydajność i status wykonania.

    Attributes:
        id: UUID grupy fokusowej (klucz główny)
        project_id: UUID projektu do którego należy grupa
        name: Nazwa grupy fokusowej
        description: Opis celu grupy fokusowej
        project_context: Dodatkowy kontekst projektu dla person
        persona_ids: Lista UUID person biorących udział w grupie
        questions: Lista pytań do zadania personom
        mode: Tryb grupy ("normal" lub "adversarial")
        status: Status wykonania ("pending", "running", "completed", "failed")

        # === METRYKI WYDAJNOŚCI ===
        total_execution_time_ms: Całkowity czas wykonania w milisekundach
        avg_response_time_ms: Średni czas odpowiedzi persony w milisekundach

        # === TIMESTAMPY ===
        created_at: Data utworzenia grupy
        started_at: Data rozpoczęcia wykonania
        completed_at: Data zakończenia wykonania

    Relations:
        project: Projekt do którego należy grupa
        responses: Lista odpowiedzi person (PersonaResponse)
    """
    __tablename__ = "focus_groups"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    project_context = Column(Text, nullable=True)
    persona_ids = Column(ARRAY(PGUUID(as_uuid=True)), nullable=False)  # [uuid1, uuid2, ...]
    questions = Column(ARRAY(Text), nullable=False)  # ["Question 1?", "Question 2?", ...]
    mode = Column(String(50), nullable=False, default="normal")  # "normal" lub "adversarial"
    status = Column(String(50), nullable=False, default="pending")  # pending/running/completed/failed

    # Metryki wydajności
    total_execution_time_ms = Column(Integer, nullable=True)  # Całkowity czas (cel: <30s)
    avg_response_time_ms = Column(Float, nullable=True)  # Średni czas odpowiedzi (cel: <3s)

    # Timestampy
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relacje
    project = relationship("Project", back_populates="focus_groups")
    responses = relationship(
        "PersonaResponse",
        back_populates="focus_group",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def meets_performance_requirements(self) -> bool:
        """
        Sprawdź czy grupa fokusowa spełnia wymagania wydajnościowe

        Wymagania:
        - Całkowity czas wykonania < 30 sekund (30,000 ms)
        - Średni czas odpowiedzi persony < 3 sekundy (3,000 ms)

        Returns:
            True jeśli wszystkie metryki są w normie, False w przeciwnym razie
        """
        thresholds = {
            "total_execution_time_ms": 30_000,  # 30 sekund
            "avg_response_time_ms": 3_000.0,    # 3 sekundy
        }

        # Sprawdź całkowity czas
        total_time = self.total_execution_time_ms
        if total_time is not None and total_time > thresholds["total_execution_time_ms"]:
            return False

        # Sprawdź średni czas odpowiedzi
        avg_time = self.avg_response_time_ms
        if avg_time is not None and avg_time > thresholds["avg_response_time_ms"]:
            return False

        return True

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<FocusGroup id={self.id} project_id={self.project_id}>"
