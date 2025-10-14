"""
Schematy Pydantic dla person (wersja v1)

Definiuje struktury danych dla:
- PersonaGenerateRequest - żądanie generowania person
- PersonaGenerationAdvancedOptions - zaawansowane opcje targetowania
- PersonaResponse - odpowiedź API z danymi persony

Uwaga: To jest wersja v1. Nowsze projekty powinny używać persona_v2.py
"""

from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PersonaGenerationAdvancedOptions(BaseModel):
    """
    Zaawansowane opcje targetowania person

    Pozwala precyzyjnie kontrolować demografię i psychografię generowanych person:

    Demograficzne:
    - age_focus: Preferowany zakres wiekowy ('balanced', 'young_adults', 'experienced_leaders')
    - gender_balance: Rozkład płci ('balanced', 'female_skew', 'male_skew')
    - urbanicity: Typ lokalizacji ('any', 'urban', 'suburban', 'rural')
    - target_cities: Lista konkretnych miast
    - target_countries: Lista krajów
    - age_min, age_max: Dokładny zakres wieku (18-90)

    Zawodowe:
    - industries: Lista branż (np. ['tech', 'healthcare'])
    - required_values: Wymagane wartości życiowe
    - excluded_values: Wykluczone wartości
    - required_interests: Wymagane zainteresowania
    - excluded_interests: Wykluczone zainteresowania

    Niestandardowe rozkłady (custom weights):
    - custom_age_groups: {'18-22': 0.3, '23-29': 0.4, '30-40': 0.3}
    - gender_weights: {'male': 0.6, 'female': 0.4}
    - location_weights: {'urban': 0.7, 'rural': 0.3}
    - education_weights: {'bachelors': 0.5, 'masters': 0.3}
    - income_weights: {'60k-100k': 0.4, '100k+': 0.6}

    Psychologiczne:
    - personality_skew: Przesunięcie cech Big Five (0.0-1.0)
      Przykład: {'extraversion': 0.7} - więcej ekstrawertycznych person
    """
    age_focus: Optional[Literal['balanced', 'young_adults', 'experienced_leaders']] = None
    gender_balance: Optional[Literal['balanced', 'female_skew', 'male_skew']] = None
    urbanicity: Optional[Literal['any', 'urban', 'suburban', 'rural']] = None
    target_cities: Optional[List[str]] = None
    target_countries: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    required_values: Optional[List[str]] = None
    excluded_values: Optional[List[str]] = None
    required_interests: Optional[List[str]] = None
    excluded_interests: Optional[List[str]] = None
    age_min: Optional[int] = Field(None, ge=18, le=90)
    age_max: Optional[int] = Field(None, ge=18, le=90)
    custom_age_groups: Optional[Dict[str, float]] = Field(
        None,
        description="Custom age group distribution, e.g., {'18-22': 0.3, '23-29': 0.4, '30-40': 0.3}"
    )
    gender_weights: Optional[Dict[str, float]] = Field(
        None,
        description="Custom gender distribution weights"
    )
    location_weights: Optional[Dict[str, float]] = Field(
        None,
        description="Custom location distribution weights"
    )
    education_weights: Optional[Dict[str, float]] = Field(
        None,
        description="Custom education level distribution weights"
    )
    income_weights: Optional[Dict[str, float]] = Field(
        None,
        description="Custom income bracket distribution weights"
    )
    personality_skew: Optional[Dict[str, float]] = Field(
        None,
        description="Skew Big Five personality traits (openness, conscientiousness, extraversion, agreeableness, neuroticism). Values 0.0-1.0 shift mean towards low/high."
    )


class PersonaGenerateRequest(BaseModel):
    """
    Schema żądania generowania person

    Podstawowe parametry:
    - num_personas: Ile person wygenerować (2-100, domyślnie 10)
    - adversarial_mode: Czy generować persony "przeciwne" dla stress testingu kampanii
      (domyślnie False - normalne persony reprezentujące target audience)
    - advanced_options: Opcjonalne zaawansowane targetowanie (PersonaGenerationAdvancedOptions)

    Przykład użycia:
    {
      "num_personas": 50,
      "adversarial_mode": false,
      "advanced_options": {
        "age_focus": "young_adults",
        "urbanicity": "urban",
        "industries": ["tech", "finance"]
      }
    }
    """
    num_personas: int = Field(
        default=10,
        ge=2,
        le=100,
        description="Number of personas to generate (2-100)"
    )
    adversarial_mode: bool = Field(
        default=False,
        description="Generate adversarial personas for campaign stress testing",
    )
    use_rag: bool = Field(
        default=True,
        description="Use RAG (Retrieval-Augmented Generation) with Polish society knowledge base",
    )
    advanced_options: Optional[PersonaGenerationAdvancedOptions] = Field(
        default=None,
        description="Optional advanced persona targeting controls",
    )


