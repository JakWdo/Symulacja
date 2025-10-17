"""
Archived Pydantic models for personas summary responses.

The frontend no longer consumes the `/personas/summary` endpoint, but we keep
the schemas here to make reinstating the dashboard trivial if needed.
"""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PersonasSummarySegment(BaseModel):
    """Information about a segment in the personas summary dashboard."""

    segment_id: Optional[str]
    segment_name: Optional[str]
    active_personas: int
    archived_personas: int


class PersonasSummaryResponse(BaseModel):
    """Aggregated summary of personas for a project."""

    project_id: UUID
    total_personas: int
    active_personas: int
    archived_personas: int
    segments: List[PersonasSummarySegment] = Field(default_factory=list)
