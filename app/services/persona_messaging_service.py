"""
PersonaMessagingService - generates marketing copy for personas.

Performance Optimizations (2025-10):
- Structured output via with_structured_output() - eliminates JSON parsing failures
- Token reduction: max_tokens 4096 → 1500 (sufficient for 3 variants)
- Temperature: Keep at 0.7 (creativity is critical for messaging)
- Target latency: <1.5s (down from 2s)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from langchain_core.language_models.chat_models import BaseChatModel

from app.models.persona import Persona
from app.schemas.persona_details import PersonaMessagingResponse
from app.services.clients import build_chat_model
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

VALID_TONES = {"friendly", "professional", "urgent", "empathetic"}
VALID_TYPES = {"email", "ad", "landing_page", "social_post"}


class PersonaMessagingService:
    """
    AI-powered messaging generation for personas.

    Performance:
    - Structured output: Eliminates JSON parsing errors
    - Token reduction: max_tokens 4096 → 1500
    - Temperature: 0.7 (keep high for creativity)
    - Target: <1.5s per messaging generation (down from 2s)
    """

    def __init__(self) -> None:
        base_llm = build_chat_model(
            model=settings.PERSONA_GENERATION_MODEL,
            temperature=0.7,  # Keep high for creative messaging
            max_tokens=1500,  # Reduced from 4096 - sufficient for 3 variants
            timeout=90,
        )
        # Use structured output for direct Pydantic model generation
        self.llm = base_llm.with_structured_output(PersonaMessagingResponse)

    async def generate_messaging(
        self,
        persona: Persona,
        *,
        tone: str,
        message_type: str,
        num_variants: int = 3,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate messaging variants for the persona.

        Optimizations:
        - Structured output (Pydantic) eliminates JSON parsing
        - Token reduction: max_tokens 4096 → 1500
        - Temperature 0.7 (keep high for creativity)

        Performance:
            Target: <1.5s (down from 2s)
        """
        import time
        start_time = time.time()

        tone_normalized = tone.lower()
        message_type_normalized = message_type.lower()

        if tone_normalized not in VALID_TONES:
            raise ValueError(f"Unsupported tone '{tone}'. Allowed: {', '.join(VALID_TONES)}")
        if message_type_normalized not in VALID_TYPES:
            raise ValueError(f"Unsupported type '{message_type}'. Allowed: {', '.join(VALID_TYPES)}")

        prompt = self._build_prompt(
            persona,
            tone=tone_normalized,
            message_type=message_type_normalized,
            num_variants=num_variants,
            context=context,
        )

        try:
            # Structured output returns PersonaMessagingResponse directly
            result: PersonaMessagingResponse = await self.llm.ainvoke(prompt)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to invoke LLM for messaging: %s", exc, exc_info=True)
            raise

        # Convert Pydantic model to dict and add metadata
        messaging_data = result.model_dump(mode="json")
        messaging_data["generated_at"] = datetime.now(timezone.utc).isoformat()
        messaging_data["generated_by"] = settings.PERSONA_GENERATION_MODEL

        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "messaging_generated",
            extra={
                "persona_id": str(persona.id),
                "duration_ms": elapsed_ms,
                "model": settings.PERSONA_GENERATION_MODEL,
                "tone": tone_normalized,
                "message_type": message_type_normalized,
                "num_variants": num_variants,
            }
        )

        return messaging_data

    def _build_prompt(
        self,
        persona: Persona,
        *,
        tone: str,
        message_type: str,
        num_variants: int,
        context: Optional[str],
    ) -> str:
        """
        Build optimized prompt for messaging generation.

        Optimizations:
        - Reduced verbosity (bullet points vs. full sentences)
        - Truncated pain points to 3 max
        - Removed JSON schema (handled by structured output)
        """
        values = ", ".join(persona.values or []) if persona.values else "brak"

        # Extract top 3 pain points (if available) and truncate
        pains = "brak"
        if persona.needs_and_pains and isinstance(persona.needs_and_pains, dict):
            pain_list = persona.needs_and_pains.get("pain_points", [])
            if pain_list and isinstance(pain_list, list):
                top_pains = [p.get("pain_title", "") for p in pain_list[:3] if isinstance(p, dict)]
                pains = ", ".join(filter(None, top_pains)) or "brak"

        interests = ", ".join(persona.interests[:3]) if persona.interests else "brak"  # Max 3 interests

        # Truncate context to 200 chars
        ctx = (context[:200] + "...") if context and len(context) > 200 else (context or "Brak")

        return f"""You are a B2B SaaS copywriter.

Generate {num_variants} {message_type} variants (tone: {tone}) for:

**Profile:**
- {persona.age}y, {persona.occupation or "?"}
- Values: {values}
- Top pain points: {pains}
- Interests: {interests}

**Campaign context:** {ctx}

Each variant:
- Headline: max 80 chars
- Subheadline: max 150 chars
- Body: 150-300 words
- CTA: action-oriented

Base copy on provided data only. No hallucinations."""

