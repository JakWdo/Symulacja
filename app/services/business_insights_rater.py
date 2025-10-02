"""
Business Insights Rater Service
Uses Gemini 2.5 Pro to generate qualitative business assessments from focus group responses
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import PersonaResponse, FocusGroup
from app.schemas.business_insights import (
    BusinessInsightsResponse,
    MarketFitAssessment,
    ReadinessLevel,
    RiskProfile,
    RiskItem,
    OpportunityAnalysis,
    OpportunityItem,
    QualityAssessment,
)
from app.services.insight_service import InsightService

settings = get_settings()
logger = logging.getLogger(__name__)


class BusinessInsightsRaterService:
    """
    Generate AI-driven business insights from focus group responses.
    Uses Gemini 2.5 Flash for deep analysis and business metric generation.
    """

    def __init__(self):
        self.settings = settings
        self.insight_service = InsightService()

        # Use Gemini 2.5 Flash for business analysis (balance of quality and cost)
        analysis_model = getattr(settings, "ANALYSIS_MODEL", settings.DEFAULT_MODEL)

        self.llm = ChatGoogleGenerativeAI(
            model=analysis_model,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3,  # Lower temperature for more consistent business analysis
            max_tokens=settings.MAX_TOKENS,
        )

        self.json_parser = JsonOutputParser()

    async def generate_complete_insights(
        self,
        db: AsyncSession,
        focus_group_id: str,
        context_metrics: Dict[str, Any]
    ) -> BusinessInsightsResponse:
        """
        Generate all AI business insights for a focus group.

        Args:
            db: Database session
            focus_group_id: Focus group ID
            context_metrics: Optional context metrics (consensus, sentiment, etc.)

        Returns:
            Complete BusinessInsightsResponse with all AI assessments
        """
        # Fetch responses
        result = await db.execute(
            select(PersonaResponse)
            .where(PersonaResponse.focus_group_id == focus_group_id)
            .order_by(PersonaResponse.created_at)
        )
        responses = result.scalars().all()

        if not responses:
            raise ValueError("No responses found for this focus group")

        # Fetch focus group for context
        fg_result = await db.execute(
            select(FocusGroup).where(FocusGroup.id == focus_group_id)
        )
        focus_group = fg_result.scalar_one_or_none()
        if not focus_group:
            raise ValueError("Focus group not found")

        # Generate all assessments in parallel (conceptually - sequential for now for simplicity)
        market_fit = await self.generate_market_fit_assessment(responses, context_metrics, focus_group)
        readiness = await self.generate_readiness_level(responses, context_metrics, focus_group)
        risk_profile = await self.identify_risks(responses, context_metrics, focus_group)
        opportunities = await self.discover_opportunities(responses, context_metrics, focus_group)
        quality = await self.assess_response_quality(responses)

        return BusinessInsightsResponse(
            focus_group_id=focus_group_id,
            market_fit=market_fit,
            readiness=readiness,
            risk_profile=risk_profile,
            opportunities=opportunities,
            quality=quality,
            generated_at=datetime.now(timezone.utc).isoformat(),
            model_used=self.llm.model,
        )

    async def generate_market_fit_assessment(
        self,
        responses: List[PersonaResponse],
        context_metrics: Dict[str, Any],
        focus_group: FocusGroup
    ) -> MarketFitAssessment:
        """Generate AI-driven market-product fit score and rationale"""

        # Prepare responses text
        responses_text = self._format_responses_for_prompt(responses)

        # Context metrics summary
        consensus = context_metrics.get('consensus', 0.0)
        avg_sentiment = context_metrics.get('average_sentiment', 0.0)
        engagement = context_metrics.get('completion_rate', 0.0)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a world-class business analyst evaluating product-market fit from focus group research.
Your task is to provide a comprehensive market fit assessment based on user responses."""),
            ("user", """Analyze these focus group responses about: {topic}

RESPONSES:
{responses_text}

CONTEXT METRICS (for reference only, not primary decision factors):
- Consensus: {consensus:.2f}
- Average sentiment: {avg_sentiment:.2f}
- Engagement rate: {engagement:.2f}

Based on the CONTENT of responses (not just metrics), assess market-product fit.

Consider:
1. Do users understand the value proposition clearly?
2. Is there genuine enthusiasm or just polite interest?
3. Are there specific use cases/needs being articulated?
4. Do responses indicate willingness to adopt/pay?
5. Are there patterns of excitement about specific features?
6. Do users mention current pain points this would solve?

Provide a market fit score (0-100):
- 0-30: Poor fit, fundamental misalignment
- 31-50: Weak fit, significant concerns
- 51-70: Moderate fit, potential with refinement
- 71-85: Strong fit, clear demand
- 86-100: Exceptional fit, enthusiastic demand

Return ONLY valid JSON (no markdown, no extra text):
{{
  "score": <0-100>,
  "confidence": "<low|medium|high>",
  "rationale": "<2-3 sentences explaining the score>",
  "supporting_evidence": "<direct quote from responses>",
  "key_insights": ["<insight 1>", "<insight 2>", "<insight 3>"]
}}""")
        ])

        chain = prompt | self.llm | self.json_parser

        try:
            result = await chain.ainvoke({
                "topic": focus_group.name,
                "responses_text": responses_text,
                "consensus": consensus,
                "avg_sentiment": avg_sentiment,
                "engagement": engagement,
            })

            return MarketFitAssessment(**result)
        except Exception as e:
            logger.error(f"Failed to generate market fit assessment: {e}")
            # Fallback
            return MarketFitAssessment(
                score=50,
                confidence="low",
                rationale="Unable to complete AI analysis. Please try again.",
                supporting_evidence="",
                key_insights=[]
            )

    async def generate_readiness_level(
        self,
        responses: List[PersonaResponse],
        context_metrics: Dict[str, Any],
        focus_group: FocusGroup
    ) -> ReadinessLevel:
        """Assess product/idea readiness for launch"""

        responses_text = self._format_responses_for_prompt(responses)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a product launch expert evaluating readiness based on focus group feedback.
