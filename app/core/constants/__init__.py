"""Constants package - demographics, personas, and Polish-specific constants.

Ten moduł re-exportuje wszystkie stałe z podmodułów aby zachować
backward compatibility z istniejącym kodem.

Organizacja:
- demographics.py - US-based demographic distributions
- personas.py - Global persona attributes (occupations, values, interests, styles)
- polish.py - Polish-specific constants for RAG system
"""

# Import US demographics
from app.core.constants.demographics import (
    DEFAULT_AGE_GROUPS,
    DEFAULT_GENDERS,
    DEFAULT_LOCATIONS,
    DEFAULT_EDUCATION_LEVELS,
    DEFAULT_INCOME_BRACKETS,
)

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
    # US Demographics
    "DEFAULT_AGE_GROUPS",
    "DEFAULT_GENDERS",
    "DEFAULT_LOCATIONS",
    "DEFAULT_EDUCATION_LEVELS",
    "DEFAULT_INCOME_BRACKETS",
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
