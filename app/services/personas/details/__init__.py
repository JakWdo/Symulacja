"""
Persona Details Module

Moduły odpowiedzialne za szczegóły i enrichment person:
- PersonaDetailsService - Główny serwis orchestrujący persona details
- Details CRUD - Operacje CRUD na szczegółach person
- DetailsEnrichment - Wzbogacanie szczegółów person (Journey, JTBD, etc.)
"""

from .persona_details_service import PersonaDetailsService
from .details_crud import (
    get_persona_details,
    create_persona_details,
    update_persona_details,
    delete_persona_details,
)
from .details_enrichment import (
    generate_customer_journey,
    generate_pain_points,
    generate_jtbd_motivations,
)

__all__ = [
    "PersonaDetailsService",
    # CRUD
    "get_persona_details",
    "create_persona_details",
    "update_persona_details",
    "delete_persona_details",
    # Enrichment
    "generate_customer_journey",
    "generate_pain_points",
    "generate_jtbd_motivations",
]
