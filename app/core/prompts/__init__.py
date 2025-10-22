"""
Scentralizowane prompty systemowe dla Sight.

Organizacja:
- persona_prompts.py - Prompty dla generowania person, JTBD, segmentów
- focus_group_prompts.py - Prompty dla orkiestracji grup fokusowych
- rag_prompts.py - Prompty dla RAG, ekstrakcji wiedzy, graph queries
- system_prompts.py - Wspólne system prompty używane w wielu miejscach

Użycie:
    from app.core.prompts.persona_prompts import JTBD_ANALYSIS_PROMPT
    from app.core.prompts.focus_group_prompts import MODERATOR_SYSTEM_PROMPT
"""

__all__ = [
    "persona_prompts",
    "focus_group_prompts",
    "rag_prompts",
    "system_prompts",
]
