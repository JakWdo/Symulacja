"""
Modele ORM dla Study Designer Chat - interaktywne projektowanie badań

Zawiera dwa główne modele:
- StudyDesignerSession: Sesja konwersacji z AI (state, plan, execution tracking)
- StudyDesignerMessage: Pojedyncza wiadomość w konwersacji (user/assistant/system)

Workflow:
1. User rozpoczyna sesję → StudyDesignerSession (status='active')
2. Konwersacja z AI → StudyDesignerMessage records
3. AI generuje plan → session.generated_plan (JSON)
4. User zatwierdza → tworzy Workflow → session.created_workflow_id
5. Execution → session.status='executing'/'completed'
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from app.db.base import Base


class SessionStatusEnum(str, enum.Enum):
    """Status sesji Study Designer."""
    ACTIVE = "active"  # Konwersacja w toku
    PLAN_READY = "plan_ready"  # Plan wygenerowany, czeka na approval
    APPROVED = "approved"  # Plan zatwierdzony, gotowy do wykonania
    EXECUTING = "executing"  # Badanie jest wykonywane
    COMPLETED = "completed"  # Badanie zakończone
    CANCELLED = "cancelled"  # Sesja anulowana przez użytkownika
    FAILED = "failed"  # Błąd podczas wykonania


class MessageRoleEnum(str, enum.Enum):
    """Rola nadawcy wiadomości."""
    USER = "user"  # Wiadomość od użytkownika
    ASSISTANT = "assistant"  # Wiadomość od AI asystenta
    SYSTEM = "system"  # Wiadomość systemowa (np. status updates)


class ConversationStageEnum(str, enum.Enum):
    """Etapy konwersacji (LangGraph nodes)."""
    WELCOME = "welcome"
    GATHER_GOAL = "gather_goal"
    DEFINE_AUDIENCE = "define_audience"
    SELECT_METHOD = "select_method"
    CONFIGURE_DETAILS = "configure_details"
    GENERATE_PLAN = "generate_plan"
    AWAIT_APPROVAL = "await_approval"
    EXECUTE = "execute"


class StudyDesignerSession(Base):
    """
    Model StudyDesignerSession - sesja interaktywnego projektowania badania

    Reprezentuje konwersację użytkownika z AI w celu zaprojektowania badania.
    Przechowuje pełny stan LangGraph, wygenerowany plan i link do utworzonego workflow.

    Attributes:
        id: UUID sesji (klucz główny)
        user_id: UUID użytkownika prowadzącego sesję
        project_id: UUID projektu (nullable - może być utworzony później)

        status: Status sesji (SessionStatusEnum)
        current_stage: Aktualny etap konwersacji (ConversationStageEnum)

        conversation_state: JSON z pełnym stanem LangGraph
            {
                "session_id": str,
                "messages": [{"role": "user", "content": "..."}],
                "current_stage": "gather_goal",
                "study_goal": str | None,
                "target_audience": dict | None,
                "research_method": str | None,
                "num_personas": int | None,
                "focus_group_config": dict | None,
                "survey_config": dict | None,
                "generated_plan": dict | None,
                "plan_approved": bool
            }

        generated_plan: JSON z planem badania (WorkflowCreate compatible)
            {
                "name": str,
                "description": str,
                "canvas_data": {...},
                "estimated_time_seconds": int,
                "estimated_cost_usd": float,
                "deliverables": [...]
            }

        created_workflow_id: UUID utworzonego Workflow (po approval)

        created_at: Data utworzenia sesji
        updated_at: Data ostatniej aktualizacji
        completed_at: Data zakończenia sesji

    Relations:
        user: Użytkownik prowadzący sesję
        project: Projekt (jeśli przypisany)
        created_workflow: Workflow utworzony po zatwierdzeniu planu
        messages: Lista wiadomości w konwersacji
    """
    __tablename__ = "study_designer_sessions"

    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Status tracking
    status = Column(
        String(50),
        nullable=False,
        default="active",
        server_default=text("'active'"),
        index=True,
    )
    current_stage = Column(
        String(50),
        nullable=False,
        default="welcome",
        server_default=text("'welcome'"),
    )

    # State persistence (LangGraph state)
    conversation_state = Column(
        JSON,
        nullable=False,
        default={},
        server_default=text("'{}'::json"),
    )

    # Generated plan (JSON, WorkflowCreate compatible)
    generated_plan = Column(JSON, nullable=True)

    # Link to created workflow (after approval)
    created_workflow_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="study_designer_sessions")
    project = relationship("Project", foreign_keys=[project_id], backref="study_designer_sessions")
    created_workflow = relationship("Workflow", foreign_keys=[created_workflow_id])
    messages = relationship(
        "StudyDesignerMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="StudyDesignerMessage.created_at",
    )

    # Indexes
    __table_args__ = (
        Index('idx_study_designer_sessions_user_id', 'user_id'),
        Index('idx_study_designer_sessions_status', 'status'),
        Index('idx_study_designer_sessions_created_at', 'created_at'),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<StudyDesignerSession id={self.id} user_id={self.user_id} status={self.status}>"

    def is_active(self) -> bool:
        """Sprawdza czy sesja jest aktywna (można wysyłać wiadomości)."""
        return self.status in [
            SessionStatusEnum.ACTIVE.value,
            SessionStatusEnum.PLAN_READY.value,
        ]

    def can_approve(self) -> bool:
        """Sprawdza czy plan może być zatwierdzony."""
        return (
            self.status == SessionStatusEnum.PLAN_READY.value
            and self.generated_plan is not None
        )

    def mark_completed(self) -> None:
        """Oznacza sesję jako zakończoną."""
        self.status = SessionStatusEnum.COMPLETED.value
        self.completed_at = func.now()


class StudyDesignerMessage(Base):
    """
    Model StudyDesignerMessage - pojedyncza wiadomość w konwersacji

    Reprezentuje jedną wymianę w konwersacji Study Designer.
    Przechowuje rolę (user/assistant/system), treść i metadane.

    Attributes:
        id: UUID wiadomości (klucz główny)
        session_id: UUID sesji do której należy wiadomość

        role: Rola nadawcy (MessageRoleEnum: user, assistant, system)
        content: Treść wiadomości (Text, może być długa)

        message_metadata: JSON z dodatkowymi danymi
            {
                "stage": "gather_goal",  # Etap konwersacji
                "question_type": "follow_up",  # Typ pytania
                "extracted_data": {...},  # Wyekstraktowane dane
                "llm_model": "gemini-2.5-flash",
                "tokens_used": 1234,
                "latency_ms": 2500
            }

        created_at: Timestamp utworzenia wiadomości

    Relations:
        session: Sesja do której należy wiadomość
    """
    __tablename__ = "study_designer_messages"

    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key
    session_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("study_designer_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message content
    role = Column(
        String(20),
        nullable=False,
    )  # MessageRoleEnum: user, assistant, system
    content = Column(Text, nullable=False)

    # Message metadata (stage, question_type, extracted_data, etc.)
    # Note: renamed from 'metadata' to avoid conflict with SQLAlchemy Base.metadata
    message_metadata = Column(
        JSON,
        nullable=True,
        default={},
        server_default=text("'{}'::json"),
    )

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # Relationships
    session = relationship("StudyDesignerSession", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index('idx_study_designer_messages_session_id', 'session_id'),
        Index('idx_study_designer_messages_created_at', 'created_at'),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<StudyDesignerMessage id={self.id} role={self.role} content={preview!r}>"