Assess if this product/idea is ready for market launch."""),
            ("user", """Analyze readiness for: {topic}

RESPONSES:
{responses_text}

Evaluate readiness considering:
1. User understanding of value prop (is it clear?)
2. Identified barriers or blockers
3. Enthusiasm and willingness to adopt
4. Concerns about pricing, UX, or competition
5. Clarity of positioning vs alternatives

Readiness levels:
- not_ready: Fundamental issues, needs major rethinking (score 0-40)
- needs_work: Core idea solid but significant gaps to address (score 41-65)
- ready: Minor refinements needed, can launch cautiously (score 66-85)
- high_confidence: Strong validation, ready to scale (score 86-100)

Return ONLY valid JSON:
{{
  "level": "<not_ready|needs_work|ready|high_confidence>",
  "score": <0-100>,
  "gaps": ["<gap 1>", "<gap 2>"],
  "strengths": ["<strength 1>", "<strength 2>"],
  "recommendation": "<1-2 sentences on what to do next>",
  "timeline_estimate": "<optional: time to address gaps, e.g., '2-3 months' or null>"
}}""")
        ])

        chain = prompt | self.llm | self.json_parser

        try:
            result = await chain.ainvoke({
                "topic": focus_group.name,
                "responses_text": responses_text,
            })

            return ReadinessLevel(**result)
        except Exception as e:
            logger.error(f"Failed to generate readiness level: {e}")
            return ReadinessLevel(
                level="needs_work",
                score=50,
                gaps=["Unable to complete analysis"],
                strengths=[],
                recommendation="Please regenerate insights."
            )

    async def identify_risks(
        self,
        responses: List[PersonaResponse],
        context_metrics: Dict[str, Any],
        focus_group: FocusGroup
    ) -> RiskProfile:
        """Identify top business risks from responses"""

        responses_text = self._format_responses_for_prompt(responses)
        total_responses = len(responses)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a risk assessment expert analyzing focus group feedback for business risks.
Identify concrete, actionable risks that could impact product success."""),
            ("user", """Identify business risks for: {topic}

RESPONSES ({total_responses} total):
{responses_text}

Risk categories:
- adoption_barrier: Obstacles preventing user adoption
- pricing_concern: Willingness-to-pay or pricing model issues
- competition_threat: Concerns about competitors or alternatives
- ux_issue: User experience or usability problems
- market_timing: Market readiness or timing concerns
- other: Other business risks

For each risk:
1. Count how many personas mentioned it (directly or indirectly)
2. Calculate percentage: (count / {total_responses}) * 100
3. Assess severity: low (<20% mention), medium (20-50%), high (>50%)

Return top 5 risks, sorted by severity/impact.

Return ONLY valid JSON:
{{
  "overall_risk_level": "<low|medium|high>",
  "risks": [
    {{
      "category": "<risk category>",
      "severity": "<low|medium|high>",
      "description": "<clear description>",
      "evidence": "<quote or summary>",
      "affected_personas_pct": <0-100>,
      "mitigation_suggestion": "<optional suggestion>"
    }}
  ],
  "risk_summary": "<1-2 sentences summarizing risk landscape>"
}}""")
        ])

        chain = prompt | self.llm | self.json_parser

        try:
            result = await chain.ainvoke({
                "topic": focus_group.name,
                "responses_text": responses_text,
                "total_responses": total_responses,
            })

            return RiskProfile(**result)
        except Exception as e:
            logger.error(f"Failed to identify risks: {e}")
            return RiskProfile(
                overall_risk_level="medium",
                risks=[],
                risk_summary="Unable to complete risk analysis."
            )

    async def discover_opportunities(
        self,
        responses: List[PersonaResponse],
        context_metrics: Dict[str, Any],
        focus_group: FocusGroup
    ) -> OpportunityAnalysis:
        """Discover unexpected opportunities, use cases, or market segments"""

        responses_text = self._format_responses_for_prompt(responses)
        total_responses = len(responses)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a strategic opportunity analyst finding hidden insights in focus group data.
