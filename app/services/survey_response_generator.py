"""
Serwis Generowania Odpowiedzi na Ankiety

Generuje odpowiedzi syntetycznych person na pytania ankietowe używając Google Gemini.
Odpowiedzi są zgodne z profilami psychologicznymi i demograficznymi person.

Wydajność: Przetwarzanie równoległe dla szybkiego generowania odpowiedzi
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
import time
from datetime import datetime, timezone
from uuid import UUID
from collections import Counter
import statistics

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from app.models import Survey, Persona, SurveyResponse
from app.schemas.survey import QuestionAnalytics
from app.core.config import get_settings

settings = get_settings()


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
        self.settings = settings

        # Initialize LangChain Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model=settings.DEFAULT_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.TEMPERATURE,
            max_tokens=1024,  # Shorter responses for surveys
        )

    async def generate_responses(
        self, db: AsyncSession, survey_id: str
    ) -> Dict[str, Any]:
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
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"📊 Starting survey {survey_id}")
        start_time = time.time()

        # Load survey
        result = await db.execute(
            select(Survey).where(Survey.id == survey_id)
        )
        survey = result.scalar_one()
        logger.info(f"📋 Survey loaded: {survey.title}, questions: {len(survey.questions)}")

        # Update status
        survey.status = "running"
        survey.started_at = datetime.now(timezone.utc)
        await db.commit()

        try:
            # Load personas from project
            personas = await self._load_project_personas(db, survey.project_id)
            logger.info(f"👥 Loaded {len(personas)} personas from project")

            if len(personas) == 0:
                raise ValueError("Project has no personas. Generate personas first.")

            # Generate responses for all personas concurrently
            logger.info(f"🔄 Generating responses for {len(personas)} personas...")
            response_times = []

            tasks = [
                self._generate_persona_survey_response(db, persona, survey)
                for persona in personas
            ]
            persona_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect response times (excluding errors)
            for result in persona_results:
                if isinstance(result, dict) and "response_time_ms" in result:
                    response_times.append(result["response_time_ms"])

            # Calculate metrics
            total_time = (time.time() - start_time) * 1000
            avg_response_time = (
                sum(response_times) / len(response_times) if response_times else 0
            )
            actual_responses = len([r for r in persona_results if not isinstance(r, Exception)])

            # Update survey
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
    ) -> List[Persona]:
        """Załaduj wszystkie persony projektu"""
        result = await db.execute(
            select(Persona).where(
                Persona.project_id == project_id,
                Persona.is_active == True
            )
        )
        return result.scalars().all()

    async def _generate_persona_survey_response(
        self, db: AsyncSession, persona: Persona, survey: Survey
    ) -> Dict[str, Any]:
        """
        Generuj odpowiedzi persony na wszystkie pytania ankiety

        Args:
            db: Sesja bazy danych
            persona: Obiekt persony
            survey: Obiekt ankiety

        Returns:
            Dict z response_time_ms i persona_id
        """
        start_time = time.time()

        # Generate answers for all questions
        answers = {}

        for question in survey.questions:
            answer = await self._generate_answer_for_question(persona, question, survey)
            answers[question["id"]] = answer

        # Save survey response to database
        survey_response = SurveyResponse(
            survey_id=survey.id,
            persona_id=persona.id,
            answers=answers,
            response_time_ms=int((time.time() - start_time) * 1000),
        )

        db.add(survey_response)
        await db.commit()

        return {
            "persona_id": str(persona.id),
            "response_time_ms": (time.time() - start_time) * 1000,
        }

    async def _generate_answer_for_question(
        self, persona: Persona, question: Dict[str, Any], survey: Survey
    ) -> Any:
        """
        Generuj odpowiedź persony na pojedyncze pytanie

        Używa LangChain do wygenerowania odpowiedzi zgodnej z profilem persony.

        Args:
            persona: Obiekt persony
            question: Dict z pytaniem (id, type, title, options, etc.)
            survey: Obiekt ankiety (kontekst)

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

        # Build persona context
        persona_context = self._build_persona_context(persona)

        # Create type-specific prompt
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
                persona_context, question_title, question_desc
            )

    def _build_persona_context(self, persona: Persona) -> str:
        """Zbuduj kontekst persony dla promptu"""
        return f"""
Age: {persona.age}, Gender: {persona.gender}
Education: {persona.education_level or 'N/A'}
Income: {persona.income_bracket or 'N/A'}
Occupation: {persona.occupation or 'N/A'}
Location: {persona.location or 'N/A'}
Values: {', '.join(persona.values) if persona.values else 'N/A'}
Interests: {', '.join(persona.interests) if persona.interests else 'N/A'}
Background: {persona.background_story or 'N/A'}
""".strip()

    async def _answer_single_choice(
        self, persona_context: str, question: str, description: str, options: List[str]
    ) -> str:
        """Generuj odpowiedź na pytanie single-choice"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are answering a survey question as a specific persona. Choose ONE option that best matches this persona's likely response. Return ONLY the chosen option text, nothing else."),
            ("user", f"""Persona Profile:
{persona_context}

