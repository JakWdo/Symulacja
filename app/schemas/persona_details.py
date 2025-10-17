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
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# KPISnapshot model removed - deprecated in favor of real-time metrics


class PersonaNarratives(BaseModel):
    """
    Narracje biznesowe persony (generowane przez PersonaNarrativeService).

    5 typów narracji:
    - person_profile: 1 akapit profilu (Flash)
    - person_motivations: 2-3 akapity motywacji JTBD (Pro)
    - segment_hero: Nazwa + tagline + opis segmentu (Pro)
    - segment_significance: 1 akapit znaczenia biznesowego (Pro)
    - evidence_context: Tło dowodowe + cytowania (Pro structured output)

    Graceful degradation: Jeśli LLM call fails, pole może być None.
    """

    person_profile: Optional[str] = Field(
        None,
        description="1 akapit profilu persony (fakty demograficzne)"
    )
    person_motivations: Optional[str] = Field(
        None,
        description="2-3 akapity motywacji (JTBD + outcomes + pains)"
    )
    segment_hero: Optional[str] = Field(
        None,
        description="Segment hero: nazwa + tagline + opis grupy"
    )
    segment_significance: Optional[str] = Field(
        None,
        description="1 akapit znaczenia biznesowego segmentu"
    )
    evidence_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Tło dowodowe: {background_narrative, key_citations[]}"
    )


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
    full_name: Optional[str]
    persona_title: Optional[str]
    headline: Optional[str]
    age: int
    gender: str
    location: Optional[str]
    education_level: Optional[str]
    income_bracket: Optional[str]
    occupation: Optional[str]

    # Psychographics
    big_five: Dict[str, Optional[float]] = Field(
        default_factory=dict, description="Big Five personality traits"
    )
    hofstede: Dict[str, Optional[float]] = Field(
        default_factory=dict, description="Hofstede cultural dimensions"
    )
    values: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    background_story: Optional[str]

    # Computed/JSONB fields (graceful degradation - może być None)
    needs_and_pains: Optional["NeedsAndPains"] = None

    # RAG data
    rag_context_used: bool = False
    rag_citations: Optional[List[Dict[str, Any]]] = None
    rag_context_details: Optional[Dict[str, Any]] = None

    # Narratives (nowe pole - generowane narracje biznesowe)
    narratives: Optional["PersonaNarratives"] = None
    narratives_status: str = Field(
        default="ok",
        description="Status narracji: ok | degraded | pending | offline"
    )

    # Audit log (last 10 actions)
    audit_log: List["PersonaAuditEntry"] = Field(default_factory=list)

    # Metadata
    segment_id: Optional[str] = None
    segment_name: Optional[str] = None
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
    sections: List[str] = Field(
        default=["overview", "profile", "behaviors"],
        description="Które sekcje uwzględnić",
    )
    include_watermark: bool = Field(
        default=True, description="Czy dodać watermark do PDF"
    )


class PersonaExportResponse(BaseModel):
    format: Literal["pdf", "csv", "json"]
    sections: List[str]
    content: Dict[str, Any]


# JourneyTouchpoint, JourneyStage, and CustomerJourney models removed
# - deprecated in favor of journey service


class JTBDJob(BaseModel):
    job_statement: str
    priority_score: Optional[int] = Field(default=None, ge=1, le=10)
    frequency: Optional[str] = None
    difficulty: Optional[str] = None
    quotes: List[str] = Field(default_factory=list)


class DesiredOutcome(BaseModel):
    outcome_statement: str
    importance: Optional[int] = Field(default=None, ge=1, le=10)
    satisfaction_current_solutions: Optional[int] = Field(default=None, ge=1, le=10)
    opportunity_score: Optional[float] = None
    is_measurable: Optional[bool] = None


class PainPoint(BaseModel):
    pain_title: str
    pain_description: Optional[str] = None
    severity: Optional[int] = Field(default=None, ge=1, le=10)
    frequency: Optional[str] = None
    percent_affected: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    quotes: List[str] = Field(default_factory=list)
    potential_solutions: List[str] = Field(default_factory=list)


class NeedsAndPains(BaseModel):
    jobs_to_be_done: List[JTBDJob] = Field(default_factory=list)
    desired_outcomes: List[DesiredOutcome] = Field(default_factory=list)
    pain_points: List[PainPoint] = Field(default_factory=list)
    generated_at: Optional[datetime] = None
    generated_by: Optional[str] = None


class PersonaMessagingRequest(BaseModel):
    tone: Literal["friendly", "professional", "urgent", "empathetic"]
    message_type: Literal["email", "ad", "landing_page", "social_post"] = Field(
        alias="type"
    )
    num_variants: int = Field(default=3, ge=1, le=5)
    context: Optional[str] = Field(
        default=None, description="Dodatkowy kontekst kampanii"
    )

    class Config:
        populate_by_name = True


class MessagingVariant(BaseModel):
    variant_id: int
    headline: str
    subheadline: Optional[str] = None
    body: str
    cta: str


class PersonaMessagingResponse(BaseModel):
    variants: List[MessagingVariant]
    generated_at: datetime
    generated_by: Optional[str] = None


class PersonaComparisonRequest(BaseModel):
    persona_ids: List[UUID] = Field(
        ...,
        description="Lista innych person do porównania (max 2, bez persony głównej)",
        min_length=0,
        max_length=2,
    )
    sections: Optional[List[str]] = Field(
        default=None,
        description="Sekcje do porównania (demographics, psychographics, kpi)",
    )


class PersonaComparisonValue(BaseModel):
    persona_id: UUID
    value: Any


class PersonaDifference(BaseModel):
    field: str
    values: List[PersonaComparisonValue]


class PersonaComparisonPersona(BaseModel):
    id: UUID
    full_name: Optional[str]
    age: int
    gender: str
    location: Optional[str]
    occupation: Optional[str]
    education_level: Optional[str]
    segment_id: Optional[str]
    segment_name: Optional[str]
    values: List[str]
    interests: List[str]
    big_five: Dict[str, Optional[float]]
    # kpi_snapshot removed - deprecated


class PersonaComparisonResponse(BaseModel):
    personas: List[PersonaComparisonPersona]
    differences: List[PersonaDifference]
    similarity: Dict[str, Dict[str, float]]


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
    reason_detail: Optional[str] = Field(
        None,
        max_length=500,
        description="Szczegóły powodu (wymagane jeśli reason=other)",
    )


class PersonaDeleteResponse(BaseModel):
    """Response dla soft delete persony z metadanymi oraz oknem undo."""

    persona_id: UUID
    full_name: Optional[str]
    status: Literal["deleted"]
    deleted_at: datetime
    deleted_by: UUID
    undo_available_until: datetime
    permanent_deletion_scheduled_at: Optional[datetime] = None
    message: str


class PersonaUndoDeleteResponse(BaseModel):
    """Response dla udanego przywrócenia persony."""

    persona_id: UUID
    full_name: Optional[str]
    status: Literal["active"]
    restored_at: datetime
    restored_by: UUID
    message: str


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
    details: Optional[Dict[str, Any]] = Field(
        None, description="Szczegóły akcji (JSON)"
    )
    user_id: Optional[UUID] = Field(None, description="Kto wykonał akcję")
    timestamp: datetime = Field(..., description="Kiedy")

    class Config:
        from_attributes = True


# Rebuild PersonaDetailsResponse AFTER all forward references are defined
PersonaDetailsResponse.model_rebuild()
