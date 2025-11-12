"""Formatowanie i generowanie opisów dla segment briefs.

Moduł odpowiada za:
- Formatowanie przykładowych person do promptów
- Generowanie nazw segmentów (LLM)
- Budowanie promptów dla segment brief
- Generowanie social context
- Ekstrakcja charakterystyk segmentu
- Generowanie opisów unikalności person
- Fallback briefs
"""

import logging
from typing import Any

from config import models, prompts
from app.models.persona import Persona
from app.schemas.segment_brief import SegmentBrief
from app.services.shared import build_chat_model

logger = logging.getLogger(__name__)


def format_example_personas(personas: list[Persona]) -> str:
    """Formatuje przykładowe persony do prompta.

    Args:
        personas: Lista person

    Returns:
        Sformatowany string z przykładami
    """
    if not personas:
        return "Brak przykładowych person z tego segmentu."

    formatted = "=== PRZYKŁADOWE PERSONY Z TEGO SEGMENTU ===\n\n"

    for idx, persona in enumerate(personas, 1):
        formatted += f"**Persona {idx}: {persona.full_name}**\n"
        formatted += f"- Wiek: {persona.age}, Zawód: {persona.occupation}\n"
        formatted += f"- Wykształcenie: {persona.education_level}\n"
        formatted += f"- Dochód: {persona.income_bracket}\n"

        # Skrócony background (max 200 chars)
        if persona.background_story:
            bg_short = persona.background_story[:200]
            if len(persona.background_story) > 200:
                bg_short += "..."
            formatted += f"- Historia: {bg_short}\n"

        # Wartości (top 3)
        if persona.values:
            values_str = ", ".join(persona.values[:3])
            formatted += f"- Wartości: {values_str}\n"

        formatted += "\n"

    return formatted


async def generate_segment_name(
    demographics: dict[str, Any],
    rag_context: str
) -> str:
    """Generuje mówiącą nazwę segmentu (np. 'Młodzi Prekariusze').

    Args:
        demographics: Demografia segmentu
        rag_context: Kontekst RAG

    Returns:
        Nazwa segmentu (5-60 chars)
    """
    age = demographics.get("age") or demographics.get("age_group", "unknown")
    gender = demographics.get("gender", "unknown")
    education = demographics.get("education") or demographics.get("education_level", "unknown")
    income = demographics.get("income") or demographics.get("income_bracket", "unknown")

    # Skrócony RAG context (max 200 chars)
    rag_short = rag_context[:200] if rag_context else "Brak"

    prompt = f"""Stwórz trafną, MÓWIĄCĄ nazwę dla segmentu demograficznego.

DEMOGRAFIA:
- Wiek: {age}
- Płeć: {gender}
- Wykształcenie: {education}
- Dochód: {income}

RAG INSIGHTS:
{rag_short}

ZASADY:
- 2-4 słowa (np. "Młodzi Prekariusze", "Aspirujące Profesjonalistki 35-44")
- Oddaje kluczową charakterystykę (wiek + status społeczno-ekonomiczny)
- Polski język, naturalnie brzmi
- Unikaj ogólników

ZWRÓĆ TYLKO NAZWĘ (bez cudzysłowów):"""

    try:
        # Gemini Flash dla szybkiego naming
        llm_flash = build_chat_model(
            model=models.config.get("defaults", {}).get("chat", {}).get("model", "gemini-2.5-flash"),
            temperature=0.7,
            max_tokens=50,
            timeout=10,
        )

        response = await llm_flash.ainvoke(prompt)
        name = response.content.strip() if hasattr(response, 'content') else str(response).strip()
        name = name.strip('"\'')  # Remove quotes

        # Walidacja (5-60 chars)
        if 5 <= len(name) <= 60:
            return name

        # Fallback
        logger.warning("Generated name invalid length: '%s' - using fallback", name)

    except Exception as exc:
        logger.warning("Błąd generowania segment name: %s - using fallback", exc)

    # Fallback name
    return f"Segment {age}, {gender}"


