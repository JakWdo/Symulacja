"""
Serwis Grup Fokusowych oparty na LangChain

Zarządza symulacjami grup fokusowych przy użyciu Google Gemini.
Osoby (persony) odpowiadają na pytania równolegle z wykorzystaniem
kontekstu rozmowy przechowywanego w MemoryService.

Wydajność: <3s na odpowiedź persony, <30s całkowity czas wykonania
"""

import logging
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import asyncio
import time
from datetime import datetime, timezone
from uuid import UUID


from app.models import FocusGroup, Persona, PersonaResponse
from app.services.focus_groups.memory_service_langchain import MemoryServiceLangChain
from app.db import AsyncSessionLocal
from app.services.shared.clients import build_chat_model
from app.services.dashboard.usage_logging import (
    UsageLogContext,
    context_with_model,
    schedule_usage_logging,
)



class FocusGroupServiceLangChain:
    """
    Zarządzanie symulacjami grup fokusowych

    Orkiestruje dyskusje między personami, zarządza kontekstem rozmowy
    i przetwarza odpowiedzi równolegle dla maksymalnej wydajności.
    """

    def __init__(self):
        """Inicjalizuj serwis z LangChain LLM i serwisem pamięci"""
        from config import models

        # Note: self.settings removed - not used anywhere in this class
        self.memory_service = MemoryServiceLangChain()

        # Model config z centralnego registry
        model_config = models.get("focus_groups", "discussion")
        self.llm = build_chat_model(**model_config.params)

    async def run_focus_group(
        self, db: AsyncSession, focus_group_id: str
    ) -> dict[str, Any]:
        """
        Wykonaj symulację grupy fokusowej przy użyciu LangChain

        Główna metoda orkiestrująca przebieg grupy fokusowej:
        1. Ładuje grupę fokusową i persony z bazy danych
        2. Dla każdego pytania, równolegle zbiera odpowiedzi od wszystkich person
        3. Zapisuje odpowiedzi do bazy i tworzy eventy w systemie pamięci
        4. Oblicza metryki wydajności (czas wykonania, średni czas odpowiedzi)
        5. Aktualizuje status grupy fokusowej

        Args:
            db: Sesja asynchroniczna do bazy danych
            focus_group_id: UUID grupy fokusowej do wykonania

        Returns:
            Słownik z wynikami:
            {
                "focus_group_id": str,
                "status": "completed" | "failed",
                "responses": List[Dict],  # odpowiedzi na każde pytanie
                "metrics": {
                    "total_execution_time_ms": float,
                    "avg_response_time_ms": float,
                    "meets_requirements": bool
                }
            }
        """
        logger = logging.getLogger(__name__)

        logger.info(f"🚀 Starting focus group {focus_group_id}")
        start_time = time.time()

        # Pobieramy grupę fokusową z bazy danych
        result = await db.execute(
            select(FocusGroup)
            .options(selectinload(FocusGroup.project))
            .where(FocusGroup.id == focus_group_id)
        )
        focus_group = result.scalar_one()
        logger.info(f"📋 Focus group loaded: {focus_group.name}, questions: {len(focus_group.questions)}")
        project_owner_id = focus_group.project.owner_id if focus_group.project else None
        project_id = focus_group.project_id

        # Aktualizujemy status grupy
        focus_group.status = "running"
        focus_group.started_at = datetime.now(timezone.utc)
        await db.commit()

        try:
            # Pobieramy persony
            personas = await self._load_personas(db, focus_group.persona_ids)
            logger.info(f"👥 Loaded {len(personas)} personas")

            # Przetwarzamy każde pytanie z listy
            all_responses = []
            response_times = []

            print(f"🔄 FOCUS GROUP: {len(focus_group.questions)} questions to process")
            for question in focus_group.questions:
                question_start = time.time()

                print(f"❓ PROCESSING QUESTION: {question} for {len(personas)} personas")
                logger.info(f"Processing question: {question} for {len(personas)} personas")

                # Równolegle pobieramy odpowiedzi od wszystkich person
                responses = await self._get_concurrent_responses(
                    personas,
                    question,
                    focus_group_id,
                    owner_id=project_owner_id,
                    project_id=project_id,
                )

                print(f"✅ GOT {len(responses)} RESPONSES for question")
                logger.info(f"Got {len(responses)} responses for question: {question}")

                question_time = (time.time() - question_start) * 1000
                response_times.append(question_time)

                all_responses.append(
                    {"question": question, "responses": responses, "time_ms": question_time}
                )

            # Wyliczamy metryki wykonywania
            total_time = (time.time() - start_time) * 1000
            avg_response_time = sum(response_times) / len(response_times)

            # Aktualizujemy rekord grupy fokusowej
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
            logger = logging.getLogger(__name__)
            logger.error(
                f"Focus group {focus_group_id} failed: {str(e)}",
                exc_info=True,
                extra={"focus_group_id": str(focus_group_id)}
            )

            focus_group.status = "failed"
            # Zapisujemy pierwsze 500 znaków błędu do debugowania
            if hasattr(focus_group, 'error_message'):
                focus_group.error_message = str(e)[:500]
            await db.commit()

            # Nie propagujemy wyjątku dalej – zadanie działa w tle, wystarczy log
            return {
                "focus_group_id": str(focus_group_id),
                "status": "failed",
                "error": str(e)
            }

    async def _load_personas(
        self, db: AsyncSession, persona_ids: list[UUID]
    ) -> list[Persona]:
        """
        Załaduj obiekty person z bazy danych

        Args:
            db: Sesja bazy danych
            persona_ids: Lista UUID person do załadowania

        Returns:
            Lista obiektów Persona
        """
        result = await db.execute(
            select(Persona)
            .options(selectinload(Persona.project))  # Prevent N+1 queries
            .where(Persona.id.in_(persona_ids))
        )
        return result.scalars().all()

    async def _get_concurrent_responses(
        self,
        personas: list[Persona],
        question: str,
        focus_group_id: str,
        owner_id: UUID | None,
        project_id: UUID,
    ) -> list[dict[str, Any]]:
        """
        Pobierz odpowiedzi od wszystkich person równolegle (concurrent execution)

        Tworzy zadania asynchroniczne dla każdej persony i wykonuje je równocześnie
        używając asyncio.gather(). To pozwala na szybkie zbieranie odpowiedzi
        (wszystkie persony odpowiadają "jednocześnie" zamiast po kolei).

        Args:
            personas: Lista obiektów Persona do odpytania
            question: Pytanie do zadania
            focus_group_id: ID grupy fokusowej (do tworzenia eventów)

        Returns:
            Lista słowników z odpowiedziami:
            [
                {"persona_id": str, "response": str, "context_used": int},
                ...
            ]
            Jeśli persona zwróciła błąd, zwraca {"persona_id": str, "response": "Error: ...", "error": True}
        """

        # Utwórz zadania asynchroniczne dla każdej persony
        tasks = [
            self._get_persona_response(
                persona,
                question,
                focus_group_id,
                owner_id,
                project_id,
            )
            for persona in personas
        ]

        # Wykonaj wszystkie zadania równolegle (gather zbiera wyniki)
        print(f"🚀 Starting {len(tasks)} concurrent persona response tasks...")
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Obsłuż wyjątki (gather może zwrócić Exception zamiast wyniku)
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
        persona: Persona,
        question: str,
        focus_group_id: str,
        owner_id: UUID | None,
        project_id: UUID,
    ) -> dict[str, Any]:
        """
        Pobierz odpowiedź od pojedynczej persony

        Przepływ:
        1. Pobiera relevantny kontekst z systemu pamięci (poprzednie odpowiedzi)
        2. Generuje odpowiedź używając LLM (Gemini) z kontekstem
        3. Tworzy event w systemie pamięci (event sourcing)
        4. Zapisuje odpowiedź do tabeli persona_responses

        Args:
            persona: Obiekt persony odpowiadającej
            question: Pytanie do odpowiedzi
            focus_group_id: ID grupy fokusowej

        Returns:
            Słownik z odpowiedzią:
            {
                "persona_id": str,
                "response": str,  # tekst odpowiedzi
                "context_used": int  # ile eventów użyto jako kontekst
            }
        """
        # Pobieramy istotny kontekst z pamięci (poprzednie interakcje)
        focus_group_uuid = focus_group_id if isinstance(focus_group_id, UUID) else UUID(str(focus_group_id))

        async with AsyncSessionLocal() as session:
            context = await self.memory_service.retrieve_relevant_context(
                session, str(persona.id), question, top_k=5
            )

            # Wygeneruj odpowiedź używając LangChain + Gemini (mierz czas)
            start_time = time.time()
            usage_context = UsageLogContext(
                user_id=owner_id,
                project_id=project_id,
                operation_type="focus_group_response",
                operation_id=focus_group_uuid,
                metadata={
                    "persona_id": str(persona.id),
                    "question": question[:120],
                },
            )

            response_text = await self._generate_response(
                persona,
                question,
                context,
                usage_context,
            )
            response_time = time.time() - start_time

            print(f"💬 Generated response (length={len(response_text) if response_text else 0}): {response_text[:50] if response_text else 'EMPTY'}...")

            # Utwórz event dla tej interakcji (event sourcing - niemodyfikowalny log)
            await self.memory_service.create_event(
                session,
                persona_id=str(persona.id),
                event_type="response_given",
                event_data={"question": question, "response": response_text},
                focus_group_id=str(focus_group_uuid),
            )

            # Zapisz odpowiedź w bazie danych
            persona_response = PersonaResponse(
                persona_id=persona.id,
                focus_group_id=focus_group_uuid,
                question_text=question,
                response_text=response_text,
                response_time_ms=int(response_time * 1000),  # Konwersja sekund na milisekundy
            )

            print("💾 Adding PersonaResponse to db...")
            session.add(persona_response)
            try:
                await session.commit()
                print("✅ Committed PersonaResponse to db")
            except Exception:
                await session.rollback()
                raise

        return {
            "persona_id": str(persona.id),
            "response": response_text,
            "context_used": len(context),
        }

    async def _generate_response(
        self,
        persona: Persona,
        question: str,
        context: list[dict[str, Any]],
        usage_context: UsageLogContext,
    ) -> str:
        """
        Wygeneruj odpowiedź persony używając LangChain

        Tworzy prompt z danymi persony i kontekstem, wysyła do Gemini
        i zwraca odpowiedź tekstową.

        Args:
            persona: Obiekt persony z pełnymi danymi (demografia, osobowość, background)
            question: Pytanie do odpowiedzi
            context: Lista poprzednich interakcji (z retrieve_relevant_context)

        Returns:
            Tekst odpowiedzi wygenerowany przez LLM
        """
        # Utwórz prompt z danych persony i kontekstu
        prompt_text = self._create_response_prompt(persona, question, context)

        logger = logging.getLogger(__name__)
        logger.info(f"Generating response for persona {persona.id}")
        logger.info(f"Persona data - name: {persona.full_name}, age: {persona.age}, occupation: {persona.occupation}")
        logger.info(f"Full prompt:\n{prompt_text}")

        response_text = await self._invoke_llm(prompt_text, usage_context)

        if response_text:
            return response_text

        logger.warning(f"Empty response from LLM for persona {persona.id}, retrying with stricter prompt")
        retry_prompt = f"""{prompt_text}

IMPORTANT INSTRUCTION:
- Provide a natural, conversational answer of at least one full sentence.
- Do not return an empty string or placeholders.
- Stay in character as the persona described above.
"""
        response_text = await self._invoke_llm(retry_prompt, usage_context)

        if response_text:
            return response_text

        fallback = self._fallback_response(persona, question)
        logger.warning(f"Using fallback response for persona {persona.id}")
        return fallback

    async def _invoke_llm(
        self,
        prompt_text: str,
        usage_context: UsageLogContext | None = None,
    ) -> str:
        """Wywołaj model LLM i zwróć oczyszczony tekst odpowiedzi."""
        logger = logging.getLogger(__name__)
        try:
            result = await self.llm.ainvoke(prompt_text)
        except Exception as err:
            logger.error(f"LLM invocation failed: {err}")
            return ""

        if usage_context:
            usage_meta = None
            if hasattr(result, "response_metadata"):
                meta = result.response_metadata or {}
                if isinstance(meta, dict):
                    usage_meta = meta.get("usage_metadata") or meta.get("token_usage") or meta
            if usage_meta is None and hasattr(result, "additional_kwargs"):
                extras = result.additional_kwargs or {}
                if isinstance(extras, dict):
                    usage_meta = extras.get("usage_metadata") or extras.get("token_usage")

            context_with_model_name = context_with_model(
                usage_context,
                getattr(self.llm, "model", None),
            )

            schedule_usage_logging(context_with_model_name, usage_meta)

        content = getattr(result, "content", "")
        if isinstance(content, list):
            # Scal tekstowe fragmenty, jeśli LangChain zwraca je w częściach
            content = " ".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)

        text = content.strip() if isinstance(content, str) else ""
        if not text:
            logger.debug(f"LLM returned empty content object: {result}")
        return text

    def _fallback_response(self, persona: Persona, question: str) -> str:
        """Zwróć przygotowaną odpowiedź zapasową, gdy LLM nic nie wygeneruje."""
        name = (persona.full_name or "Ta persona").split(" ")[0]
        occupation = persona.occupation or "uczestnik badania"
        return (
            f"{name}, pracując jako {occupation}, potrzebuje chwili, by uporządkować myśli wokół pytania "
            f"\"{question}\". Zaznacza jednak, że chętnie wróci do tematu, bo uważa go za ważny dla całej dyskusji."
        )

    def _create_response_prompt(
        self, persona: Persona, question: str, context: list[dict[str, Any]]
    ) -> str:
        """
        Utwórz prompt dla generowania odpowiedzi persony

        Buduje szczegółowy prompt zawierający:
        - Dane demograficzne persony (wiek, płeć, zawód, etc.)
        - Cechy osobowości (wartości, zainteresowania)
        - Fragment historii życiowej
        - Kontekst poprzednich interakcji (jeśli istnieją)
        - Aktualne pytanie

        Args:
            persona: Obiekt persony
            question: Pytanie do odpowiedzi
            context: Lista istotnych poprzednich interakcji (z event sourcing)

        Returns:
            Pełny prompt gotowy do wysłania do LLM
        """

        # Formatuj kontekst poprzednich odpowiedzi (maksymalnie 3 najbardziej istotne)
        context_text = ""
        if context:
            context_text = "\n\nPast interactions:\n"
            for i, ctx in enumerate(context[:3], 1):  # Ograniczamy do 3 najważniejszych wpisów
                if ctx["event_type"] == "response_given":
                    context_text += f"{i}. Q: {ctx['event_data'].get('question', '')}\n"
                    context_text += f"   A: {ctx['event_data'].get('response', '')}\n"

        # Używamy pełnej historii tła persony
        background = persona.background_story if persona.background_story else 'Has diverse life experiences'

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
