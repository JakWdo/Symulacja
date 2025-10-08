"""
Schematy Pydantic dla projektów badawczych

Definiuje struktury danych dla operacji CRUD na projektach:
- ProjectCreate - tworzenie nowego projektu
- ProjectUpdate - aktualizacja istniejącego projektu
- ProjectResponse - odpowiedź API z danymi projektu
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
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
    description: Optional[str] = Field(None, max_length=1000)
    target_audience: Optional[str] = None
    research_objectives: Optional[str] = None
    additional_notes: Optional[str] = None
    target_demographics: Dict[str, Dict[str, float]] = Field(
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
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    target_audience: Optional[str] = None
    research_objectives: Optional[str] = None
    additional_notes: Optional[str] = None
    target_demographics: Optional[Dict[str, Dict[str, float]]] = None
    target_sample_size: Optional[int] = Field(None, ge=10, le=1000)


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
    description: Optional[str]
    target_audience: Optional[str]
    research_objectives: Optional[str]
    additional_notes: Optional[str]
    target_demographics: Dict[str, Dict[str, float]]
    target_sample_size: int
    chi_square_statistic: Optional[Dict[str, Any]]
    p_values: Optional[Dict[str, Any]]
    is_statistically_valid: bool
    validation_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
