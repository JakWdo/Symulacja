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
    - target_demographics: Docelowe rozkłady demograficzne populacji
      Przykład: {
        'age': {'18-24': 0.15, '25-34': 0.20},
        'gender': {'male': 0.49, 'female': 0.51}
      }

    Pola opcjonalne:
    - description: Opis projektu (max 1000 znaków)
    - target_audience: Opis docelowej grupy odbiorców
    - research_objectives: Cele badawcze projektu
    - additional_notes: Dodatkowe uwagi
    - target_sample_size: Docelowa liczba person (domyślnie 100, zakres 10-1000)
    """
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    target_audience: str | None = None
    research_objectives: str | None = None
    additional_notes: str | None = None
    target_demographics: dict[str, dict[str, float]] = Field(
        ...,
        description="Target population distribution. Example: {'age': {'18-24': 0.15, '25-34': 0.20}, 'gender': {'male': 0.49, 'female': 0.51}}",
    )
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
    - target_demographics: Nowe rozkłady demograficzne
    - target_sample_size: Nowa docelowa liczba person (10-1000)

    Pola nie podane w requestcie pozostają bez zmian.
    """
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    target_audience: str | None = None
    research_objectives: str | None = None
    additional_notes: str | None = None
    target_demographics: dict[str, dict[str, float]] | None = None
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
    - target_demographics: Docelowe rozkłady demograficzne
    - target_sample_size: Docelowa liczba person

    Statystyki walidacji:
    - chi_square_statistic: Wartości statystyki χ² dla każdej kategorii demograficznej
    - p_values: Wartości p dla testów χ² (p > 0.05 = dobra zgodność)
    - is_statistically_valid: Czy wygenerowane persony pasują do rozkładu
    - validation_date: Kiedy ostatnio przeprowadzono walidację

    Metadata:
    - created_at: Data utworzenia projektu
    - updated_at: Data ostatniej aktualizacji
    - is_active: Czy projekt jest aktywny (soft delete)

    Konfiguracja:
    - from_attributes = True: Umożliwia tworzenie z modeli SQLAlchemy
    """
    id: UUID
    name: str
    description: str | None
    target_audience: str | None
    research_objectives: str | None
    additional_notes: str | None
    target_demographics: dict[str, dict[str, float]]
    target_sample_size: int
    chi_square_statistic: dict[str, Any] | None
    p_values: dict[str, Any] | None
    is_statistically_valid: bool
    validation_date: datetime | None
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class ProjectDeleteResponse(BaseModel):
    """
    Schema odpowiedzi po soft delete projektu

    Zwraca informacje o usuniętym projekcie i możliwości restore:
    - project_id: UUID usuniętego projektu
    - name: Nazwa projektu
    - status: "deleted"
    - deleted_at: Timestamp usunięcia
    - deleted_by: UUID użytkownika który usunął projekt
    - permanent_deletion_scheduled_at: Kiedy projekt zostanie trwale usunięty (deleted_at + 30 dni)
    - message: Komunikat dla użytkownika
    """
    project_id: UUID
    name: str
    status: str  # "deleted"
    deleted_at: datetime
    deleted_by: UUID
    permanent_deletion_scheduled_at: datetime
    message: str


class ProjectUndoDeleteResponse(BaseModel):
    """
    Schema odpowiedzi po przywróceniu (undo delete) projektu

    Zwraca informacje o przywróconym projekcie:
    - project_id: UUID przywróconego projektu
    - name: Nazwa projektu
    - status: "active"
    - restored_at: Timestamp przywrócenia
    - restored_by: UUID użytkownika który przywrócił projekt
    - message: Komunikat dla użytkownika
    """
    project_id: UUID
    name: str
    status: str  # "active"
    restored_at: datetime
    restored_by: UUID
    message: str