Question: {question}
{f'Description: {description}' if description else ''}

Options:
{chr(10).join(f'- {opt}' for opt in options)}

Choose the ONE option this persona would most likely select:""")
        ])

        chain = prompt | self.llm
        response = await chain.ainvoke({})
        answer = response.content.strip()

        # Validate against options (fuzzy match)
        answer_lower = answer.lower()
        for option in options:
            if option.lower() in answer_lower or answer_lower in option.lower():
                return option

        # Fallback to first option if no match
        return options[0]

    async def _answer_multiple_choice(
        self, persona_context: str, question: str, description: str, options: List[str]
    ) -> List[str]:
        """Generuj odpowiedź na pytanie multiple-choice"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are answering a survey question as a specific persona. Choose one or MORE options that match this persona's likely response. Return ONLY a comma-separated list of chosen options, nothing else."),
            ("user", f"""Persona Profile:
{persona_context}

Question: {question}
{f'Description: {description}' if description else ''}

Options:
{chr(10).join(f'- {opt}' for opt in options)}

Choose the options this persona would select (comma-separated):""")
        ])

        chain = prompt | self.llm
        response = await chain.ainvoke({})
        answer = response.content.strip()

        # Parse comma-separated answers
        selected = []
        answer_parts = [a.strip() for a in answer.split(',')]

        for part in answer_parts:
            part_lower = part.lower()
            for option in options:
                if option.lower() in part_lower or part_lower in option.lower():
                    if option not in selected:
                        selected.append(option)

        # Return at least one option
        return selected if selected else [options[0]]

    async def _answer_rating_scale(
        self, persona_context: str, question: str, description: str, scale_min: int, scale_max: int
    ) -> int:
        """Generuj odpowiedź na pytanie rating-scale"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"You are answering a survey question as a specific persona. Provide a rating on a scale from {scale_min} to {scale_max}. Return ONLY the number, nothing else."),
            ("user", f"""Persona Profile:
{persona_context}

Question: {question}
{f'Description: {description}' if description else ''}

