"""
Schematy Pydantic dla Szczegółowego Widoku Persony (MVP)

Definiuje struktury danych dla:
- PersonaDetailsResponse - pełny detail view
- NeedsAndPains - JTBD, desired outcomes, pain points
- PersonaExportRequest - żądanie eksportu
- PersonaDeleteRequest - żądanie usunięcia
- PersonaAuditEntry - wpis w audit log
- PersonaMessagingRequest/Response - generowanie komunikatów
- PersonaComparisonRequest/Response - porównywanie person
"""

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# KPISnapshot model removed - deprecated in favor of real-time metrics


class PersonaDetailsResponse(BaseModel):
    """
    Response dla GET /personas/{id}/details

    Pełny detail view persony z wszystkimi danymi:
    - Base persona data (demographics, psychographics)
    - Needs and pains (optional - JTBD, desired outcomes, pain points)
    - RAG insights (z rag_context_details)
    - Audit log (last 10 actions)
    - Metadata

    Graceful degradation: Jeśli część danych nie jest dostępna, zwróć None dla tych pól.
    """

    # Base persona data
    id: UUID
    project_id: UUID
    full_name: str | None
    persona_title: str | None
    headline: str | None
    age: int
    gender: str
    location: str | None
    education_level: str | None
    income_bracket: str | None
    occupation: str | None

    # Psychographics
    big_five: dict[str, float | None] = Field(
        default_factory=dict, description="Big Five personality traits"
    )
    hofstede: dict[str, float | None] = Field(
        default_factory=dict, description="Hofstede cultural dimensions"
    )
    values: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    background_story: str | None

    # Computed/JSONB fields (graceful degradation - może być None)
    needs_and_pains: Optional["NeedsAndPains"] = None

    # RAG data
    rag_context_used: bool = False
    rag_citations: list[dict[str, Any]] | None = None
    rag_context_details: dict[str, Any] | None = None

    # Audit log (last 10 actions)
    audit_log: list["PersonaAuditEntry"] = Field(default_factory=list)

    # Metadata
    segment_id: str | None = None
    segment_name: str | None = None
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class PersonaExportRequest(BaseModel):
    """
    Request dla POST /personas/{id}/actions/export

    Konfiguracja eksportu persony do PDF/CSV/JSON:
    - format: Format pliku
    - sections: Które sekcje uwzględnić
    - include_watermark: Czy dodać watermark
    - pii_mask: Czy maskować PII (True dla Viewer/Editor, False tylko dla Admin)

    Example:
        >>> export_req = PersonaExportRequest(
        ...     format="pdf",
        ...     sections=["overview", "profile", "behaviors"],
        ...     include_watermark=True
        ... )
    """

    format: Literal["pdf", "csv", "json"] = Field(..., description="Format pliku")
    sections: list[str] = Field(
        default=["overview", "profile", "behaviors"],
        description="Które sekcje uwzględnić",
    )
    include_watermark: bool = Field(
        default=True, description="Czy dodać watermark do PDF"
    )


class PersonaExportResponse(BaseModel):
    format: Literal["pdf", "csv", "json"]
    sections: list[str]
    content: dict[str, Any]


# JourneyTouchpoint, JourneyStage, and CustomerJourney models removed
# - deprecated in favor of journey service


class JTBDJob(BaseModel):
    job_statement: str
    priority_score: int | None = Field(default=None, ge=1, le=10)
    frequency: str | None = None
    difficulty: str | None = None
    quotes: list[str] = Field(default_factory=list)


class DesiredOutcome(BaseModel):
    outcome_statement: str
    importance: int | None = Field(default=None, ge=1, le=10)
    satisfaction_current_solutions: int | None = Field(default=None, ge=1, le=10)
    opportunity_score: float | None = None
    is_measurable: bool | None = None


class PainPoint(BaseModel):
    pain_title: str
    pain_description: str | None = None
    severity: int | None = Field(default=None, ge=1, le=10)
    frequency: str | None = None
    percent_affected: float | None = Field(default=None, ge=0.0, le=1.0)
    quotes: list[str] = Field(default_factory=list)
    potential_solutions: list[str] = Field(default_factory=list)


class NeedsAndPains(BaseModel):
    jobs_to_be_done: list[JTBDJob] = Field(default_factory=list)
    desired_outcomes: list[DesiredOutcome] = Field(default_factory=list)
    pain_points: list[PainPoint] = Field(default_factory=list)
    generated_at: datetime | None = None
    generated_by: str | None = None


