from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    target_demographics: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Target population distribution. Example: {'age': {'18-24': 0.15, '25-34': 0.20}, 'gender': {'male': 0.49, 'female': 0.51}}",
    )
    target_sample_size: int = Field(default=100, ge=10, le=1000)


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    target_demographics: Optional[Dict[str, Dict[str, float]]] = None
    target_sample_size: Optional[int] = Field(None, ge=10, le=1000)


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    target_demographics: Dict[str, Dict[str, float]]
    target_sample_size: int
    chi_square_statistic: Optional[Dict[str, Any]]
    p_values: Optional[Dict[str, Any]]
    is_statistically_valid: bool
    validation_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True