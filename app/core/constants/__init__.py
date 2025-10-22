"""Constants package - personas and Polish-specific constants.

Ten moduł re-exportuje wszystkie stałe z podmodułów aby zachować
backward compatibility z istniejącym kodem.

Organizacja:
- personas.py - Global persona attributes (occupations, values, interests, styles)
- polish.py - Polish-specific constants for RAG system

UWAGA: US-based demographics (demographics.py) zostały usunięte w ramach refaktoryzacji
segment-based generation (2025-10-22). Generacja person opiera się teraz wyłącznie na
orchestration → RAG → LLM, bez target_demographics jako input.
"""

# Import persona attributes
from app.core.constants.personas import (
    DEFAULT_OCCUPATIONS,
    DEFAULT_VALUES,
    DEFAULT_INTERESTS,
    DEFAULT_COMMUNICATION_STYLES,
    DEFAULT_DECISION_STYLES,
    DEFAULT_LIFE_SITUATIONS,
)

# Import Polish constants
from app.core.constants.polish import (
    POLISH_LOCATIONS,
    POLISH_VALUES,
    POLISH_INTERESTS,
    POLISH_OCCUPATIONS,
    POLISH_MALE_NAMES,
    POLISH_FEMALE_NAMES,
    POLISH_SURNAMES,
    POLISH_COMMUNICATION_STYLES,
    POLISH_DECISION_STYLES,
    POLISH_INCOME_BRACKETS,
    POLISH_EDUCATION_LEVELS,
)

__all__ = [
    # Persona Attributes
    "DEFAULT_OCCUPATIONS",
    "DEFAULT_VALUES",
    "DEFAULT_INTERESTS",
    "DEFAULT_COMMUNICATION_STYLES",
    "DEFAULT_DECISION_STYLES",
    "DEFAULT_LIFE_SITUATIONS",
    # Polish Constants
    "POLISH_LOCATIONS",
    "POLISH_VALUES",
    "POLISH_INTERESTS",
    "POLISH_OCCUPATIONS",
    "POLISH_MALE_NAMES",
    "POLISH_FEMALE_NAMES",
    "POLISH_SURNAMES",
    "POLISH_COMMUNICATION_STYLES",
    "POLISH_DECISION_STYLES",
    "POLISH_INCOME_BRACKETS",
    "POLISH_EDUCATION_LEVELS",
]