Look for UNEXPECTED opportunities, not obvious features or use cases."""),
            ("user", """Discover opportunities for: {topic}

RESPONSES ({total_responses} total):
{responses_text}

Look for:
1. Mentioned use cases that weren't the primary intent
2. Surprising demographic segments showing interest
3. Adjacent markets or applications
4. Feature requests revealing new value propositions
5. Positioning insights (how users describe it vs how you intended)

Opportunity categories:
- new_use_case: Unanticipated application or use case
- unexpected_segment: Demographic or customer segment not originally targeted
- adjacent_market: Related market opportunity
- feature_request: Feature ideas that unlock new value
- positioning_insight: Better way to position/message the product
- other: Other strategic opportunities

Rank by potential business impact (0-100).

Return top 5 opportunities ONLY if truly valuable (not generic observations).

Return ONLY valid JSON:
{{
  "opportunities": [
    {{
      "description": "<clear, specific description>",
      "impact_score": <0-100>,
      "category": "<category>",
      "evidence": "<supporting quotes>",
      "personas_mentioning": <count>
    }}
  ],
  "opportunity_summary": "<1-2 sentences on top opportunities>",
  "strategic_recommendation": "<how to capitalize on these>"
}}""")
        ])

        chain = prompt | self.llm | self.json_parser

        try:
            result = await chain.ainvoke({
                "topic": focus_group.name,
                "responses_text": responses_text,
                "total_responses": total_responses,
            })

            return OpportunityAnalysis(**result)
        except Exception as e:
            logger.error(f"Failed to discover opportunities: {e}")
            return OpportunityAnalysis(
                opportunities=[],
                opportunity_summary="No significant opportunities identified.",
                strategic_recommendation="Focus on core value proposition."
            )

    async def assess_response_quality(
        self,
        responses: List[PersonaResponse]
    ) -> QualityAssessment:
        """Assess quality and authenticity of responses"""

        responses_text = self._format_responses_for_prompt(responses)
        total_responses = len(responses)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a qualitative research expert assessing focus group response quality.
Evaluate thoughtfulness, depth, and authenticity of participant feedback."""),
            ("user", """Assess quality of these {total_responses} responses:

{responses_text}

Evaluate:
1. Authenticity: Are responses genuine or formulaic/superficial?
2. Detail level: Do participants provide specific examples vs vague statements?
3. Engagement: Evidence of thoughtful consideration vs rushed answers?
4. Constructiveness: Do responses contain actionable suggestions/ideas?

Authenticity score (0-100):
- 0-30: Superficial, generic responses
- 31-60: Adequate but formulaic
- 61-85: Thoughtful and specific
- 86-100: Exceptional depth and authenticity

Detail level:
- superficial: Vague, one-word answers
- adequate: Some specifics
- detailed: Rich examples and context
- exceptional: Deep insights and nuance

Count responses with constructive keywords (suggest, recommend, could, should, improve, idea, propose).

Return ONLY valid JSON:
{{
  "authenticity_score": <0-100>,
  "detail_level": "<superficial|adequate|detailed|exceptional>",
  "engagement_quality": "<low|moderate|high>",
  "constructive_feedback_ratio": <0.0-1.0>,
  "interpretation": "<overall quality summary>",
  "notable_patterns": ["<pattern 1>", "<pattern 2>"]
}}""")
        ])

        chain = prompt | self.llm | self.json_parser

        try:
            result = await chain.ainvoke({
                "responses_text": responses_text,
                "total_responses": total_responses,
            })

            return QualityAssessment(**result)
        except Exception as e:
            logger.error(f"Failed to assess response quality: {e}")
            return QualityAssessment(
                authenticity_score=50,
                detail_level="adequate",
                engagement_quality="moderate",
                constructive_feedback_ratio=0.0,
                interpretation="Unable to complete quality analysis.",
                notable_patterns=[]
            )

    def _format_responses_for_prompt(self, responses: List[PersonaResponse], max_chars: int = 15000) -> str:
        """Format responses for LLM prompt, with truncation if too long"""
        formatted = []

        for i, response in enumerate(responses, 1):
            formatted.append(
                f"[Response {i}]\n"
                f"Q: {response.question}\n"
                f"A: {response.response}\n"
            )

        full_text = "\n".join(formatted)

        # Truncate if too long (leave room for prompt template)
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + "\n\n... (truncated for length)"

        return full_text
