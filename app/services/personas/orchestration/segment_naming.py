"""Generacja nazw segmentów używając Gemini Flash.

Ten moduł generuje krótkie (2-4 słowa), mówiące nazwy dla segmentów demograficznych
bazując na ich cechach i graph insights. Używa Gemini 2.5 Flash dla szybkości.
"""

from __future__ import annotations

import logging
from typing import Any

from config import models
from app.services.shared import build_chat_model

logger = logging.getLogger(__name__)


async def generate_segment_name(
    segment_data: dict[str, Any],
    llm_flash: Any | None = None
) -> str:
    """Generuje mówiącą nazwę segmentu używając Gemini 2.5 Flash.

    Nazwa powinna być krótka (2-4 słowa), mówiąca i odzwierciedlać
    kluczowe cechy grupy demograficznej bazując na insightach.

    Args:
        segment_data: Dict z demographics, graph_insights, brief
        llm_flash: Optional Gemini Flash LLM (jeśli None, utworzy nowy)

    Returns:
        Nazwa segmentu (np. "Młodzi Prekariusze", "Aspirujące Profesjonalistki 35-44")

    Raises:
        ValueError: Jeśli LLM nie zwróci poprawnej nazwy (fallback do template)
    """
    # Extract demographics
    demographics = segment_data.get('demographics', {})
    graph_insights = segment_data.get('graph_insights', [])

    age_range = demographics.get('age', demographics.get('age_group', 'nieznany'))
    gender = demographics.get('gender', 'nieznana')
    education = demographics.get('education', demographics.get('education_level', 'nieznane'))
    income = demographics.get('income', demographics.get('income_bracket', 'nieznany'))

    # Format insights (use GraphInsight objects if available)
    insights_text = "\n".join([
        f"- {ins.summary} ({ins.confidence})" if hasattr(ins, 'summary')
        else f"- {ins.get('summary', 'N/A')} ({ins.get('confidence', 'medium')})"
        for ins in graph_insights[:3]  # Top 3
    ]) if graph_insights else "Brak insights"

    prompt = f"""Stwórz trafną, MÓWIĄCĄ nazwę dla poniższego segmentu demograficznego.

DANE SEGMENTU:
- Wiek: {age_range}
- Płeć: {gender}
- Wykształcenie: {education}
- Dochód: {income}

INSIGHTS Z GRAFU:
{insights_text}

ZASADY:
1. Nazwa powinna być 2-4 słowa (np. "Młodzi Prekariusze", "Aspirujące Profesjonalistki 35-44")
2. Oddaje kluczową charakterystykę grupy (wiek + status społeczno-ekonomiczny)
3. Używa polskiego języka, brzmi naturalnie
4. Bazuje na insightach (np. jeśli grupa ma niskie dochody + młody wiek → "Młodzi Prekariusze")
5. Unikaj ogólników ("Grupa A", "Segment 1")
6. Jeśli wiek jest istotny, włącz go (np. "35-44")

PRZYKŁADY DOBRYCH NAZW:
- "Młodzi Prekariusze" (18-24, niskie dochody)
- "Aspirujące Profesjonalistki 35-44" (kobiety, wyższe wykształcenie, średnie dochody)
- "Dojrzali Eksperci" (45-54, wysokie dochody, stabilna kariera)
- "Początkujący Profesjonaliści" (25-34, pierwsze kroki w karierze)

ZWRÓĆ TYLKO NAZWĘ (bez cudzysłowów, bez dodatkowych wyjaśnień):"""

    try:
        # Use provided LLM or create new Gemini Flash
        if llm_flash is None:
            model_config = models.get("global", "chat")
            llm_flash = build_chat_model(
                model=model_config.params.get("model", "gemini-2.5-flash"),
                temperature=0.7,
                max_tokens=50,
                timeout=10,
            )

        response = await llm_flash.ainvoke(prompt)
        segment_name = response.content.strip() if hasattr(response, 'content') else str(response).strip()

        # Clean up (remove quotes if present)
        segment_name = segment_name.strip('"\'')

        # Validation: nazwa powinna mieć 5-60 znaków
        if len(segment_name) < 5 or len(segment_name) > 60:
            logger.warning(f"Generated segment name too short/long: '{segment_name}', using fallback")
            # Fallback: template name
            segment_name = f"Segment {age_range}, {gender}"

        logger.info(f"✅ Generated segment name: '{segment_name}'")
        return segment_name

    except Exception as e:
        logger.error(f"❌ Failed to generate segment name: {e}")
        # Fallback: template name
        fallback_name = f"Segment {age_range}, {gender}"
        logger.warning(f"Using fallback segment name: '{fallback_name}'")
        return fallback_name
