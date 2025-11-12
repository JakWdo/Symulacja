"""Cross-encoder reranking dla hybrid search results.

Moduł odpowiada za:
- Inicjalizację cross-encoder modelu (sentence-transformers)
- Reranking candidates używając attention mechanism
- Async offload do thread pool (CPU-bound task)
- Timeout protection (15s max)
"""

import asyncio
import logging
import time
from functools import partial
from typing import Optional

from langchain_core.documents import Document

from config import rag

logger = logging.getLogger(__name__)


def init_reranker() -> Optional[any]:
    """Inicjalizuj cross-encoder dla reranking (opcjonalny).

    Returns:
        CrossEncoder instance lub None jeśli disabled/failed
    """
    if not rag.retrieval.use_reranking:
        return None

    try:
        from sentence_transformers import CrossEncoder
        reranker = CrossEncoder(
            rag.retrieval.reranker_model,
            max_length=512
        )
        logger.info(
            "Cross-encoder reranker zainicjalizowany: %s",
            rag.retrieval.reranker_model
        )
        return reranker
    except ImportError:
        logger.warning(
            "sentence-transformers nie jest zainstalowany - reranking wyłączony. "
            "Zainstaluj: pip install sentence-transformers"
        )
        return None
    except Exception as rerank_exc:
        logger.warning(
            "Nie udało się załadować reranker: %s - kontynuacja bez rerankingu",
            rerank_exc
        )
        return None


async def rerank_with_cross_encoder(
    query: str,
    candidates: list[tuple[Document, float]],
    reranker: Optional[any],
    top_k: int = 5
) -> list[tuple[Document, float]]:
    """Użyj cross-encoder aby precyzyjnie re-score query-document pairs.

    Cross-encoder ma attention mechanism który widzi query i document razem,
    co daje lepszą precision niż bi-encoder (używany w vector search).

    Args:
        query: Query użytkownika
        candidates: Lista (Document, RRF_score) par z RRF fusion
        reranker: CrossEncoder instance (or None if disabled)
        top_k: Liczba top wyników do zwrócenia

    Returns:
        Lista (Document, rerank_score) sorted by rerank_score descending
    """
    if not reranker or not candidates:
        logger.info("Reranker niedostępny lub brak candidates - skip reranking")
        return candidates[:top_k]

    try:
        rerank_start = time.perf_counter()

        # Przygotuj pary (query, document) dla cross-encoder
        pairs = [(query, doc.page_content[:512]) for doc, _ in candidates]
        # Limit do 512 znaków dla cross-encoder (max_length)

        # Cross-encoder prediction - ASYNC offload to thread pool (CPU-bound task)
        # Prevents blocking event loop and disables noisy tqdm progress bar
        predict_fn = partial(
            reranker.predict,
            pairs,
            show_progress_bar=False,
            batch_size=16,
            num_workers=0,
        )

        # Safety timeout: if reranking is abnormally slow, fall back to RRF
        try:
            scores = await asyncio.wait_for(
                asyncio.to_thread(predict_fn),
                timeout=15.0,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "⏱️ Reranker timed out after 15s – using RRF scores"
            )
            return candidates[:top_k]

        # Połącz dokumenty z nowymi scores
        reranked = list(zip([doc for doc, _ in candidates], scores))

        # Sortuj po cross-encoder score (descending)
        reranked.sort(key=lambda x: x[1], reverse=True)

        rerank_duration = time.perf_counter() - rerank_start
        logger.info(
            "✅ Reranking completed: %s candidates → top %s results (%.2fs)",
            len(candidates),
            top_k,
            rerank_duration
        )

        return reranked[:top_k]

    except Exception as exc:
        logger.error("❌ Reranking failed: %s - fallback to RRF ranking", exc)
        return candidates[:top_k]