def build_segment_brief_prompt(
    segment_name: str,
    demographics: dict[str, Any],
    rag_context: str,
    example_personas: str
) -> str:
    """Buduje prompt dla generowania segment brief.

    Args:
        segment_name: Nazwa segmentu
        demographics: Demografia segmentu
        rag_context: Kontekst RAG
        example_personas: Sformatowane przykładowe persony

    Returns:
        Kompletny prompt dla LLM
    """
    age_range = demographics.get("age") or demographics.get("age_group", "unknown")
    gender = demographics.get("gender", "unknown")
    education = demographics.get("education") or demographics.get("education_level", "unknown")
    location = demographics.get("location", "unknown")
    income = demographics.get("income") or demographics.get("income_bracket", "unknown")

    # Get prompts from YAML config
    polish_expert = prompts.get("system.polish_society_expert")
    storytelling = prompts.get("system.storytelling")
    conversational = prompts.get("system.conversational_tone")
    segment_brief_prompt = prompts.get("personas.segment_brief")

    # Build system prompt by combining multiple system prompts
    system_messages = []
    for prompt in [polish_expert, storytelling, conversational]:
        # Extract system messages from each prompt
        for msg in prompt.messages:
            if msg.role == "system":
                system_messages.append(msg.content)

    combined_system_prompt = "\n\n".join(system_messages)

    # Render segment brief prompt with variables
    rendered_brief = segment_brief_prompt.render(
        segment_name=segment_name,
        age_range=age_range,
        gender=gender,
        education=education,
        location=location,
        income=income,
        rag_context=rag_context,
        example_personas=example_personas
    )

    # Extract system content from segment_brief_prompt (it's already in messages format)
    segment_brief_content = rendered_brief[0].content if rendered_brief else ""

    return f"{combined_system_prompt}\n\n{segment_brief_content}"


async def generate_social_context(
    segment_name: str,
    demographics: dict[str, Any],
    rag_context: str
) -> str:
    """Generuje social context (300-500 słów).

    Args:
        segment_name: Nazwa segmentu
        demographics: Demografia
        rag_context: Kontekst RAG

    Returns:
        Social context string
    """
    # Dla prostoty, wyekstraktujemy to z głównego briefu lub użyjemy uproszczonej wersji
    # W produkcji można to wygenerować osobnym LLM callem
    age = demographics.get("age") or demographics.get("age_group", "unknown")
    education = demographics.get("education") or demographics.get("education_level", "unknown")
    location = demographics.get("location", "unknown")

    return (
        f"Segment '{segment_name}' charakteryzuje się specyficznym kontekstem społeczno-ekonomicznym. "
        f"Osoby w wieku {age}, z wykształceniem {education}, mieszkające w lokalizacji {location}, "
        f"znajdują się w unikalnym momencie życia, który kształtuje ich wartości, aspiracje i wyzwania."
    )


def extract_characteristics(
    demographics: dict[str, Any],
    rag_context: str
) -> list[str]:
    """Ekstraktuje 5-7 kluczowych cech segmentu.

    Args:
        demographics: Demografia
        rag_context: Kontekst RAG

    Returns:
        Lista cech (strings)
    """
    characteristics = []

    # Z demografii
    age = demographics.get("age") or demographics.get("age_group", "")
    if "25-34" in str(age):
        characteristics.append("Młodzi profesjonaliści")
    elif "35-44" in str(age):
        characteristics.append("Established professionals")

    education = demographics.get("education") or demographics.get("education_level", "")
    if "wyższe" in str(education).lower() or "magisterskie" in str(education).lower():
        characteristics.append("Wysoko wykształceni")

    location = demographics.get("location", "")
    if location.lower() in ["warszawa", "kraków", "wrocław", "gdańsk", "poznań"]:
        characteristics.append("Mieszkańcy dużych miast")

    # Domyślne cechy (jeśli za mało)
    if len(characteristics) < 3:
        characteristics.extend([
            "Aktywni zawodowo",
            "Otwarci na zmiany",
            "Konsumenci świadomi"
        ])

    return characteristics[:7]  # Max 7


