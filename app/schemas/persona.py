from typing import List, Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PersonaGenerateRequest(BaseModel):
    num_personas: int = Field(
        default=10,
        ge=2,
        le=100,
        description="Number of personas to generate (2-100)"
    )
    adversarial_mode: bool = Field(
        default=False,
        description="Generate adversarial personas for campaign stress testing",
    )


class PersonaResponse(BaseModel):
    id: UUID
    project_id: UUID
    age: int
    gender: str
    location: Optional[str]
    education_level: Optional[str]
    income_bracket: Optional[str]
    occupation: Optional[str]
    openness: Optional[float]
    conscientiousness: Optional[float]
    extraversion: Optional[float]
    agreeableness: Optional[float]
    neuroticism: Optional[float]
    power_distance: Optional[float]
    individualism: Optional[float]
    masculinity: Optional[float]
    uncertainty_avoidance: Optional[float]
    long_term_orientation: Optional[float]
    indulgence: Optional[float]
    values: Optional[List[str]]
    interests: Optional[List[str]]
    background_story: Optional[str]
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
