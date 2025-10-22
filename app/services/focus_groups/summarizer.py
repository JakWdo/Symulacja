"""
Serwis Podsumowań Dyskusji oparty na AI

Generuje automatyczne podsumowania grup fokusowych przy użyciu Google Gemini.
Analizuje wszystkie odpowiedzi i tworzy executive summary, key insights,
rekomendacje biznesowe oraz segmentację demograficzną.

Obsługuje dwa modele:
- Gemini 2.5 Flash: szybsze podsumowania (domyślne)
- Gemini 2.5 Pro: bardziej szczegółowa analiza
"""

import re
from datetime import datetime
from typing import Any, Dict, List

import numpy as np

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.prompts import DISCUSSION_SUMMARIZER_CHAT_PROMPT, create_summary_prompt
from app.models import FocusGroup, PersonaResponse, Persona
from app.services.clients import build_chat_model

settings = get_settings()

# Słowa kluczowe do analizy sentymentu
_POSITIVE_WORDS = {
    "good", "great", "excellent", "love", "like", "enjoy", "positive",
    "amazing", "wonderful", "fantastic", "best", "happy", "yes", "agree",
    "excited", "helpful", "valuable", "useful"
}
_NEGATIVE_WORDS = {
    "bad", "terrible", "hate", "dislike", "awful", "worst", "negative",
    "horrible", "poor", "no", "disagree", "concern", "worried", "against",
    "confusing", "hard", "difficult"
}

_BULLET_PREFIX_RE = re.compile(r"^[-*•\d\.\)\s]+")
_SEGMENT_LINE_RE = re.compile(r"\*\*(.+?)\*\*\s*[:\-–]\s*(.+)")


def _simple_sentiment_score(text: str) -> float:
    """
    Prosta analiza sentymentu na podstawie słów kluczowych

    Algorytm:
    1. Liczy wystąpienia słów pozytywnych (POSITIVE_WORDS)
    2. Liczy wystąpienia słów negatywnych (NEGATIVE_WORDS)
    3. Oblicza score = (pozytywne - negatywne) / wszystkie

    Args:
        text: Tekst do analizy

    Returns:
        Wartość od -1.0 (czysto negatywny) do 1.0 (czysto pozytywny)
        0.0 = neutralny lub brak słów kluczowych
    """
    lowered = text.lower()
    pos = sum(1 for token in _POSITIVE_WORDS if token in lowered)
    neg = sum(1 for token in _NEGATIVE_WORDS if token in lowered)
    total = pos + neg
    if total == 0:
        return 0.0
    return float((pos - neg) / total)


