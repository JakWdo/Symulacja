"""
Stałe demograficzne dla Sight.

Organizacja:
- polish_constants.py - Polskie dane demograficzne (imiona, miasta, zawody, wykształcenie)
- international_constants.py - Międzynarodowe wartości domyślne
- segment_definitions.py - Definicje segmentów społecznych

Użycie:
    from app.core.demographics.polish_constants import POLISH_MALE_NAMES, POLISH_LOCATIONS
    from app.core.demographics.international_constants import DEFAULT_AGE_GROUPS
"""

__all__ = [
    "polish_constants",
    "international_constants",
    "segment_definitions",
]
