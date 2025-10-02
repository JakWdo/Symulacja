"""Insight Rater Service
Uses LLM to produce qualitative 1-100 assessments of focus group sessions."""

from __future__ import annotations

from typing import Any, Dict, List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.core.config import get_settings

settings = get_settings()


class InsightRaterService:
    """LLM-based scoring for focus group outcomes."""

    def __init__(self, use_pro_model: bool | None = None) -> None:
        model_name = (
            getattr(settings, "ANALYSIS_MODEL", settings.DEFAULT_MODEL)
            if use_pro_model
            else getattr(settings, "PERSONA_GENERATION_MODEL", settings.DEFAULT_MODEL)
        )
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.2,
            max_tokens=1024,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a senior market research strategist. Rate focus group outcomes between 1-100.",
            ),
            (
                "user",
                "{prompt}",
            ),
        ])
        self.parser = JsonOutputParser()
        self.chain = self.prompt | self.llm | self.parser

    async def rate_focus_group(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Produce qualitative ratings based on aggregated focus group insights."""
        prompt = self._build_prompt(payload)
        result = await self.chain.ainvoke({"prompt": prompt})
        strengths = self._normalize_signal_items(result.get("strengths"))
        risks = self._normalize_signal_items(result.get("risks"))
        opportunities = self._normalize_signal_items(result.get("opportunities"))

        return {
            "idea_score": float(result.get("idea_score", 0.0)),
            "confidence": float(result.get("confidence", 0.0)),
            "rationale": result.get("rationale", ""),
            "strengths": strengths,
            "risks": risks,
            "opportunities": opportunities,
        }

    def _normalize_signal_items(self, value: Any) -> List[Dict[str, str]]:
        """Coerce LLM output into a clean list of signal dictionaries."""
        normalized: List[Dict[str, str]] = []

        if isinstance(value, list):
            candidates = value
        elif isinstance(value, dict):
            candidates = [value]
        elif isinstance(value, str):
            candidates = [value]
        else:
            candidates = []

        for item in candidates:
            if isinstance(item, dict):
                title = str(item.get("title") or item.get("name") or "Insight").strip()
                summary = str(
                    item.get("summary")
                    or item.get("description")
                    or item.get("detail")
                    or ""
                ).strip()
                entry: Dict[str, str] = {"title": title or "Insight", "summary": summary or ""}
                evidence = item.get("evidence") or item.get("quote") or item.get("support")
                if evidence:
                    entry["evidence"] = str(evidence).strip()
                normalized.append(entry)
            elif isinstance(item, str):
                text = item.strip()
                normalized.append({
                    "title": text[:80] or "Insight",
                    "summary": text,
                })

        return normalized

    def _build_prompt(self, payload: Dict[str, Any]) -> str:
        questions = payload.get("question_breakdown", [])
        question_summary: List[str] = []
        for item in questions[:5]:
            summary = (
                f"Q: {item.get('question')[:120]}\n"
                f" - Sentiment avg: {item.get('avg_sentiment', 0):+.2f}\n"
                f" - Consensus: {item.get('consensus', 0):.2f}\n"
                f" - Idea score (prev): {item.get('idea_score', 0):.1f}\n"
            )
            question_summary.append(summary)

        themes = payload.get("key_themes", [])
        theme_text = ''.join(
            f"• {theme.get('keyword')} ({theme.get('mentions')} mentions)\n" for theme in themes[:6]
        ) or '• No dominant themes detected\n'

        sentiment = payload.get("metrics", {}).get("sentiment_summary", {})
        engagement = payload.get("metrics", {}).get("engagement", {})

        return f"""
You will assign a holistic 1-100 rating for this focus group session. Score meaning:
- 90-100: Outstanding validation. Participants strongly endorse the concept with rich, actionable feedback.
- 75-89: Strong traction. Clear positive response with minor caveats to address.
- 55-74: Mixed reception. Valuable insights but notable concerns or polarization remain.
- 40-54: Weak signal. Concept needs significant refinement or better alignment with target personas.
- 0-39: Reject. Concept failed to resonate; major rethink required.

Respond ONLY with minified JSON using this schema:
{{
  "idea_score": float,
  "confidence": float,
  "rationale": string,
  "strengths": [{{"title": string, "summary": string, "evidence": string}}],
  "risks": [{{"title": string, "summary": string, "evidence": string}}],
  "opportunities": [{{"title": string, "summary": string, "evidence": string}}]
}}
If you lack evidence for a field, return an empty string.

=== SESSION SNAPSHOT ===
Total responses: {payload.get('total_responses', 'unknown')}
Participants: {payload.get('participant_count', 'unknown')}
Consensus: {payload.get('metrics', {}).get('consensus', 0):.2f}
Sentiment avg: {payload.get('metrics', {}).get('average_sentiment', 0):+.2f}
Positive ratio: {sentiment.get('positive_ratio', 0):.2f}
Negative ratio: {sentiment.get('negative_ratio', 0):.2f}
Completion rate: {engagement.get('completion_rate', 0):.2f}
Consistency score: {engagement.get('consistency_score', 0) if engagement.get('consistency_score') is not None else 'null'}

=== KEY THEMES ===
{theme_text}

=== QUESTION DETAILS (subset) ===
{''.join(question_summary) or 'No question level data provided.'}

Summarize strengths, risks, and commercial opportunities before scoring. Use short, insight-driven language.
"""
