"""
Modele ankiet wykorzystywane do funkcjonalności syntetycznych badań.

Umożliwia tworzenie ankiet i zbieranie odpowiedzi od syntetycznych person.
"""

import uuid
from typing import Any, Dict

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, expression
from app.db.base import Base


class Survey(Base):
    """
    Model reprezentujący syntetyczną ankietę.

    Survey pozwala na stworzenie zestawu pytań, które zostaną zadane
    syntetycznym personom projektu. AI generuje odpowiedzi bazując na
    profilach psychologicznych i demograficznych person.
    """
    __tablename__ = "surveys"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    # Podstawowe informacje
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Pytania ankietowe zapisane jako tablica JSON obiektów pytania
    # Format: [{"id": "q1", "type": "single-choice", "title": "...", "options": [...], ...}, ...]
    questions = Column(JSON, nullable=False)

    # Status ankiety
    status = Column(
        String(50),
        default="draft",
        nullable=False,
        index=True
    )  # draft, running, completed, failed

    # Statystyki odpowiedzi
    target_responses = Column(Integer, default=1000, nullable=False)
    actual_responses = Column(Integer, default=0, nullable=False)

    # Znacznik czasus
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Metryki wykonania (podobnie jak w FocusGroup)
    total_execution_time_ms = Column(Integer, nullable=True)
    avg_response_time_ms = Column(Integer, nullable=True)

    # Miękkie usunięcie
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        server_default=expression.true(),
    )

    # Relacje
    project = relationship("Project", back_populates="surveys")
    responses = relationship("SurveyResponse", back_populates="survey", cascade="all, delete-orphan")


class SurveyResponse(Base):
    """
    Model reprezentujący odpowiedź persony na ankietę.

    Każda persona w projekcie może odpowiedzieć na ankietę.
    Odpowiedzi są generowane przez AI na podstawie profilu persony.

    Wersja rozszerzona o pola pomocnicze do pracy na pojedynczych pytaniach:

    Attributes:
        id: UUID odpowiedzi (klucz główny)
        survey_id: UUID ankiety, której dotyczy odpowiedź
        persona_id: UUID persony udzielającej odpowiedzi

        # === DANE MERYTORYCZNE ===
        question_id: Opcjonalne ID pojedynczego pytania używane w prostych formularzach
        answer: Opcjonalna odpowiedź dla `question_id` (string/liczba/lista w zależności od pytania)
        answers: Kompletny słownik odpowiedzi `{question_id: answer}` dla całej ankiety

        # === METADANE ===
        completed_at: Timestamp zakończenia udzielania odpowiedzi
        response_time_ms: Łączny czas potrzebny personie na odpowiedź (ms)

    Logika modelu synchronizuje `question_id` i `answer` ze strukturą `answers`,
    aby aplikacja mogła wygodnie obsługiwać zarówno pojedyncze, jak i wielopytaniowe
    ankiety bez duplikacji kodu.
    """
    __tablename__ = "survey_responses"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id = Column(PGUUID(as_uuid=True), ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False, index=True)
    persona_id = Column(PGUUID(as_uuid=True), ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True)

    # Odpowiedzi na pytania
    # Format `answers`: {"question_id": "answer_value", ...}
    # Dla single-choice: {"q1": "Option 1"}
    # Dla multiple-choice: {"q1": ["Option 1", "Option 2"]}
    # Dla rating-scale: {"q1": 4}
    # Dla open-text: {"q1": "Free text response..."}
    # Pola `question_id` i `answer` przechowują pojedynczą parę
    # i są synchronizowane z `answers` (np. na potrzeby starszych formularzy).
    question_id = Column(String, nullable=True)
    answer = Column(JSON, nullable=True)
    answers = Column(JSON, nullable=False)

    # Znacznik czasu
    completed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Metryki wykonania
    response_time_ms = Column(Integer, nullable=True)

    # Relacje
    survey = relationship("Survey", back_populates="responses")
    persona = relationship("Persona")

    def __init__(self, **kwargs):
        """
        Obsłuż zarówno pojedyncze, jak i zbiorcze odpowiedzi.

        Konstruktor akceptuje te same parametry co wcześniej (`answers`),
        ale dodatkowo wspiera przekazanie `question_id` i `answer`. Jeżeli
        użytkownik poda wyłącznie te dwa pola, model automatycznie zbuduje
        słownik `answers`. Gdy dostarczony jest pełny słownik odpowiedzi,
        `question_id` i `answer` zostaną z nim zsynchronizowane (o ile tylko
        jedna odpowiedź jest dostępna) lub pozostaną puste przy ankietach
        wielopytaniowych.
        """

        single_question_id = kwargs.pop("question_id", None)
        single_answer = kwargs.pop("answer", None)

        answers = kwargs.get("answers")
        if single_question_id is not None:
            if answers is None:
                kwargs["answers"] = {single_question_id: single_answer}
            else:
                normalized_answers: Dict[str, Any] = dict(answers)
                normalized_answers.setdefault(single_question_id, single_answer)
                kwargs["answers"] = normalized_answers
        elif answers is None:
            kwargs["answers"] = {}

        super().__init__(**kwargs)

        self.question_id = single_question_id
        self.answer = single_answer

        if (
            self.question_id is not None
            and self.answer is None
            and isinstance(self.answers, dict)
        ):
            self.answer = self.answers.get(self.question_id)

        if (
            self.question_id is None
            and isinstance(self.answers, dict)
            and len(self.answers) == 1
        ):
            only_question_id, only_answer = next(iter(self.answers.items()))
            self.question_id = only_question_id
            if self.answer is None:
                self.answer = only_answer
