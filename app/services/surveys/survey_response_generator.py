"""
Serwis Generowania Odpowiedzi na Ankiety

Generuje odpowiedzi syntetycznych person na pytania ankietowe używając Google Gemini.
Odpowiedzi są zgodne z profilami psychologicznymi i demograficznymi person.

Wydajność: Przetwarzanie równoległe dla szybkiego generowania odpowiedzi
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
import time
from datetime import datetime, timezone
from uuid import UUID
from collections import Counter
import statistics

from langchain_core.prompts import ChatPromptTemplate

from app.models import Survey, Persona, SurveyResponse
from app.schemas.survey import QuestionAnalytics
from app.db import AsyncSessionLocal
from app.services.shared.clients import build_chat_model
from app.types import (
    QuestionDict,
    AnswerValue,
    AnswerDict,
    QuestionStatistics,
    DemographicBreakdown,
)



class SurveyResponseGenerator:
    """
    Generowanie odpowiedzi person na ankiety

    Wykorzystuje AI do generowania realistycznych odpowiedzi bazując na:
    - Demografii persony (wiek, płeć, wykształcenie, dochód)
    - Cechach osobowości (Big Five)
    - Wymiarach kulturowych (Hofstede)
    - Historii i tle persony
    """

    def __init__(self):
        """Inicjalizuj serwis z LangChain LLM"""
        # Lazy import to prevent crashes if config folder is missing during app startup
        from config import prompts, models

        self.prompts = prompts
        self.models = models

        # Pobierz model config z ModelRegistry
        model_config = self.models.get("surveys", "response")

        # Inicjalizujemy model Gemini w LangChain
        self.llm = build_chat_model(
            **model_config.params
        )

    async def generate_responses(
        self, db: AsyncSession, survey_id: str
    ) -> dict[str, str | int | dict[str, int | float]]:
        """
        Generuj odpowiedzi wszystkich person na ankietę

        Główna metoda orkiestrująca generowanie odpowiedzi:
        1. Ładuje ankietę i persony projektu
        2. Dla każdej persony generuje odpowiedzi na wszystkie pytania
        3. Zapisuje odpowiedzi do bazy danych
        4. Oblicza metryki wydajności
        5. Aktualizuje status ankiety

        Args:
            db: Sesja asynchroniczna do bazy danych
            survey_id: UUID ankiety

        Returns:
            Słownik z wynikami wykonania
        """
        logger = logging.getLogger(__name__)

        logger.info(f"📊 Starting survey {survey_id}")
        start_time = time.time()

        # Pobieramy ankietę z bazy
        result = await db.execute(
            select(Survey).where(Survey.id == survey_id)
        )
        survey = result.scalar_one()
        logger.info(f"📋 Survey loaded: {survey.title}, questions: {len(survey.questions)}")

        # Aktualizujemy status ankiety
        survey.status = "running"
        survey.started_at = datetime.now(timezone.utc)
        await db.commit()

        try:
            # Pobieramy persony przypisane do projektu
            personas = await self._load_project_personas(db, survey.project_id)
            logger.info(f"👥 Loaded {len(personas)} personas from project")

            if len(personas) == 0:
                raise ValueError("Project has no personas. Generate personas first.")

            # Generujemy odpowiedzi równolegle dla wszystkich person
            logger.info(f"🔄 Generating responses for {len(personas)} personas...")
            response_times = []

            tasks = [
                self._generate_persona_survey_response(persona, survey.id, survey.questions)
                for persona in personas
            ]
            persona_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Zbieramy czasy odpowiedzi (pomijając błędy)
            for result in persona_results:
                if isinstance(result, dict) and "response_time_ms" in result:
                    response_times.append(result["response_time_ms"])

            # Wyliczamy metryki wydajności
            total_time = (time.time() - start_time) * 1000
            avg_response_time = (
                sum(response_times) / len(response_times) if response_times else 0
            )
            actual_responses = len([r for r in persona_results if not isinstance(r, Exception)])

            # Zapisujemy metryki w rekordzie ankiety
            survey.status = "completed"
            survey.completed_at = datetime.now(timezone.utc)
            survey.total_execution_time_ms = int(total_time)
            survey.avg_response_time_ms = int(avg_response_time)
            survey.actual_responses = actual_responses

            await db.commit()

            logger.info(f"✅ Survey completed: {actual_responses} responses in {total_time:.0f}ms")

            return {
                "survey_id": str(survey_id),
                "status": "completed",
                "actual_responses": actual_responses,
                "metrics": {
                    "total_execution_time_ms": total_time,
                    "avg_response_time_ms": avg_response_time,
                },
            }

        except Exception as e:
            logger.error(f"Survey {survey_id} failed: {str(e)}", exc_info=True)

            survey.status = "failed"
            await db.commit()

            return {
                "survey_id": str(survey_id),
                "status": "failed",
                "error": str(e)
            }

    async def _load_project_personas(
        self, db: AsyncSession, project_id: UUID
    ) -> list[Persona]:
        """Załaduj wszystkie persony projektu"""
        result = await db.execute(
            select(Persona).where(
                Persona.project_id == project_id,
                Persona.is_active.is_(True),
            )
        )
        return result.scalars().all()

    async def _generate_persona_survey_response(
        self, persona: Persona, survey_id: UUID, questions: list[QuestionDict]
    ) -> dict[str, str | float]:
        """
        Generuj odpowiedzi persony na wszystkie pytania ankiety

        Args:
            persona: Obiekt persony
            survey_id: UUID ankiety
            questions: Lista pytań ankiety

        Returns:
            Dict z response_time_ms i persona_id
        """
        start_time = time.time()

        # Generujemy odpowiedzi dla wszystkich pytań ankiety
        answers = {}

        for question in questions:
            answer = await self._generate_answer_for_question(persona, question)
            answers[question["id"]] = answer

        # Zapisujemy odpowiedzi ankietowe w bazie danych
        async with AsyncSessionLocal() as session:
            survey_response = SurveyResponse(
                survey_id=survey_id if isinstance(survey_id, UUID) else UUID(str(survey_id)),
                persona_id=persona.id,
                answers=answers,
                response_time_ms=int((time.time() - start_time) * 1000),
            )

            session.add(survey_response)
            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return {
            "persona_id": str(persona.id),
            "response_time_ms": (time.time() - start_time) * 1000,
        }

    async def _generate_answer_for_question(
        self, persona: Persona, question: QuestionDict
    ) -> AnswerValue:
        """
        Generuj odpowiedź persony na pojedyncze pytanie

        Używa LangChain do wygenerowania odpowiedzi zgodnej z profilem persony.

        Args:
            persona: Obiekt persony
            question: Dict z pytaniem (id, type, title, options, etc.)

        Returns:
            Odpowiedź w formacie odpowiednim dla typu pytania:
            - single-choice: str (wybrany option)
            - multiple-choice: List[str] (wybrane options)
            - rating-scale: int (wartość na skali)
            - open-text: str (wolna odpowiedź)
        """
        question_type = question["type"]
        question_title = question["title"]
        question_desc = question.get("description", "")

        # Budujemy kontekst persony
        persona_context = self._build_persona_context(persona)

        # Tworzymy prompt zależny od typu pytania
        if question_type == "single-choice":
            return await self._answer_single_choice(
                persona_context, question_title, question_desc, question["options"]
            )
        elif question_type == "multiple-choice":
            return await self._answer_multiple_choice(
                persona_context, question_title, question_desc, question["options"]
            )
        elif question_type == "rating-scale":
            scale_min = question.get("scaleMin", 1)
            scale_max = question.get("scaleMax", 5)
            return await self._answer_rating_scale(
                persona_context, question_title, question_desc, scale_min, scale_max
            )
        elif question_type == "open-text":
            return await self._answer_open_text(
                persona, persona_context, question_title, question_desc
            )

    def _build_persona_context(self, persona: Persona) -> str:
        """
        Zbuduj wzbogacony kontekst persony dla promptu

        Zawiera demografię, psychografię (Big Five) i historię życiową
        aby LLM mógł generować zróżnicowane odpowiedzi bazujące na
        unikalnych cechach każdej persony.
        """
        # Helper dla generation labels
        def get_generation_label(age: int) -> str:
            if age < 25:
                return "Gen Z"
            elif age < 40:
                return "Millennial"
            elif age < 56:
                return "Gen X"
            else:
                return "Boomer"

        # Helper dla interpretacji personality traits
        def get_personality_summary(persona: Persona) -> str:
            traits = []

            # Otwartość
            if persona.openness is not None:
                if persona.openness > 0.7:
                    traits.append("Bardzo Otwarty/a na nowe doświadczenia")
                elif persona.openness > 0.5:
                    traits.append("Umiarkowanie Otwarty/a")
                elif persona.openness > 0.3:
                    traits.append("Tradycyjny/a w podejściu")
                else:
                    traits.append("Preferuje sprawdzone rozwiązania")

            # Ekstrawersja
            if persona.extraversion is not None:
                if persona.extraversion > 0.6:
                    traits.append("Ekstrawertyczny/a")
                elif persona.extraversion < 0.4:
                    traits.append("Introwertyczny/a")

            # Sumienność
            if persona.conscientiousness is not None:
                if persona.conscientiousness > 0.7:
                    traits.append("Bardzo Sumienny/a i Zdyscyplinowany/a")
                elif persona.conscientiousness < 0.3:
                    traits.append("Spontaniczny/a i Elastyczny/a")

            # Ugodowość
            if persona.agreeableness is not None:
                if persona.agreeableness > 0.7:
                    traits.append("Empatyczny/a i Ugodowy/a")
                elif persona.agreeableness < 0.4:
                    traits.append("Asertywny/a i Niezależny/a")

            # Neurotyzm
            if persona.neuroticism is not None:
                if persona.neuroticism > 0.6:
                    traits.append("Emocjonalny/a")
                elif persona.neuroticism < 0.3:
                    traits.append("Stabilny/a emocjonalnie")

            return ", ".join(traits) if traits else "Osobowość zrównoważona"

        # Buduj wzbogacony kontekst
        generation = get_generation_label(persona.age)
        personality_summary = get_personality_summary(persona)

        # Formatowanie Big Five scores (jeśli dostępne)
        big_five_scores = []
        if persona.openness is not None:
            big_five_scores.append(f"Otwartość: {persona.openness:.2f}")
        if persona.conscientiousness is not None:
            big_five_scores.append(f"Sumienność: {persona.conscientiousness:.2f}")
        if persona.extraversion is not None:
            big_five_scores.append(f"Ekstrawersja: {persona.extraversion:.2f}")
        if persona.agreeableness is not None:
            big_five_scores.append(f"Ugodowość: {persona.agreeableness:.2f}")
        if persona.neuroticism is not None:
            big_five_scores.append(f"Neurotyzm: {persona.neuroticism:.2f}")

        big_five_str = " | ".join(big_five_scores) if big_five_scores else "N/A"

        # Background (skrócony do 400 znaków dla optymalizacji tokenów)
        background_short = (
            persona.background_story[:400] + "..."
            if persona.background_story and len(persona.background_story) > 400
            else persona.background_story or "N/A"
        )

        return f"""
