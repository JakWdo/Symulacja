"""
Focus group and discussion services.

Serwisy odpowiedzialne za symulacje grup fokusowych i ich analizę:
- FocusGroupServiceLangChain - Orkiestracja dyskusji grup fokusowych
- DiscussionSummarizerService - AI-powered podsumowania dyskusji
- MemoryServiceLangChain - Event sourcing dla person (pamięć długoterminowa)
"""

from .discussion import FocusGroupServiceLangChain
from .summaries import DiscussionSummarizerService
from .memory import MemoryServiceLangChain

__all__ = [
    "FocusGroupServiceLangChain",
    "DiscussionSummarizerService",
    "MemoryServiceLangChain",
]
