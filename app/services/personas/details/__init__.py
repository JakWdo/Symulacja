"""
Persona Details Module

Moduły odpowiedzialne za szczegóły i enrichment person:
- PersonaDetailsService - Główny serwis orchestrujący persona details
- Details CRUD - Operacje CRUD na szczegółach person
- DetailsEnrichment - Wzbogacanie szczegółów person (Journey, JTBD, etc.)
"""

from .persona_details_service import PersonaDetailsService

__all__ = [
    "PersonaDetailsService",
]
