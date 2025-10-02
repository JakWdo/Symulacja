"""
Business Insights Schemas
AI-generated business metrics and assessments
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class MarketFitAssessment(BaseModel):
    """AI-generated market-product fit assessment"""
    score: int = Field(..., ge=0, le=100, description="Market fit score 0-100")
    confidence: Literal["low", "medium", "high"] = Field(..., description="Model confidence in assessment")
    rationale: str = Field(..., description="2-3 sentence explanation of score")
    supporting_evidence: str = Field(..., description="Direct quote from responses supporting the assessment")
    key_insights: List[str] = Field(default_factory=list, description="Bullet points of key findings")


class ReadinessLevel(BaseModel):
    """AI assessment of product/idea readiness for launch"""
    level: Literal["not_ready", "needs_work", "ready", "high_confidence"] = Field(
        ...,
        description="Overall readiness level"
    )
    score: int = Field(..., ge=0, le=100, description="Numeric readiness score")
    gaps: List[str] = Field(
        default_factory=list,
        description="Identified gaps or barriers preventing launch"
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="Key strengths supporting readiness"
    )
    recommendation: str = Field(..., description="What to do next")
    timeline_estimate: Optional[str] = Field(
        None,
        description="Estimated time to address gaps if not ready"
    )


class RiskItem(BaseModel):
    """Individual business risk identified from responses"""
    category: Literal[
        "adoption_barrier",
        "pricing_concern",
        "competition_threat",
        "ux_issue",
        "market_timing",
        "other"
    ]
    severity: Literal["low", "medium", "high"]
    description: str = Field(..., description="Clear description of the risk")
    evidence: str = Field(..., description="Quote or summary from responses")
    affected_personas_pct: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage of personas mentioning this concern"
    )
    mitigation_suggestion: Optional[str] = Field(
        None,
        description="AI-suggested mitigation strategy"
    )


class RiskProfile(BaseModel):
    """Overall risk analysis"""
    overall_risk_level: Literal["low", "medium", "high"]
    risks: List[RiskItem] = Field(
        default_factory=list,
        description="Top identified risks, sorted by severity"
    )
    risk_summary: str = Field(..., description="1-2 sentence summary of risk landscape")


class OpportunityItem(BaseModel):
    """Unexpected opportunity or use case discovered"""
    description: str = Field(..., description="Clear description of the opportunity")
    impact_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Potential business impact 0-100"
    )
    category: Literal[
        "new_use_case",
        "unexpected_segment",
        "adjacent_market",
        "feature_request",
        "positioning_insight",
        "other"
    ]
    evidence: str = Field(..., description="Supporting quotes or patterns from responses")
    personas_mentioning: int = Field(
        ...,
        description="Number of personas who mentioned this"
    )


class OpportunityAnalysis(BaseModel):
    """Discovered opportunities from focus group"""
    opportunities: List[OpportunityItem] = Field(
        default_factory=list,
        description="Identified opportunities, sorted by impact"
    )
    opportunity_summary: str = Field(
        ...,
        description="1-2 sentence summary of top opportunities"
    )
    strategic_recommendation: str = Field(
        ...,
        description="How to capitalize on these opportunities"
    )


class QualityAssessment(BaseModel):
    """Assessment of response quality and authenticity"""
    authenticity_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="How authentic/thoughtful responses are (0-100)"
    )
    detail_level: Literal["superficial", "adequate", "detailed", "exceptional"]
    engagement_quality: Literal["low", "moderate", "high"]
    constructive_feedback_ratio: float = Field(
        ...,
        ge=0,
        le=1,
        description="Ratio of responses containing actionable suggestions"
    )
    interpretation: str = Field(
        ...,
        description="Overall quality interpretation"
    )
    notable_patterns: List[str] = Field(
        default_factory=list,
        description="Notable patterns in response quality"
    )


class BusinessInsightsResponse(BaseModel):
    """Complete AI-generated business insights"""
    focus_group_id: str
    market_fit: MarketFitAssessment
    readiness: ReadinessLevel
    risk_profile: RiskProfile
    opportunities: OpportunityAnalysis
    quality: QualityAssessment
    generated_at: str = Field(..., description="ISO timestamp of generation")
    model_used: str = Field(default="gemini-2.5-flash", description="LLM model used for analysis")
