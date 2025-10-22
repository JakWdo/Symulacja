"""
Stałe demograficzne dla Sight.

Organizacja:
- polish_constants.py - Polskie dane demograficzne (imiona, miasta, zawody, wykształcenie)

Użycie:
    from app.core.demographics.polish_constants import POLISH_MALE_NAMES, POLISH_LOCATIONS

Uwaga: DEFAULT_* constants zostały usunięte - generacja person oparta na RAG + segment-based allocation.
"""

__all__ = [
    "polish_constants",
]