class PersonaMessagingRequest(BaseModel):
    tone: Literal["friendly", "professional", "urgent", "empathetic"]
    message_type: Literal["email", "ad", "landing_page", "social_post"] = Field(
        alias="type"
    )
    num_variants: int = Field(default=3, ge=1, le=5)
    context: str | None = Field(
        default=None, description="Dodatkowy kontekst kampanii"
    )

    class Config:
        populate_by_name = True


class MessagingVariant(BaseModel):
    variant_id: int
    headline: str
    subheadline: str | None = None
    body: str
    cta: str


class PersonaMessagingResponse(BaseModel):
    variants: list[MessagingVariant]
    generated_at: datetime
    generated_by: str | None = None


class PersonaComparisonRequest(BaseModel):
    persona_ids: list[UUID] = Field(
        ...,
        description="Lista innych person do porównania (max 2, bez persony głównej)",
        min_length=0,
        max_length=2,
    )
    sections: list[str] | None = Field(
        default=None,
        description="Sekcje do porównania (demographics, psychographics, kpi)",
    )


class PersonaComparisonValue(BaseModel):
    persona_id: UUID
    value: Any


class PersonaDifference(BaseModel):
    field: str
    values: list[PersonaComparisonValue]


class PersonaComparisonPersona(BaseModel):
    id: UUID
    full_name: str | None
    age: int
    gender: str
    location: str | None
    occupation: str | None
    education_level: str | None
    segment_id: str | None
    segment_name: str | None
    values: list[str]
    interests: list[str]
    big_five: dict[str, float | None]
    # kpi_snapshot removed - deprecated


class PersonaComparisonResponse(BaseModel):
    personas: list[PersonaComparisonPersona]
    differences: list[PersonaDifference]
    similarity: dict[str, dict[str, float]]


class PersonaDeleteRequest(BaseModel):
    """
    Request dla DELETE /personas/{id}

    Powód usunięcia persony (do audit log):
    - reason: Kategoria powodu
    - reason_detail: Szczegóły (wymagane jeśli reason="other")

    Example:
        >>> delete_req = PersonaDeleteRequest(
        ...     reason="duplicate",
        ...     reason_detail="Duplicate of persona XYZ"
        ... )
    """

    reason: Literal["duplicate", "outdated", "test_data", "other"] = Field(
        ..., description="Kategoria powodu usunięcia"
    )
    reason_detail: str | None = Field(
        None,
        max_length=500,
        description="Szczegóły powodu (wymagane jeśli reason=other)",
    )


class PersonaDeleteResponse(BaseModel):
    """Response dla soft delete persony z metadanymi oraz oknem undo."""

    persona_id: UUID
    full_name: str | None
    status: Literal["deleted"]
    deleted_at: datetime
    deleted_by: UUID
    undo_available_until: datetime
    permanent_deletion_scheduled_at: datetime | None = None
    message: str


class PersonaUndoDeleteResponse(BaseModel):
    """Response dla udanego przywrócenia persony."""

    persona_id: UUID
    full_name: str | None
    status: Literal["active"]
    restored_at: datetime
    restored_by: UUID
    message: str


class PersonasSummarySegment(BaseModel):
    """Informacje o segmencie w podsumowaniu person projektu."""

    segment_id: str | None
    segment_name: str | None
    active_personas: int
    archived_personas: int


class PersonasSummaryResponse(BaseModel):
    """Podsumowanie person projektu (dashboard view)."""

    project_id: UUID
    total_personas: int
    active_personas: int
    archived_personas: int
    segments: list[PersonasSummarySegment] = Field(default_factory=list)


class PersonaAuditEntry(BaseModel):
    """
    Wpis w audit log persony

    Reprezentuje pojedynczą akcję na personie:
    - action: Typ akcji (view, export, compare, delete, etc.)
    - details: Szczegóły akcji (JSON)
    - user_id: Kto wykonał akcję
    - timestamp: Kiedy

    Example:
        >>> entry = PersonaAuditEntry(
        ...     id=UUID(...),
        ...     action="export",
        ...     details={"format": "pdf", "sections": ["overview"]},
        ...     user_id=UUID(...),
        ...     timestamp=datetime.utcnow()
        ... )
    """

    id: UUID
    action: str = Field(..., description="Typ akcji")
    details: dict[str, Any] | None = Field(
        None, description="Szczegóły akcji (JSON)"
    )
    user_id: UUID | None = Field(None, description="Kto wykonał akcję")
    timestamp: datetime = Field(..., description="Kiedy")

    class Config:
        from_attributes = True


# Rebuild PersonaDetailsResponse AFTER all forward references are defined
PersonaDetailsResponse.model_rebuild()
