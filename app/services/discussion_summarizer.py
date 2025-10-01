"""
AI-powered Discussion Summarizer using Gemini 2.0 Flash Exp or Gemini 2.5 Pro
Generates executive summaries, key insights, and actionable recommendations
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import FocusGroup, PersonaResponse, Persona
from app.services.insight_service import InsightService

settings = get_settings()


class DiscussionSummarizerService:
    """
    Generate AI-powered summaries of focus group discussions
    Uses advanced LLM for nuanced analysis and strategic recommendations
    """

    def __init__(self, use_pro_model: bool = False):
        """
        Initialize summarizer with choice of model

        Args:
            use_pro_model: If True, use gemini-2.5-pro (slower, higher quality)
                          If False, use gemini-2.0-flash-exp (faster, good quality)
        """
        self.settings = settings

        # Choose model based on need
        model_name = "gemini-2.0-flash-exp" if not use_pro_model else "gemini-2.5-pro"

        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3,  # Lower temperature for more factual summaries
            max_tokens=4096,  # Long-form output
        )

        self.insight_service = InsightService()
        self.str_parser = StrOutputParser()

        # Create summarization prompt
        self.summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a world-class market research analyst specializing in qualitative research synthesis.
Your role is to analyze focus group discussions and generate strategic insights for product teams.

IMPORTANT GUIDELINES:
- Be concise yet comprehensive
- Focus on actionable insights, not just description
- Identify patterns, contradictions, and surprising findings
- Consider demographic differences in opinions
- Provide strategic recommendations grounded in data
- Use professional, business-oriented language
- Avoid generic statements - be specific and evidence-based"""),
            ("user", "{prompt}")
        ])

        self.chain = self.summary_prompt | self.llm | self.str_parser

    async def generate_discussion_summary(
        self,
        db: AsyncSession,
        focus_group_id: str,
        include_demographics: bool = True,
        include_recommendations: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive AI summary of focus group discussion

        Returns:
            {
                "executive_summary": str,
                "key_insights": List[str],
                "surprising_findings": List[str],
                "segment_analysis": Dict[str, Any],
                "recommendations": List[str],
                "sentiment_narrative": str,
                "metadata": Dict[str, Any]
            }
        """
        # Fetch focus group
        result = await db.execute(
            select(FocusGroup).where(FocusGroup.id == focus_group_id)
        )
        focus_group = result.scalar_one_or_none()

        if not focus_group:
            raise ValueError("Focus group not found")

        if focus_group.status != "completed":
            raise ValueError("Focus group must be completed to generate summary")

        # Fetch all responses
        result = await db.execute(
            select(PersonaResponse)
            .where(PersonaResponse.focus_group_id == focus_group_id)
            .order_by(PersonaResponse.created_at)
        )
        responses = result.scalars().all()

        if not responses:
            raise ValueError("No responses found for this focus group")

        # Fetch personas for demographic context
        persona_ids = list(set(str(r.persona_id) for r in responses))
        result = await db.execute(
            select(Persona).where(Persona.id.in_(persona_ids))
        )
        personas = {str(p.id): p for p in result.scalars().all()}

        # Prepare discussion data
        discussion_data = self._prepare_discussion_data(
            focus_group, responses, personas, include_demographics
        )

        # Generate AI summary
        prompt_text = self._create_summary_prompt(
            discussion_data, include_recommendations
        )

        ai_response = await self.chain.ainvoke({"prompt": prompt_text})

        # Parse structured response
        parsed_summary = self._parse_ai_response(ai_response)

        # Add metadata
        parsed_summary["metadata"] = {
            "focus_group_id": focus_group_id,
            "focus_group_name": focus_group.name,
            "generated_at": datetime.utcnow().isoformat(),
            "model_used": self.llm.model,
            "total_responses": len(responses),
            "total_participants": len(persona_ids),
            "questions_asked": len(focus_group.questions),
        }

        return parsed_summary

    def _prepare_discussion_data(
        self,
        focus_group: FocusGroup,
        responses: List[PersonaResponse],
        personas: Dict[str, Persona],
        include_demographics: bool,
    ) -> Dict[str, Any]:
        """Prepare structured discussion data for AI analysis"""

        # Group responses by question
        responses_by_question = {}
        for response in responses:
            if response.question not in responses_by_question:
                responses_by_question[response.question] = []

            persona = personas.get(str(response.persona_id))
            response_data = {
                "response": response.response,
                "sentiment": self.insight_service.sentiment_score(response.response),
                "consistency_score": response.consistency_score,
            }

            if include_demographics and persona:
                response_data["demographics"] = {
                    "age": persona.age,
                    "gender": persona.gender,
                    "education": persona.education_level,
                    "occupation": persona.occupation,
                }

            responses_by_question[response.question].append(response_data)

        # Aggregate demographic info
        demographic_summary = None
        if include_demographics:
            ages = [p.age for p in personas.values()]
            genders = [p.gender for p in personas.values()]
            educations = [p.education_level for p in personas.values() if p.education_level]

            demographic_summary = {
                "age_range": f"{min(ages)}-{max(ages)}" if ages else "N/A",
                "gender_distribution": dict(zip(*np.unique(genders, return_counts=True))) if genders else {},
                "education_levels": list(set(educations)),
                "sample_size": len(personas),
            }

        return {
            "topic": focus_group.name,
            "description": focus_group.description,
            "responses_by_question": responses_by_question,
            "demographic_summary": demographic_summary,
            "total_responses": len(responses),
        }

    def _create_summary_prompt(
        self, discussion_data: Dict[str, Any], include_recommendations: bool
    ) -> str:
        """Create detailed prompt for AI summarization"""

        topic = discussion_data["topic"]
        description = discussion_data["description"] or "No description provided"
        responses_by_question = discussion_data["responses_by_question"]
        demo_summary = discussion_data.get("demographic_summary")

        # Format questions and responses
        formatted_discussion = []
        for idx, (question, responses) in enumerate(responses_by_question.items(), 1):
            formatted_discussion.append(f"\n**Question {idx}:** {question}")
            formatted_discussion.append(f"*({len(responses)} responses)*\n")

            for ridx, resp in enumerate(responses[:15], 1):  # Limit to avoid token overflow
                text = resp["response"][:300]  # Truncate very long responses
                sentiment = resp["sentiment"]
                sentiment_label = "positive" if sentiment > 0.15 else "negative" if sentiment < -0.15 else "neutral"

                demo_str = ""
                if "demographics" in resp:
                    demo = resp["demographics"]
                    demo_str = f" ({demo['gender']}, {demo['age']}, {demo['occupation']})"

                formatted_discussion.append(
                    f"{ridx}. [{sentiment_label.upper()}]{demo_str} \"{text}\""
                )

        discussion_text = "\n".join(formatted_discussion)

        # Demographic context
        demo_context = ""
        if demo_summary:
            demo_context = f"""
**PARTICIPANT DEMOGRAPHICS:**
- Sample size: {demo_summary['sample_size']}
- Age range: {demo_summary['age_range']}
- Gender distribution: {demo_summary['gender_distribution']}
- Education levels: {', '.join(demo_summary['education_levels'][:5])}
"""

        recommendations_section = ""
        if include_recommendations:
            recommendations_section = """
## 5. STRATEGIC RECOMMENDATIONS
Provide 3-5 concrete, actionable recommendations for the product/marketing team based on findings.
Each recommendation should:
- Be specific and implementable
- Reference evidence from the discussion
- Consider potential impact and effort
"""

        prompt = f"""Analyze this focus group discussion and generate a comprehensive strategic summary.

**FOCUS GROUP TOPIC:** {topic}
**DESCRIPTION:** {description}

{demo_context}

**DISCUSSION TRANSCRIPT:**
{discussion_text}

---

Please provide a detailed analysis in the following structure:

## 1. EXECUTIVE SUMMARY (150-200 words)
Synthesize the core findings into a high-level overview that answers:
- What was the overall reception to the concept/topic?
- What are the most critical takeaways?
- What is the strategic implication?

## 2. KEY INSIGHTS (5-7 bullet points)
Identify the most important patterns and themes from the discussion.
Each insight should be:
- Evidence-based (reference specific comments)
- Actionable (implications for product/strategy)
- Prioritized (most important first)

## 3. SURPRISING FINDINGS (2-4 bullet points)
Highlight unexpected or counterintuitive discoveries that challenge assumptions.
These could be:
- Contradictions between what participants say vs. underlying sentiment
- Minority opinions that reveal edge cases
- Demographic differences that weren't anticipated

## 4. SEGMENT ANALYSIS
Break down how different demographic segments (age, gender, occupation) responded differently.
Structure as:
- **Segment name**: Key differentiator and quote/evidence

{recommendations_section}

## 6. SENTIMENT NARRATIVE (50-100 words)
Describe the emotional journey of the discussion:
- How did sentiment evolve across questions?
- Were there polarizing topics?
- What drove positive vs. negative reactions?

---

**IMPORTANT:**
- Use specific quotes and data points as evidence
- Avoid generic marketing jargon
- Be honest about weaknesses or concerns raised
- Consider both explicit feedback and implicit patterns
- Format using Markdown for readability
"""

        return prompt

    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """
        Parse AI response into structured format
        Handles markdown sections and extracts key components
        """
        sections = {
            "executive_summary": "",
            "key_insights": [],
            "surprising_findings": [],
            "segment_analysis": {},
            "recommendations": [],
            "sentiment_narrative": "",
            "full_analysis": ai_response,  # Keep full text for reference
        }

        current_section = None
        current_content = []

        lines = ai_response.split("\n")

        for line in lines:
            line_lower = line.lower().strip()

            # Detect section headers
            if "executive summary" in line_lower and line.startswith("#"):
                if current_section:
                    self._finalize_section(sections, current_section, current_content)
                current_section = "executive_summary"
                current_content = []
            elif "key insights" in line_lower and line.startswith("#"):
                if current_section:
                    self._finalize_section(sections, current_section, current_content)
                current_section = "key_insights"
                current_content = []
            elif "surprising findings" in line_lower and line.startswith("#"):
                if current_section:
                    self._finalize_section(sections, current_section, current_content)
                current_section = "surprising_findings"
                current_content = []
            elif "segment analysis" in line_lower and line.startswith("#"):
                if current_section:
                    self._finalize_section(sections, current_section, current_content)
                current_section = "segment_analysis"
                current_content = []
            elif "recommendation" in line_lower and line.startswith("#"):
                if current_section:
                    self._finalize_section(sections, current_section, current_content)
                current_section = "recommendations"
                current_content = []
            elif "sentiment narrative" in line_lower and line.startswith("#"):
                if current_section:
                    self._finalize_section(sections, current_section, current_content)
                current_section = "sentiment_narrative"
                current_content = []
            else:
                if current_section and line.strip():
                    current_content.append(line)

        # Finalize last section
        if current_section:
            self._finalize_section(sections, current_section, current_content)

        return sections

    def _finalize_section(
        self, sections: Dict[str, Any], section_name: str, content: List[str]
    ):
        """Finalize a parsed section"""
        content_text = "\n".join(content).strip()

        if section_name in ["executive_summary", "sentiment_narrative"]:
            sections[section_name] = content_text
        elif section_name in ["key_insights", "surprising_findings", "recommendations"]:
            # Extract bullet points
            bullets = []
            for line in content:
                if line.strip().startswith(("-", "*", "•")) or (line.strip() and line.strip()[0].isdigit()):
                    bullet_text = line.strip().lstrip("-*•0123456789. ")
                    if bullet_text:
                        bullets.append(bullet_text)
            sections[section_name] = bullets
        elif section_name == "segment_analysis":
            # Parse segment analysis (key-value pairs)
            segments = {}
            current_segment = None
            for line in content:
                if line.strip().startswith("**") and ":**" in line:
                    parts = line.split(":**", 1)
                    current_segment = parts[0].strip("*").strip()
                    segments[current_segment] = parts[1].strip() if len(parts) > 1 else ""
                elif current_segment and line.strip():
                    segments[current_segment] += " " + line.strip()
            sections[section_name] = segments


# Import numpy for demographic aggregation
import numpy as np
