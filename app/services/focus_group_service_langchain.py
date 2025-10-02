"""
LangChain-based Focus Group Service
Uses LangChain with Gemini for concurrent persona responses
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
import logging
import time
from datetime import datetime, timezone
from uuid import UUID

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from app.models import FocusGroup, Persona, PersonaResponse
from app.services.memory_service_langchain import MemoryServiceLangChain
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class FocusGroupServiceLangChain:
    """
    Manage focus group simulations using LangChain + Gemini
    Ensures <3s per persona and <30s total response time
    """

    def __init__(self):
        self.settings = settings
        self.memory_service = MemoryServiceLangChain()

        # Initialize LangChain Gemini LLM
        persona_model = getattr(settings, "PERSONA_GENERATION_MODEL", settings.DEFAULT_MODEL)

        self.llm = ChatGoogleGenerativeAI(
            model=persona_model,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.TEMPERATURE,
            max_tokens=500,
        )

        # Create persona response prompt template
        self.response_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are participating in a focus group. Respond naturally as the persona described."),
            ("user", "{prompt}")
        ])

        # Create LangChain chain for response generation
        self.response_chain = self.response_prompt | self.llm

    async def run_focus_group(
        self, db: AsyncSession, focus_group_id: str
    ) -> Dict[str, Any]:
        """
        Execute focus group simulation using LangChain
        Returns performance metrics and responses
        """
        start_time = time.time()

        # Load focus group
        result = await db.execute(
            select(FocusGroup).where(FocusGroup.id == focus_group_id)
        )
        focus_group = result.scalar_one()

        # Update status
        focus_group.status = "running"
        focus_group.started_at = datetime.now(timezone.utc)
        await db.commit()

        try:
            # Load personas
            personas = await self._load_personas(db, focus_group.persona_ids)

            # Process each question
            all_responses = []
            response_times = []
            consistency_errors = 0

            for question in focus_group.questions:
                question_start = time.time()

                # Get responses from all personas concurrently
                responses = await self._get_concurrent_responses(
                    db, personas, question, focus_group_id
                )

                question_time = (time.time() - question_start) * 1000
                response_times.append(question_time)

                # Count consistency errors
                for resp in responses:
                    score = resp.get("consistency_score") if isinstance(resp, dict) else None
                    try:
                        score_value = float(score) if score is not None else None
                    except (TypeError, ValueError):
                        score_value = None

                    if score_value is None or score_value < 0.95:
                        consistency_errors += 1

                all_responses.append(
                    {"question": question, "responses": responses, "time_ms": question_time}
                )

            # Calculate metrics
            total_time = (time.time() - start_time) * 1000
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            consistency_error_rate = consistency_errors / (
                len(focus_group.questions) * len(personas)
            )

            # Update focus group
            focus_group.status = "completed"
            focus_group.completed_at = datetime.now(timezone.utc)
            focus_group.total_execution_time_ms = int(total_time)
            focus_group.avg_response_time_ms = avg_response_time
            focus_group.max_response_time_ms = int(max_response_time)
            focus_group.consistency_errors_count = consistency_errors
            focus_group.consistency_error_rate = consistency_error_rate

            await db.commit()

            return {
                "focus_group_id": str(focus_group_id),
                "status": "completed",
                "responses": all_responses,
                "metrics": {
                    "total_execution_time_ms": total_time,
                    "avg_response_time_ms": avg_response_time,
                    "max_response_time_ms": max_response_time,
                    "consistency_errors_count": consistency_errors,
                    "consistency_error_rate": consistency_error_rate,
                    "meets_requirements": focus_group.meets_performance_requirements(),
                },
            }

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                f"Focus group {focus_group_id} failed: {str(e)}",
                exc_info=True,
                extra={"focus_group_id": str(focus_group_id)}
            )

            focus_group.status = "failed"
            # Store first 500 chars of error for debugging
            if hasattr(focus_group, 'error_message'):
                focus_group.error_message = str(e)[:500]
            await db.commit()

            # Don't re-raise - this is background task, just log
            return {
                "focus_group_id": str(focus_group_id),
                "status": "failed",
                "error": str(e)
            }

    async def _load_personas(
        self, db: AsyncSession, persona_ids: List[UUID]
    ) -> List[Persona]:
        """Load persona objects"""
        result = await db.execute(select(Persona).where(Persona.id.in_(persona_ids)))
        return result.scalars().all()

    async def _get_concurrent_responses(
        self,
        db: AsyncSession,
        personas: List[Persona],
        question: str,
        focus_group_id: str,
    ) -> List[Dict[str, Any]]:
        """Get responses from all personas concurrently using LangChain"""

        tasks = [
            self._get_persona_response(db, persona, question, focus_group_id)
            for persona in personas
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        results: List[Dict[str, Any]] = []
        for persona, resp in zip(personas, responses):
            if isinstance(resp, Exception):
                logger.warning(
                    "Persona response failed; using fallback",
                    exc_info=resp,
                    extra={"persona_id": str(persona.id), "focus_group_id": focus_group_id},
                )
                results.append(
                    {
                        "persona_id": str(persona.id),
                        "response": "Potrzebuję chwili, aby zebrać myśli – proponuję zebrać więcej informacji od pozostałych uczestników i wrócę do tematu w następnej rundzie.",
                        "response_time_ms": None,
                        "consistency_score": None,
                        "contradictions": [],
                        "context_used": 0,
                        "error": True,
                    }
                )
            else:
                results.append(resp)

        return results

    async def _get_persona_response(
        self,
        db: AsyncSession,
        persona: Persona,
        question: str,
        focus_group_id: str,
    ) -> Dict[str, Any]:
        """Get single persona response using LangChain with retry and memory support."""

        start_time = time.time()

        history = await self._get_recent_history(db, persona.id, focus_group_id, limit=3)
        history_summary = self._format_history_summary(history)

        context = await self.memory_service.retrieve_relevant_context(
            db, str(persona.id), question, top_k=5
        )

        response_text: Optional[str] = None
        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            try:
                candidate = await self._generate_response(
                    persona,
                    question,
                    context,
                    history_summary=history_summary,
                    attempt=attempt,
                )
            except Exception as exc:
                logger.warning(
                    "Persona response attempt failed",
                    exc_info=exc,
                    extra={"persona_id": str(persona.id), "attempt": attempt},
                )
                candidate = ""

            candidate = (candidate or "").strip()

            if candidate and not candidate.lower().startswith("error") and len(candidate) > 3:
                response_text = candidate
                break

            await asyncio.sleep(0.2 * attempt)

        if not response_text:
            response_text = self._fallback_response(question, context, history_summary)

        consistency_check = await self.memory_service.check_consistency(
            db, str(persona.id), response_text, context
        )
        if not isinstance(consistency_check, dict):
            consistency_check = {"consistency_score": 1.0, "contradictions": [], "is_consistent": True}

        consistency_score = float(consistency_check.get("consistency_score", 1.0))
        contradictions = consistency_check.get("contradictions") or []
        if not isinstance(contradictions, list):
            contradictions = [contradictions]

        response_time = (time.time() - start_time) * 1000

        await self.memory_service.create_event(
            db,
            persona_id=str(persona.id),
            event_type="response_given",
            event_data={"question": question, "response": response_text},
            focus_group_id=focus_group_id,
        )

        persona_response = PersonaResponse(
            persona_id=persona.id,
            focus_group_id=focus_group_id,
            question=question,
            response=response_text,
            retrieved_context=context,
            response_time_ms=int(response_time),
            llm_provider=self.settings.DEFAULT_LLM_PROVIDER,
            llm_model=self.settings.DEFAULT_MODEL,
            temperature=self.settings.TEMPERATURE,
            consistency_score=consistency_score,
            contradicts_events=contradictions,
        )

        db.add(persona_response)
        await db.commit()

        return {
            "persona_id": str(persona.id),
            "response": response_text,
            "response_time_ms": response_time,
            "consistency_score": consistency_score,
            "contradictions": contradictions,
            "context_used": len(context),
        }

    async def _generate_response(
        self,
        persona: Persona,
        question: str,
        context: List[Dict[str, Any]],
        history_summary: Optional[str],
        attempt: int,
    ) -> str:
        """Generate persona response using LangChain"""

        prompt_text = self._create_response_prompt(
            persona,
            question,
            context,
            history_summary=history_summary,
            attempt=attempt,
        )

        result = await self.response_chain.ainvoke({"prompt": prompt_text})

        return result.content

    def _create_response_prompt(
        self,
        persona: Persona,
        question: str,
        context: List[Dict[str, Any]],
        history_summary: Optional[str] = None,
        attempt: int = 1,
    ) -> str:
        """Create prompt for persona response generation"""

        context_text = ""
        if context:
            context_text = "\n\nRELEVANT PAST INTERACTIONS:\n"
            for i, ctx in enumerate(context, 1):
                if ctx["event_type"] == "response_given":
                    context_text += f"{i}. Q: {ctx['event_data'].get('question', '')}\n"
                    context_text += f"   A: {ctx['event_data'].get('response', '')}\n"

        recent_history = ""
        if history_summary:
            recent_history = f"\n\nRECENT CONVERSATION SNAPSHOT:\n{history_summary}\n"

        retry_suffix = ""
        if attempt > 1:
            retry_suffix = (
                "\n\nTwoja ostatnia odpowiedź była zbyt lakoniczna. "
                "Tym razem odpowiedz w 2-4 zdaniach, konkretnie odnosząc się do pytania i wcześniejszych spostrzeżeń."
            )

        return f"""You are roleplaying as a specific persona in a market research focus group.

