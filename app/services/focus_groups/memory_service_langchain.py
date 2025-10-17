"""
Serwis Pamięci oparty na LangChain z Event Sourcingiem

Zarządza historią zdarzeń person i umożliwia wyszukiwanie kontekstu
dla kolejnych odpowiedzi w grupach fokusowych przy użyciu embeddingów.
"""

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import numpy as np

from app.models import PersonaEvent, PersonaResponse, Persona
from app.core.config import get_settings
from app.services.core.clients import get_embeddings

settings = get_settings()
logger = logging.getLogger(__name__)


class MemoryServiceLangChain:
    """
    Event sourcing i wyszukiwanie kontekstu

    Utrzymuje spójność czasową poprzez niemodyfikowalny log zdarzeń.
    Używa embeddingów Google Gemini do wyszukiwania semantycznego.
    """

    def __init__(self):
        """Inicjalizuj serwis pamięci z embeddings"""
        self.settings = settings

        # Inicjalizujemy embeddingi LangChain Gemini
        self.embeddings = get_embeddings()

    async def create_event(
        self,
        db: AsyncSession,
        persona_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        focus_group_id: Optional[str] = None,
    ) -> PersonaEvent:
        """
        Utwórz niemodyfikowalny event w event store (event sourcing)

        Event sourcing to wzorzec gdzie każda zmiana stanu jest zapisywana jako
        niemodyfikowalny event. To pozwala na odtworzenie pełnej historii i kontekstu.

        Proces:
        1. Pobiera ostatni numer sekwencyjny dla tej persony
        2. Konwertuje dane eventu na tekst i generuje embedding (Google Gemini)
        3. Zapisuje event w bazie z embeddingiem (do późniejszego semantic search)

        Args:
            db: Sesja bazy danych
            persona_id: UUID persony
            event_type: Typ eventu (np. "response_given", "question_asked")
            event_data: Dane eventu (słownik, np. {"question": "...", "response": "..."})
            focus_group_id: Opcjonalnie UUID grupy fokusowej

        Returns:
            Utworzony obiekt PersonaEvent
        """

        # Pobierz numer sekwencyjny (każda persona ma swoją sekwencję 1, 2, 3...)
        result = await db.execute(
            select(PersonaEvent)
            .where(PersonaEvent.persona_id == persona_id)
            .order_by(PersonaEvent.sequence_number.desc())
            .limit(1)
        )
        last_event = result.scalar_one_or_none()
        sequence_number = (last_event.sequence_number + 1) if last_event else 1

        # Wygeneruj embedding używając Google Gemini (na potrzeby późniejszego wyszukiwania semantycznego)
        event_text = self._event_to_text(event_type, event_data)
        embedding = await self._generate_embedding(event_text)

        # Utwórz event (niemodyfikowalny – log tylko do dopisywania)
        event = PersonaEvent(
            persona_id=persona_id,
            focus_group_id=focus_group_id,
            event_type=event_type,
            event_data=event_data,
            sequence_number=sequence_number,
            embedding=embedding,
            timestamp=datetime.now(timezone.utc),
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
        Pobierz relevantny kontekst z historii eventów persony (semantic search)

        Używa embeddingów (wektorów semantycznych) do znalezienia najbardziej
        relevantnych poprzednich interakcji persony dla danego zapytania.

        Algorytm:
        1. Generuje embedding dla query (pytania)
        2. Dla każdego eventu w historii, oblicza cosine similarity
        3. Opcjonalnie stosuje temporal decay (starsze eventy mają niższy score)
        4. Zwraca top-k najrelevantniejszych eventów

        Args:
            db: Sesja bazy danych
            persona_id: UUID persony
            query: Tekst zapytania (np. aktualne pytanie do persony)
            top_k: Ile eventów zwrócić (domyślnie 5)
            time_decay: Czy stosować temporal decay (starsze = niższy score)

        Returns:
            Lista słowników z eventami posortowana po relevance_score:
            [
                {
                    "event_id": str,
                    "event_type": str,
                    "event_data": dict,
                    "timestamp": str,
                    "relevance_score": float,  # podobieństwo * współczynnik zaniku
                    "similarity": float,       # czysty cosinusowy wynik podobieństwa
                    "age_days": float          # wiek eventu w dniach
                },
                ...
            ]
        """

        # Wygeneruj embedding dla zapytania
        query_embedding = await self._generate_embedding(query)

        # Pobierz wszystkie eventy persony
        result = await db.execute(
            select(PersonaEvent)
            .where(PersonaEvent.persona_id == persona_id)
            .order_by(PersonaEvent.timestamp.desc())
        )
        events = result.scalars().all()

        if not events:
            return []

        # Oblicz wynik dopasowania dla każdego eventu
        scored_events = []
        current_time = datetime.now(timezone.utc)

        for event in events:
            if event.embedding is None:
                continue

            # Cosine similarity (miara podobieństwa semantycznego)
            similarity = self._cosine_similarity(query_embedding, event.embedding)

            # Zastosuj temporal decay jeśli włączony
            time_diff = 0.0
            if time_decay:
                time_diff = (current_time - event.timestamp).total_seconds()
                # Współczynnik zaniku: exp(-t/30 dni) – po 30 dniach wynik maleje do ~37%
                decay_factor = np.exp(-time_diff / (30 * 24 * 3600))
                score = similarity * decay_factor
            else:
                score = similarity

            scored_events.append(
                {
                    "event": event,
                    "score": score,
                    "similarity": similarity,
                    "age_days": time_diff / (24 * 3600) if time_decay else 0.0,
                }
            )

        # Posortuj po wyniku i wybierz top-k
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


    async def get_persona_history(
        self, db: AsyncSession, persona_id: str, limit: int = 50
    ) -> List[PersonaEvent]:
        """
        Pobierz pełną historię eventów persony

        Args:
            db: Sesja bazy danych
            persona_id: UUID persony
            limit: Maksymalna liczba eventów do pobrania

        Returns:
            Lista obiektów PersonaEvent posortowana po sequence_number (malejąco)
        """
        result = await db.execute(
            select(PersonaEvent)
            .where(PersonaEvent.persona_id == persona_id)
            .order_by(PersonaEvent.sequence_number.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Wygeneruj wektor embeddingu używając Google Gemini

        Args:
            text: Tekst do zaembeddowania

        Returns:
            Lista floatów reprezentująca wektor embedding (768 wymiarów dla Gemini)
        """
        embedding = await self.embeddings.aembed_query(text)
        return embedding

    def _event_to_text(self, event_type: str, event_data: Dict[str, Any]) -> str:
        """
        Konwertuj event na tekst do embeddingu

        Różne typy eventów mają różne formatowanie tekstowe:
        - response_given: "Question: ... Response: ..."
        - question_asked: "Question: ..."
        - inne: str(event_data)

        Args:
            event_type: Typ eventu
            event_data: Dane eventu (słownik)

        Returns:
            Sformatowany tekst reprezentujący event
        """
        if event_type == "response_given":
            return f"Question: {event_data.get('question', '')}\nResponse: {event_data.get('response', '')}"
        elif event_type == "question_asked":
            return f"Question: {event_data.get('question', '')}"
        else:
            return str(event_data)

    def _format_context(self, context: List[Dict[str, Any]]) -> str:
        """
        Sformatuj kontekst do konsumpcji przez LLM

        Tworzy czytelny tekst z listy eventów do wstawienia w prompt.

        Args:
            context: Lista eventów (słowniki z retrieve_relevant_context)

        Returns:
            Sformatowany tekst kontekstu
        """
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
        """
        Oblicz cosine similarity między dwoma wektorami

        Cosine similarity to miara podobieństwa wektorów w przestrzeni n-wymiarowej.
        Wartość 1.0 = identyczne, 0.0 = ortogonalne, -1.0 = przeciwne.

        Args:
            a: Pierwszy wektor (lista floatów)
            b: Drugi wektor (lista floatów)

        Returns:
            Cosine similarity w przedziale [-1, 1]
        """
        a_arr = np.array(a)
        b_arr = np.array(b)
        return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))
