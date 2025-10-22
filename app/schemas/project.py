"""
Schematy Pydantic dla projektów badawczych

Definiuje struktury danych dla operacji CRUD na projektach:
- ProjectCreate - tworzenie nowego projektu
- ProjectUpdate - aktualizacja istniejącego projektu
- ProjectResponse - odpowiedź API z danymi projektu
"""

from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime
from uuid import UUID


class ProjectCreate(BaseModel):
    """
    Schema do tworzenia nowego projektu badawczego

    Pola wymagane:
    - name: Nazwa projektu (1-255 znaków)

    Pola opcjonalne:
    - description: Opis projektu (max 1000 znaków)
    - target_audience: Opis docelowej grupy odbiorców
    - research_objectives: Cele badawcze projektu
    - additional_notes: Dodatkowe uwagi
    - target_sample_size: Docelowa liczba person (domyślnie 100, zakres 10-1000)

    Note: Demographics są generowane przez RAG + segment-based allocation,
          nie przez target_demographics.
    """
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    target_audience: str | None = None
    research_objectives: str | None = None
    additional_notes: str | None = None
    target_sample_size: int = Field(default=100, ge=10, le=1000)


class ProjectUpdate(BaseModel):
    """
    Schema do aktualizacji istniejącego projektu

    Wszystkie pola opcjonalne - aktualizuj tylko to, co chcesz zmienić:
    - name: Nowa nazwa projektu (1-255 znaków)
    - description: Nowy opis (max 1000 znaków)
    - target_audience: Nowy opis docelowej grupy odbiorców
    - research_objectives: Nowe cele badawcze
    - additional_notes: Nowe dodatkowe uwagi
    - target_sample_size: Nowa docelowa liczba person (10-1000)

    Pola nie podane w requestcie pozostają bez zmian.
    """
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    target_audience: str | None = None
    research_objectives: str | None = None
    additional_notes: str | None = None
    target_sample_size: int | None = Field(None, ge=10, le=1000)


class ProjectResponse(BaseModel):
    """
    Schema odpowiedzi API z danymi projektu

    Zwraca kompletne informacje o projekcie włącznie z:

    Podstawowe dane:
    - id: UUID projektu
    - name: Nazwa
    - description: Opis
    - target_audience: Opis docelowej grupy odbiorców
    - research_objectives: Cele badawcze
    - additional_notes: Dodatkowe uwagi
    - target_sample_size: Docelowa liczba person

    Metadata:
    - created_at: Data utworzenia projektu
    - updated_at: Data ostatniej aktualizacji
    - is_active: Czy projekt jest aktywny (soft delete)

    Note: Demographics są generowane przez RAG + segment-based allocation.
          Statistical validation (chi-square) została usunięta.

    Konfiguracja:
    - from_attributes = True: Umożliwia tworzenie z modeli SQLAlchemy
    """
    id: UUID
    name: str
    description: str | None
    target_audience: str | None
    research_objectives: str | None
    additional_notes: str | None
    target_sample_size: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
