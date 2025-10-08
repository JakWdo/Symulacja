"""
Schematy Pydantic dla grup fokusowych (focus groups)

Definiuje struktury danych dla:
- FocusGroupCreate - tworzenie nowej grupy fokusowej
- FocusGroupResponse - podstawowa odpowiedź API
- FocusGroupResultResponse - odpowiedź z wynikami i metrykami
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class FocusGroupCreate(BaseModel):
    """
    Schema do tworzenia nowej grupy fokusowej

    Grupa fokusowa = symulowana dyskusja między personami AI na zadany temat

    Pola wymagane:
    - name: Nazwa grupy (1-255 znaków)
    - persona_ids: Lista UUID person uczestniczących (0-100 person, minimum 2 do uruchomienia)
    - questions: Lista pytań do dyskusji (0-50 pytań, minimum 1 do uruchomienia)

    Pola opcjonalne:
    - description: Opis grupy (max 1000 znaków)
    - project_context: Kontekst projektu dla AI (max 5000 znaków)
      Np. "Badamy reakcje na nową aplikację fitness dla młodych dorosłych"
    - mode: Tryb dyskusji ('normal' lub 'adversarial')
      normal = normalna dyskusja
      adversarial = persony są bardziej krytyczne/sceptyczne

    Uwaga: Puste listy persona_ids/questions są dozwolone dla draftu,
    ale przed uruchomieniem (run) wymagane minimum 2 persony i 1 pytanie.
    """
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    project_context: Optional[str] = Field(None, max_length=5000)
    persona_ids: List[UUID] = Field(default_factory=list, max_items=100)
    questions: List[str] = Field(default_factory=list, max_items=50)
    mode: str = Field(default="normal", pattern="^(normal|adversarial)$")


class FocusGroupResponse(BaseModel):
    """
    Schema podstawowej odpowiedzi API dla grupy fokusowej

    Zwraca informacje o grupie fokusowej bez szczegółowych wyników dyskusji:

    Konfiguracja:
    - id: UUID grupy fokusowej
    - project_id: UUID projektu
    - name: Nazwa grupy
    - description: Opis
    - project_context: Kontekst projektu
    - persona_ids: Lista UUID uczestniczących person
    - questions: Lista pytań dyskusyjnych
    - mode: Tryb ('normal' lub 'adversarial')

    Status wykonania:
    - status: Stan grupy ('pending', 'running', 'completed', 'failed')
    - total_execution_time_ms: Całkowity czas wykonania (ms)
    - avg_response_time_ms: Średni czas odpowiedzi person (ms)

    Timestamps:
    - created_at: Kiedy utworzono grupę
    - started_at: Kiedy rozpoczęto dyskusję
    - completed_at: Kiedy zakończono dyskusję

    Konfiguracja:
    - from_attributes = True: Konwersja z SQLAlchemy
    """
    id: UUID
    project_id: UUID
    name: str
    description: Optional[str]
    project_context: Optional[str]
    persona_ids: List[UUID]
    questions: List[str]
    mode: str
    status: str
    total_execution_time_ms: Optional[int]
    avg_response_time_ms: Optional[float]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class FocusGroupResultResponse(BaseModel):
    """
    Schema odpowiedzi z wynikami i metrykami grupy fokusowej

    Rozszerza FocusGroupResponse o szczegółowe wyniki analizy:

    Wszystkie pola z FocusGroupResponse +

    Metryki i analiza (w polu metrics):
    - idea_score: Ocena pomysłu (0-100)
    - consensus: Poziom zgody między personami (0-1)
    - sentiment: Analiza sentymentu
      - overall: Ogólny sentyment (-1 do 1)
      - positive_rate: % pozytywnych odpowiedzi
      - negative_rate: % negatywnych odpowiedzi
    - demographic_insights: Różnice w opiniach według demografii
    - key_themes: Główne tematy dyskusji
    - response_distribution: Rozkład odpowiedzi person

    Typ metrics: Dict[str, Any] - elastyczna struktura dla różnych typów analiz

    Używane przez endpoint GET /focus-groups/{id}/results
    """
    id: UUID
    project_id: UUID
    name: str
    description: Optional[str]
    project_context: Optional[str]
    persona_ids: List[UUID]
    questions: List[str]
    mode: str
    status: str
    metrics: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
