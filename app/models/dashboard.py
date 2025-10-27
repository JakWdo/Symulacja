"""
Dashboard Models - Modele dla dashboardu, metryk i monitoringu

Zawiera:
- DashboardMetric: Metryki KPI (TTI, adoption rate, coverage, trends)
- ProjectHealthLog: Historia health status projektów (time-series)
- InsightEvidence: Traceability dla insights + evidence trail
- UsageMetric: Token usage & cost tracking per operation
- UserNotification: System notifications & alerts
- ActionLog: Event sourcing - user actions log (observability)
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class DashboardMetric(Base):
    """
    Metryki KPI dla dashboardu

    Przechowuje wyliczone metryki dzienne/tygodniowe:
    - time_to_insight: Mediana czasu od utworzenia projektu do pierwszego insightu (seconds)
    - time_to_insight_p90: P90 czasu do insightu
    - insight_adoption_rate: % insightów oznaczonych jako adopted/exported/shared
    - active_projects_count: Liczba aktywnych projektów
    - blocked_projects_count: Liczba zablokowanych projektów
    - persona_coverage_avg: Średnie % demographic coverage
    - weekly_*: Liczniki operacji w tym tygodniu

    Attributes:
        id: UUID metryki (klucz główny)
        user_id: UUID użytkownika (NULL = global metrics)
        metric_date: Data metryki (dzień)
        time_to_insight_median: Mediana czasu do insightu (sekundy)
        time_to_insight_p90: P90 czasu do insightu (sekundy)
        insight_adoption_rate: Wskaźnik adopcji insightów (0-1)
        active_projects_count: Liczba aktywnych projektów
        blocked_projects_count: Liczba zablokowanych projektów
        persona_coverage_avg: Średnie pokrycie demograficzne (0-1)
        weekly_personas_generated: Liczba wygenerowanych person w tym tygodniu
        weekly_focus_groups_completed: Liczba ukończonych grup fokusowych w tym tygodniu
        weekly_insights_extracted: Liczba wyekstrahowanych insightów w tym tygodniu
        created_at: Data utworzenia rekordu

    Relations:
        user: Użytkownik (nullable - global metrics gdy NULL)
    """

    __tablename__ = "dashboard_metrics"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    metric_date = Column(Date, nullable=False, index=True)
    time_to_insight_median = Column(Float, nullable=True)  # seconds
    time_to_insight_p90 = Column(Float, nullable=True)  # seconds
    insight_adoption_rate = Column(Float, nullable=True)  # 0-1
    active_projects_count = Column(Integer, nullable=False, default=0)
    blocked_projects_count = Column(Integer, nullable=False, default=0)
    persona_coverage_avg = Column(Float, nullable=True)  # 0-1
    weekly_personas_generated = Column(Integer, nullable=False, default=0)
    weekly_focus_groups_completed = Column(Integer, nullable=False, default=0)
    weekly_insights_extracted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<DashboardMetric user_id={self.user_id} date={self.metric_date}>"


class ProjectHealthLog(Base):
    """
    Historia health status projektu (time-series)

    Zapisuje snapshot health status każdego projektu w czasie:
    - health_status: 'on_track' | 'at_risk' | 'blocked'
    - health_score: 0-100 (numeric score based on blockers)
    - blockers: JSON array z blokerami i ich severity

    Umożliwia tracking zmian health status w czasie i analytics.

    Attributes:
        id: UUID logu (klucz główny)
        project_id: UUID projektu
        health_status: Status zdrowia projektu ('on_track', 'at_risk', 'blocked')
        health_score: Numeryczny score 0-100
        blockers: JSON z listą blokerów [{"type": "no_personas", "severity": "high", ...}]
        checked_at: Data sprawdzenia health status

    Relations:
        project: Projekt (cascade delete)
    """

    __tablename__ = "project_health_logs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    health_status = Column(String(50), nullable=False)  # 'on_track', 'at_risk', 'blocked'
    health_score = Column(Integer, nullable=False)  # 0-100
    blockers = Column(JSON, nullable=False, default=list)  # [{"type": "...", "severity": "...", ...}]
    checked_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    # Relationships
    project = relationship("Project", back_populates="health_logs")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<ProjectHealthLog project_id={self.project_id} status={self.health_status} score={self.health_score}>"


class InsightEvidence(Base):
    """
    Traceability dla insights - evidence trail & provenance

    Przechowuje:
    - Insight text: Wyekstrahowany insight z focus group
    - Evidence: Cytaty, snippety, koncepty wspierające insight
    - Provenance: Model version, prompt hash, sources, timestamp (reproducibility)
    - Adoption tracking: viewed, shared, exported, adopted timestamps
    - Scoring: confidence (0-1), impact (1-10)

    Umożliwia:
    - Traceability: "Skąd pochodzi ten insight?"
    - Reproducibility: "Jak został wygenerowany?"
    - Adoption analytics: "Czy użytkownicy działają na podstawie insightów?"

    Attributes:
        id: UUID insightu (klucz główny)
        project_id: UUID projektu
        focus_group_id: UUID grupy fokusowej (nullable - może być z innego źródła)
        insight_type: Typ insightu ('opportunity', 'risk', 'trend', 'pattern')
        insight_text: Treść insightu
        confidence_score: Pewność modelu (0-1)
        impact_score: Ocena wpływu (1-10)
        evidence: JSON z evidence [{"type": "quote", "text": "...", "source": "persona_X", ...}]
        concepts: JSON z kluczowymi konceptami ["concept1", "concept2", ...]
        sentiment: Sentiment insightu ('positive', 'negative', 'neutral', 'mixed')
        model_version: Wersja modelu użyta do generacji
        prompt_hash: SHA256 hash promptu (reproducibility)
        sources: JSON z source references [{"type": "focus_group_message", "id": "uuid", ...}]
        viewed_at: Data pierwszego wyświetlenia
        shared_at: Data udostępnienia
        exported_at: Data eksportu
        adopted_at: Data oznaczenia jako "adopted" (działanie użytkownika)
        created_at: Data utworzenia

    Relations:
        project: Projekt
        focus_group: Grupa fokusowa (nullable)
    """

    __tablename__ = "insight_evidences"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    focus_group_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("focus_groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    insight_type = Column(String(100), nullable=False)  # 'opportunity', 'risk', 'trend', 'pattern'
    insight_text = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)  # 0-1
    impact_score = Column(Integer, nullable=False)  # 1-10

    # Evidence & Context
    evidence = Column(JSON, nullable=False, default=list)  # [{"type": "quote", "text": "...", ...}]
    concepts = Column(JSON, nullable=False, default=list)  # ["concept1", "concept2", ...]
    sentiment = Column(String(50), nullable=True)  # 'positive', 'negative', 'neutral', 'mixed'

    # Provenance (reproducibility & transparency)
    model_version = Column(String(100), nullable=False)  # 'gemini-2.5-flash'
    prompt_hash = Column(String(64), nullable=True)  # SHA256 hash
    sources = Column(JSON, nullable=False, default=list)  # [{"type": "focus_group_message", "id": "uuid"}]

    # Adoption tracking
    viewed_at = Column(DateTime(timezone=True), nullable=True)
    shared_at = Column(DateTime(timezone=True), nullable=True)
    exported_at = Column(DateTime(timezone=True), nullable=True)
    adopted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    project = relationship("Project")
    focus_group = relationship("FocusGroup")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<InsightEvidence id={self.id} type={self.insight_type} confidence={self.confidence_score:.2f}>"


class UsageMetric(Base):
    """
    Token usage & cost tracking per operation

    Loguje każdą operację LLM z:
    - Token usage (input, output, total)
    - Cost calculation (input_cost, output_cost, total_cost in USD)
    - Model używany
    - Context operacji (user, project, operation type)

    Umożliwia:
    - Budget tracking
    - Cost forecasting
    - Usage analytics per user/project/operation
    - Budget alerts (>90% usage)

    Attributes:
        id: UUID metryki (klucz główny)
        user_id: UUID użytkownika
        project_id: UUID projektu (nullable - niektóre operacje globalne)
        operation_type: Typ operacji ('persona_generation', 'focus_group', 'analysis', 'insight_extraction')
        operation_id: UUID konkretnej operacji (persona.id, focus_group.id, nullable)
        input_tokens: Liczba tokenów wejściowych
        output_tokens: Liczba tokenów wyjściowych
        total_tokens: Suma tokenów
        input_cost: Koszt tokenów wejściowych (USD)
        output_cost: Koszt tokenów wyjściowych (USD)
        total_cost: Łączny koszt (USD)
        model_name: Nazwa modelu ('gemini-2.5-flash', 'gemini-2.5-pro')
        operation_timestamp: Data i czas operacji

    Relations:
        user: Użytkownik
        project: Projekt (nullable)
    """

    __tablename__ = "usage_metrics"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    operation_type = Column(String(100), nullable=False, index=True)  # 'persona_generation', 'focus_group', etc.
    operation_id = Column(PGUUID(as_uuid=True), nullable=True)  # ID konkretnej operacji

    # Token usage
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)

    # Cost (USD)
    input_cost = Column(Float, nullable=False)
    output_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)

    # Model used
    model_name = Column(String(100), nullable=False)  # 'gemini-2.5-flash', 'gemini-2.5-pro'

    operation_timestamp = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    project = relationship("Project", foreign_keys=[project_id])

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<UsageMetric operation={self.operation_type} tokens={self.total_tokens} cost=${self.total_cost:.4f}>"


class UserNotification(Base):
    """
    System notifications & alerts dla użytkowników

    Typy notyfikacji:
    - insights_ready: Nowe insighty dostępne do przejrzenia
    - focus_idle_48h: Focus group bezczynny >48h
    - confidence_drop: Spadek confidence score <0.5
    - low_coverage: Niska persona coverage <60%
    - budget_exceeded: Przekroczono 90% budżetu tokenów
    - project_blocked: Projekt zablokowany (critical blockers)

    Attributes:
        id: UUID notyfikacji (klucz główny)
        user_id: UUID użytkownika
        notification_type: Typ notyfikacji
        priority: Priorytet ('high', 'medium', 'low')
        title: Tytuł notyfikacji (krótki)
        message: Treść notyfikacji (szczegółowa)
        project_id: UUID projektu (nullable - context)
        focus_group_id: UUID focus group (nullable - context)
        action_url: URL do akcji (np. /projects/{id})
        action_label: Label przycisku akcji (np. "View Insights")
        is_read: Czy przeczytana
        is_done: Czy wykonana (dismissed/acted upon)
        read_at: Data przeczytania
        done_at: Data wykonania
        created_at: Data utworzenia
        expires_at: Data wygaśnięcia (auto-delete po tym czasie)

    Relations:
        user: Użytkownik
        project: Projekt (nullable)
        focus_group: Grupa fokusowa (nullable)
    """

    __tablename__ = "user_notifications"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notification_type = Column(String(100), nullable=False, index=True)
    priority = Column(String(50), nullable=False)  # 'high', 'medium', 'low'
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Context
    project_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    focus_group_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("focus_groups.id", ondelete="CASCADE"),
        nullable=True,
    )
    action_url = Column(String(500), nullable=True)  # URL do akcji
    action_label = Column(String(100), nullable=True)  # Label przycisku

    # Status
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    is_done = Column(Boolean, nullable=False, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    done_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Auto-delete po tym czasie

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    project = relationship("Project", foreign_keys=[project_id])
    focus_group = relationship("FocusGroup", foreign_keys=[focus_group_id])

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<UserNotification type={self.notification_type} priority={self.priority} read={self.is_read}>"


class ActionLog(Base):
    """
    Event sourcing - user actions log (observability & analytics)

    Loguje product events dla observability i analytics:
    - research.created: Utworzono projekt
    - personas.generated: Wygenerowano persony
    - focus.started/resumed/completed: Akcje na focus group
    - insights.extracted: Wyekstrahowano insighty
    - insight.viewed/shared/exported/adopted: Akcje na insightach
    - blocker.detected/resolved: Zmiana statusu blokera

    Umożliwia:
    - Product analytics (funnel analysis)
    - User behavior tracking
    - Observability (co się dzieje w systemie)
    - Debugging user flows

    Attributes:
        id: UUID logu (klucz główny)
        user_id: UUID użytkownika
        project_id: UUID projektu (nullable - niektóre akcje globalne)
        event_type: Typ eventu ('research.created', 'personas.generated', etc.)
        event_data: JSON z dodatkowymi danymi eventu
        ip_address: IP użytkownika (nullable)
        user_agent: User agent przeglądarki (nullable)
        created_at: Data eventu

    Relations:
        user: Użytkownik
        project: Projekt (nullable)
    """

    __tablename__ = "action_logs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    event_type = Column(String(100), nullable=False, index=True)  # 'research.created', etc.
    event_data = Column(JSON, nullable=False, default=dict)  # {"count": 20, "duration_seconds": 45, ...}

    # Context
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    project = relationship("Project", foreign_keys=[project_id])

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<ActionLog event={self.event_type} user_id={self.user_id}>"
