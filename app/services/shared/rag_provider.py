"""
RAG Singleton Provider - Zapewnia jedną globalną instancję PolishSocietyRAG.

Problem (przed):
- PolishSocietyRAG inicjalizowany 4x w różnych serwisach
- 4x Redis connections, 4x CrossEncoder models (~3.6GB RAM)
- Wielokrotne HEAD requests do HuggingFace przy każdym cold start

Rozwiązanie (po):
- Jedna shared instance używana przez wszystkie serwisy
- 1x Redis connection, 1x CrossEncoder model (~900MB RAM)
- Oszczędność: ~2.7GB RAM + szybszy cold start

Usage:
    from app.services.shared.rag_provider import get_polish_society_rag

    rag = get_polish_society_rag()
    results = await rag.hybrid_search("query", top_k=5)
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.rag import PolishSocietyRAG

logger = logging.getLogger(__name__)

# Global singleton instance
_POLISH_RAG_INSTANCE: "PolishSocietyRAG | None" = None


def get_polish_society_rag() -> "PolishSocietyRAG":
    """
    Zwraca singleton instancję PolishSocietyRAG.

    Lazy initialization - tworzy instancję przy pierwszym wywołaniu,
    następnie zwraca tę samą instancję dla wszystkich kolejnych wywołań.

    Returns:
        PolishSocietyRAG: Shared instance RAG service

    Example:
        >>> rag = get_polish_society_rag()
        >>> results = await rag.hybrid_search("demografia Polski", top_k=5)
    """
    global _POLISH_RAG_INSTANCE

    if _POLISH_RAG_INSTANCE is None:
        logger.info("🔄 Initializing PolishSocietyRAG singleton (first call)")
        from app.services.rag import PolishSocietyRAG

        _POLISH_RAG_INSTANCE = PolishSocietyRAG()
        logger.info("✅ PolishSocietyRAG singleton initialized successfully")
    else:
        logger.debug("♻️  Reusing existing PolishSocietyRAG singleton")

    return _POLISH_RAG_INSTANCE


def reset_polish_society_rag() -> None:
    """
    Reset singleton instance - TYLKO dla testów!

    W testach potrzebujesz czystego stanu między test cases.
    NIE używaj w production code!

    Example (pytest):
        @pytest.fixture(autouse=True)
        def reset_rag():
            yield
            reset_polish_society_rag()
    """
    global _POLISH_RAG_INSTANCE
    _POLISH_RAG_INSTANCE = None
    logger.debug("🔄 PolishSocietyRAG singleton reset (test mode)")
