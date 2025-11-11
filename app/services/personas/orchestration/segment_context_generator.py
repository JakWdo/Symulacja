"""Generacja kontekstu społecznego dla segmentów używając Gemini 2.5 Pro.

Ten moduł tworzy długie (500-800 znaków) edukacyjne briefe dla segmentów
demograficznych z konkretnymi danymi i wyjaśnieniami "dlaczego".
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def generate_segment_context(
    segment_data: dict[str, Any],
    graph_insights: list[Any],
    llm_pro: Any
) -> str:
    """Generuje kontekst społeczny dla segmentu używając Gemini 2.5 Pro.

    Kontekst powinien być 500-800 znaków, edukacyjny i specyficzny dla TEJ grupy.

    Args:
        segment_data: Dict z segment_name, demographics, brief
        graph_insights: Lista GraphInsight objects dla tej grupy
        llm_pro: Gemini 2.5 Pro LLM instance

    Returns:
        Kontekst społeczny (500-800 znaków)

    Raises:
        ValueError: Jeśli LLM nie zwróci poprawnego kontekstu (fallback do minimal)
    """
    segment_name = segment_data.get('segment_name', 'Segment')
    demographics = segment_data.get('demographics', {})
    project_goal = segment_data.get('project_goal')

    # Extract key demographics
    age_range = demographics.get('age', demographics.get('age_group', 'nieznany'))
    gender = demographics.get('gender', 'nieznana')
    education = demographics.get('education', demographics.get('education_level', 'nieznane'))
    income = demographics.get('income', demographics.get('income_bracket', 'nieznany'))

    # Format insights with details (check if GraphInsight objects or dicts)
    insights_text = "\n".join([
        f"- **{ins.summary if hasattr(ins, 'summary') else ins.get('summary', 'N/A')}**\n"
        f"  Magnitude: {ins.magnitude if hasattr(ins, 'magnitude') else ins.get('magnitude', 'N/A')}, "
        f"Confidence: {ins.confidence if hasattr(ins, 'confidence') else ins.get('confidence', 'medium')}, "
        f"Source: {ins.source if hasattr(ins, 'source') else ins.get('source', 'N/A')}, "
        f"Year: {ins.time_period if hasattr(ins, 'time_period') else ins.get('time_period', 'N/A')}\n"
        f"  Why it matters: {(ins.why_matters if hasattr(ins, 'why_matters') else ins.get('why_matters', ''))[:150]}..."
        for ins in graph_insights[:5]  # Top 5
    ]) if graph_insights else "Brak insights"

    prompt = f"""Stwórz kontekst społeczny dla segmentu "{segment_name}".

DEMOGRAFIA SEGMENTU:
- Wiek: {age_range}
- Płeć: {gender}
- Wykształcenie: {education}
- Dochód: {income}

INSIGHTS Z GRAFU WIEDZY:
{insights_text}

CEL PROJEKTU:
{project_goal or "Badanie syntetycznych person"}

WYTYCZNE:
1. Długość: 500-800 znaków (WAŻNE!)
2. Kontekst SPECYFICZNY dla KONKRETNEJ GRUPY (nie ogólny opis Polski!)
3. Zacznij od opisu charakterystyki grupy (jak w przykładzie)
4. Struktura:
   a) Pierwsza część (2-3 zdania): KIM są te osoby, co ich charakteryzuje
   b) Druga część (2-3 zdania): Ich WARTOŚCI i ASPIRACJE
   c) Trzecia część (2-3 zdania): WYZWANIA i kontekst ekonomiczny z konkretnymi liczbami
5. Ton: konkretny, praktyczny, opisujący TYCH ludzi (nie teoretyczny!)
6. Używaj konkretnych liczb z insights tam gdzie dostępne
7. Unikaj: ogólników ("polska społeczeństwo"), teoretyzowania

PRZYKŁAD DOBREGO KONTEKSTU (na wzór Figmy):
"Tech-Savvy Profesjonaliści to osoby w wieku 28 lat, pracujące jako Marketing Manager w dużych miastach jak Warszawa czy Kraków. Charakteryzują się wysokim wykształceniem (licencjat lub wyżej), stabilną karierą w branży technologicznej i dochodami 8k-12k PLN netto. Są early adopters nowych technologii i cenią sobie work-life balance. Ich główne wartości to innovation, ciągły rozwój i sustainability. Aspirują do awansu na wyższe stanowiska (senior manager, director), własnego mieszkania w atrakcyjnej lokalizacji (co przy cenach 15-20k PLN/m2 wymaga oszczędzania przez 10+ lat) i rozwoju kompetencji w digital marketing oraz AI tools. Wyzwania: rosnąca konkurencja na rynku pracy (według GUS 78% osób z tej grupy ma wyższe wykształcenie), wysokie koszty życia w dużych miastach (średni czynsz ~3500 PLN), presja na ciągły rozwój i keeping up with tech trends."

WAŻNE: Pisz o KONKRETNEJ grupie ludzi, używaj przykładów zawodów, konkretnych liczb, opisuj ICH życie.

ZWRÓĆ TYLKO KONTEKST (bez nagłówków, bez komentarzy, 500-800 znaków):"""

    try:
        response = await llm_pro.ainvoke(prompt)  # Use Gemini 2.5 Pro
        segment_context = response.content.strip() if hasattr(response, 'content') else str(response).strip()

        # Validation: kontekst powinien mieć 400-1200 znaków
        if len(segment_context) < 400 or len(segment_context) > 1200:
            logger.warning(
                f"Generated segment context length ({len(segment_context)}) outside range 400-1200, "
                "but accepting anyway"
            )

        logger.info(f"✅ Generated segment context: {len(segment_context)} chars")
        return segment_context

    except Exception as e:
        logger.error(f"❌ Failed to generate segment context: {e}")
        # Fallback: minimal context
        fallback_context = (
            f"Segment '{segment_name}' obejmuje osoby w wieku {age_range}, {gender}, "
            f"z wykształceniem {education} i dochodami {income}. "
            f"Ta grupa stanowi istotną część polskiego społeczeństwa i wymaga szczególnej uwagi "
            f"w kontekście badań rynkowych."
        )
        logger.warning(f"Using fallback segment context: {len(fallback_context)} chars")
        return fallback_context
