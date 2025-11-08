"""
Pydantic schemas dla Study Designer Chat API

Request/Response schemas dla wszystkich endpointów Study Designer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


# === REQUEST SCHEMAS ===


class SessionCreate(BaseModel):
    """Request do utworzenia nowej sesji."""

    project_id: UUID | None = Field(
        None, description="UUID projektu (opcjonalnie, może być utworzony później)"
    )


class MessageSend(BaseModel):
    """Request do wysłania wiadomości."""

    message: str = Field(..., min_length=1, max_length=5000, description="Treść wiadomości")


class PlanApproval(BaseModel):
    """Request do zatwierdzenia planu (może być pusty)."""

    approved: bool = Field(True, description="Czy plan zatwierdzony")


# === RESPONSE SCHEMAS ===


class MessageResponse(BaseModel):
    """Response pojedynczej wiadomości."""

    id: UUID
    role: Literal["user", "assistant", "system"]
    content: str
    metadata: dict = {}
    created_at: datetime

    class Config:
        from_attributes = True


class GeneratedPlanResponse(BaseModel):
    """Response wygenerowanego planu badania."""

    markdown_summary: str = Field(..., description="Pełny plan w markdown")
    estimated_time_seconds: int = Field(..., description="Szacowany czas wykonania w sekundach")
    estimated_cost_usd: float = Field(..., description="Szacowany koszt w USD")
    estimated_tokens: int | None = Field(None, description="Szacowana liczba tokenów")


class SessionResponse(BaseModel):
    """Response sesji Study Designer."""

    id: UUID
    user_id: UUID
    project_id: UUID | None
    status: str  # active, plan_ready, approved, executing, completed, cancelled
    current_stage: str  # welcome, gather_goal, define_audience, etc.
    generated_plan: GeneratedPlanResponse | None = None
    created_workflow_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    messages: list[MessageResponse] = []  # Tylko jeśli załadowane

    class Config:
        from_attributes = True


class SessionCreateResponse(BaseModel):
    """Response po utworzeniu sesji."""

    session: SessionResponse
    welcome_message: str = Field(..., description="Welcome message od AI")


class MessageSendResponse(BaseModel):
    """Response po wysłaniu wiadomości."""

    session: SessionResponse
    new_messages: list[MessageResponse] = Field(
        ..., description="Nowe wiadomości (asystent)"
    )
    plan_ready: bool = Field(False, description="Czy plan został wygenerowany")


class SessionListResponse(BaseModel):
    """Response listy sesji użytkownika."""

    sessions: list[SessionResponse]
    total: int
