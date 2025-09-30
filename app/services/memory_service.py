from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
import numpy as np
from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer

from app.models import PersonaEvent, PersonaResponse, Persona
from app.core.config import get_settings

settings = get_settings()


class MemoryService:
    """
    Event sourcing and memory retrieval for personas
    Maintains temporal consistency through immutable event log
    """

    def __init__(self):
        self.settings = settings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def create_event(
        self,
        db: AsyncSession,
        persona_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        focus_group_id: Optional[str] = None,
    ) -> PersonaEvent:
        """Create immutable event in event store"""

        # Get sequence number
        result = await db.execute(
            select(PersonaEvent)
            .where(PersonaEvent.persona_id == persona_id)
            .order_by(PersonaEvent.sequence_number.desc())
        )
        last_event = result.scalar_one_or_none()
        sequence_number = (last_event.sequence_number + 1) if last_event else 1

        # Generate embedding for semantic search
        event_text = self._event_to_text(event_type, event_data)
        embedding = await self._generate_embedding(event_text)

        event = PersonaEvent(
            persona_id=persona_id,
            focus_group_id=focus_group_id,
            event_type=event_type,
            event_data=event_data,
            sequence_number=sequence_number,
            embedding=embedding,
            timestamp=datetime.utcnow(),
        )

        db.add(event)
        await db.commit()
        await db.refresh(event)

        return event

    async def retrieve_relevant_context(
        self,
        db: AsyncSession,
        persona_id: str,
        query: str,
        top_k: int = 5,
        time_decay: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context from persona's event history
        Uses vector similarity + temporal weighting
        """

        # Generate query embedding
        query_embedding = await self._generate_embedding(query)

        # Get all events for persona
        result = await db.execute(
            select(PersonaEvent)
            .where(PersonaEvent.persona_id == persona_id)
            .order_by(PersonaEvent.timestamp.desc())
        )
        events = result.scalars().all()

        if not events:
            return []

        # Calculate similarity scores
        scored_events = []
        current_time = datetime.utcnow()

        for event in events:
            if event.embedding is None:
                continue

            # Cosine similarity
            similarity = self._cosine_similarity(query_embedding, event.embedding)

            # Apply temporal decay if enabled
            if time_decay:
                time_diff = (current_time - event.timestamp).total_seconds()
                decay_factor = np.exp(-time_diff / (30 * 24 * 3600))  # 30-day half-life
                score = similarity * decay_factor
            else:
                score = similarity

            scored_events.append(
                {
                    "event": event,
                    "score": score,
                    "similarity": similarity,
                    "age_days": time_diff / (24 * 3600) if time_decay else 0,
                }
            )

        # Sort by score and return top-k
        scored_events.sort(key=lambda x: x["score"], reverse=True)
        top_events = scored_events[:top_k]

        return [
            {
                "event_id": str(e["event"].id),
                "event_type": e["event"].event_type,
                "event_data": e["event"].event_data,
                "timestamp": e["event"].timestamp.isoformat(),
                "relevance_score": float(e["score"]),
                "similarity": float(e["similarity"]),
                "age_days": float(e["age_days"]),
            }
            for e in top_events
        ]

    async def check_consistency(
        self,
        db: AsyncSession,
        persona_id: str,
        new_response: str,
        context: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Check if new response contradicts past events
        Returns consistency score and list of contradictions
        """

        if not context:
            return {"consistency_score": 1.0, "contradictions": [], "is_consistent": True}

        # Build context summary
        context_text = self._format_context(context)

        # Use LLM to detect contradictions
        prompt = f"""You are analyzing consistency in a persona's responses over time.

PAST CONTEXT:
{context_text}

NEW RESPONSE:
{new_response}

Analyze if the new response contradicts any information in the past context. Consider:
1. Factual contradictions (changed opinions, preferences, or stated facts)
2. Behavioral inconsistencies (out of character actions)
3. Value contradictions (violates stated values or principles)

Respond with JSON:
{{
    "contradictions": [
        {{"event_id": "...", "contradiction": "description", "severity": 0-1}}
    ],
    "consistency_score": 0-1,
    "is_consistent": true/false
}}

If no contradictions, return empty list and consistency_score=1.0"""

        if self.settings.DEFAULT_LLM_PROVIDER == "openai":
            result = await self._check_consistency_openai(prompt)
        else:
            result = await self._check_consistency_anthropic(prompt)

        return result

    async def _check_consistency_openai(self, prompt: str) -> Dict[str, Any]:
        """Use OpenAI to check consistency"""
        import json

        response = await self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a consistency checker for market research personas. Respond only with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        return json.loads(response.choices[0].message.content)

    async def _check_consistency_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Use Anthropic Claude to check consistency"""
        from anthropic import AsyncAnthropic
        import json

        client = AsyncAnthropic(api_key=self.settings.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0.3,
            messages=[{"role": "user", "content": f"{prompt}\n\nRespond only with valid JSON."}],
        )

        return json.loads(response.content[0].text)

    async def get_persona_history(
        self, db: AsyncSession, persona_id: str, limit: int = 50
    ) -> List[PersonaEvent]:
        """Get full event history for a persona"""
        result = await db.execute(
            select(PersonaEvent)
            .where(PersonaEvent.persona_id == persona_id)
            .order_by(PersonaEvent.sequence_number.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        # Use sentence-transformers for faster local embeddings
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def _event_to_text(self, event_type: str, event_data: Dict[str, Any]) -> str:
        """Convert event to text for embedding"""
        if event_type == "response_given":
            return f"Question: {event_data.get('question', '')}\nResponse: {event_data.get('response', '')}"
        elif event_type == "question_asked":
            return f"Question: {event_data.get('question', '')}"
        else:
            return str(event_data)

    def _format_context(self, context: List[Dict[str, Any]]) -> str:
        """Format context for LLM consumption"""
        formatted = []
        for i, ctx in enumerate(context, 1):
            event_type = ctx["event_type"]
            event_data = ctx["event_data"]
            timestamp = ctx["timestamp"]

            formatted.append(f"{i}. [{timestamp}] {event_type}:")
            if event_type == "response_given":
                formatted.append(f"   Q: {event_data.get('question', '')}")
                formatted.append(f"   A: {event_data.get('response', '')}")
            else:
                formatted.append(f"   {event_data}")

        return "\n".join(formatted)

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        a_arr = np.array(a)
        b_arr = np.array(b)
        return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))