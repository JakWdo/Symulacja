from typing import List, Optional, Literal, Dict
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PersonaGenerationAdvancedOptions(BaseModel):
    age_focus: Optional[Literal['balanced', 'young_adults', 'experienced_leaders']] = None
    gender_balance: Optional[Literal['balanced', 'female_skew', 'male_skew']] = None
    urbanicity: Optional[Literal['any', 'urban', 'suburban', 'rural']] = None
    target_cities: Optional[List[str]] = None
    target_countries: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    required_values: Optional[List[str]] = None
    excluded_values: Optional[List[str]] = None
    required_interests: Optional[List[str]] = None
    excluded_interests: Optional[List[str]] = None
    age_min: Optional[int] = Field(None, ge=18, le=90)
    age_max: Optional[int] = Field(None, ge=18, le=90)
    custom_age_groups: Optional[Dict[str, float]] = Field(
        None,
        description="Custom age group distribution, e.g., {'18-22': 0.3, '23-29': 0.4, '30-40': 0.3}"
    )
    gender_weights: Optional[Dict[str, float]] = Field(
        None,
        description="Custom gender distribution weights"
    )
    location_weights: Optional[Dict[str, float]] = Field(
        None,
        description="Custom location distribution weights"
    )
    education_weights: Optional[Dict[str, float]] = Field(
        None,
        description="Custom education level distribution weights"
    )
    income_weights: Optional[Dict[str, float]] = Field(
        None,
        description="Custom income bracket distribution weights"
    )
    personality_skew: Optional[Dict[str, float]] = Field(
        None,
        description="Skew Big Five personality traits (openness, conscientiousness, extraversion, agreeableness, neuroticism). Values 0.0-1.0 shift mean towards low/high."
    )


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
    advanced_options: Optional[PersonaGenerationAdvancedOptions] = Field(
        default=None,
        description="Optional advanced persona targeting controls",
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
    full_name: Optional[str]
    persona_title: Optional[str]
    headline: Optional[str]
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