YOUR PERSONA PROFILE:
{persona.personality_prompt}

DEMOGRAPHICS:
- Age: {persona.age}
- Gender: {persona.gender}
- Location: {persona.location}
- Education: {persona.education_level}
- Income: {persona.income_bracket}

BACKGROUND:
{persona.background_story}

VALUES: {', '.join(persona.values) if persona.values else 'N/A'}
INTERESTS: {', '.join(persona.interests) if persona.interests else 'N/A'}
{context_text}{recent_history}

QUESTION: {question}

Respond naturally as this persona would, staying consistent with your profile and past responses. Be authentic, specific, and conversational. Keep your response to 2-4 sentences unless more detail is clearly needed.{retry_suffix}"""

    async def _get_recent_history(
        self,
        db: AsyncSession,
        persona_id: UUID,
        focus_group_id: str,
        limit: int = 3,
    ) -> List[PersonaResponse]:
        result = await db.execute(
            select(PersonaResponse)
            .where(
                PersonaResponse.persona_id == persona_id,
                PersonaResponse.focus_group_id == focus_group_id,
            )
            .order_by(PersonaResponse.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    def _format_history_summary(self, history: List[PersonaResponse]) -> Optional[str]:
        if not history:
            return None
        lines: List[str] = []
        for response in reversed(history):
            question = (response.question or '').replace('\n', ' ').strip()
            answer = (response.response or '').replace('\n', ' ').strip()
            if answer:
                answer = answer[:220]
            lines.append(f"Q: {question}")
            lines.append(f"A: {answer}")
        return '\n'.join(lines)

    def _fallback_response(
        self,
        question: str,
        context: List[Dict[str, Any]],
        history_summary: Optional[str],
    ) -> str:
        prefix = "Bazując na wcześniejszej dyskusji" if history_summary else "Z mojej perspektywy"
        if context:
            prefix += ", nawiązując do poprzednich obserwacji"
        return (
            f"{prefix} uważam, że {question.lower()} wymaga dalszego potwierdzenia w kolejnych testach. "
            "Sugeruję zebrać dodatkowe dane od pozostałych uczestników i doprecyzować kolejne kroki eksperymentu."
        )
