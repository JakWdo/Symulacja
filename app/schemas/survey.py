"""
Schematy Pydantic dla ankiet (surveys)

Definiuje struktury danych dla:
- QuestionSchema - pojedyncze pytanie ankiety
- SurveyCreate - tworzenie nowej ankiety
- SurveyResponse - odpowiedź API z danymi ankiety
- SurveyResultsResponse - odpowiedź z wynikami i statystykami
"""

from pydantic import BaseModel, Field
from typing import Any, Literal
from datetime import datetime
from uuid import UUID


class QuestionSchema(BaseModel):
    """
    Schema reprezentująca pojedyncze pytanie w ankiecie

    Pytanie może mieć jeden z 4 typów:
    - single-choice: Wybór jednej opcji z listy (radio buttons)
    - multiple-choice: Wybór wielu opcji (checkboxes)
    - rating-scale: Skala liczbowa (np. 1-5, 1-10)
    - open-text: Wolna odpowiedź tekstowa

    Pola:
    - id: Unikalny identyfikator pytania w ankiecie (string)
    - type: Typ pytania (jeden z powyższych)
    - title: Treść pytania (wymagane, 1-500 znaków)
    - description: Opcjonalny opis/kontekst pytania (max 1000 znaków)
    - options: Lista opcji (wymagane dla single/multiple-choice)
    - required: Czy pytanie jest obowiązkowe (default: True)
    - scaleMin: Min wartość dla rating-scale (default: 1)
    - scaleMax: Max wartość dla rating-scale (default: 5)
    """
    id: str = Field(..., min_length=1, max_length=100)
    type: Literal["single-choice", "multiple-choice", "rating-scale", "open-text"]
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(None, max_length=1000)
    options: list[str] | None = Field(None, max_items=50)
    required: bool = Field(default=True)
    scaleMin: int | None = Field(None, ge=0, le=100)
    scaleMax: int | None = Field(None, ge=1, le=100)


class SurveyCreate(BaseModel):
    """
    Schema do tworzenia nowej ankiety

    Survey = zestaw pytań, na które odpowiadają syntetyczne persony.
    AI generuje odpowiedzi bazując na profilach psychologicznych person.

    Pola wymagane:
    - title: Nazwa ankiety (1-255 znaków)
    - questions: Lista pytań (min 1, max 100)

    Pola opcjonalne:
    - description: Opis ankiety (max 1000 znaków)
    - target_responses: Docelowa liczba odpowiedzi (default: 1000)
      Liczba person × liczba pytań = faktyczna liczba odpowiedzi
    """
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    questions: list[QuestionSchema] = Field(..., min_items=1, max_items=100)
    target_responses: int = Field(default=1000, ge=10, le=100000)


class SurveyResponse(BaseModel):
    """
    Schema podstawowej odpowiedzi API dla ankiety

    Zwraca informacje o ankiecie bez szczegółowych wyników:

    Konfiguracja:
    - id: UUID ankiety
    - project_id: UUID projektu
    - title: Nazwa ankiety
    - description: Opis
    - questions: Lista pytań

    Status wykonania:
    - status: Stan ankiety ('draft', 'running', 'completed', 'failed')
    - target_responses: Docelowa liczba odpowiedzi
    - actual_responses: Rzeczywista liczba zebranych odpowiedzi

    Metryki wykonania:
    - total_execution_time_ms: Całkowity czas wykonania (ms)
    - avg_response_time_ms: Średni czas odpowiedzi persony (ms)

    Timestamps:
    - created_at: Kiedy utworzono ankietę
    - started_at: Kiedy rozpoczęto zbieranie odpowiedzi
    - completed_at: Kiedy zakończono zbieranie odpowiedzi

    Konfiguracja:
    - from_attributes = True: Konwersja z SQLAlchemy ORM
    """
    id: UUID
    project_id: UUID
    title: str
    description: str | None
    questions: list[dict[str, Any]]  # QuestionSchema as dict
    status: str
    target_responses: int
    actual_responses: int
    total_execution_time_ms: int | None
    avg_response_time_ms: int | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    is_active: bool

    class Config:
        from_attributes = True


class QuestionAnalytics(BaseModel):
    """
    Statystyki i analiza dla pojedynczego pytania

    Zawiera:
    - question_id: ID pytania
    - question_type: Typ pytania
    - question_title: Treść pytania
    - responses_count: Liczba odpowiedzi
    - statistics: Statystyki specyficzne dla typu pytania:
      * single-choice/multiple-choice: rozkład odpowiedzi {"Option 1": 45, "Option 2": 55}
      * rating-scale: mean, median, std, min, max
      * open-text: length stats, word cloud data
    """
    question_id: str
    question_type: str
    question_title: str
    responses_count: int
    statistics: dict[str, Any]


class SurveyResultsResponse(BaseModel):
    """
    Schema odpowiedzi z wynikami i analizą ankiety

    Rozszerza SurveyResponse o szczegółowe wyniki:

    Wszystkie pola z SurveyResponse +

    Analiza wyników:
    - question_analytics: Lista analiz dla każdego pytania (QuestionAnalytics)
    - demographic_breakdown: Odpowiedzi rozłożone według demografii
      Np. {"age_group": {"18-24": {...}, "25-34": {...}}}
    - completion_rate: % person, które odpowiedziały (0-100)
    - average_response_time_ms: Średni czas odpowiedzi na ankietę

    Używane przez endpoint GET /surveys/{id}/results
    """
    # Pola z SurveyResponse
    id: UUID
    project_id: UUID
    title: str
    description: str | None
    questions: list[dict[str, Any]]
    status: str
    target_responses: int
    actual_responses: int
    total_execution_time_ms: int | None
    avg_response_time_ms: int | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    # Wyniki i analiza
    question_analytics: list[QuestionAnalytics]
    demographic_breakdown: dict[str, dict[str, Any]]
    completion_rate: float
    average_response_time_ms: float | None

    class Config:
        from_attributes = True
