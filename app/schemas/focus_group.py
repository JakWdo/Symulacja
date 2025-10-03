from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class FocusGroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    project_context: Optional[str] = Field(None, max_length=5000)
    persona_ids: List[UUID] = Field(..., min_items=2, max_items=100)
    questions: List[str] = Field(..., min_items=1, max_items=50)
    mode: str = Field(default="normal", pattern="^(normal|adversarial)$")


class FocusGroupResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: Optional[str]
    project_context: Optional[str]
    persona_ids: List[UUID]
    questions: List[str]
    mode: str
    status: str
    total_execution_time_ms: Optional[int]
    avg_response_time_ms: Optional[float]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class FocusGroupResultResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: Optional[str]
    project_context: Optional[str]
    persona_ids: List[UUID]
    questions: List[str]
    mode: str
    status: str
    metrics: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
