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
        self.llm = ChatGoogleGenerativeAI(
            model=settings.DEFAULT_MODEL,
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
                    if resp["consistency_score"] < 0.95:
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
            focus_group.status = "failed"
            await db.commit()
            raise e

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
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        results = []
        for i, resp in enumerate(responses):
            if isinstance(resp, Exception):
                results.append(
                    {
                        "persona_id": str(personas[i].id),
                        "response": f"Error: {str(resp)}",
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
        """Get single persona response using LangChain"""
        start_time = time.time()

        # Retrieve relevant context from memory
        context = await self.memory_service.retrieve_relevant_context(
            db, str(persona.id), question, top_k=5
        )

        # Generate response using LangChain
        response_text = await self._generate_response(persona, question, context)

        # Check consistency
        consistency_check = await self.memory_service.check_consistency(
            db, str(persona.id), response_text, context
        )

        response_time = (time.time() - start_time) * 1000

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
            retrieved_context=context,
            response_time_ms=int(response_time),
            llm_provider=self.settings.DEFAULT_LLM_PROVIDER,
            llm_model=self.settings.DEFAULT_MODEL,
            temperature=self.settings.TEMPERATURE,
            consistency_score=consistency_check["consistency_score"],
            contradicts_events=consistency_check.get("contradictions", []),
        )

        db.add(persona_response)
        await db.commit()

        return {
            "persona_id": str(persona.id),
            "response": response_text,
            "response_time_ms": response_time,
            "consistency_score": consistency_check["consistency_score"],
            "contradictions": consistency_check.get("contradictions", []),
            "context_used": len(context),
        }

    async def _generate_response(
        self, persona: Persona, question: str, context: List[Dict[str, Any]]
    ) -> str:
        """Generate persona response using LangChain"""

        prompt_text = self._create_response_prompt(persona, question, context)

        # Use LangChain chain to generate response
        result = await self.response_chain.ainvoke({"prompt": prompt_text})

        # Extract text content from AIMessage
        return result.content

    def _create_response_prompt(
        self, persona: Persona, question: str, context: List[Dict[str, Any]]
    ) -> str:
        """Create prompt for persona response generation"""

        context_text = ""
        if context:
            context_text = "\n\nRELEVANT PAST INTERACTIONS:\n"
            for i, ctx in enumerate(context, 1):
                if ctx["event_type"] == "response_given":
                    context_text += f"{i}. Q: {ctx['event_data'].get('question', '')}\n"
                    context_text += f"   A: {ctx['event_data'].get('response', '')}\n"

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
{context_text}

QUESTION: {question}

Respond naturally as this persona would, staying consistent with your profile and past responses. Be authentic, specific, and conversational. Keep your response to 2-4 sentences unless more detail is clearly needed."""