"""
Model ORM dla Workflow Builder - wieloetapowe przepływy badawcze

Zawiera trzy główne modele:
- Workflow: Główny kontener dla flow (canvas_data, status, ownership)
- WorkflowStep: Pojedyncze kroki w workflow (nodes z React Flow)
- WorkflowExecution: Historia wykonań z tracking statusu i wyników
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
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from app.db.base import Base


class WorkflowStatusEnum(str, enum.Enum):
    """Status workflow."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ExecutionStatusEnum(str, enum.Enum):
    """Status wykonania workflow."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStepTypeEnum(str, enum.Enum):
    """Typy węzłów workflow."""
    START = "start"
    END = "end"
    CREATE_PROJECT = "create-project"
    GENERATE_PERSONAS = "generate-personas"
    CREATE_SURVEY = "create-survey"
    RUN_FOCUS_GROUP = "run-focus-group"
    ANALYSIS = "analysis"
    DECISION = "decision"
    WAIT = "wait"
    EXPORT_PDF = "export-pdf"
    WEBHOOK = "webhook"
    CONDITION = "condition"
    LOOP = "loop"
    MERGE = "merge"


class Workflow(Base):
    """
    Model Workflow - wieloetapowy przepływ badawczy

    Reprezentuje wizualny workflow składający się z połączonych nodes (Goal, Persona, Focus Group).
    Canvas data zawiera pełny stan React Flow (nodes, edges, positions).

    Attributes:
        id: UUID workflow (klucz główny)
        project_id: UUID projektu do którego należy workflow
        owner_id: UUID użytkownika właściciela
        name: Nazwa workflow
        description: Opis celu workflow
        canvas_data: JSON ze stanem canvas ({nodes: [], edges: []})
        status: Status workflow (WorkflowStatusEnum: "draft", "active", "archived")
        is_template: Czy workflow jest szablonem (read-only dla użytkowników)

        # === SOFT DELETE ===
        is_active: Czy workflow jest aktywny
        deleted_at: Data soft delete
        deleted_by: UUID użytkownika który usunął

        # === TIMESTAMPS ===
        created_at: Data utworzenia
        updated_at: Data ostatniej aktualizacji

    Relations:
        owner: Użytkownik właściciel workflow
        project: Projekt do którego należy workflow
        steps: Lista kroków (WorkflowStep) w workflow
        executions: Historia wykonań (WorkflowExecution)
    """
    __tablename__ = "workflows"

    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    project_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    owner_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Core fields
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    canvas_data = Column(
        JSON,
        nullable=False,
        default={},
        server_default=text("'{}'::json"),
    )  # {nodes: [], edges: []} React Flow state
    status = Column(
        String(50),
        nullable=False,
        default="draft",
        server_default=text("'draft'"),
    )  # draft, active, archived (WorkflowStatusEnum)
    is_template = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )  # Czy jest szablonem (read-only)

    # Soft delete pattern
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        server_default=text("true"),
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
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

    # Relationships
    owner = relationship(
        "User",
        foreign_keys=[owner_id],
        backref="workflows",
    )
    project = relationship(
        "Project",
        foreign_keys=[project_id],
        backref="workflows",
    )
    steps = relationship(
        "WorkflowStep",
        back_populates="workflow",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    executions = relationship(
        "WorkflowExecution",
        back_populates="workflow",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    deleted_by_user = relationship(
        "User",
        foreign_keys=[deleted_by],
        overlaps="workflows",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Workflow id={self.id} name={self.name!r} status={self.status}>"

    def is_running(self) -> bool:
        """
        Sprawdza czy workflow ma aktywne wykonanie ze statusem 'running'.

        Returns:
            True jeśli istnieje wykonanie ze statusem 'running', False w przeciwnym razie
        """
        return any(
            execution.status == ExecutionStatusEnum.RUNNING.value
            for execution in self.executions
        )

    def can_execute(self) -> bool:
        """
        Sprawdza czy workflow może być wykonany.

        Workflow może być wykonany gdy:
        - Ma status 'active'
        - Nie ma aktywnego wykonania ze statusem 'running'

        Returns:
            True jeśli workflow może być wykonany, False w przeciwnym razie
        """
        return self.status == WorkflowStatusEnum.ACTIVE.value and not self.is_running()


class WorkflowStep(Base):
    """
    Model WorkflowStep - pojedynczy krok w workflow

    Reprezentuje jeden node z React Flow canvas. Przechowuje konfigurację
    specyficzną dla typu kroku.

    Attributes:
        id: UUID kroku (klucz główny)
        workflow_id: UUID workflow do którego należy krok
        node_id: Identyfikator node z React Flow (np. "node-1234567890")
        step_type: Typ kroku (WorkflowStepTypeEnum):
            - start: Entry point
            - end: Completion
            - create-project: Setup research
            - generate-personas: AI persona generation
            - create-survey: Survey builder
            - run-focus-group: Simulated discussion
            - analyze-results: AI analysis
            - decision: Conditional branching
            - wait: Delay execution
            - export-pdf: Report generation
            - webhook: External integrations
            - condition: Multi-branch logic
            - loop: Array iteration
            - merge: Branch consolidation
        step_order: Kolejność wykonania (z topological sort DAG)
        config: JSON z konfiguracją specyficzną dla typu node
        created_at: Data utworzenia kroku

    Relations:
        workflow: Workflow do którego należy krok
    """
    __tablename__ = "workflow_steps"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Node identification (z React Flow)
    node_id = Column(String(100), nullable=False)  # React Flow node.id

    # Step config
    step_type = Column(String(50), nullable=False)  # WorkflowStepTypeEnum (14 typów)
    step_order = Column(Integer, nullable=False)  # Execution order (z topological sort)
    config = Column(
        JSON,
        nullable=False,
        default={},
        server_default=text("'{}'::json"),
    )  # Node-specific config z node.data.config

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    workflow = relationship("Workflow", back_populates="steps")

    # Constraints
    __table_args__ = (
        UniqueConstraint('workflow_id', 'node_id', name='uq_workflow_step_node'),
        Index('idx_workflow_steps_workflow_id', 'workflow_id'),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<WorkflowStep id={self.id} node_id={self.node_id!r} type={self.step_type}>"


class WorkflowExecution(Base):
    """
    Model WorkflowExecution - historia wykonań workflow

    Śledzi asynchroniczne wykonanie workflow z pełnym tracking statusu,
    wyników każdego kroku i potencjalnych błędów.

    Attributes:
        id: UUID wykonania (klucz główny)
        workflow_id: UUID workflow które jest wykonywane
        triggered_by: UUID użytkownika który uruchomił workflow
        status: Status wykonania (ExecutionStatusEnum):
            - pending: Queued
            - running: In progress
            - completed: Success
            - failed: Error
        current_step_id: UUID aktualnie wykonywanego kroku (nullable)
        result_data: JSON z wynikami każdego kroku {step_node_id: {persona_ids: [...], focus_group_id: ...}}
        error_message: Komunikat błędu (jeśli status="failed")

        # === TIMESTAMPS ===
        started_at: Data rozpoczęcia wykonania
        completed_at: Data zakończenia wykonania
        created_at: Data utworzenia rekordu execution

    Relations:
        workflow: Workflow które jest wykonywane
        current_step: Aktualnie wykonywany krok (WorkflowStep)
    """
    __tablename__ = "workflow_executions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
    )
    triggered_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    # Execution state
    status = Column(
        String(50),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
    )  # ExecutionStatusEnum: pending, running, completed, failed
    current_step_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("workflow_steps.id"),
        nullable=True,
    )

    # Results & errors
    result_data = Column(JSON, nullable=True)  # {step_node_id: {persona_ids: [...], focus_group_id: ...}}
    error_message = Column(Text, nullable=True)

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    current_step = relationship("WorkflowStep", foreign_keys=[current_step_id])

    # Indexes
    __table_args__ = (
        Index('idx_workflow_executions_workflow_id', 'workflow_id'),
        Index('idx_workflow_executions_status', 'status'),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<WorkflowExecution id={self.id} workflow_id={self.workflow_id} status={self.status}>"
