"""
Focus group and discussion services.

Serwisy odpowiedzialne za symulacje grup fokusowych i ich analizę:
- FocusGroupServiceLangChain - Orkiestracja dyskusji grup fokusowych
- DiscussionSummarizerService - AI-powered podsumowania dyskusji
- MemoryServiceLangChain - Event sourcing dla person (pamięć długoterminowa)
"""

from .focus_group_service_langchain import FocusGroupServiceLangChain
from .discussion_summarizer import DiscussionSummarizerService
from .memory_service_langchain import MemoryServiceLangChain

__all__ = [
    "FocusGroupServiceLangChain",
    "DiscussionSummarizerService",
    "MemoryServiceLangChain",
]
