"""
Serwis Grup Fokusowych oparty na LangChain

Zarządza symulacjami grup fokusowych przy użyciu Google Gemini.
Osoby (persony) odpowiadają na pytania równolegle z wykorzystaniem
kontekstu rozmowy przechowywanego w MemoryService.

Wydajność: <3s na odpowiedź persony, <30s całkowity czas wykonania
"""

import logging
import asyncio
import time
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import List, Dict, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import get_settings
from app.models import FocusGroup, Persona, PersonaResponse
from app.services.memory_service_langchain import MemoryServiceLangChain

settings = get_settings()


class FocusGroupServiceLangChain:
    """Zarządzanie symulacjami grup fokusowych."""

    def __init__(self) -> None:
        """Inicjalizuj serwis z klientami LLM i pamięci."""
        self.settings = settings
        self.memory_service = MemoryServiceLangChain()
        self.llm = ChatGoogleGenerativeAI(
            model=settings.DEFAULT_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.TEMPERATURE,
            max_tokens=2048,
        )

    async def run_focus_group(self, db: AsyncSession, focus_group_id: str) -> Dict[str, Any]:
        """
        Przeprowadź kompletną symulację grupy fokusowej z użyciem LangChain.

        Metoda pełni rolę głównego orkiestratora przebiegu badania. Odpowiada za:

        1. Pobranie z bazy danych rekordu `FocusGroup` wraz z listą pytań
           oraz aktualizację statusu na `running`.
        2. Załadowanie wszystkich powiązanych person przy użyciu
           `_load_focus_group_personas`, włącznie z obsługą fallbacków.
        3. Iteracyjne przetwarzanie pytań i równoległe generowanie odpowiedzi
           poprzez `_generate_responses_for_question`.
        4. Zapis każdego zestawu odpowiedzi do tabeli `persona_responses`
           za pomocą `_save_responses` i rejestrowanie zdarzeń w pamięci.
        5. Wyliczenie metryk czasowych przy udziale `_calculate_metrics`,
           aktualizację rekordu grupy oraz uruchomienie automatycznej budowy grafu.

        Args:
            db: Asynchroniczna sesja SQLAlchemy wykorzystywana do wszystkich operacji.
            focus_group_id: Identyfikator UUID grupy fokusowej przekazany w formie tekstowej.

        Returns:
            Struktura słownikowa zawierająca status wykonania, listę odpowiedzi
            pogrupowaną per pytanie oraz metryki czasowe (łączny czas wykonania,
            średni czas odpowiedzi i spełnienie wymagań wydajnościowych).
        """
        logger = logging.getLogger(__name__)
        logger.info("🚀 Rozpoczynam symulację grupy fokusowej %s", focus_group_id)

        execution_start = time.time()
        focus_group_uuid = UUID(str(focus_group_id))

        result = await db.execute(select(FocusGroup).where(FocusGroup.id == focus_group_uuid))
        focus_group = result.scalar_one()

        focus_group.status = "running"
        focus_group.started_at = datetime.now(timezone.utc)
        await db.commit()

        try:
            personas = await self._load_focus_group_personas(db, focus_group_uuid)
            logger.info("👥 Załadowano %s person", len(personas))

            focus_group_description = focus_group.description or ""
            responses_per_question: List[Dict[str, Any]] = []

            for index, question in enumerate(focus_group.questions or []):
                logger.info(
                    "❓ Przetwarzam pytanie %s/%s: %s",
                    index + 1,
                    len(focus_group.questions or []),
                    question,
                )
                question_start = time.time()

                persona_responses = await self._generate_responses_for_question(
                    db=db,
                    personas=personas,
                    question=question,
                    question_index=index,
                    focus_group_id=focus_group_uuid,
                    focus_group_description=focus_group_description,
                )

                await self._save_responses(db, focus_group_uuid, persona_responses)

                question_time_ms = (time.time() - question_start) * 1000
                responses_per_question.append(
                    {
                        "question": question,
                        "responses": persona_responses,
                        "time_ms": question_time_ms,
                    }
                )

            total_time_ms = (time.time() - execution_start) * 1000
            metrics = self._calculate_metrics(
                [entry["responses"] for entry in responses_per_question],
                total_time_ms,
            )

            focus_group.total_execution_time_ms = int(metrics["total_execution_time_ms"])
            focus_group.avg_response_time_ms = metrics["avg_response_time_ms"]
            focus_group.completed_at = datetime.now(timezone.utc)
            focus_group.status = "completed"
            await db.commit()

            # Aktualizujemy flagę na podstawie realnych danych obiektu
            metrics["meets_requirements"] = focus_group.meets_performance_requirements()

            logger.info(
                "✅ Zakończono symulację %s w %.2f ms",
                focus_group_id,
                total_time_ms,
            )

            try:
                from app.services.graph_service import GraphService

                graph_service = GraphService()
                graph_stats = await graph_service.build_graph_from_focus_group(db, str(focus_group_uuid))
                await graph_service.close()
                logger.info("🧠 Automatycznie zbudowano graf wiedzy: %s", graph_stats)
            except Exception as graph_error:  # pragma: no cover - operacja poboczna
                logger.error("⚠️ Błąd budowy grafu (niekrytyczny): %s", graph_error, exc_info=True)

            return {
                "focus_group_id": str(focus_group_uuid),
                "status": "completed",
                "responses": responses_per_question,
                "metrics": metrics,
            }

        except Exception as exc:  # pragma: no cover - logujemy i zwracamy status błędu
            logger.error(
                "❌ Symulacja %s zakończona błędem: %s",
                focus_group_id,
                exc,
                exc_info=True,
                extra={"focus_group_id": str(focus_group_uuid)},
            )

            focus_group.status = "failed"
            if hasattr(focus_group, "error_message"):
                focus_group.error_message = str(exc)[:500]
            await db.commit()

            return {
                "focus_group_id": str(focus_group_uuid),
                "status": "failed",
                "error": str(exc),
            }

    async def _load_focus_group_personas(self, db: AsyncSession, focus_group_id: UUID) -> List[Persona]:
        """
        Pobierz persony przypisane do wskazanej grupy fokusowej.

        Procedura obejmuje:

        * Odnalezienie rekordu `FocusGroup` w bazie danych przy użyciu `select`.
        * Rozwiązanie listy `persona_ids` i przekazanie jej do `_load_personas`.
        * Fallback do person powiązanych z projektem (jeśli brak jawnej listy).

        Raises:
            ValueError: Gdy nie znaleziono grupy fokusowej lub żadnej przypisanej persony.

        Returns:
            Lista modeli `Persona` gotowych do dalszego przetwarzania.
        """
        logger = logging.getLogger(__name__)

        result = await db.execute(select(FocusGroup).where(FocusGroup.id == focus_group_id))
        focus_group = result.scalar_one_or_none()
        if not isinstance(focus_group, FocusGroup):
            # Fallback: mogło nastąpić mockowanie w testach, więc próbujemy metodę get
            try:
                focus_group = await db.get(FocusGroup, focus_group_id)
            except AttributeError:  # pragma: no cover - brak metody get
                focus_group = None

        if focus_group is None:
            raise ValueError(f"Focus group {focus_group_id} not found")

        persona_ids = list(getattr(focus_group, "persona_ids", []) or [])
        personas: List[Persona] = []

        if persona_ids:
            personas = await self._load_personas(db, persona_ids)
        else:
            project_id = getattr(focus_group, "project_id", None)
            if project_id:
                fallback_result = await db.execute(
                    select(Persona).where(Persona.project_id == project_id)
                )
                personas = fallback_result.scalars().all()

        if not personas:
            raise ValueError("No personas found")

        logger.debug("Załadowano %s person do grupy %s", len(personas), focus_group_id)
        return personas

    async def _load_personas(self, db: AsyncSession, persona_ids: List[UUID]) -> List[Persona]:
        """Załaduj persony na podstawie listy identyfikatorów."""
        if not persona_ids:
            return []
        result = await db.execute(select(Persona).where(Persona.id.in_(persona_ids)))
        return result.scalars().all()

    def _format_persona_profile(self, persona: Persona) -> str:
        """
        Zbuduj zwięzły, lecz informacyjny profil persony do promptów LLM.

        Profil konsoliduje kluczowe dane demograficzne, skrócony opis
        cech osobowości według modelu Big Five, preferowane wartości oraz
        najważniejsze elementy historii życia. Dzięki temu każda odpowiedź
        generowana przez model językowy zachowuje spójność z charakterem
        persony.
        """
        name = getattr(persona, "full_name", None) or getattr(persona, "name", None) or "Uczestnik"
        age = getattr(persona, "age", None)
        gender = getattr(persona, "gender", None)
        location = getattr(persona, "location", None)
        occupation = getattr(persona, "occupation", None)
        education = getattr(persona, "education_level", None)

        big_five_parts = []
        for label, value in {
            "otwartość/openness": getattr(persona, "openness", None),
            "sumienność/conscientiousness": getattr(persona, "conscientiousness", None),
            "ekstrawersja/extraversion": getattr(persona, "extraversion", None),
            "ugodowość/agreeableness": getattr(persona, "agreeableness", None),
            "neurotyzm/neuroticism": getattr(persona, "neuroticism", None),
        }.items():
            if value is not None:
                big_five_parts.append(f"{label}: {value:.2f}")
        big_five = ", ".join(big_five_parts) if big_five_parts else "Brak danych Big Five"

        values = getattr(persona, "values", None) or []
        values_text = ", ".join(values) if values else "brak wskazanych wartości"

        background = getattr(persona, "background_story", None) or "Brak historii tła"

        parts = [
            f"Imię i nazwisko: {name}",
            f"Wiek: {age}" if age is not None else "Wiek: n/d",
            f"Płeć: {gender}" if gender else "Płeć: n/d",
            f"Lokalizacja: {location}" if location else "Lokalizacja: n/d",
            f"Zawód: {occupation}" if occupation else "Zawód: n/d",
            f"Wykształcenie: {education}" if education else "Wykształcenie: n/d",
            f"Big Five: {big_five}",
            f"Kluczowe wartości: {values_text}",
            f"Tło: {background}",
        ]
        return " | ".join(parts)

    def _create_persona_prompt(
        self,
        persona: Persona,
        question: str,
        context: List[Dict[str, Any]],
        focus_group_description: str,
    ) -> List[Any]:
        """
        Utwórz listę wiadomości (systemową i użytkownika) dla wywołania LLM.

        Kompozycja promptu obejmuje:

        * Szczegółowy opis spotkania oraz oczekiwaną konwencję wypowiedzi.
        * Sformatowany profil persony przygotowany przez `_format_persona_profile`.
        * Zsyntetyzowany kontekst z poprzednich odpowiedzi (pytanie ↔ odpowiedź).
        * Bieżące pytanie wraz z instrukcją dotyczącą długości i tonu odpowiedzi.

        Args:
            persona: Model ORM reprezentujący uczestnika badania.
            question: Tekst aktualnego pytania moderatora.
            context: Lista zdarzeń pamięci zawierająca wcześniejsze wypowiedzi.
            focus_group_description: Opis merytoryczny grupy fokusowej.

        Returns:
            Lista wiadomości kompatybilna z interfejsem LangChain ChatModel.
        """
        profile_text = self._format_persona_profile(persona)

        context_lines: List[str] = []
        for item in context or []:
            data = item.get("event_data", {}) if isinstance(item, dict) else {}
            asked = data.get("question")
            answered = data.get("response")
            if asked or answered:
                snippet = []
                if asked:
                    snippet.append(f"Pytanie: {asked}")
                if answered:
                    snippet.append(f"Odpowiedź: {answered}")
                context_lines.append(" | ".join(snippet))

        context_block = "\n".join(context_lines) if context_lines else "Brak wcześniejszego kontekstu."

        system_message = SystemMessage(
            content=(
                "Jesteś symulowaną personą biorącą udział w badaniu rynku. "
                "Zachowuj spójny charakter, odpowiadaj naturalnie i zwięźle. "
                f"Opis spotkania: {focus_group_description or 'Brak opisu.'}"
            )
        )

        human_message = HumanMessage(
            content=(
                "Profil uczestnika:\n"
                f"{profile_text}\n\n"
                "Kontekst rozmowy:\n"
                f"{context_block}\n\n"
                f"Aktualne pytanie: {question}\n"
                "Udziel odpowiedzi w 2-4 zdaniach, pamiętając o perspektywie persony."
            )
        )

        return [system_message, human_message]

    async def _generate_single_response(
        self,
        db: AsyncSession,
        persona: Persona,
        question: str,
        focus_group_id: UUID,
        focus_group_description: str,
        question_index: int,
    ) -> Dict[str, Any]:
        """
        Wygeneruj odpowiedź jednej persony wraz z obsługą kontekstu i logowaniem.

        Sekwencja działań:

        1. Pobiera relewantne fragmenty rozmowy z `MemoryServiceLangChain`.
        2. Buduje prompt składający się z wiadomości systemowej i użytkownika.
        3. Wywołuje model Gemini asynchronicznie (`ainvoke`) i mierzy czas odpowiedzi.
        4. Rejestruje zdarzenie w pamięci (lub loguje ostrzeżenie przy błędzie).
        5. Zapewnia odporność na wyjątki LLM, zwracając komunikat o błędzie.

        Returns:
            Słownik z identyfikatorem persony, treścią odpowiedzi, czasem reakcji,
            użytym kontekstem oraz flagą błędu.
        """
        logger = logging.getLogger(__name__)
        persona_name = getattr(persona, "full_name", None) or getattr(persona, "name", None) or "Uczestnik"
        start_time = time.time()

        context: List[Dict[str, Any]] = []
        try:
            if hasattr(self.memory_service, "get_relevant_context"):
                context = await self.memory_service.get_relevant_context(
                    db=db,
                    persona_id=str(persona.id),
                    query=question,
                    focus_group_id=str(focus_group_id),
                    limit=5,
                )
            else:
                context = await self.memory_service.retrieve_relevant_context(
                    db=db,
                    persona_id=str(persona.id),
                    query=question,
                    top_k=5,
                )
        except Exception as context_error:  # pragma: no cover - logowanie pomocnicze
            logger.warning(
                "⚠️ Nie udało się pobrać kontekstu dla persony %s: %s",
                persona.id,
                context_error,
                exc_info=True,
            )
            context = []

        prompt_messages = self._create_persona_prompt(
            persona=persona,
            question=question,
            context=context,
            focus_group_description=focus_group_description,
        )

        response_text = ""
        error_message = None
        try:
            llm_response = await self.llm.ainvoke(prompt_messages)
            content = getattr(llm_response, "content", "")
            if isinstance(content, list):
                content = " ".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
            response_text = content.strip() if isinstance(content, str) else ""
            if not response_text:
                response_text = ""
        except Exception as llm_error:
            logger.error(
                "❌ Błąd LLM dla persony %s: %s",
                persona.id,
                llm_error,
                exc_info=True,
            )
            error_message = str(llm_error)
            response_text = f"Error: {llm_error}" if llm_error else ""

        response_time_ms = (time.time() - start_time) * 1000

        event_payload = {
            "question": question,
            "question_index": question_index,
            "response": response_text,
            "response_time_ms": response_time_ms,
            "context_used": context,
            "error": error_message is not None,
        }

        try:
            if hasattr(self.memory_service, "record_event"):
                await self.memory_service.record_event(
                    db=db,
                    persona_id=str(persona.id),
                    event_type="response_given",
                    event_data=event_payload,
                    focus_group_id=str(focus_group_id),
                )
            else:
                await self.memory_service.create_event(
                    db=db,
                    persona_id=str(persona.id),
                    event_type="response_given",
                    event_data=event_payload,
                    focus_group_id=str(focus_group_id),
                )
        except Exception as event_error:  # pragma: no cover - log pomocniczy
            logger.warning(
                "⚠️ Nie udało się zapisać eventu dla persony %s: %s",
                persona.id,
                event_error,
                exc_info=True,
            )

        return {
            "persona_id": str(persona.id),
            "persona_name": persona_name,
            "question": question,
            "response": response_text,
            "response_time_ms": response_time_ms,
            "context_items": context,
            "error": error_message is not None,
        }

    async def _generate_responses_for_question(
        self,
        db: AsyncSession,
        personas: List[Persona],
        question: str,
        question_index: int,
        focus_group_id: UUID,
        focus_group_description: str,
    ) -> List[Dict[str, Any]]:
        """
        Wygeneruj odpowiedzi od wszystkich person równolegle.

        Metoda uruchamia `_generate_single_response` dla każdej persony i
        wykorzystuje `asyncio.gather` do współbieżnej obsługi wywołań. Dzięki
        parametrowi `return_exceptions=True` zapewnia miękkie przechwycenie
        błędów, mapując wyjątki na znormalizowane odpowiedzi błędowe.

        Returns:
            Lista słowników uporządkowana zgodnie z kolejnością person.
        """
        tasks = [
            self._generate_single_response(
                db=db,
                persona=persona,
                question=question,
                focus_group_id=focus_group_id,
                focus_group_description=focus_group_description,
                question_index=question_index,
            )
            for persona in personas
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results: List[Dict[str, Any]] = []
        for persona, result in zip(personas, results):
            if isinstance(result, Exception):
                final_results.append(
                    {
                        "persona_id": str(persona.id),
                        "persona_name": getattr(persona, "full_name", None)
                        or getattr(persona, "name", None)
                        or "Uczestnik",
                        "question": question,
                        "response": f"Error: {result}",
                        "response_time_ms": 0.0,
                        "context_items": [],
                        "error": True,
                    }
                )
            else:
                final_results.append(result)

        return final_results

    async def _save_responses(
        self,
        db: AsyncSession,
        focus_group_id: UUID,
        responses: List[Dict[str, Any]],
    ) -> None:
        """
        Zapisz wygenerowane odpowiedzi w tabeli `persona_responses`.

        Każda odpowiedź zostaje zmaterializowana jako rekord ORM. Metoda dba o
        transakcyjność: w razie błędu następuje `rollback`, co zapobiega
        powstaniu częściowych zapisów.
        """
        try:
            for response in responses:
                persona_id = response.get("persona_id")
                question = response.get("question")
                text = response.get("response", "")

                if not persona_id or not question:
                    continue

                persona_uuid = UUID(str(persona_id))
                focus_group_uuid = UUID(str(focus_group_id))

                db.add(
                    PersonaResponse(
                        persona_id=persona_uuid,
                        focus_group_id=focus_group_uuid,
                        question=question,
                        response=text,
                    )
                )

            await db.commit()
        except Exception:
            await db.rollback()
            raise

    def _calculate_metrics(
        self,
        all_responses: List[List[Dict[str, Any]]],
        total_time_ms: float,
    ) -> Dict[str, Any]:
        """
        Oblicz metryki czasowe na podstawie wszystkich odpowiedzi.

        Wykorzystuje zebrane czasy reakcji do obliczenia średniej oraz
        deleguje walidację spełnienia wymagań do metody
        `FocusGroup.meets_performance_requirements`.

        Args:
            all_responses: Lista list odpowiedzi (zgrupowanych per pytanie).
            total_time_ms: Całkowity czas wykonania symulacji w milisekundach.

        Returns:
            Słownik z łącznym czasem, średnim czasem odpowiedzi i flagą
            `meets_requirements`.
        """
        response_times = [
            response.get("response_time_ms")
            for responses in all_responses
            for response in responses
            if response.get("response_time_ms") is not None
        ]

        avg_response_time = (
            sum(response_times) / len(response_times)
            if response_times
            else 0.0
        )

        focus_group_stub = SimpleNamespace(
            total_execution_time_ms=int(total_time_ms),
            avg_response_time_ms=avg_response_time,
        )
        meets_requirements = FocusGroup.meets_performance_requirements(focus_group_stub)

        return {
            "total_execution_time_ms": float(total_time_ms),
            "avg_response_time_ms": avg_response_time,
            "meets_requirements": meets_requirements,
        }
