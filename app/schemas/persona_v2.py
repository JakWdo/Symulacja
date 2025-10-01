"""
Enhanced Persona schemas with better structure and readability
Backward compatible with v1 through mappers
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class GeoLocation(BaseModel):
    """Geographic location details"""
    city: str
    state: Optional[str] = None
    country: str = "United States"
    timezone: Optional[str] = None


class EducationInfo(BaseModel):
    """Education details"""
    level: str = Field(..., description="Education level (e.g., Bachelor's degree)")
    field: Optional[str] = Field(None, description="Field of study")
    institution: Optional[str] = None


class IncomeInfo(BaseModel):
    """Income details"""
    bracket: str = Field(..., description="Income bracket (e.g., $50k-$75k)")
    currency: str = "USD"
    employment_status: Optional[str] = None


class OccupationInfo(BaseModel):
    """Occupation details"""
    title: str
    industry: Optional[str] = None
    seniority_level: Optional[str] = None
    years_of_experience: Optional[int] = None


class PersonaDemographics(BaseModel):
    """Demographic information"""
    age: int = Field(..., ge=18, le=100)
    age_group: str
    gender: str
    location: GeoLocation
    education: EducationInfo
    income: IncomeInfo
    occupation: OccupationInfo


class BigFiveTraits(BaseModel):
    """Big Five personality traits (OCEAN)"""
    openness: float = Field(..., ge=0.0, le=1.0)
    conscientiousness: float = Field(..., ge=0.0, le=1.0)
    extraversion: float = Field(..., ge=0.0, le=1.0)
    agreeableness: float = Field(..., ge=0.0, le=1.0)
    neuroticism: float = Field(..., ge=0.0, le=1.0)


class HofstedeDimensions(BaseModel):
    """Hofstede cultural dimensions"""
    power_distance: float = Field(..., ge=0.0, le=1.0)
    individualism: float = Field(..., ge=0.0, le=1.0)
    masculinity: float = Field(..., ge=0.0, le=1.0)
    uncertainty_avoidance: float = Field(..., ge=0.0, le=1.0)
    long_term_orientation: float = Field(..., ge=0.0, le=1.0)
    indulgence: float = Field(..., ge=0.0, le=1.0)


class CognitiveProfile(BaseModel):
    """Cognitive and decision-making style"""
    decision_making_style: str
    communication_style: str
    learning_preference: Optional[str] = None
    risk_tolerance: Optional[float] = Field(None, ge=0.0, le=1.0)


class PersonaPsychology(BaseModel):
    """Psychological profile"""
    big_five: BigFiveTraits
    hofstede: HofstedeDimensions
    cognitive_style: CognitiveProfile


class LifestyleSegment(BaseModel):
    """Lifestyle and life stage information"""
    life_stage: Optional[str] = Field(None, description="e.g., 'Young Professional', 'Empty Nester'")
    family_status: Optional[str] = None
    living_situation: Optional[str] = None
    tech_savviness: Optional[float] = Field(None, ge=0.0, le=1.0)


class PersonaProfile(BaseModel):
    """Personal profile and preferences"""
    values: List[str] = Field(default_factory=list, max_length=10)
    interests: List[str] = Field(default_factory=list, max_length=15)
    lifestyle: LifestyleSegment
    background_story: str
    motivations: Optional[List[str]] = Field(default_factory=list, max_length=5)
    pain_points: Optional[List[str]] = Field(default_factory=list, max_length=5)


class PersonaMetadata(BaseModel):
    """Metadata about persona generation"""
    generator_version: str = "v2"
    model_used: Optional[str] = None
    generation_prompt: Optional[str] = None
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    diversity_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PersonaV2(BaseModel):
    """Enhanced Persona model v2 with structured data"""
    id: str
    project_id: str
    demographics: PersonaDemographics
    psychology: PersonaPsychology
    profile: PersonaProfile
    metadata: PersonaMetadata
    is_active: bool = True

    class Config:
        from_attributes = True


class PersonaV2Create(BaseModel):
    """Schema for creating a new persona v2"""
    project_id: str
    demographics: PersonaDemographics
    psychology: PersonaPsychology
    profile: PersonaProfile
    metadata: Optional[PersonaMetadata] = None


class CustomDemographicDistribution(BaseModel):
    """Custom demographic distribution for persona generation"""
    age_groups: Optional[Dict[str, float]] = None
    genders: Optional[Dict[str, float]] = None
    education_levels: Optional[Dict[str, float]] = None
    income_brackets: Optional[Dict[str, float]] = None
    locations: Optional[Dict[str, float]] = None

    @field_validator('age_groups', 'genders', 'education_levels', 'income_brackets', 'locations')
    @classmethod
    def validate_distribution(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        """Validate that distribution sums to ~1.0"""
        if v is None:
            return v
        total = sum(v.values())
        if not (0.95 <= total <= 1.05):
            raise ValueError(f"Distribution must sum to ~1.0, got {total}")
        return v


class GeographicConstraints(BaseModel):
    """Geographic filtering for persona generation"""
    countries: Optional[List[str]] = None
    states: Optional[List[str]] = None
    cities: Optional[List[str]] = None
    urban_rural_ratio: Optional[float] = Field(None, ge=0.0, le=1.0, description="0=rural, 1=urban")


class PsychographicTargets(BaseModel):
    """Psychographic targeting parameters"""
    required_values: Optional[List[str]] = None
    excluded_values: Optional[List[str]] = None
    required_interests: Optional[List[str]] = None
    excluded_interests: Optional[List[str]] = None
    personality_ranges: Optional[Dict[str, tuple[float, float]]] = None


class OccupationFilter(BaseModel):
    """Occupation filtering"""
    whitelist: Optional[List[str]] = None
    blacklist: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    seniority_levels: Optional[List[str]] = None


class CustomPersonaGenerateRequest(BaseModel):
    """Enhanced persona generation request with custom parameters"""
    num_personas: int = Field(..., ge=10, le=1000, description="Number of personas to generate")
    adversarial_mode: bool = False

    # Custom distributions
    custom_demographics: Optional[CustomDemographicDistribution] = None

    # Advanced filters
    geographic_constraints: Optional[GeographicConstraints] = None
    psychographic_targets: Optional[PsychographicTargets] = None
    occupation_filter: Optional[OccupationFilter] = None

    # Age override
    age_range_override: Optional[tuple[int, int]] = Field(
        None,
        description="Override age range, e.g., (25, 45)"
    )

    # Cultural context
    cultural_dimensions_target: Optional[Dict[str, float]] = Field(
        None,
        description="Target values for Hofstede dimensions"
    )

    # Diversity control
    ensure_diversity: bool = Field(True, description="Ensure diversity in generated personas")
    similarity_threshold: float = Field(0.75, ge=0.0, le=1.0, description="Min diversity threshold")


# ============================================================================
# BACKWARD COMPATIBILITY MAPPERS
# ============================================================================

def persona_v1_to_v2(v1_data: dict) -> PersonaV2:
    """Map v1 persona data to v2 structure"""

    # Parse location string to GeoLocation
    location_str = v1_data.get("location") or "Unknown, Unknown"
    city_parts = location_str.split(",")
    city = city_parts[0].strip() if city_parts else "Unknown"
    state = city_parts[1].strip() if len(city_parts) > 1 else None

    demographics = PersonaDemographics(
        age=v1_data["age"],
        age_group=_infer_age_group(v1_data["age"]),
        gender=v1_data["gender"],
        location=GeoLocation(
            city=city,
            state=state,
            country="United States"
        ),
        education=EducationInfo(
            level=v1_data.get("education_level") or "Unknown",
            field=None
        ),
        income=IncomeInfo(
            bracket=v1_data.get("income_bracket") or "Unknown",
            employment_status=None
        ),
        occupation=OccupationInfo(
            title=v1_data.get("occupation") or "Unknown",
            industry=None,
            seniority_level=None
        )
    )

    psychology = PersonaPsychology(
        big_five=BigFiveTraits(
            openness=v1_data.get("openness") or 0.5,
            conscientiousness=v1_data.get("conscientiousness") or 0.5,
            extraversion=v1_data.get("extraversion") or 0.5,
            agreeableness=v1_data.get("agreeableness") or 0.5,
            neuroticism=v1_data.get("neuroticism") or 0.5
        ),
        hofstede=HofstedeDimensions(
            power_distance=v1_data.get("power_distance") or 0.5,
            individualism=v1_data.get("individualism") or 0.5,
            masculinity=v1_data.get("masculinity") or 0.5,
            uncertainty_avoidance=v1_data.get("uncertainty_avoidance") or 0.5,
            long_term_orientation=v1_data.get("long_term_orientation") or 0.5,
            indulgence=v1_data.get("indulgence") or 0.5
        ),
        cognitive_style=CognitiveProfile(
            decision_making_style="Unknown",
            communication_style="Unknown"
        )
    )

    profile = PersonaProfile(
        values=v1_data.get("values") or [],
        interests=v1_data.get("interests") or [],
        lifestyle=LifestyleSegment(),
        background_story=v1_data.get("background_story") or ""
    )

    metadata = PersonaMetadata(
        generator_version="v1_migrated",
        generation_prompt=v1_data.get("personality_prompt"),
        created_at=v1_data.get("created_at")
    )

    return PersonaV2(
        id=str(v1_data["id"]),
        project_id=str(v1_data["project_id"]),
        demographics=demographics,
        psychology=psychology,
        profile=profile,
        metadata=metadata,
        is_active=v1_data.get("is_active", True)
    )


def persona_v2_to_v1(v2: PersonaV2) -> dict:
    """Map v2 persona back to v1 structure for backward compatibility"""
    return {
        "id": v2.id,
        "project_id": v2.project_id,
        "age": v2.demographics.age,
        "gender": v2.demographics.gender,
        "location": f"{v2.demographics.location.city}, {v2.demographics.location.state or ''}".strip(", "),
        "education_level": v2.demographics.education.level,
        "income_bracket": v2.demographics.income.bracket,
        "occupation": v2.demographics.occupation.title,
        "openness": v2.psychology.big_five.openness,
        "conscientiousness": v2.psychology.big_five.conscientiousness,
        "extraversion": v2.psychology.big_five.extraversion,
        "agreeableness": v2.psychology.big_five.agreeableness,
        "neuroticism": v2.psychology.big_five.neuroticism,
        "power_distance": v2.psychology.hofstede.power_distance,
        "individualism": v2.psychology.hofstede.individualism,
        "masculinity": v2.psychology.hofstede.masculinity,
        "uncertainty_avoidance": v2.psychology.hofstede.uncertainty_avoidance,
        "long_term_orientation": v2.psychology.hofstede.long_term_orientation,
        "indulgence": v2.psychology.hofstede.indulgence,
        "values": v2.profile.values,
        "interests": v2.profile.interests,
        "background_story": v2.profile.background_story,
        "personality_prompt": v2.metadata.generation_prompt,
        "created_at": v2.metadata.created_at,
        "is_active": v2.is_active
    }


def _infer_age_group(age: int) -> str:
    """Infer age group from age"""
    if age < 25:
        return "18-24"
    elif age < 35:
        return "25-34"
    elif age < 45:
        return "35-44"
    elif age < 55:
        return "45-54"
    elif age < 65:
        return "55-64"
    else:
        return "65+"