Rate from {scale_min} (lowest) to {scale_max} (highest):""")
        ])

        chain = prompt | self.llm
        response = await chain.ainvoke({})
        answer = response.content.strip()

        # Extract number
        try:
            rating = int(''.join(filter(str.isdigit, answer)) or scale_min)
            # Clamp to range
            return max(scale_min, min(scale_max, rating))
        except:
            # Fallback to middle value
            return (scale_min + scale_max) // 2

    async def _answer_open_text(
        self, persona_context: str, question: str, description: str
    ) -> str:
        """Generuj odpowiedź na pytanie open-text"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are answering a survey question as a specific persona. Provide a realistic, authentic response (2-4 sentences) that reflects this persona's perspective. Be concise and natural."),
            ("user", f"""Persona Profile:
{persona_context}

Question: {question}
{f'Description: {description}' if description else ''}

Your response:""")
        ])

        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return response.content.strip()

    async def get_survey_analytics(
        self, db: AsyncSession, survey_id: str
    ) -> Dict[str, Any]:
        """
        Oblicz statystyki i analizę wyników ankiety

        Returns:
            Dict zawierający:
            - question_analytics: Lista QuestionAnalytics dla każdego pytania
            - demographic_breakdown: Odpowiedzi rozłożone według demografii
            - completion_rate: Procent person, które odpowiedziały
            - average_response_time_ms: Średni czas odpowiedzi
        """
        # Load survey and responses
        survey_result = await db.execute(
            select(Survey).where(Survey.id == survey_id)
        )
        survey = survey_result.scalar_one()

        responses_result = await db.execute(
            select(SurveyResponse).where(SurveyResponse.survey_id == survey_id)
        )
        responses = responses_result.scalars().all()

        # Load personas for demographic breakdown
        persona_ids = [r.persona_id for r in responses]
        personas_result = await db.execute(
            select(Persona).where(Persona.id.in_(persona_ids))
        )
        personas = {p.id: p for p in personas_result.scalars().all()}

        # Calculate analytics for each question
        question_analytics = []

        for question in survey.questions:
            q_id = question["id"]
            q_type = question["type"]
            q_title = question["title"]

            # Collect answers for this question
            answers = [r.answers.get(q_id) for r in responses if q_id in r.answers]
            answers = [a for a in answers if a is not None]  # Filter None values

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

        # Demographic breakdown
        demographic_breakdown = self._calculate_demographic_breakdown(
            responses, personas, survey.questions
        )

        # Overall metrics
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

    def _calculate_question_stats(self, question_type: str, answers: List[Any]) -> Dict[str, Any]:
        """Oblicz statystyki dla pytania na podstawie typu"""
        if question_type == "single-choice":
            # Count occurrences
            counter = Counter(answers)
            return {
                "distribution": dict(counter),
                "most_common": counter.most_common(1)[0][0] if counter else None,
            }

        elif question_type == "multiple-choice":
            # Flatten lists and count
            all_options = [opt for answer_list in answers for opt in answer_list]
            counter = Counter(all_options)
            return {
                "distribution": dict(counter),
                "most_common": counter.most_common(3),
            }

        elif question_type == "rating-scale":
            # Numeric statistics
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
            # Text statistics
            texts = [str(a) for a in answers]
            lengths = [len(t.split()) for t in texts]
            return {
                "total_responses": len(texts),
                "avg_word_count": sum(lengths) / len(lengths) if lengths else 0,
                "sample_responses": texts[:5],  # First 5 responses as sample
            }

        return {}

    def _calculate_demographic_breakdown(
        self, responses: List[SurveyResponse], personas: Dict[UUID, Persona], questions: List[Dict]
    ) -> Dict[str, Dict[str, Any]]:
        """Rozłóż odpowiedzi według demografii"""
        # Group by age_group, gender, education, income
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

            # Age group
            age_group = f"{(persona.age // 10) * 10}-{(persona.age // 10) * 10 + 9}"
            if age_group not in breakdown["by_age"]:
                breakdown["by_age"][age_group] = {"count": 0}
            breakdown["by_age"][age_group]["count"] += 1

            # Gender
            gender = persona.gender
            if gender not in breakdown["by_gender"]:
                breakdown["by_gender"][gender] = {"count": 0}
            breakdown["by_gender"][gender]["count"] += 1

            # Education
            education = persona.education_level or "Unknown"
            if education not in breakdown["by_education"]:
                breakdown["by_education"][education] = {"count": 0}
            breakdown["by_education"][education]["count"] += 1

            # Income
            income = persona.income_bracket or "Unknown"
            if income not in breakdown["by_income"]:
                breakdown["by_income"][income] = {"count": 0}
            breakdown["by_income"][income]["count"] += 1

        return breakdown
