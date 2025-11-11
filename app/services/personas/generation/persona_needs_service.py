"""
PersonaNeedsService - extracts Jobs-to-be-Done and pain points for personas.

Combines focus-group responses with Gemini analysis to produce structured
needs data (jobs, desired outcomes, pain ranking). Output is cached by
PersonaDetailsService to avoid repeated LLM calls.

Performance Optimizations (2025-10):
- Structured output via with_structured_output() - eliminates JSON parsing failures
- Token reduction: max_tokens 6000 → 2000, focus group responses 20 → 10
- Temperature: 0.35 → 0.25 (more deterministic, faster inference)
- Target latency: <2s (down from 2-3s)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.persona import Persona
from app.models.persona_events import PersonaResponse
from app.schemas.persona_details import NeedsAndPains
from app.services.shared.clients import build_chat_model
from config import models

logger = logging.getLogger(__name__)


class PersonaNeedsService:
    """
    Generate JTBD, desired outcomes and pain points for a persona.

    Performance:
    - Structured output: Eliminates JSON parsing errors, reduces tokens
    - Focus group responses: Limited to 10 (vs. 20) for speed
    - Temperature: 0.25 for deterministic, fast inference
    - Target: <2s per needs analysis (down from 2-3s)
    """

    def __init__(self, db: AsyncSession) -> None:
        from config import models

        self.db = db
        # Model config z centralnego registry
        model_config = models.get("personas", "needs")
        base_llm = build_chat_model(**model_config.params)
        # Use structured output for direct Pydantic model generation
        self.llm = base_llm.with_structured_output(NeedsAndPains)

    async def generate_needs_analysis(
        self,
        persona: Persona,
        rag_context: str | None = None
    ) -> dict[str, Any]:
        """
        Generate structured needs data using LLM, focus group responses, and RAG context.

        Optimizations:
        - Structured output (Pydantic) eliminates JSON parsing
        - RAG context integration for consistency with segment data
        - Reduced focus group responses: 20 → 10 for speed
        - Temperature 0.25 for faster, deterministic inference

        Args:
            persona: Persona ORM instance
            rag_context: Optional RAG context (segment_context + graph_insights)

        Performance:
            Target: <2s (down from 2-3s)
        """
        import time
        start_time = time.time()

        responses = await self._fetch_recent_responses(persona.id)
        prompt = self._build_prompt(persona, responses, rag_context)

        try:
            # Structured output returns NeedsAndPains Pydantic model directly
            result: NeedsAndPains = await self.llm.ainvoke(prompt)
        except Exception as exc:  # pragma: no cover - network failure
            logger.error("Failed to invoke LLM for needs analysis: %s", exc, exc_info=True)
            raise

        # Convert Pydantic model to dict and add metadata
        needs_data = result.model_dump(mode="json")
        needs_data["generated_at"] = datetime.now(timezone.utc).isoformat()
        needs_data["generated_by"] = models.get("personas", "needs").model

        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "needs_analysis_generated",
            extra={
                "persona_id": str(persona.id),
                "duration_ms": elapsed_ms,
                "model": models.get("personas", "needs").model,
                "num_focus_group_responses": len(responses),
            }
        )

        return needs_data

    async def _fetch_recent_responses(self, persona_id) -> list[dict[str, str]]:
        """
        Fetch latest focus group responses for persona.

        Optimizations:
        - Limit reduced from 20 → 10 for speed (sufficient for JTBD analysis)
        """
        result = await self.db.execute(
            select(PersonaResponse)
            .where(PersonaResponse.persona_id == persona_id)
            .order_by(PersonaResponse.created_at.desc())
            .limit(10)  # Reduced from 20 for faster processing
        )
        responses = []
        for record in result.scalars():
            responses.append(
                {
                    "question": record.question_text,
                    "answer": record.response_text,
                }
            )
        return responses

    def _build_prompt(
        self,
        persona: Persona,
        responses: list[dict[str, str]],
        rag_context: str | None = None
    ) -> str:
        """
        Build optimized prompt for needs analysis with RAG context.

        Optimizations:
        - Reduced verbosity (bullet points vs. full sentences)
        - Truncated background story to 300 chars
        - RAG context integration for consistency with segment data
        - Removed JSON schema (handled by structured output)

        Args:
            persona: Persona instance
            responses: Focus group responses
            rag_context: Optional RAG context (segment_context + graph_insights)
        """
        # Truncate background story to 300 chars for speed
        background = (persona.background_story[:300] + "...") if persona.background_story and len(persona.background_story) > 300 else (persona.background_story or "Brak")
        values = ", ".join(persona.values or []) if persona.values else "brak"
        interests = ", ".join(persona.interests or []) if persona.interests else "brak"

        formatted_responses = ""
        if responses:
            formatted = [
                f"- Q: {entry['question'][:100]}...\n  A: {entry['answer'][:150]}..."
                if len(entry['question']) > 100 or len(entry['answer']) > 150
                else f"- Q: {entry['question']}\n  A: {entry['answer']}"
                for entry in responses[:10]  # Max 10 responses
            ]
            formatted_responses = "\n".join(formatted)
        else:
            formatted_responses = "Brak danych z grup fokusowych."

        # Build RAG context section if available
        rag_section = ""
        if rag_context:
            # Truncate RAG context to 800 chars for balanced quality/speed
            truncated_rag = (rag_context[:800] + "...") if len(rag_context) > 800 else rag_context
            rag_section = f"""

**Context from RAG (Market Research Data):**
{truncated_rag}

IMPORTANT: Use RAG context to understand the REAL problems and challenges this persona faces.
Ground your JTBD and pain points in the demographic/economic realities described in RAG context.
"""

        return f"""You are a product strategist using Jobs-to-be-Done methodology.

Extract JTBD insights for:

**Profile:**
- {persona.age}y, {persona.occupation or "?"}
- Values: {values}
- Interests: {interests}
- Background: {background}
- Segment: {persona.segment_name or "Unknown"}{rag_section}

**Focus Group Insights (latest 10):**
{formatted_responses}

Generate:
1. Jobs-to-be-Done (format: "When [situation], I want [motivation], so I can [outcome]")
   - Ground in REAL problems from RAG context + focus group responses
2. Desired outcomes (importance 1-10, satisfaction 1-10, opportunity score)
   - Based on persona's actual life situation (not generic)
3. Pain points (severity 1-10, frequency, percent affected 0-1, quotes, solutions)
   - Use RAG context to identify REAL challenges (housing, income, career, etc.)

Base on provided data only. DO NOT invent generic problems."""

