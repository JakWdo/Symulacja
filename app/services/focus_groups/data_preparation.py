"""
Data preparation utilities for discussion summarization.

Prepares structured data from focus group responses for AI analysis.
"""

import logging
from typing import Any

import numpy as np

from app.models import FocusGroup, PersonaResponse, Persona
from .nlp.sentiment_analysis import simple_sentiment_score

logger = logging.getLogger(__name__)


def prepare_discussion_data(
    focus_group: FocusGroup,
    responses: list[PersonaResponse],
    personas: dict[str, Persona],
    include_demographics: bool,
) -> dict[str, Any]:
    """
    Przygotowuje ustrukturyzowane dane dyskusji do analizy AI.

    Proces:
    1. Grupuje odpowiedzi po pytaniach (każde pytanie ma listę odpowiedzi)
    2. Dla każdej odpowiedzi oblicza sentiment score
    3. Dodaje dane demograficzne persony (jeśli include_demographics=True)
    4. Agreguje statystyki demograficzne całej grupy

    Args:
        focus_group: Obiekt grupy fokusowej
        responses: Lista wszystkich odpowiedzi person
        personas: Słownik {persona_id: Persona}
        include_demographics: Czy dodać dane demograficzne

    Returns:
        Słownik z danymi:
        {
            "topic": str,
            "description": str,
            "responses_by_question": {
                "Question 1?": [
                    {"response": str, "sentiment": float, "demographics": {...}},
                    ...
                ]
            },
            "demographic_summary": {
                "age_range": "25-65",
                "gender_distribution": {"male": 5, "female": 5},
                "education_levels": ["Bachelor's", "Master's"],
                "sample_size": 10
            },
            "total_responses": int
        }
    """

    # Grupuj odpowiedzi po pytaniach
    responses_by_question = {}
    for response in responses:
        if response.question_text not in responses_by_question:
            responses_by_question[response.question_text] = []

        persona = personas.get(str(response.persona_id))
        response_data = {
            "response": response.response_text,
            "sentiment": simple_sentiment_score(response.response_text),  # -1.0 do 1.0
        }

        # Dodaj demografię jeśli włączona
        if include_demographics and persona:
            response_data["demographics"] = {
                "age": persona.age,
                "gender": persona.gender,
                "education": persona.education_level,
                "occupation": persona.occupation,
            }

        responses_by_question[response.question_text].append(response_data)

    # Agreguj statystyki demograficzne całej grupy
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


def prepare_prompt_variables(
    discussion_data: dict[str, Any],
    include_recommendations: bool,
    language: str = 'pl',
) -> dict[str, str]:
    """
    Przygotowuje zmienne do renderowania promptu z YAML.

    Formatuje pytania, odpowiedzi, sentiment i demografię.
    Parametryzuje język dla treści AI output (nagłówki sekcji pozostają po angielsku).

    Args:
        discussion_data: Dane dyskusji z responses, questions, demographics
        include_recommendations: Czy zawrzeć sekcję Strategic Recommendations
        language: Język dla treści podsumowania ('pl' lub 'en')

    Returns:
        Słownik zmiennych do podstawienia w prompt template
    """

    topic = discussion_data["topic"]
    description = discussion_data["description"] or "No description provided"
    responses_by_question = discussion_data["responses_by_question"]
    demo_summary = discussion_data.get("demographic_summary")

    # Formatujemy pytania wraz z odpowiedziami
    formatted_discussion = []
    for idx, (question, responses) in enumerate(responses_by_question.items(), 1):
        formatted_discussion.append(f"\n**Question {idx}:** {question}")
        formatted_discussion.append(f"*({len(responses)} responses)*\n")

        for ridx, resp in enumerate(responses[:15], 1):  # Ograniczamy liczbę odpowiedzi, aby nie przekroczyć limitu tokenów
            text = resp["response"][:300]  # Skracamy bardzo długie wypowiedzi
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

    # Kontekst demograficzny
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
## 5. STRATEGIC RECOMMENDATIONS (2-3 bullet points, ≤25 words each)
Give the most valuable next steps for the product/marketing team.
Format every bullet as: **Actionable theme**: succinct action with expected impact.
Use proper markdown bold syntax: **text** (two asterisks on both sides).
Tie each recommendation to evidence from the discussion.
"""

    # Instrukcja językowa (nagłówki po angielsku, treść w wybranym języku)
    language_instruction_map = {
        'pl': (
            "\n\n**CRITICAL LANGUAGE INSTRUCTION:**\n"
            "- Keep ALL section headings in ENGLISH (e.g., ## 1. EXECUTIVE SUMMARY, ## 2. KEY INSIGHTS)\n"
            "- Write ALL content (paragraphs, bullet points, analysis, quotes) in POLISH\n"
            "- Use Polish grammar, vocabulary, and phrasing throughout the content\n"
            "- Example: '## 2. KEY INSIGHTS' followed by '**Główny problem**: Użytkownicy oczekują...'\n"
        ),
        'en': (
            "\n\n**CRITICAL LANGUAGE INSTRUCTION:**\n"
            "- Keep ALL section headings in ENGLISH (e.g., ## 1. EXECUTIVE SUMMARY, ## 2. KEY INSIGHTS)\n"
            "- Write ALL content (paragraphs, bullet points, analysis, quotes) in ENGLISH\n"
            "- Use English grammar, vocabulary, and phrasing throughout the content\n"
            "- Example: '## 2. KEY INSIGHTS' followed by '**Main concern**: Users expect...'\n"
        ),
    }

    language_instruction = language_instruction_map.get(
        language,
        language_instruction_map['pl']
    )

    return {
        "topic": topic,
        "description": description,
        "demo_context": demo_context,
        "discussion_text": discussion_text,
        "recommendations_section": recommendations_section,
        "language_instruction": language_instruction,
    }
