"""
Moduł Formatowania i Analityki Odpowiedzi na Ankiety

Odpowiedzialny za:
- Obliczanie statystyk pytań (rozkłady, średnie, mediany)
- Generowanie rozłożenia demograficznego odpowiedzi
- Analitykę wyników ankiet
- Fallback responses dla pytań otwartych
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from collections import Counter
import statistics

from app.models import Survey, Persona, SurveyResponse
from app.schemas.survey import QuestionAnalytics
from app.types import (
    QuestionDict,
    AnswerValue,
    QuestionStatistics,
    DemographicBreakdown,
)


logger = logging.getLogger(__name__)


class SurveyResponseFormatter:
    """
    Formatowanie i analityka odpowiedzi na ankiety

    Zajmuje się obliczaniem statystyk, generowaniem rozkładów demograficznych
    i przygotowywaniem danych analitycznych z odpowiedzi person.
    """

    def _fallback_open_text_response(self, persona: Persona, question: str) -> str:
        """
        Zwróć bezpieczną odpowiedź fallback dla pytań otwartych

        Używane gdy LLM nie wygeneruje odpowiedzi, aby uniknąć pustych wartości.

        Args:
            persona: Obiekt persony
            question: Treść pytania

        Returns:
            Fallback response jako string
        """
        name = (persona.full_name or "Ta persona").split(" ")[0]
        occupation = persona.occupation or "uczestnik badania"
        return (
            f"{name}, pracując jako {occupation}, potrzebuje chwili, aby w pełni odpowiedzieć na pytanie "
            f'"{question}". Podkreśla jednak, że temat jest dla niego ważny i wróci do niego po krótkim namyśle.'
        )

    async def get_survey_analytics(
        self, db: AsyncSession, survey_id: str
    ) -> dict[str, list[dict] | DemographicBreakdown | float | None]:
        """
        Oblicz statystyki i analizę wyników ankiety

        Args:
            db: Sesja asynchroniczna do bazy danych
            survey_id: UUID ankiety

        Returns:
            Dict zawierający:
            - question_analytics: Lista QuestionAnalytics dla każdego pytania
            - demographic_breakdown: Odpowiedzi rozłożone według demografii
            - completion_rate: Procent person, które odpowiedziały
            - average_response_time_ms: Średni czas odpowiedzi
        """
        # Wczytujemy ankietę i odpowiedzi
        survey_result = await db.execute(
            select(Survey).where(Survey.id == survey_id)
        )
        survey = survey_result.scalar_one()

        responses_result = await db.execute(
            select(SurveyResponse).where(SurveyResponse.survey_id == survey_id)
        )
        responses = responses_result.scalars().all()

        # Wczytujemy persony do analizy demograficznej
        persona_ids = [r.persona_id for r in responses]
        personas_result = await db.execute(
            select(Persona).where(Persona.id.in_(persona_ids))
        )
        personas = {p.id: p for p in personas_result.scalars().all()}

        # Obliczamy statystyki dla każdego pytania
        question_analytics = []

        for question in survey.questions:
            q_id = question["id"]
            q_type = question["type"]
            q_title = question["title"]

            # Zbieramy odpowiedzi dla tego pytania
            answers = [r.answers.get(q_id) for r in responses if q_id in r.answers]
            answers = [a for a in answers if a is not None]  # Usuwamy wartości None

            stats = self._calculate_question_stats(q_type, answers)

            question_analytics.append(
                QuestionAnalytics(
                    question_id=q_id,
                    question_type=q_type,
                    question_title=q_title,
                    responses_count=len(answers),
                    statistics=stats,
                )
            )

        # Przygotowujemy rozbicie demograficzne
        demographic_breakdown = self._calculate_demographic_breakdown(
            responses, personas, survey.questions
        )

        # Zestawiamy metryki globalne
        total_personas = len(personas)
        completion_rate = (len(responses) / total_personas * 100) if total_personas > 0 else 0

        avg_response_time = None
        if responses:
            times = [r.response_time_ms for r in responses if r.response_time_ms]
            avg_response_time = sum(times) / len(times) if times else None

        return {
            "question_analytics": [qa.model_dump() for qa in question_analytics],
            "demographic_breakdown": demographic_breakdown,
            "completion_rate": completion_rate,
            "average_response_time_ms": avg_response_time,
        }

    def _calculate_question_stats(self, question_type: str, answers: list[AnswerValue]) -> QuestionStatistics:
        """
        Oblicz statystyki dla pytania na podstawie typu

        Args:
            question_type: Typ pytania (single-choice, multiple-choice, rating-scale, open-text)
            answers: Lista odpowiedzi

        Returns:
            Dict ze statystykami odpowiednimi dla typu pytania
        """
        if question_type == "single-choice":
            # Zliczamy wystąpienia
            counter = Counter(answers)
            return {
                "distribution": dict(counter),
                "most_common": counter.most_common(1)[0][0] if counter else None,
            }

        elif question_type == "multiple-choice":
            # Spłaszczamy listy i zliczamy
            all_options = [opt for answer_list in answers for opt in answer_list]
            counter = Counter(all_options)
            return {
                "distribution": dict(counter),
                "most_common": counter.most_common(3),
            }

        elif question_type == "rating-scale":
            # Statystyki liczbowe
            numeric_answers = [int(a) for a in answers if isinstance(a, (int, float, str)) and str(a).isdigit()]
            if numeric_answers:
                return {
                    "mean": statistics.mean(numeric_answers),
                    "median": statistics.median(numeric_answers),
                    "mode": statistics.mode(numeric_answers) if len(numeric_answers) > 1 else numeric_answers[0],
                    "min": min(numeric_answers),
                    "max": max(numeric_answers),
                    "std": statistics.stdev(numeric_answers) if len(numeric_answers) > 1 else 0,
                    "distribution": dict(Counter(numeric_answers)),
                }
            return {}

        elif question_type == "open-text":
            # Statystyki tekstowe
            texts = [str(a) for a in answers]
            lengths = [len(t.split()) for t in texts]
            return {
                "total_responses": len(texts),
                "avg_word_count": sum(lengths) / len(lengths) if lengths else 0,
                "sample_responses": texts[:5],  # Pierwsze 5 odpowiedzi jako próbka
            }

        return {}

    def _calculate_demographic_breakdown(
        self, responses: list[SurveyResponse], personas: dict[UUID, Persona], questions: list[QuestionDict]
    ) -> DemographicBreakdown:
        """
        Rozłóż odpowiedzi według demografii

        Args:
            responses: Lista odpowiedzi person
            personas: Dict mapujący persona_id -> Persona
            questions: Lista pytań ankiety

        Returns:
            Dict z rozkładem demograficznym (by_age, by_gender, by_education, by_income)
        """
        # Grupujemy według wieku, płci, wykształcenia i dochodu
        breakdown = {
            "by_age": {},
            "by_gender": {},
            "by_education": {},
            "by_income": {},
        }

        for response in responses:
            persona = personas.get(response.persona_id)
            if not persona:
                continue

            # Przedział wiekowy
            age_group = f"{(persona.age // 10) * 10}-{(persona.age // 10) * 10 + 9}"
            if age_group not in breakdown["by_age"]:
                breakdown["by_age"][age_group] = {"count": 0}
            breakdown["by_age"][age_group]["count"] += 1

            # Płeć
            gender = persona.gender
            if gender not in breakdown["by_gender"]:
                breakdown["by_gender"][gender] = {"count": 0}
            breakdown["by_gender"][gender]["count"] += 1

            # Wykształcenie
            education = persona.education_level or "Unknown"
            if education not in breakdown["by_education"]:
                breakdown["by_education"][education] = {"count": 0}
            breakdown["by_education"][education]["count"] += 1

            # Dochód
            income = persona.income_bracket or "Unknown"
            if income not in breakdown["by_income"]:
                breakdown["by_income"][income] = {"count": 0}
            breakdown["by_income"][income]["count"] += 1

        return breakdown