class DiscussionSummarizerService:
    """
    Generuje AI-powered podsumowania dyskusji grup fokusowych

    Wykorzystuje Google Gemini do analizy wszystkich odpowiedzi
    i tworzenia strukturalnych insightów biznesowych.
    """

    def __init__(self, use_pro_model: bool = False):
        """
        Inicjalizuj summarizer z wyborem modelu

        Args:
            use_pro_model: True = gemini-2.5-pro (wolniejszy, lepsza jakość)
                          False = gemini-2.5-flash (szybszy, zbalansowana jakość)
        """
        self.settings = settings

        # Dobieramy model do jakości i czasu wykonania
        analysis_model = getattr(settings, "ANALYSIS_MODEL", "gemini-2.5-pro")
        generation_model = getattr(settings, "PERSONA_GENERATION_MODEL", settings.DEFAULT_MODEL)

        model_name = analysis_model if use_pro_model else generation_model

        self.llm = build_chat_model(
            model=model_name,
            temperature=0.3,  # Niższa temperatura dla bardziej faktycznych podsumowań
            max_tokens=4096,  # Długie odpowiedzi
        )

        self.str_parser = StrOutputParser()

        # Używamy centralnego prompta z app/core/prompts/focus_groups.py
        self.summary_prompt = DISCUSSION_SUMMARIZER_CHAT_PROMPT

        self.chain = self.summary_prompt | self.llm | self.str_parser

    async def generate_discussion_summary(
        self,
        db: AsyncSession,
        focus_group_id: str,
        include_demographics: bool = True,
        include_recommendations: bool = True,
    ) -> Dict[str, Any]:
        """
        Generuje kompleksowe AI-powered podsumowanie dyskusji grupy fokusowej

        Args:
            db: Sesja bazy danych
            focus_group_id: ID grupy fokusowej
            include_demographics: Czy uwzględnić dane demograficzne
            include_recommendations: Czy zawrzeć rekomendacje strategiczne

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
        # Pobieramy grupę fokusową
        result = await db.execute(
            select(FocusGroup).where(FocusGroup.id == focus_group_id)
        )
        focus_group = result.scalar_one_or_none()

        if not focus_group:
            raise ValueError("Focus group not found")

        if focus_group.status != "completed":
            raise ValueError("Focus group must be completed to generate summary")

        # Pobieramy wszystkie odpowiedzi
        result = await db.execute(
            select(PersonaResponse)
            .where(PersonaResponse.focus_group_id == focus_group_id)
            .order_by(PersonaResponse.created_at)
        )
        responses = result.scalars().all()

        if not responses:
            raise ValueError("No responses found for this focus group")

        # Pobieramy persony, aby mieć kontekst demograficzny
        persona_ids = list(set(str(r.persona_id) for r in responses))
        result = await db.execute(
            select(Persona).where(Persona.id.in_(persona_ids))
        )
        personas = {str(p.id): p for p in result.scalars().all()}

        # Przygotowujemy dane dyskusji w ustrukturyzowanej formie
        discussion_data = self._prepare_discussion_data(
            focus_group, responses, personas, include_demographics
        )

        # Generujemy podsumowanie przez model AI (używając centralnego prompta)
        prompt_text = create_summary_prompt(
            discussion_data, include_recommendations
        )

        ai_response = await self.chain.ainvoke({"prompt": prompt_text})

        # Przetwarzamy odpowiedź modelu do struktury słownika
        parsed_summary = self._parse_ai_response(ai_response)

        # Dodajemy metadane techniczne
        parsed_summary["metadata"] = {
            "focus_group_id": focus_group_id,
            "focus_group_name": focus_group.name,
            "generated_at": datetime.utcnow().isoformat(),
            "model_used": self.llm.model,
            "total_responses": len(responses),
            "total_participants": len(persona_ids),
            "questions_asked": len(focus_group.questions),
        }

        # Przypisujemy podsumowanie do obiektu grupy (commit wykona wywołujący)
        focus_group.ai_summary = parsed_summary

        return parsed_summary

    def _prepare_discussion_data(
        self,
        focus_group: FocusGroup,
        responses: List[PersonaResponse],
        personas: Dict[str, Persona],
        include_demographics: bool,
    ) -> Dict[str, Any]:
        """
        Przygotowuje ustrukturyzowane dane dyskusji do analizy AI

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
                "sentiment": _simple_sentiment_score(response.response_text),  # -1.0 do 1.0
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


    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """
        Przetwarza odpowiedź AI na ustrukturyzowaną postać
        Obsługuje sekcje w formacie Markdown i wydobywa kluczowe elementy
        """
        sections = {
            "executive_summary": "",
            "key_insights": [],
            "surprising_findings": [],
            "segment_analysis": {},
            "recommendations": [],
            "sentiment_narrative": "",
            "full_analysis": ai_response,  # Zachowujemy pełny tekst dla wglądu
        }

        current_section = None
        current_content = []

        lines = ai_response.split("\n")

        for line in lines:
            line_lower = line.lower().strip()

            # Wykrywamy nagłówki sekcji
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

        # Zapisujemy ostatnią sekcję
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
            # Wyodrębniamy wypunktowania
            bullets = []
            for line in content:
                stripped = line.strip()
                if stripped.startswith(("-", "*", "•")) or (stripped and stripped[0].isdigit()):
                    bullet_text = _BULLET_PREFIX_RE.sub("", stripped)
                    if bullet_text:
                        bullets.append(bullet_text)
            sections[section_name] = bullets
        elif section_name == "segment_analysis":
            # Parsujemy analizę segmentów (pary klucz-wartość)
            segments = {}
            current_segment = None
            for line in content:
                stripped = line.strip()
                match = _SEGMENT_LINE_RE.search(stripped)
                if match:
                    current_segment = match.group(1).strip()
                    segments[current_segment] = match.group(2).strip()
                elif current_segment and stripped:
                    segments[current_segment] += " " + stripped
            sections[section_name] = segments
