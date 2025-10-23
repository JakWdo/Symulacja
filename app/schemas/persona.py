"""
Schematy Pydantic dla person (wersja v1)

Definiuje struktury danych dla:
- PersonaGenerateRequest - żądanie generowania person
- PersonaGenerationAdvancedOptions - zaawansowane opcje targetowania
- PersonaResponse - odpowiedź API z danymi persony

Uwaga: To jest wersja v1. Nowsze projekty powinny używać persona_v2.py
"""

import re
from typing import Literal, Any
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, validator
from app.schemas.rag import RAGCitation


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
    age_focus: Literal['balanced', 'young_adults', 'experienced_leaders'] | None = None
    gender_balance: Literal['balanced', 'female_skew', 'male_skew'] | None = None
    urbanicity: Literal['any', 'urban', 'suburban', 'rural'] | None = None
    target_cities: list[str] | None = None
    target_countries: list[str] | None = None
    industries: list[str] | None = None
    required_values: list[str] | None = None
    excluded_values: list[str] | None = None
    required_interests: list[str] | None = None
    excluded_interests: list[str] | None = None
    age_min: int | None = Field(None, ge=18, le=90)
    age_max: int | None = Field(None, ge=18, le=90)
    custom_age_groups: dict[str, float] | None = Field(
        None,
        description="Custom age group distribution, e.g., {'18-22': 0.3, '23-29': 0.4, '30-40': 0.3}"
    )
    gender_weights: dict[str, float] | None = Field(
        None,
        description="Custom gender distribution weights"
    )
    location_weights: dict[str, float] | None = Field(
        None,
        description="Custom location distribution weights"
    )
    education_weights: dict[str, float] | None = Field(
        None,
        description="Custom education level distribution weights"
    )
    income_weights: dict[str, float] | None = Field(
        None,
        description="Custom income bracket distribution weights"
    )
    personality_skew: dict[str, float] | None = Field(
        None,
        description="Skew Big Five personality traits (openness, conscientiousness, extraversion, agreeableness, neuroticism). Values 0.0-1.0 shift mean towards low/high."
    )

    # === FRONTEND UI OPTIONS (z PersonaGenerationWizard) ===
    # Te pola są wysyłane przez frontend ale były ignorowane przez backend!

    focus_area: str | None = Field(
        None,
        description="Area of interest from UI dropdown: technology, lifestyle, finance, shopping, entertainment, general. Used to enforce persona interests."
    )

    demographic_preset: str | None = Field(
        None,
        description="Demographic preset from UI dropdown: gen-z, millennials, gen-x, boomers, diverse. Provides additional age/generation context."
    )

    target_audience_description: str | None = Field(
        None,
        description="Additional description of target audience from UI textarea (user-provided text). High priority in prompt context."
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
    advanced_options: PersonaGenerationAdvancedOptions | None = Field(
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
    location: str | None
    education_level: str | None
    income_bracket: str | None
    occupation: str | None
    full_name: str | None
    persona_title: str | None
    headline: str | None
    openness: float | None
    conscientiousness: float | None
    extraversion: float | None
    agreeableness: float | None
    neuroticism: float | None
    power_distance: float | None
    individualism: float | None
    masculinity: float | None
    uncertainty_avoidance: float | None
    long_term_orientation: float | None
    indulgence: float | None
    values: list[str] | None
    interests: list[str] | None
    background_story: str | None
    created_at: datetime
    is_active: bool
    # RAG fields
    rag_context_used: bool = False
    rag_citations: list[RAGCitation] | None = Field(
        None,
        description="Lista cytowań z bazy wiedzy RAG (zgodne z RAGCitation schema)"
    )
    rag_context_details: dict[str, Any] | None = Field(
        None,
        description="Szczegółowe dane RAG (graph nodes, search type, enrichment info) - dla View Details"
    )

    @validator('occupation', 'full_name', 'location', 'headline', 'persona_title', pre=True)
    def sanitize_single_line_fields(cls, v):
        """
        Validator Pydantic do sanityzacji pól jednoliniowych

        Usuwa nadmiarowe znaki nowej linii i białe znaki z pól tekstowych.
        Zapobiega wyświetlaniu "Zawód\\n\\nJuż" w UI.

        Args:
            v: Wartość pola do sanityzacji

        Returns:
            Zsanityzowana wartość (wszystkie \\n zamienione na spacje)
        """
        if isinstance(v, str):
            # Usuń wszystkie \\n i znormalizuj spacje
            return re.sub(r'\s+', ' ', v).strip()
        return v

    @validator('background_story', pre=True)
    def sanitize_background_story(cls, v):
        """
        Validator Pydantic do sanityzacji background_story

        Zachowuje podział na akapity (\\n\\n) ale normalizuje każdy akapit.

        Args:
            v: Wartość pola do sanityzacji

        Returns:
            Zsanityzowana wartość z zachowanymi podziałami akapitów
        """
        if isinstance(v, str):
            # Zachowaj podział na akapity ale znormalizuj każdy akapit
            paragraphs = v.split('\n')
            paragraphs = [re.sub(r'\s+', ' ', p).strip() for p in paragraphs if p.strip()]
            return '\n\n'.join(paragraphs)
        return v

    class Config:
        from_attributes = True


# === SEGMENT-BASED ARCHITECTURE SCHEMAS ===

class DemographicConstraints(BaseModel):
    """
    HARD constraints dla generowania person w ramach segmentu.

    Te constraints są WYMUSZANE przez generator - persona musi pasować do tych bounds.
    Używane przez SegmentDefinition do zapewnienia spójności persona ↔ segment.
    """
    age_min: int = Field(ge=18, le=100, description="Minimalny wiek (18-100)")
    age_max: int = Field(ge=18, le=100, description="Maksymalny wiek (18-100)")
    gender: str = Field(description="Płeć: 'female', 'male', 'non-binary'")
    education_levels: list[str] = Field(min_items=1, description="Dozwolone poziomy wykształcenia")
    income_brackets: list[str] = Field(min_items=1, description="Dozwolone przedziały dochodowe")
    locations: list[str] | None = Field(None, description="Dozwolone lokalizacje (None = any)")

    @validator('age_max')
    def age_max_greater_than_min(cls, v, values):
        """Walidacja: age_max musi być >= age_min."""
        if 'age_min' in values and v < values['age_min']:
            raise ValueError(f'age_max ({v}) must be >= age_min ({values["age_min"]})')
        return v

    @validator('gender')
    def validate_gender(cls, v):
        """Walidacja: gender musi być jednym z dozwolonych wartości."""
        allowed = ['female', 'male', 'non-binary', 'kobieta', 'mężczyzna']
        if v.lower() not in allowed:
            raise ValueError(f'gender must be one of {allowed}, got: {v}')
        return v


class RAGCitationQuality(BaseModel):
    """
    High-quality RAG citation z filtrowaniem.

    Tylko cytaty o confidence > 0.7 i relevance 'high' lub 'medium'.
    Usunięte dziwne metryki (np. relevance -412%).
    """
    source: str = Field(description="Źródło dokumentu (np. 'GUS_Rynek_Pracy_2024')")
    content: str = Field(max_length=500, description="Treść cytatu (max 500 znaków)")
    year: int | None = Field(None, ge=2000, le=2030, description="Rok danych (2000-2030)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    relevance: str = Field(description="Relevance: 'high' lub 'medium' (nie 'low')")

    @validator('relevance')
    def validate_relevance(cls, v):
        """Walidacja: relevance tylko 'high' lub 'medium'."""
        allowed = ['high', 'medium']
        if v.lower() not in allowed:
            raise ValueError(f'relevance must be "high" or "medium", got: {v}')
        return v


class SegmentDefinition(BaseModel):
    """
    Structured definition segmentu demograficznego.

    Każdy segment ma:
    - Unikalną nazwę (LLM-generated, np. "Młodzi Prekariusze")
    - HARD demographic constraints (wymuszane przez generator)
    - Indywidualny kontekst społeczny (500-800 znaków)
    - Per-segment graph insights i RAG citations
    - Persona count (ile person w tym segmencie)

    To jest "contract" między orchestration a generator - zapewnia spójność.
    """
    segment_id: str = Field(
        pattern="^seg_[a-z0-9_]+$",
        description="Unikalny ID segmentu (np. 'seg_young_precariat')"
    )
    segment_name: str = Field(
        min_length=5,
        max_length=60,
        description="Mówiąca nazwa segmentu (np. 'Młodzi Prekariusze', 'Aspirujące Profesjonalistki 35-44')"
    )
    segment_description: str | None = Field(
        None,
        max_length=300,
        description="Krótki opis segmentu (1-2 zdania)"
    )
    demographics: DemographicConstraints = Field(description="HARD constraints dla person")
    segment_context: str = Field(
        min_length=400,
        max_length=1200,
        description="Kontekst społeczny dla TEJ grupy (500-800 znaków typowo)"
    )
    graph_insights: list["GraphInsightResponse"] = Field(
        default_factory=list,
        description="Graph insights filtrowane dla tego segmentu"
    )
    rag_citations: list[RAGCitationQuality] = Field(
        default_factory=list,
        max_items=10,
        description="Top 10 high-quality RAG citations"
    )
    persona_count: int = Field(ge=1, description="Liczba person do wygenerowania w tym segmencie")
    persona_brief: str = Field(
        min_length=200,
        max_length=800,
        description="Instructions dla LLM generującego persony (dlaczego ten segment ważny)"
    )


# === ORCHESTRATION REASONING SCHEMAS ===

class GraphInsightResponse(BaseModel):
    """Pojedynczy insight z grafu wiedzy.

    UWAGA: Ten schema używa ANGIELSKICH property names dla API backward compatibility.
    Dane w grafie Neo4j używają POLSKICH nazw (streszczenie, skala, pewnosc, etc.).

    Mapowanie (wykonywane przez _map_graph_node_to_insight() w persona_orchestration.py):
    - streszczenie → summary
    - skala → magnitude
    - pewnosc → confidence ("wysoka"→"high", "srednia"→"medium", "niska"→"low")
    - okres_czasu → time_period
    - kluczowe_fakty → why_matters (z dodatkowym kontekstem)
    """

    type: str = Field(description="Typ węzła (Wskaznik, Obserwacja, Trend, etc.)")
    summary: str = Field(description="Jednozdaniowe podsumowanie")
    magnitude: str | None = Field(default=None, description="Wartość liczbowa jeśli istnieje (np. '78.4%')")
    confidence: str = Field(default="medium", description="Poziom pewności: high, medium, low")
    time_period: str | None = Field(default=None, description="Okres czasu (np. '2022')")
    source: str | None = Field(default=None, description="Źródło danych (np. 'GUS', 'CBOS')")
    why_matters: str = Field(description="Edukacyjne wyjaśnienie dlaczego to ważne")


class PersonaReasoningResponse(BaseModel):
    """Szczegółowe reasoning persony - dla zakładki 'Uzasadnienie' w UI.

    **NOWE POLA (segment-based architecture):**
    - segment_name: Mówiąca nazwa segmentu (np. "Młodzi Prekariusze")
    - segment_id: Unikalny ID segmentu
    - segment_description: Krótki opis segmentu (1-2 zdania)
    - segment_social_context: Kontekst społeczny dla TEJ grupy (500-800 znaków)

    **LEGACY POLA (deprecated, zachowane dla backward compatibility):**
    - orchestration_brief: Użyj zamiast tego persona_brief z SegmentDefinition
    - overall_context: Użyj zamiast tego segment_social_context

    **AKTUALNE POLA:**
    - graph_insights: Lista wskaźników z Graph RAG
    - allocation_reasoning: Dlaczego tyle person w tej grupie
    - demographics: Docelowa demografia tej grupy
    """

    # === NOWE POLA (segment-based) ===
    segment_name: str | None = Field(
        None,
        description="Mówiąca nazwa segmentu (np. 'Młodzi Prekariusze', 'Aspirujące Profesjonalistki 35-44')"
    )
    segment_id: str | None = Field(
        None,
        description="Unikalny ID segmentu (np. 'seg_young_precariat')"
    )
    segment_description: str | None = Field(
        None,
        description="Krótki opis segmentu (1-2 zdania)"
    )
    segment_social_context: str | None = Field(
        None,
        description="Kontekst społeczny dla TEJ grupy demograficznej (500-800 znaków)"
    )
    segment_characteristics: list[str] | None = Field(
        None,
        description="4-6 kluczowych cech segmentu (np. ['Profesjonaliści z wielkich miast', 'Wysoko wykształceni'])"
    )

    # === LEGACY POLA (dla kompatybilności wstecznej) ===
    orchestration_brief: str | None = Field(
        None,
        description="Legacy brief wygenerowany przez orchestration agent (900-1200 znaków)"
    )
    overall_context: str | None = Field(
        None,
        description="Ogólny kontekst społeczny Polski (legacy pole - preferuj segment_social_context)"
    )

    # === AKTUALNE POLA ===
    graph_insights: list[GraphInsightResponse] = Field(
        default_factory=list,
        description="Lista wskaźników z Graph RAG"
    )
    allocation_reasoning: str | None = Field(
        None,
        description="Dlaczego tyle person w tej grupie"
    )
    demographics: dict[str, Any] | None = Field(
        None,
        description="Docelowa demografia tej grupy"
    )

    class Config:
        from_attributes = True
