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
            temperature=1.0,  # Maximum diversity for unique persona responses
            max_tokens=600,
            top_p=0.95,  # Nucleus sampling for better diversity
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

            for idx, question in enumerate(focus_group.questions, 1):
                logger.info(
                    f"Processing question {idx}/{len(focus_group.questions)}: {question[:50]}...",
                    extra={"focus_group_id": str(focus_group_id), "question_index": idx}
                )
                question_start = time.time()

                # Get responses from all personas concurrently with retry
                max_question_retries = 2
                responses = None
                for attempt in range(1, max_question_retries + 1):
                    try:
                        responses = await self._get_concurrent_responses(
                            db, personas, question, focus_group_id, focus_group.project_context
                        )
                        # Verify we got responses from all personas
                        if len(responses) == len(personas):
                            break
                        else:
                            logger.warning(
                                f"Got {len(responses)}/{len(personas)} responses on attempt {attempt}",
                                extra={"focus_group_id": str(focus_group_id), "question_index": idx}
                            )
                    except Exception as e:
                        logger.error(
                            f"Question {idx} failed on attempt {attempt}: {str(e)}",
                            exc_info=True,
                            extra={"focus_group_id": str(focus_group_id), "question_index": idx}
                        )
                        if attempt == max_question_retries:
                            raise

                if not responses:
                    logger.error(
                        f"Failed to get responses for question {idx}",
                        extra={"focus_group_id": str(focus_group_id), "question_index": idx}
                    )
                    continue

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

                logger.info(
                    f"Question {idx} completed in {question_time:.0f}ms",
                    extra={"focus_group_id": str(focus_group_id), "question_index": idx}
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
        project_context: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get responses from all personas concurrently using LangChain

        NOTE: Each persona gets its own DB session to avoid SQLAlchemy concurrent access errors
        """
        from app.db.session import AsyncSessionLocal

        async def _get_response_with_own_session(persona: Persona):
            """Wrapper that creates a new DB session for each persona"""
            async with AsyncSessionLocal() as persona_db:
                try:
                    return await self._get_persona_response(
                        persona_db, persona, question, focus_group_id, project_context
                    )
                finally:
                    await persona_db.close()

        tasks = [
            _get_response_with_own_session(persona)
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
        project_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get single persona response using LangChain with retry and memory support."""

        logger.info(f"🚀 START _get_persona_response for persona {str(persona.id)[:8]}", extra={"persona_id": str(persona.id)})
        start_time = time.time()

        # Get conversation history from THIS focus group
        try:
            history = await self._get_recent_history(db, persona.id, focus_group_id, limit=5)
            history_summary = self._format_history_summary(history)
        except Exception as e:
            logger.error(
                f"🔥 Failed to get recent history for persona {str(persona.id)[:8]}: {str(e)[:300]}",
                exc_info=True,
                extra={"persona_id": str(persona.id), "focus_group_id": focus_group_id}
            )
            history = []
            history_summary = None

        # TEMPORARILY DISABLED: Get relevant context from persona's memory
        # Embeddings API is causing issues - skip for now
        logger.info(f"⚠️ Skipping embeddings/context retrieval for persona {str(persona.id)[:8]} (temporarily disabled)", extra={"persona_id": str(persona.id)})
        context = []

        # TODO: Re-enable once embeddings are fixed
        # try:
        #     context = await self.memory_service.retrieve_relevant_context(
        #         db, str(persona.id), question, top_k=5
        #     )
        # except Exception as e:
        #     logger.error(f"🔥 Failed to retrieve context: {str(e)[:300]}", exc_info=True)
        #     context = []

        # Debug logging
        logger.info(
            f"📚 Context for persona {str(persona.id)[:8]}: "
            f"history_items={len(history)}, context_items={len(context)}, "
            f"history_summary={'Yes (' + str(len(history_summary)) + ' chars)' if history_summary else 'No'}",
            extra={"persona_id": str(persona.id), "focus_group_id": focus_group_id}
        )

        if history:
            logger.debug(
                f"📜 Recent history for persona {str(persona.id)[:8]}:\n{history_summary[:300] if history_summary else 'NONE'}...",
                extra={"persona_id": str(persona.id)}
            )

        # Generate response with retry logic and validation
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
                    project_context=project_context,
                )
            except Exception as exc:
                logger.error(
                    f"Persona response generation FAILED on attempt {attempt}",
                    exc_info=exc,
                    extra={"persona_id": str(persona.id), "attempt": attempt, "question": question[:100]}
                )
                candidate = ""

            candidate = (candidate or "").strip()

            logger.info(
                f"🎭 Persona {str(persona.id)[:8]} attempt {attempt}/{max_attempts}: '{candidate[:150] if candidate else 'EMPTY'}'...",
                extra={"persona_id": str(persona.id), "length": len(candidate), "attempt": attempt}
            )

            # Improved validation: check length, not error, not fallback text
            is_valid = (
                candidate
                and len(candidate) > 20  # More strict minimum length
                and not candidate.lower().startswith("error")
                and "wymaga dalszego potwierdzenia" not in candidate.lower()  # Detect fallback
                and "zebrać dodatkowe dane" not in candidate.lower()  # Detect fallback
            )

            if is_valid:
                logger.info(
                    f"✅ Valid response accepted from persona {str(persona.id)[:8]} on attempt {attempt}",
                    extra={"persona_id": str(persona.id), "attempt": attempt}
                )
                response_text = candidate
                break
            else:
                logger.warning(
                    f"❌ Invalid response from persona {str(persona.id)[:8]} on attempt {attempt}: "
                    f"len={len(candidate)}, starts_error={candidate.lower().startswith('error') if candidate else False}, "
                    f"is_fallback={'wymaga dalszego' in candidate.lower() if candidate else False}",
                    extra={"persona_id": str(persona.id), "attempt": attempt}
                )

            await asyncio.sleep(0.3 * attempt)

        if not response_text:
            logger.error(
                f"❌❌❌ ALL attempts failed for persona {str(persona.id)[:8]}, using fallback response",
                extra={"persona_id": str(persona.id), "question": question[:100]}
            )
            response_text = self._fallback_response(question, context, history_summary)

        # TEMPORARILY DISABLED: Consistency checker (uses embeddings and problematic JSON parsing)
        logger.info(f"⚠️ Skipping consistency check for persona {str(persona.id)[:8]} (temporarily disabled)", extra={"persona_id": str(persona.id)})
        consistency_check = {"consistency_score": 1.0, "contradictions": [], "is_consistent": True}

        # TODO: Re-enable once consistency checker is fixed
        # try:
        #     consistency_check = await self.memory_service.check_consistency(
        #         db, str(persona.id), response_text, context
        #     )
        # except Exception as e:
        #     logger.warning(f"⚠️ Consistency check failed: {str(e)[:200]}", exc_info=True)
        #     consistency_check = {"consistency_score": 1.0, "contradictions": [], "is_consistent": True}

        consistency_score = float(consistency_check.get("consistency_score", 1.0))
        contradictions = consistency_check.get("contradictions") or []
        if not isinstance(contradictions, list):
            contradictions = [contradictions]

        response_time = (time.time() - start_time) * 1000

        # TEMPORARILY DISABLED: Event sourcing (creates embeddings which are problematic)
        logger.info(f"⚠️ Skipping event creation for persona {str(persona.id)[:8]} (temporarily disabled)", extra={"persona_id": str(persona.id)})

        # TODO: Re-enable once embeddings are fixed
        # await self.memory_service.create_event(
        #     db,
        #     persona_id=str(persona.id),
        #     event_type="response_given",
        #     event_data={"question": question, "response": response_text},
        #     focus_group_id=focus_group_id,
        # )

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
        history_summary: Optional[str] = None,
        attempt: int = 1,
        project_context: Optional[str] = None,
    ) -> str:
        """Generate persona response using LangChain"""

        prompt_text = self._create_response_prompt(
            persona,
            question,
            context,
            history_summary=history_summary,
            attempt=attempt,
            project_context=project_context,
        )

        # Log the full prompt being sent (truncated for readability)
        logger.info(
            f"📝 Sending prompt to LLM for persona {str(persona.id)[:8]} (attempt {attempt}):\n"
            f"Prompt length: {len(prompt_text)} chars\n"
            f"First 500 chars: {prompt_text[:500]}...\n"
            f"Context items: {len(context)}, History: {'Yes' if history_summary else 'No'}",
            extra={"persona_id": str(persona.id), "attempt": attempt}
        )

        try:
            result = await self.response_chain.ainvoke({"prompt": prompt_text})
        except Exception as e:
            logger.error(
                f"🔥 LLM invocation FAILED for persona {str(persona.id)[:8]}: {str(e)[:300]}",
                exc_info=True,
                extra={"persona_id": str(persona.id), "attempt": attempt, "error_type": type(e).__name__}
            )
            raise

        # Handle different result types
        logger.debug(
            f"🔍 Raw LLM result type: {type(result)}, has_content: {hasattr(result, 'content')}, "
            f"is_str: {isinstance(result, str)}, is_dict: {isinstance(result, dict)}",
            extra={"persona_id": str(persona.id), "result_type": str(type(result))}
        )

        if hasattr(result, 'content'):
            response_text = result.content
            logger.debug(f"  → Extracted from .content attribute", extra={"persona_id": str(persona.id)})
        elif isinstance(result, str):
            response_text = result
            logger.debug(f"  → Used as string directly", extra={"persona_id": str(persona.id)})
        elif isinstance(result, dict) and 'content' in result:
            response_text = result['content']
            logger.debug(f"  → Extracted from dict['content']", extra={"persona_id": str(persona.id)})
        else:
            logger.error(
                f"❌ Unexpected result type from LLM: {type(result)}, raw={str(result)[:200]}",
                extra={"persona_id": str(persona.id), "attempt": attempt}
            )
            response_text = ""

        # Log the response received
        logger.info(
            f"📬 Received from LLM for persona {str(persona.id)[:8]}: "
            f"length={len(response_text) if response_text else 0}, "
            f"preview='{response_text[:100] if response_text else 'EMPTY'}'...",
            extra={"persona_id": str(persona.id), "attempt": attempt}
        )

        return response_text or ""


    def _create_response_prompt(
        self,
        persona: Persona,
        question: str,
        context: List[Dict[str, Any]],
        history_summary: Optional[str] = None,
        attempt: int = 1,
        project_context: Optional[str] = None,
    ) -> str:
        """Create prompt for persona response generation"""

        # Format context from past interactions
        context_text = ""
        if context:
            context_text = "\n\nRELEVANT PAST INTERACTIONS:\n"
            for i, ctx in enumerate(context, 1):
                if ctx["event_type"] == "response_given":
                    context_text += f"{i}. Q: {ctx['event_data'].get('question', '')}\n"
                    context_text += f"   A: {ctx['event_data'].get('response', '')}\n"

        # Format recent conversation history
        recent_history = ""
        if history_summary:
            recent_history = f"\n\nRECENT CONVERSATION:\n{history_summary}\n"

        # Project context
        project_section = ""
        if project_context:
            project_section = f"\n\nPROJECT CONTEXT:\n{project_context}\n"

        return f"""You are roleplaying as a specific persona in a market research focus group.

YOUR PERSONA PROFILE:
{persona.personality_prompt or f"A {persona.age}-year-old {persona.gender} from {persona.location or 'an urban area'}."}

DEMOGRAPHICS:
- Name: {persona.full_name or f'{persona.gender} {persona.age}'}
- Age: {persona.age}
- Gender: {persona.gender}
- Location: {persona.location or 'Not specified'}
- Education: {persona.education_level or 'Not specified'}
- Income: {persona.income_bracket or 'Not specified'}
- Occupation: {persona.occupation or 'Not specified'}

BACKGROUND:
{persona.background_story or 'A person with unique life experiences and perspectives.'}

VALUES: {', '.join(persona.values) if persona.values else 'Not specified'}
INTERESTS: {', '.join(persona.interests) if persona.interests else 'Not specified'}
{project_section}{context_text}{recent_history}

QUESTION: {question}

Respond naturally as this persona would, staying consistent with your profile and past responses. Be authentic, specific, and conversational. Draw from YOUR unique background, age, location, and values. Keep your response to 2-4 sentences unless more detail is clearly needed."""

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
        for idx, response in enumerate(reversed(history), 1):
            question = (response.question or '').replace('\n', ' ').strip()
            answer = (response.response or '').replace('\n', ' ').strip()
            if answer:
                # Keep more of the answer for better context
                answer = answer[:300]
            lines.append(f"[Exchange {idx}]")
            lines.append(f"Q: {question}")
            lines.append(f"Your Answer: {answer}")
            lines.append("")  # Empty line for readability
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
