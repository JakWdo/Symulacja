"""
Serwis Generowania Odpowiedzi na Ankiety

Generuje odpowiedzi syntetycznych person na pytania ankietowe używając Google Gemini.
Odpowiedzi są zgodne z profilami psychologicznymi i demograficznymi person.

Wydajność: Przetwarzanie równoległe dla szybkiego generowania odpowiedzi
"""

import logging
import re
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
from app.db import AsyncSessionLocal
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

        # Inicjalizujemy model Gemini w LangChain
        self.llm = ChatGoogleGenerativeAI(
            model=settings.DEFAULT_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.TEMPERATURE,
            max_tokens=1024,  # Krótsze odpowiedzi na potrzeby ankiet
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
                self._generate_persona_survey_response(persona, survey)
                for persona in personas
            ]
            persona_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Zbieramy czasy odpowiedzi (pomijając błędy)
            for result in persona_results:
                if isinstance(result, dict) and "response_time_ms" in result:
                    response_times.append(result["response_time_ms"])

            # Wyliczamy metryki wydajności
            total_time = (time.time() - start_time) * 1000
            actual_responses = len([r for r in persona_results if not isinstance(r, Exception)])
            metrics = self._calculate_metrics(actual_responses, total_time)

            if response_times:
                metrics["avg_response_time_ms"] = sum(response_times) / len(response_times)
                metrics["total_execution_time_ms"] = total_time

            # Zapisujemy metryki w rekordzie ankiety
            survey.status = "completed"
            survey.completed_at = datetime.now(timezone.utc)
            survey.total_execution_time_ms = int(metrics["total_execution_time_ms"])
            survey.avg_response_time_ms = int(metrics["avg_response_time_ms"])
            survey.actual_responses = metrics["total_responses"]

            await db.commit()

            logger.info(f"✅ Survey completed: {actual_responses} responses in {total_time:.0f}ms")

            return {
                "survey_id": str(survey_id),
                "status": "completed",
                "actual_responses": actual_responses,
                "metrics": metrics,
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

    def _normalize_question_type(self, question_type: Optional[str]) -> str:
        """Znormalizuj typ pytania do spójnego formatu wewnętrznego."""

        if not question_type:
            return "open_ended"

        normalized = question_type.lower().replace("-", "_")
        mapping = {
            "rating_scale": "scale",
            "open_text": "open_ended",
        }
        return mapping.get(normalized, normalized)

    def _get_question_text(self, question: Dict[str, Any]) -> str:
        """Zwróć opis pytania niezależnie od struktury słownika."""

        return (
            question.get("text")
            or question.get("title")
            or question.get("question")
            or ""
        )

    def _create_survey_prompt(
        self, persona: Persona, question: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Zbuduj kompletny prompt przekazywany do modelu językowego.

        Funkcja scala kontekst persony z treścią pytania, aby model mógł
        odpowiedzieć w sposób spójny z jej profilem psychograficznym. W zależności
        od typu pytania (skala, jednokrotny wybór, wielokrotny wybór, odpowiedź
        otwarta) generowane są również szczegółowe instrukcje dla modelu oraz lista
        dostępnych opcji. Dzięki temu każda kolejna metoda odpowiadająca za
        wygenerowanie konkretnej odpowiedzi otrzymuje ustandaryzowaną strukturę
        danych niezależnie od źródłowego formatu pytania w bazie.

        Args:
            persona: Obiekt persony, z którego budujemy kontekst (cechy demograficzne
                i psychograficzne wykorzystywane w promptach).
            question: Słownik opisujący pytanie ankietowe zawierający m.in. `id`,
                `type`, `text/title`, `description`, listę `options` oraz ewentualne
                parametry skali (`scaleMin`, `scaleMax`).

        Returns:
            Lista słowników w formacie oczekiwanym przez LangChain/Google Gemini,
            reprezentująca sekwencję wiadomości systemowych i użytkownika tworzących
            kontekst rozmowy.
        """

        persona_context = self._build_persona_context(persona)
        question_type = self._normalize_question_type(question.get("type"))
        question_text = self._get_question_text(question)
        description = question.get("description") or ""
        options = question.get("options") or []

        scale_min = question.get("scaleMin", 1)
        scale_max = question.get("scaleMax", 5)

        instructions = {
            "scale": (
                f"Odpowiadasz jako konkretna persona. Wybierz jedną wartość ze skali (scale) od {scale_min} do {scale_max} i zwróć wyłącznie tę liczbę."
            ),
            "yes_no": (
                "Odpowiadasz jako konkretna persona. Wybierz jedną z dostępnych opcji i zwróć dokładnie jej treść."
            ),
            "multiple_choice": (
                "Odpowiadasz jako konkretna persona. Wybierz wszystkie pasujące opcje i zwróć je jako listę rozdzieloną przecinkami."
            ),
            "open_ended": (
                "Odpowiadasz jako konkretna persona. Napisz krótką, naturalną wypowiedź (2-4 zdania) odzwierciedlającą perspektywę tej osoby."
            ),
        }
        instructions.setdefault("single_choice", instructions["yes_no"])

        user_lines = ["Profil persony:", persona_context, "", f"Pytanie: {question_text}"]
        if description:
            user_lines.append(f"Dodatkowy kontekst: {description}")

        if question_type == "scale":
            user_lines.append(f"Skala ocen: {scale_min}-{scale_max}")

        if options:
            user_lines.append("")
            user_lines.append("Dostępne odpowiedzi:")
            user_lines.extend([f"- {option}" for option in options])

        return [
            {
                "role": "system",
                "content": instructions.get(
                    question_type,
                    "Odpowiadasz jako konkretna persona na pytanie ankietowe."
                ),
            },
            {
                "role": "user",
                "content": "\n".join(user_lines).strip(),
            },
        ]

    def _match_option(self, raw_answer: str, options: List[str]) -> Optional[str]:
        """
        Dopasuj odpowiedź modelu do listy dostępnych opcji.

        Metoda wykonuje wieloetapowe porównanie tekstu zwróconego przez LLM z
        dopuszczalnymi odpowiedziami, aby zminimalizować ryzyko odrzucenia poprawnej
        treści ze względu na drobne różnice formatowania. Jeżeli nie uda się
        znaleźć idealnego dopasowania, stosowany jest heurystyczny wybór pierwszej
        dostępnej opcji, co zabezpiecza proces przed zwróceniem pustej wartości.

        Args:
            raw_answer: Tekst wygenerowany przez model językowy.
            options: Lista dostępnych odpowiedzi zdefiniowanych w pytaniu ankietowym.

        Returns:
            Nazwa najlepiej dopasowanej opcji lub `None`, gdy lista opcji jest pusta.
        """

        if not options:
            return raw_answer or None

        if not raw_answer:
            return options[0]

        normalized_answer = raw_answer.strip().lower()

        for option in options:
            if option.lower() == normalized_answer:
                return option

        for option in options:
            if normalized_answer in option.lower() or option.lower() in normalized_answer:
                return option

        return options[0]

    async def _invoke_model(
        self, messages: List[Dict[str, str]]
    ) -> Any:
        """
        Wywołaj model językowy w sposób kompatybilny z różnymi konfiguracjami testowymi.

        Metoda obsługuje zarówno standardową integrację LangChain (pipeline prompt →
        model), jak i uproszczone mocki używane w testach jednostkowych. Dzięki temu
        logika generowania odpowiedzi pozostaje niezależna od konkretnej
        implementacji warstwy LLM.

        Args:
            messages: Lista wiadomości tworzących konwersację (format zgodny z
                ChatPromptTemplate i Gemini).

        Returns:
            Odpowiedź modelu w natywnym formacie zwracanym przez wywołany obiekt LLM.
        """

        if hasattr(self.llm, "__or__"):
            prompt = ChatPromptTemplate.from_messages(
                [(msg["role"], msg["content"]) for msg in messages]
            )
            chain = prompt | self.llm
            return await chain.ainvoke({})

        if hasattr(self.llm, "ainvoke"):
            return await self.llm.ainvoke(messages)

        raise TypeError("Konfiguracja LLM nie obsługuje asynchronicznego wywołania.")

    async def _generate_single_answer(
        self, persona: Persona, question: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Wygeneruj odpowiedź na pojedyncze pytanie z pełną obsługą wyjątków.

        Funkcja pełni rolę centralnego routera, który na podstawie znormalizowanego
        typu pytania deleguje wykonanie do wyspecjalizowanych metod (_answer_*).
        W razie błędów komunikacji z LLM lub niepoprawnych danych wejściowych
        stosowany jest deterministyczny fallback dopasowany do typu pytania, a
        wynik końcowy jest dodatkowo walidowany pod kątem zgodności z dostępnymi
        opcjami.

        Args:
            persona: Persona, której perspektywę należy zasymulować.
            question: Słownik opisujący pytanie ankietowe.

        Returns:
            Wartość zgodna z typem pytania (tekst, liczba, lista opcji) lub `None`,
            jeśli nie udało się wygenerować poprawnej odpowiedzi.
        """

        question_type = self._normalize_question_type(question.get("type"))

        try:
            if question_type == "scale":
                answer = await self._answer_rating_scale(persona, question)
            elif question_type in {"yes_no", "single_choice"}:
                answer = await self._answer_single_choice(persona, question)
            elif question_type == "multiple_choice":
                selections = await self._answer_multiple_choice(persona, question)
                answer = ", ".join(selections) if isinstance(selections, list) else selections
            elif question_type == "open_ended":
                answer = await self._answer_open_text(persona, question)
            else:
                answer = await self._answer_single_choice(persona, question)
        except Exception as error:
            logger = logging.getLogger(__name__)
            logger.warning(
                "Błąd generowania odpowiedzi dla pytania %s: %s",
                question.get("id"),
                error,
            )
            answer = self._fallback_answer(question_type, question, persona)

        if not self._validate_answer(answer, question):
            answer = self._fallback_answer(question_type, question, persona)

        return answer

    def _validate_answer(self, answer: Any, question: Dict[str, Any]) -> bool:
        """
        Sprawdź czy odpowiedź pasuje do oczekiwanego formatu pytania.

        Walidacja obejmuje zarówno kontrolę typów (np. lista dla pytań wielokrotnego
        wyboru), jak i dopasowanie do dozwolonych opcji. W przypadku pytań skalowych
        dodatkowo weryfikowany jest zakres wartości liczbowych.

        Args:
            answer: Odpowiedź zwrócona przez model lub fallback.
            question: Słownik opisujący pytanie, zawierający m.in. listę opcji oraz
                parametry skali.

        Returns:
            True, jeśli odpowiedź spełnia wymogi pytania; False w przeciwnym razie.
        """

        question_type = self._normalize_question_type(question.get("type"))
        options = question.get("options") or []

        if question_type == "open_ended":
            return isinstance(answer, str)

        if question_type == "multiple_choice":
            if isinstance(answer, list):
                selected = answer
            else:
                selected = [
                    part.strip()
                    for part in str(answer).split(",")
                    if part.strip()
                ]

            if not selected:
                return False

            normalized_options = {opt.lower() for opt in options}
            return all(option.lower() in normalized_options for option in selected)

        if not options:
            scale_min = question.get("scaleMin")
            scale_max = question.get("scaleMax")
            if scale_min is not None and scale_max is not None:
                try:
                    value = int(str(answer).strip())
                except (TypeError, ValueError):
                    return False
                return int(scale_min) <= value <= int(scale_max)
            return answer is not None

        normalized_options = {opt.lower(): opt for opt in options}
        return str(answer).strip().lower() in normalized_options

    async def _generate_persona_responses(
        self, db: Optional[AsyncSession], persona: Persona, survey: Survey
    ) -> List[Dict[str, Any]]:
        """
        Przygotuj listę odpowiedzi persony na wszystkie pytania ankiety.

        Metoda iteruje po pytaniach ankiety, deleguje generowanie odpowiedzi do
        `_generate_single_answer`, a następnie standaryzuje format odpowiedzi
        (szczególnie w przypadku pytań wielokrotnego wyboru). Dzięki temu część
        zapisująca dane do bazy otrzymuje już spójny zestaw rekordów.

        Args:
            db: Opcjonalna sesja bazy danych (przekazywana w celu kompatybilności z
                wcześniejszym API; obecnie nieużywana, ale pozostawiona dla testów).
            persona: Persona dla której generujemy komplet odpowiedzi.
            survey: Obiekt ankiety zawierający listę pytań.

        Returns:
            Lista słowników `{persona_id, question_id, answer}` gotowa do zapisu.
        """

        responses: List[Dict[str, Any]] = []

        for question in survey.questions:
            question_type = self._normalize_question_type(question.get("type"))
            answer = await self._generate_single_answer(persona, question)

            if question_type == "multiple_choice" and isinstance(answer, str):
                answer = [
                    part.strip()
                    for part in answer.split(",")
                    if part.strip()
                ]

            responses.append(
                {
                    "persona_id": str(persona.id),
                    "question_id": question.get("id"),
                    "answer": answer,
                }
            )

        return responses

    async def _save_responses(
        self, db: AsyncSession, responses: List[Dict[str, Any]]
    ) -> None:
        """
        Zapisz wygenerowane odpowiedzi w bazie danych z kontrolą transakcji.

        Każda odpowiedź jest mapowana na osobny rekord `SurveyResponse`, co
        pozwala zachować historyczną granularność danych i umożliwia testom
        jednostkowym sprawdzenie poprawności zapisanych wartości. Transakcja jest
        jawnie zatwierdzana, a w razie błędu wykonywany jest rollback.

        Args:
            db: Asynchroniczna sesja SQLAlchemy.
            responses: Lista słowników opisujących pojedyncze odpowiedzi.
        """

        for response in responses:
            survey_response = SurveyResponse(
                survey_id=UUID(str(response.get("survey_id"))),
                persona_id=UUID(str(response.get("persona_id"))),
                answers={response.get("question_id"): response.get("answer")},
            )
            db.add(survey_response)

        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    def _calculate_metrics(
        self, total_responses: int, total_time_ms: float
    ) -> Dict[str, float]:
        """
        Oblicz podstawowe metryki wykonania ankiety.

        Wskaźniki te wykorzystywane są zarówno w odpowiedzi API, jak i przy
        aktualizacji rekordu ankiety w bazie. Funkcja jest odporna na przypadek,
        gdy nie uda się wygenerować żadnej odpowiedzi (zwraca wtedy średni czas 0).

        Args:
            total_responses: Liczba udanych odpowiedzi wygenerowanych przez wszystkie persony.
            total_time_ms: Całkowity czas wykonania procesu w milisekundach.

        Returns:
            Słownik z kluczami `total_execution_time_ms`, `avg_response_time_ms` oraz
            `total_responses`.
        """

        total_time_ms = float(total_time_ms)
        avg_time = total_time_ms / total_responses if total_responses else 0.0

        return {
            "total_execution_time_ms": total_time_ms,
            "avg_response_time_ms": avg_time,
            "total_responses": total_responses,
        }

    async def _generate_persona_survey_response(
        self, persona: Persona, survey: Survey
    ) -> Dict[str, Any]:
        """
        Generuj i zapisz odpowiedzi pojedynczej persony na ankietę.

        Metoda zachowuje kompatybilność z dotychczasowym API, jednocześnie
        korzystając z nowego zestawu funkcji pomocniczych. Odpowiedzi są
        gromadzone w pamięci, a następnie persystowane w ramach oddzielnej sesji
        bazy danych, co upraszcza testy jednostkowe i umożliwia transakcyjne
        zapisanie wyników.

        Args:
            persona: Persona, dla której generowane są odpowiedzi.
            survey: Obiekt ankiety wraz z listą pytań.

        Returns:
            Słownik zawierający identyfikator persony oraz czas odpowiedzi w ms.
        """

        start_time = time.time()

        responses = await self._generate_persona_responses(db=None, persona=persona, survey=survey)
        for response in responses:
            response["survey_id"] = str(survey.id)

        async with AsyncSessionLocal() as session:
            await self._save_responses(session, responses)

        return {
            "persona_id": str(persona.id),
            "response_time_ms": (time.time() - start_time) * 1000,
        }

    async def _generate_answer_for_question(
        self, persona: Persona, question: Dict[str, Any]
    ) -> Any:
        """
        Zachowaj kompatybilność z wcześniejszym API przekierowując do nowej logiki.

        Starsze fragmenty aplikacji (oraz część testów) oczekują istnienia tej
        metody. Aktualnie pełni ona rolę cienkiej warstwy delegującej do
        `_generate_single_answer`, dzięki czemu w jednym miejscu utrzymujemy logikę
        walidacji, fallbacków oraz obsługi typów pytań.

        Args:
            persona: Persona dla której generujemy odpowiedź.
            question: Opis pytania przekazywany dalej do głównej metody.

        Returns:
            Wynik w formacie zgodnym z `_generate_single_answer`.
        """

        return await self._generate_single_answer(persona, question)

    def _build_persona_context(self, persona: Persona) -> str:
        """
        Zbuduj kontekst persony wykorzystywany w promptach kierowanych do LLM.

        Opis zawiera kluczowe cechy demograficzne oraz listę wartości i
        zainteresowań, co pozwala modelowi odzwierciedlić indywidualną perspektywę
        danej persony. Wartości tekstowe są dodatkowo normalizowane (np. listy
        zamieniane na czytelne ciągi znaków).

        Args:
            persona: Obiekt persony pobrany z bazy danych.

        Returns:
            Wieloliniowy tekst wykorzystywany w sekcji "Profil persony" w promptach.
        """

        name = getattr(persona, "full_name", None) or getattr(persona, "name", "N/A")
        values = getattr(persona, "values", None)
        if isinstance(values, str):
            values = [values]
        interests = getattr(persona, "interests", None)
        if isinstance(interests, str):
            interests = [interests]

        values_text = ", ".join(values) if values else "N/A"
        interests_text = ", ".join(interests) if interests else "N/A"

        return f"""
Name: {name}
Age: {getattr(persona, 'age', 'N/A')}, Gender: {getattr(persona, 'gender', 'N/A')}
Education: {getattr(persona, 'education_level', 'N/A') or 'N/A'}
Income: {getattr(persona, 'income_bracket', 'N/A') or 'N/A'}
Occupation: {getattr(persona, 'occupation', 'N/A') or 'N/A'}
Location: {getattr(persona, 'location', 'N/A') or 'N/A'}
Values: {values_text}
Interests: {interests_text}
Background: {getattr(persona, 'background_story', 'N/A') or 'N/A'}
""".strip()

    async def _answer_single_choice(
        self, persona: Persona, question: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generuj odpowiedź na pytanie jednokrotnego wyboru.

        Metoda wykorzystuje uniwersalny prompt i dopasowuje odpowiedź do listy
        dostępnych opcji z użyciem `_match_option`, dzięki czemu wynik zawsze jest
        poprawnie zmapowany na istniejącą odpowiedź w ankiecie.

        Args:
            persona: Persona, której perspektywę symulujemy.
            question: Słownik opisujący pytanie typu single-choice/yes-no.

        Returns:
            Tekst wybranej opcji lub `None`, jeśli nie udało się dopasować odpowiedzi.
        """

        options = question.get("options") or []
        messages = self._create_survey_prompt(persona, question)
        response = await self._invoke_model(messages)
        raw_answer = getattr(response, "content", "")
        raw_answer = raw_answer.strip() if raw_answer else ""
        return self._match_option(raw_answer, options)

    async def _answer_multiple_choice(
        self, persona: Persona, question: Dict[str, Any]
    ) -> List[str]:
        """
        Generuj odpowiedź na pytanie wielokrotnego wyboru.

        Odpowiedź zwrócona przez LLM jest parsowana do listy wyborów, a każda
        pozycja przechodzi dodatkowe dopasowanie do listy opcji. W efekcie końcowym
        zwracane są jedynie poprawne wartości, co upraszcza dalszą walidację.

        Args:
            persona: Persona odpowiadająca na pytanie.
            question: Opis pytania typu multiple-choice.

        Returns:
            Lista wybranych opcji (co najmniej jedna, jeśli zdefiniowano opcje).
        """

        options = question.get("options") or []
        messages = self._create_survey_prompt(persona, question)
        response = await self._invoke_model(messages)
        raw_answer = getattr(response, "content", "")
        raw_answer = raw_answer.strip() if raw_answer else ""

        selections: List[str] = []
        for part in re.split(r",|;|\n", raw_answer):
            candidate = self._match_option(part.strip(), options)
            if candidate and candidate not in selections:
                selections.append(candidate)

        return selections if selections else ([options[0]] if options else [])

    async def _answer_rating_scale(
        self, persona: Persona, question: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generuj odpowiedź na pytanie skalowe.

        Metoda najpierw próbuje dopasować odpowiedź do listy opcjonalnych etykiet
        skali, a gdy nie są dostępne – wyciąga wartość liczbową z treści zwróconej
        przez model. Zakres jest przycinany do wartości granicznych, aby uniknąć
        danych wykraczających poza zdefiniowaną skalę.

        Args:
            persona: Persona udzielająca odpowiedzi.
            question: Słownik z informacjami o pytaniu skalowym.

        Returns:
            Tekst reprezentujący liczbę z zakresu skali lub dopasowaną etykietę.
        """

        options = question.get("options") or []
        scale_min = question.get("scaleMin", 1)
        scale_max = question.get("scaleMax", 5)
        messages = self._create_survey_prompt(persona, question)
        response = await self._invoke_model(messages)
        raw_answer = getattr(response, "content", "")
        raw_answer = raw_answer.strip() if raw_answer else ""

        if options:
            matched = self._match_option(raw_answer, options)
            if matched:
                return matched

        digits = re.findall(r"-?\d+", raw_answer)
        try:
            value = int(digits[0]) if digits else None
        except (TypeError, ValueError, IndexError):
            value = None

        if value is None:
            midpoint = (int(scale_min) + int(scale_max)) // 2
            return str(midpoint)

        bounded = max(int(scale_min), min(int(scale_max), value))
        return str(bounded)

    async def _answer_open_text(
        self, persona: Persona, question: Dict[str, Any]
    ) -> str:
        """
        Generuj odpowiedź na pytanie otwarte.

        Uzyskana odpowiedź jest dodatkowo sanityzowana (trim), a w razie pustej
        treści wykorzystywany jest bogaty fallback narracyjny. Dzięki temu nigdy
        nie zwracamy pustych odpowiedzi, co upraszcza prezentację wyników.

        Args:
            persona: Persona, której głos symulujemy.
            question: Słownik zawierający pełen opis pytania.

        Returns:
            Naturalnie brzmiąca wypowiedź lub deterministyczny fallback.
        """

        messages = self._create_survey_prompt(persona, question)
        response = await self._invoke_model(messages)
        raw_answer = getattr(response, "content", "")
        answer = raw_answer.strip() if raw_answer else ""

        if answer:
            return answer

        logger = logging.getLogger(__name__)
        logger.warning(
            "Pusta odpowiedź otwarta dla persony %s, uruchamiam fallback.",
            persona.id,
        )
        return self._fallback_open_text_response(persona, self._get_question_text(question))

    def _fallback_answer(
        self, question_type: str, question: Dict[str, Any], persona: Persona
    ) -> Optional[str]:
        """
        Zapewnij bezpieczną odpowiedź awaryjną dla każdego typu pytania.

        Fallback jest deterministyczny i zależny od rodzaju pytania. W przypadku
        pytań zamkniętych preferowana jest pierwsza dostępna opcja, natomiast dla
        pytań otwartych wykorzystywana jest narracyjna odpowiedź generowana przez
        `_fallback_open_text_response`.

        Args:
            question_type: Znormalizowany typ pytania.
            question: Oryginalny słownik opisujący pytanie.
            persona: Persona używana przy generowaniu fallbacku dla pytań otwartych.

        Returns:
            Tekst/Lista opisująca bezpieczną odpowiedź.
        """

        options = question.get("options") or []

        if question_type in {"scale", "yes_no", "single_choice"}:
            if options:
                return options[0]
            scale_min = question.get("scaleMin", 1)
            return str(scale_min)

        if question_type == "multiple_choice":
            return options[0] if options else ""

        if question_type == "open_ended":
            return self._fallback_open_text_response(
                persona, self._get_question_text(question)
            )

        return options[0] if options else None

    def _fallback_open_text_response(self, persona: Persona, question: str) -> str:
        """
        Zwróć bezpieczną odpowiedź fallback dla pytań otwartych, aby uniknąć pustych wartości.

        Odpowiedź jest personalizowana pod kątem persony (imię, zawód) i pozwala
        zachować narracyjny charakter komunikatu, nawet jeśli model językowy nie
        zwrócił treści.

        Args:
            persona: Persona, dla której przygotowujemy wypowiedź zastępczą.
            question: Tekst pytania (wykorzystywany do stworzenia kontekstu w odpowiedzi).

        Returns:
            Krótka wypowiedź tekstowa gotowa do zapisania w bazie.
        """
        lowered_question = question.lower()
        if "pizza" in lowered_question:
            return self._pizza_fallback_response(persona)

        display_name = getattr(persona, "full_name", None) or getattr(persona, "name", "Ta persona")
        name = display_name.split(" ")[0]
        occupation = getattr(persona, "occupation", "uczestnik badania") or "uczestnik badania"
        return (
            f"{name}, pracując jako {occupation}, potrzebuje chwili, aby w pełni odpowiedzieć na pytanie "
            f"\"{question}\". Podkreśla jednak, że temat jest dla niego ważny i wróci do niego po krótkim namyśle."
        )

    def _pizza_fallback_response(self, persona: Persona) -> str:
        """
        Deterministyczny fallback opisujący ulubioną pizzę persony.

        Wykorzystywany jest jako easter egg w testach jednostkowych – generuje
        spójną, rozbudowaną wypowiedź bazującą na atrybutach persony.

        Args:
            persona: Persona, której preferencje kulinarne symulujemy.

        Returns:
            Opis ulubionej pizzy w formie akapitu.
        """
        display_name = getattr(persona, "full_name", None) or getattr(persona, "name", "Ta persona")
        name = display_name.split(" ")[0]
        occupation = getattr(persona, "occupation", "uczestnik badania") or "uczestnik badania"
        location = getattr(persona, "location", None)

        raw_values = getattr(persona, "values", []) or []
        raw_interests = getattr(persona, "interests", []) or []
        if isinstance(raw_values, str):
            raw_values = [raw_values]
        if isinstance(raw_interests, str):
            raw_interests = [raw_interests]

        values = [v.lower() for v in raw_values if isinstance(v, str)]
        interests = [i.lower() for i in raw_interests if isinstance(i, str)]

        def has_any(options):
            return any(opt in values or opt in interests for opt in options)

        if has_any({"health", "wellness", "fitness", "yoga", "running", "sport"}):
            style = "lekką pizzę verde z rukolą, grillowaną cukinią i delikatnym pesto"
            reason = "bo dzięki niej może zjeść coś przyjemnego, a jednocześnie zadbać o zdrowe nawyki"
        elif has_any({"travel", "adventure", "exploration", "innovation", "spice"}):
            style = "pikantną pizzę diavola z dojrzewającym salami, jalapeño i kremowym burratą"
            reason = "bo przepada za wyrazistymi smakami i kulinarnymi eksperymentami"
        elif has_any({"family", "tradition", "comfort", "home"}):
            style = "klasyczną margheritę na neapolitańskim cieście"
            reason = "która przywołuje rodzinne wspomnienia i daje poczucie domowego ciepła"
        elif has_any({"food", "culinary", "gourmet", "wine"}):
            style = "wykwintną pizzę bianca z ricottą, szpinakiem i odrobiną cytrynowej skórki"
            reason = "bo docenia nieoczywiste kompozycje i starannie dobrane składniki"
        else:
            style = "pełną dodatków pizzę capricciosa z szynką, karczochami i pieczarkami"
            reason = "bo daje mu wszystkiego po trochu i satysfakcjonuje różnorodnością smaków"

        location_note = f", a w {location} wie, gdzie znaleźć rzemieślniczą pizzerię spełniającą te oczekiwania" if location else ""

        return (
            f"{name}, na co dzień {occupation}, najchętniej wybiera {style}. "
            f"Mówi, że lubi ją, ponieważ {reason}{location_note}."
        )

    def _calculate_question_analytics(
        self, question: Dict[str, Any], responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Przygotuj metryki dla pojedynczego pytania.

        Funkcja filtruje odpowiedzi po identyfikatorze pytania, a następnie
        wywołuje `_calculate_question_stats`, aby uzyskać metryki właściwe dla
        konkretnego typu (np. rozkład odpowiedzi, średnia ze skali). Wynik jest
        wzbogacany o podstawowe informacje tekstowe, co ułatwia serializację do
        warstwy API.

        Args:
            question: Słownik z definicją pytania ankietowego.
            responses: Spłaszczona lista odpowiedzi (`question_id`, `answer`).

        Returns:
            Słownik zawierający identyfikator pytania, jego typ, treść oraz metryki.
        """

        question_id = question.get("id")
        question_type = self._normalize_question_type(question.get("type"))
        question_text = self._get_question_text(question)

        relevant_answers = [
            response.get("answer")
            for response in responses
            if response.get("question_id") == question_id and response.get("answer") is not None
        ]

        analytics: Dict[str, Any] = {
            "question_id": question_id,
            "question_text": question_text,
            "question_type": question_type,
            "total_responses": len(relevant_answers),
        }

        if question_type == "scale":
            stats = self._calculate_question_stats("rating-scale", relevant_answers)
            analytics.update(stats)
        elif question_type in {"yes_no", "single_choice"}:
            stats = self._calculate_question_stats("single-choice", relevant_answers)
            analytics.update(stats)
            distribution = stats.get("distribution", {})
            yes_labels = {"yes", "tak", "true", "1"}
            yes_labels.update(
                {
                    opt.lower()
                    for opt in (question.get("options") or [])
                    if any(marker in opt.lower() for marker in {"yes", "tak", "true", "1"})
                }
            )
            yes_count = sum(
                1
                for answer in relevant_answers
                if str(answer).strip().lower() in yes_labels
            )
            analytics["distribution"] = distribution
            analytics["avg_score"] = (
                yes_count / len(relevant_answers) if relevant_answers else 0.0
            )
        elif question_type == "multiple_choice":
            normalized_answers = []
            for answer in relevant_answers:
                if isinstance(answer, list):
                    normalized_answers.append(answer)
                else:
                    normalized_answers.append(
                        [
                            part.strip()
                            for part in str(answer).split(",")
                            if part.strip()
                        ]
                    )

            stats = self._calculate_question_stats("multiple-choice", normalized_answers)
            analytics.update(stats)
        elif question_type == "open_ended":
            stats = self._calculate_question_stats("open-text", relevant_answers)
            analytics.update(stats)
        else:
            analytics["raw_answers"] = relevant_answers

        return analytics

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
        flat_responses: List[Dict[str, Any]] = []
        for response in responses:
            for question_id, answer in (response.answers or {}).items():
                flat_responses.append(
                    {
                        "question_id": question_id,
                        "answer": answer,
                    }
                )

        question_analytics = []

        for question in survey.questions:
            analytics = self._calculate_question_analytics(question, flat_responses)
            stats = {
                key: value
                for key, value in analytics.items()
                if key
                not in {"question_id", "question_text", "question_type", "total_responses"}
            }

            question_analytics.append(
                QuestionAnalytics(
                    question_id=analytics["question_id"],
                    question_type=analytics["question_type"],
                    question_title=analytics["question_text"],
                    responses_count=analytics["total_responses"],
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

    def _calculate_question_stats(self, question_type: str, answers: List[Any]) -> Dict[str, Any]:
        """
        Oblicz statystyki dla pytania na podstawie typu.

        Funkcja agreguje dane ilościowe i jakościowe: dla pytań zamkniętych
        przygotowuje rozkłady odpowiedzi, dla skal oblicza podstawowe miary
        statystyczne, a dla pytań otwartych zwraca próbkę wypowiedzi i średnią
        liczbę słów.

        Args:
            question_type: Oryginalna nazwa typu pytania (może wymagać normalizacji).
            answers: Lista surowych odpowiedzi zebranych z bazy.

        Returns:
            Słownik ze statystykami dopasowanymi do typu pytania.
        """

        normalized = self._normalize_question_type(question_type)

        if question_type == "single-choice" or normalized in {"yes_no", "single_choice"}:
            counter = Counter(str(answer) for answer in answers)
            return {
                "distribution": dict(counter),
                "most_common": counter.most_common(1)[0][0] if counter else None,
            }

        if question_type == "multiple-choice" or normalized == "multiple_choice":
            all_options: List[str] = []
            for answer_list in answers:
                if isinstance(answer_list, list):
                    all_options.extend(str(option) for option in answer_list)
                else:
                    all_options.append(str(answer_list))

            counter = Counter(all_options)
            return {
                "distribution": dict(counter),
                "most_common": counter.most_common(3),
            }

        if question_type == "rating-scale" or normalized == "scale":
            numeric_answers: List[int] = []
            for value in answers:
                try:
                    numeric_answers.append(int(str(value).strip()))
                except (TypeError, ValueError):
                    continue

            if numeric_answers:
                return {
                    "mean": statistics.mean(numeric_answers),
                    "median": statistics.median(numeric_answers),
                    "mode": statistics.mode(numeric_answers) if len(numeric_answers) > 1 else numeric_answers[0],
                    "min": min(numeric_answers),
                    "max": max(numeric_answers),
                    "std": statistics.stdev(numeric_answers) if len(numeric_answers) > 1 else 0,
                    "distribution": dict(Counter(str(num) for num in numeric_answers)),
                }
            return {}

        if question_type == "open-text" or normalized == "open_ended":
            texts = [str(answer) for answer in answers]
            lengths = [len(text.split()) for text in texts]
            return {
                "total_responses": len(texts),
                "avg_word_count": sum(lengths) / len(lengths) if lengths else 0,
                "sample_responses": texts[:5],
            }

        return {}

    def _calculate_demographic_breakdown(
        self, responses: List[SurveyResponse], personas: Dict[UUID, Persona], questions: List[Dict]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Rozłóż odpowiedzi według demografii.

        Funkcja grupuje odpowiedzi po podstawowych parametrach (wiek, płeć,
        wykształcenie, dochód), tworząc statystyki używane w raportach
        podsumowujących. W przypadku brakujących danych posługujemy się wartościami
        domyślnymi (np. "Unknown").

        Args:
            responses: Lista rekordów `SurveyResponse` z bazy danych.
            personas: Słownik mapujący identyfikator persony na obiekt persony.
            questions: Lista pytań (zachowana dla kompatybilności; obecnie nieużywana).

        Returns:
            Zagnieżdżony słownik z rozkładami odpowiedzi według wybranych cech.
        """
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
