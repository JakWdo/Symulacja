"""
Serwisy szczegółów person (Persona Details MVP)

Ten moduł zawiera serwisy do:
- Orkiestracji widoku szczegółów (details_service.py)
- Analizy potrzeb - JTBD (needs.py)

Archived:
- Generowania messaging (messaging.py) - przeniesiony do app/services/archived/
"""

from app.services.personas_details.details_service import PersonaDetailsService
from app.services.personas_details.needs import PersonaNeedsService

__all__ = [
    "PersonaDetailsService",
    "PersonaNeedsService",
]