class PersonaResponse(BaseModel):
    """
    Schema odpowiedzi API z danymi persony

    Zwraca kompletny profil wygenerowanej persony:

    Podstawowe dane:
    - id: UUID persony
    - project_id: UUID projektu do którego należy
    - full_name: Pełne imię i nazwisko
    - persona_title: Tytuł/rola (np. "Tech-savvy Millennial")
    - headline: Krótki opis (1-2 zdania)

    Demografia:
    - age: Wiek (liczba)
    - gender: Płeć
    - location: Lokalizacja (miasto, stan)
    - education_level: Poziom wykształcenia
    - income_bracket: Przedział dochodowy
    - occupation: Zawód

    Cechy Big Five (0-1, gdzie 1=wysoka cecha):
    - openness: Otwartość na doświadczenia
    - conscientiousness: Sumienność
    - extraversion: Ekstrawersja
    - agreeableness: Ugodowość
    - neuroticism: Neurotyczność

    Wymiary kulturowe Hofstede (0-1):
    - power_distance: Dystans władzy
    - individualism: Indywidualizm
    - masculinity: Męskość
    - uncertainty_avoidance: Unikanie niepewności
    - long_term_orientation: Orientacja długoterminowa
    - indulgence: Pobłażliwość

    Profile psychograficzny:
    - values: Lista wartości życiowych
    - interests: Lista zainteresowań
    - background_story: Historia osobista persony (narrracja AI)

    Metadata:
    - created_at: Data utworzenia
    - is_active: Czy persona jest aktywna

    Konfiguracja:
    - from_attributes = True: Konwersja z modeli SQLAlchemy
    """
    id: UUID
    project_id: UUID
    age: int
    gender: str
    location: Optional[str]
    education_level: Optional[str]
    income_bracket: Optional[str]
    occupation: Optional[str]
    full_name: Optional[str]
    persona_title: Optional[str]
    headline: Optional[str]
    openness: Optional[float]
    conscientiousness: Optional[float]
    extraversion: Optional[float]
    agreeableness: Optional[float]
    neuroticism: Optional[float]
    power_distance: Optional[float]
    individualism: Optional[float]
    masculinity: Optional[float]
    uncertainty_avoidance: Optional[float]
    long_term_orientation: Optional[float]
    indulgence: Optional[float]
    values: Optional[List[str]]
    interests: Optional[List[str]]
    background_story: Optional[str]
    created_at: datetime
    is_active: bool
    # RAG fields
    rag_context_used: bool = False
    rag_citations: Optional[List[Dict[str, Any]]] = None
    rag_context_details: Optional[Dict[str, Any]] = Field(
        None,
        description="Szczegółowe dane RAG (graph nodes, search type, enrichment info) - dla View Details"
    )

    class Config:
        from_attributes = True


# === ORCHESTRATION REASONING SCHEMAS ===

class GraphInsightResponse(BaseModel):
    """Pojedynczy insight z grafu wiedzy."""

    type: str = Field(description="Typ węzła (Wskaznik, Obserwacja, Trend, etc.)")
    summary: str = Field(description="Jednozdaniowe podsumowanie")
    magnitude: Optional[str] = Field(default=None, description="Wartość liczbowa jeśli istnieje (np. '78.4%')")
    confidence: str = Field(default="medium", description="Poziom pewności: high, medium, low")
    time_period: Optional[str] = Field(default=None, description="Okres czasu (np. '2022')")
    source: Optional[str] = Field(default=None, description="Źródło danych (np. 'GUS', 'CBOS')")
    why_matters: str = Field(description="Edukacyjne wyjaśnienie dlaczego to ważne")


class PersonaReasoningResponse(BaseModel):
    """Szczegółowe reasoning persony - dla zakładki 'Uzasadnienie' w UI.

    Zawiera:
    - orchestration_brief: DŁUGI (2000-3000 znaków) edukacyjny brief od Gemini 2.5 Pro
    - graph_insights: Lista wskaźników z Graph RAG z wyjaśnieniami
    - allocation_reasoning: Dlaczego tyle person w tej grupie demograficznej
    - overall_context: Ogólny kontekst społeczny Polski
    """

    orchestration_brief: Optional[str] = Field(
        None,
        description="Długi (2000-3000 znaków) edukacyjny brief od orchestration agent"
    )
    graph_insights: List[GraphInsightResponse] = Field(
        default_factory=list,
        description="Lista wskaźników z Graph RAG"
    )
    allocation_reasoning: Optional[str] = Field(
        None,
        description="Dlaczego tyle person w tej grupie"
    )
    demographics: Optional[Dict[str, Any]] = Field(
        None,
        description="Docelowa demografia tej grupy"
    )
    overall_context: Optional[str] = Field(
        None,
        description="Ogólny kontekst społeczny Polski (500-800 znaków)"
    )

    class Config:
        from_attributes = True