=== DEMOGRAFIA ===
Imię: {persona.full_name or 'N/A'}
Wiek: {persona.age} ({generation})
Płeć: {persona.gender}
Wykształcenie: {persona.education_level or 'N/A'}
Dochód: {persona.income_bracket or 'N/A'}
Zawód: {persona.occupation or 'N/A'}
Lokalizacja: {persona.location or 'N/A'}

=== PSYCHOGRAFIA ===
Typ osobowości: {personality_summary}
Big Five Scores (0.0-1.0): {big_five_str}

=== WARTOŚCI I ZAINTERESOWANIA ===
Wartości: {', '.join(persona.values[:5]) if persona.values else 'N/A'}
Zainteresowania: {', '.join(persona.interests[:5]) if persona.interests else 'N/A'}

=== HISTORIA ===
{background_short}

KLUCZOWY INSIGHT: Odpowiedzi tej persony powinny odzwierciedlać jej unikalny profil osobowości, wartości i doświadczenia życiowe. Nie wszystkie persony myślą tak samo!
""".strip()

    async def _answer_single_choice(
        self, persona_context: str, question: str, description: str, options: list[str]
    ) -> str:
        """Generuj odpowiedź na pytanie single-choice"""
        # Load prompt from PromptRegistry
        prompt_template = self.prompts.get("surveys.single_choice")

        # Render with variables
        rendered_messages = prompt_template.render(
            persona_context=persona_context,
            question=question,
            description=f"Description: {description}" if description else "",
            options="\n".join(f"- {opt}" for opt in options)
        )

        # Create LangChain prompt
        prompt = ChatPromptTemplate.from_messages([
            (msg["role"], msg["content"]) for msg in rendered_messages
        ])

        chain = prompt | self.llm
        response = await chain.ainvoke({})
        answer = response.content.strip()

        # Sprawdzamy zgodność z listą opcji (dopasowanie przybliżone)
        answer_lower = answer.lower()
        for option in options:
            if option.lower() in answer_lower or answer_lower in option.lower():
                return option

        # Jeśli nie ma dopasowania, wybieramy pierwszą opcję
        return options[0]

    async def _answer_multiple_choice(
        self, persona_context: str, question: str, description: str, options: list[str]
    ) -> list[str]:
        """Generuj odpowiedź na pytanie multiple-choice"""
        # Load prompt from PromptRegistry
        prompt_template = self.prompts.get("surveys.multiple_choice")

        # Render with variables
        rendered_messages = prompt_template.render(
            persona_context=persona_context,
            question=question,
            description=f"Description: {description}" if description else "",
            options="\n".join(f"- {opt}" for opt in options)
        )

        # Create LangChain prompt
        prompt = ChatPromptTemplate.from_messages([
            (msg["role"], msg["content"]) for msg in rendered_messages
        ])

        chain = prompt | self.llm
        response = await chain.ainvoke({})
        answer = response.content.strip()

        # Parsujemy odpowiedzi rozdzielone przecinkami
        selected = []
        answer_parts = [a.strip() for a in answer.split(',')]

        for part in answer_parts:
            part_lower = part.lower()
            for option in options:
                if option.lower() in part_lower or part_lower in option.lower():
                    if option not in selected:
                        selected.append(option)

        # Gwarantujemy zwrot co najmniej jednej opcji
        return selected if selected else [options[0]]

    async def _answer_rating_scale(
        self, persona_context: str, question: str, description: str, scale_min: int, scale_max: int
    ) -> int:
        """Generuj odpowiedź na pytanie rating-scale"""
        # Load prompt from PromptRegistry
        prompt_template = self.prompts.get("surveys.rating_scale")

        # Render with variables
        rendered_messages = prompt_template.render(
            persona_context=persona_context,
            question=question,
            description=f"Description: {description}" if description else "",
            scale_min=str(scale_min),
            scale_max=str(scale_max)
        )

        # Create LangChain prompt
        prompt = ChatPromptTemplate.from_messages([
            (msg["role"], msg["content"]) for msg in rendered_messages
        ])

        chain = prompt | self.llm
        response = await chain.ainvoke({})
        answer = response.content.strip()

        # Wyciągamy wartość liczbową z odpowiedzi
        try:
            rating = int(''.join(filter(str.isdigit, answer)) or scale_min)
            # Ograniczamy wynik do dozwolonego zakresu
            return max(scale_min, min(scale_max, rating))
        except Exception:
            # W razie problemów bierzemy wartość środkową
            return (scale_min + scale_max) // 2

    async def _answer_open_text(
        self, persona: Persona, persona_context: str, question: str, description: str
    ) -> str:
        """Generuj odpowiedź na pytanie open-text"""
        # Load prompt from PromptRegistry
        prompt_template = self.prompts.get("surveys.open_text")

        # Render with variables
        rendered_messages = prompt_template.render(
            persona_context=persona_context,
            question=question,
            description=f"Description: {description}" if description else ""
        )

        # Create LangChain prompt
        prompt = ChatPromptTemplate.from_messages([
            (msg["role"], msg["content"]) for msg in rendered_messages
        ])

        chain = prompt | self.llm
        response = await chain.ainvoke({})
        answer = response.content.strip() if response.content else ""

        if answer:
            return answer

        logger = logging.getLogger(__name__)
        logger.warning(f"Empty open-text response for persona {persona.id}, providing fallback.")
        return self._fallback_open_text_response(persona, question)

    def _fallback_open_text_response(self, persona: Persona, question: str) -> str:
        """Zwróć bezpieczną odpowiedź fallback dla pytań otwartych, aby uniknąć pustych wartości."""
        name = (persona.full_name or "Ta persona").split(" ")[0]
        occupation = persona.occupation or "uczestnik badania"
        return (
            f"{name}, pracując jako {occupation}, potrzebuje chwili, aby w pełni odpowiedzieć na pytanie "
            f"\"{question}\". Podkreśla jednak, że temat jest dla niego ważny i wróci do niego po krótkim namyśle."
        )

    async def get_survey_analytics(
        self, db: AsyncSession, survey_id: str
    ) -> dict[str, list[dict] | DemographicBreakdown | float | None]:
        """
        Oblicz statystyki i analizę wyników ankiety

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
        """Oblicz statystyki dla pytania na podstawie typu"""
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
        """Rozłóż odpowiedzi według demografii"""
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