def generate_fallback_brief(
    segment_name: str,
    demographics: dict[str, Any]
) -> str:
    """Fallback brief gdy LLM zawiedzie.

    Args:
        segment_name: Nazwa segmentu
        demographics: Demografia

    Returns:
        Prosty fallback brief
    """
    age = demographics.get("age") or demographics.get("age_group", "unknown")
    education = demographics.get("education") or demographics.get("education_level", "unknown")
    location = demographics.get("location", "unknown")

    return (
        f"Segment '{segment_name}' obejmuje osoby w wieku {age}, "
        f"z wykształceniem {education}, mieszkające w {location}. "
        f"Ta grupa demograficzna stanowi istotną część polskiego społeczeństwa "
        f"i charakteryzuje się specyficznymi wartościami, aspiracjami oraz wyzwaniami życiowymi."
    )


async def generate_persona_uniqueness(
    persona: Persona,
    segment_brief: SegmentBrief
) -> str:
    """Generuje opis unikalności persony w kontekście segmentu.

    Args:
        persona: Persona object
        segment_brief: Brief segmentu do którego należy persona

    Returns:
        Opis unikalności (2-4 zdania, max 300 znaków)
    """
    # Skróć segment brief summary (max 500 chars)
    brief_summary = segment_brief.description[:500]
    if len(segment_brief.description) > 500:
        brief_summary += "..."

    # Format values i interests
    values_str = ", ".join(persona.values[:3]) if persona.values else "brak danych"
    interests_str = ", ".join(persona.interests[:3]) if persona.interests else "brak danych"

    # Skróć background (max 400 chars)
    background = persona.background_story[:400] if persona.background_story else "Brak historii"
    if persona.background_story and len(persona.background_story) > 400:
        background += "..."

    # Użyj segment_name z persony (z orchestration) dla consistency
    # segment_brief.segment_name może być inne (generowane dynamicznie przez LLM)
    segment_name_to_use = persona.segment_name or segment_brief.segment_name

    # Get persona uniqueness prompt from YAML config
    uniqueness_prompt = prompts.get("personas.persona_uniqueness")

    # Render prompt with persona data
    rendered_messages = uniqueness_prompt.render(
        persona_name=persona.full_name or "Ta osoba",
        segment_name=segment_name_to_use,
        age=persona.age,
        occupation=persona.occupation or "brak danych",
        background_story=background,
        values=values_str,
        interests=interests_str,
        segment_brief_summary=brief_summary
    )

    # Convert to string prompt (combine all messages)
    prompt = "\n\n".join(msg.content for msg in rendered_messages)

    try:
        # Gemini Flash dla szybkiego generowania
        llm_flash = build_chat_model(
            model=models.config.get("defaults", {}).get("chat", {}).get("model", "gemini-2.5-flash"),
            temperature=0.7,
            max_tokens=600,  # 3-4 akapity (250-400 słów)
            timeout=20,
        )

        response = await llm_flash.ainvoke(prompt)
        uniqueness = response.content.strip() if hasattr(response, 'content') else str(response).strip()

        # Brak limitu długości - AI dostaje pełną swobodę (250-400 słów jak w promptcie)

        logger.info(
            "✅ Persona uniqueness wygenerowana dla %s (length: %s chars)",
            persona.full_name,
            len(uniqueness)
        )

        return uniqueness

    except Exception as exc:
        logger.warning(
            "⚠️ Błąd generowania persona uniqueness dla %s: %s",
            persona.full_name,
            exc
        )

        # Fallback
        return (
            f"{persona.full_name or 'Ta osoba'} wyróżnia się w segmencie "
            f"'{segment_brief.segment_name}' swoim unikalnym podejściem do życia i pracy."
        )
