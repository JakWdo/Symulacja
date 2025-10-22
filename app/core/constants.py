"""Constants module - backward compatibility wrapper.

DEPRECATED: Ten plik jest przestarzały. Użyj bezpośrednio:
- from app.core.constants.demographics import ...
- from app.core.constants.personas import ...
- from app.core.constants.polish import ...

Lub importuj z package __init__:
- from app.core.constants import ...

Ten plik istnieje tylko dla backward compatibility z istniejącym kodem.
"""

# Re-export wszystkiego z nowej struktury folderów
from app.core.constants import *  # noqa: F401, F403

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
