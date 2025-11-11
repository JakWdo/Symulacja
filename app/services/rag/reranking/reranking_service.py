"""Cross-encoder reranking dla hybrid search results.

Cross-encoder używa attention mechanism aby precyzyjnie ocenić pary (query, document),
co daje lepszą precision niż bi-encoder używany w vector search.
"""

import asyncio
import logging
import time
from typing import List, Tuple
from functools import partial

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


async def rerank_with_cross_encoder(
    query: str,
    candidates: List[Tuple[Document, float]],
    reranker_model,
    top_k: int = 5
) -> List[Tuple[Document, float]]:
    """Użyj cross-encoder aby precyzyjnie re-score query-document pairs.

    Cross-encoder ma attention mechanism który widzi query i document razem,
    co daje lepszą precision niż bi-encoder (używany w vector search).

    Args:
        query: Query użytkownika
        candidates: Lista (Document, RRF_score) par z RRF fusion
        reranker_model: Cross-encoder model instance
        top_k: Liczba top wyników do zwrócenia

    Returns:
        Lista (Document, rerank_score) sorted by rerank_score descending
    """
    if not reranker_model or not candidates:
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
            reranker_model.predict,
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
