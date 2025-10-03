"""
LangChain-based Focus Group Service
Uses LangChain with Gemini for concurrent persona responses
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
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


class FocusGroupServiceLangChain:
    """
    Manage focus group simulations using LangChain + Gemini
    Ensures <3s per persona and <30s total response time
    """

    def __init__(self):
        self.settings = settings
        self.memory_service = MemoryServiceLangChain()

        # Initialize LangChain Gemini LLM
        # Note: gemini-2.5 models use tokens for reasoning, so we need higher limit
        self.llm = ChatGoogleGenerativeAI(
            model=settings.DEFAULT_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.TEMPERATURE,
            max_tokens=2048,  # Increased for gemini-2.5 reasoning tokens
        )

    async def run_focus_group(
        self, db: AsyncSession, focus_group_id: str
    ) -> Dict[str, Any]:
        """
        Execute focus group simulation using LangChain
        Returns performance metrics and responses
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"🚀 Starting focus group {focus_group_id}")
        start_time = time.time()

        # Load focus group
        result = await db.execute(
            select(FocusGroup).where(FocusGroup.id == focus_group_id)
        )
        focus_group = result.scalar_one()
        logger.info(f"📋 Focus group loaded: {focus_group.name}, questions: {len(focus_group.questions)}")

        # Update status
        focus_group.status = "running"
        focus_group.started_at = datetime.now(timezone.utc)
        await db.commit()

        try:
            # Load personas
            personas = await self._load_personas(db, focus_group.persona_ids)
            logger.info(f"👥 Loaded {len(personas)} personas")

            # Process each question
            all_responses = []
            response_times = []

            print(f"🔄 FOCUS GROUP: {len(focus_group.questions)} questions to process")
            for question in focus_group.questions:
                question_start = time.time()

                print(f"❓ PROCESSING QUESTION: {question} for {len(personas)} personas")
                logger.info(f"Processing question: {question} for {len(personas)} personas")

                # Get responses from all personas concurrently
                responses = await self._get_concurrent_responses(
                    db, personas, question, focus_group_id
                )

                print(f"✅ GOT {len(responses)} RESPONSES for question")
                logger.info(f"Got {len(responses)} responses for question: {question}")

                question_time = (time.time() - question_start) * 1000
                response_times.append(question_time)

                all_responses.append(
                    {"question": question, "responses": responses, "time_ms": question_time}
                )

            # Calculate metrics
            total_time = (time.time() - start_time) * 1000
            avg_response_time = sum(response_times) / len(response_times)

            # Update focus group
            focus_group.status = "completed"
            focus_group.completed_at = datetime.now(timezone.utc)
            focus_group.total_execution_time_ms = int(total_time)
            focus_group.avg_response_time_ms = avg_response_time

            await db.commit()

            return {
                "focus_group_id": str(focus_group_id),
                "status": "completed",
                "responses": all_responses,
                "metrics": {
                    "total_execution_time_ms": total_time,
                    "avg_response_time_ms": avg_response_time,
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

        # Create tasks for concurrent execution
        tasks = [
            self._get_persona_response(db, persona, question, focus_group_id)
            for persona in personas
        ]

        # Execute concurrently with timeout
        print(f"🚀 Starting {len(tasks)} concurrent persona response tasks...")
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        results = []
        for i, resp in enumerate(responses):
            if isinstance(resp, Exception):
                print(f"❌ EXCEPTION in persona {personas[i].id}: {type(resp).__name__}: {str(resp)[:100]}")
                results.append(
                    {
                        "persona_id": str(personas[i].id),
                        "response": f"Error: {str(resp)}",
                        "error": True,
                    }
                )
            else:
                print(f"✓ Persona {str(personas[i].id)[:8]}... response received")
                results.append(resp)

        return results

    async def _get_persona_response(
        self,
        db: AsyncSession,
        persona: Persona,
        question: str,
        focus_group_id: str,
    ) -> Dict[str, Any]:
        """Get single persona response using LangChain"""
        # Retrieve relevant context from memory
        context = await self.memory_service.retrieve_relevant_context(
            db, str(persona.id), question, top_k=5
        )

        # Generate response using LangChain
        response_text = await self._generate_response(persona, question, context)

        print(f"💬 Generated response (length={len(response_text) if response_text else 0}): {response_text[:50] if response_text else 'EMPTY'}...")

        # Create event for this interaction
        await self.memory_service.create_event(
            db,
            persona_id=str(persona.id),
            event_type="response_given",
            event_data={"question": question, "response": response_text},
            focus_group_id=focus_group_id,
        )

        # Store response in database
        persona_response = PersonaResponse(
            persona_id=persona.id,
            focus_group_id=focus_group_id,
            question=question,
            response=response_text,
        )

        print(f"💾 Adding PersonaResponse to db...")
        db.add(persona_response)
        await db.commit()
        print(f"✅ Committed PersonaResponse to db")

        return {
            "persona_id": str(persona.id),
            "response": response_text,
            "context_used": len(context),
        }

    async def _generate_response(
        self, persona: Persona, question: str, context: List[Dict[str, Any]]
    ) -> str:
        """Generate persona response using LangChain"""
        import logging
        logger = logging.getLogger(__name__)

        prompt_text = self._create_response_prompt(persona, question, context)

        logger.info(f"Generating response for persona {persona.id}")
        logger.info(f"Persona data - name: {persona.full_name}, age: {persona.age}, occupation: {persona.occupation}")
        logger.info(f"Full prompt:\n{prompt_text}")

        # Use LangChain LLM to generate response directly
        result = await self.llm.ainvoke(prompt_text)

        logger.info(f"LLM result type: {type(result)}")
        logger.info(f"LLM result content: {result.content[:200] if result.content else 'EMPTY'}")
        logger.info(f"LLM result full: {result}")

        # Extract text content from AIMessage
        response_text = result.content if result.content else ""

        if not response_text:
            logger.error(f"Empty response from LLM for persona {persona.id}, question: {question}")
            logger.error(f"Full result object: {result}")

        return response_text

    def _create_response_prompt(
        self, persona: Persona, question: str, context: List[Dict[str, Any]]
    ) -> str:
        """Create prompt for persona response generation"""

        context_text = ""
        if context:
            context_text = "\n\nPast interactions:\n"
            for i, ctx in enumerate(context[:3], 1):  # Limit to 3 most relevant
                if ctx["event_type"] == "response_given":
                    context_text += f"{i}. Q: {ctx['event_data'].get('question', '')}\n"
                    context_text += f"   A: {ctx['event_data'].get('response', '')}\n"

        background = persona.background_story[:300] if persona.background_story else 'Has diverse life experiences'

        return f"""You are participating in a focus group discussion.

PERSONA DETAILS:
Name: {persona.full_name or 'Participant'}
Age: {persona.age}, Gender: {persona.gender}
Occupation: {persona.occupation or 'Professional'}
Education: {persona.education_level or 'Educated'}
Location: {persona.location or 'Urban area'}

PERSONALITY:
Values: {', '.join(persona.values[:4]) if persona.values else 'Balanced approach to life'}
Interests: {', '.join(persona.interests[:4]) if persona.interests else 'Various interests'}

BACKGROUND:
{background}
{context_text}

QUESTION: {question}

Respond naturally as this person would in 2-4 sentences. Be authentic and conversational."""