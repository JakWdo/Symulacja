"""Reciprocal Rank Fusion (RRF) algorithm dla łączenia wyników wyszukiwania.

RRF to algorytm fuzji który łączy rankingi z różnych źródeł (vector + keyword search)
używając wzoru: score = sum(1 / (k + rank)) gdzie k=60 (domyślnie).
"""

import logging
from typing import List, Tuple, Union

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def rrf_fusion(
    vector_results: List[Tuple[Document, float]],
    keyword_results: List[Union[Document, Tuple[Document, float]]],
    k: int = 60,
) -> List[Tuple[Document, float]]:
    """Łączy wyniki vector i keyword search przy pomocy Reciprocal Rank Fusion.
    
    Args:
        vector_results: List of (Document, score) from vector search
        keyword_results: List of Document or (Document, score) from keyword search
        k: RRF constant (default 60)
        
    Returns:
        Fused list of (Document, fused_score) sorted by score desc
    """
    scores: dict[int, float] = {}
    doc_map: dict[int, Tuple[Document, float]] = {}

    # Process vector results
    for rank, (doc, original_score) in enumerate(vector_results):
        doc_hash = hash(doc.page_content)
        scores[doc_hash] = scores.get(doc_hash, 0.0) + 1.0 / (k + rank + 1)
        doc_map[doc_hash] = (doc, original_score)

    # Process keyword results
    for rank, item in enumerate(keyword_results):
        if isinstance(item, tuple):
            doc, keyword_score = item
        else:
            doc, keyword_score = item, 0.0

        doc_hash = hash(doc.page_content)
        scores[doc_hash] = scores.get(doc_hash, 0.0) + 1.0 / (k + rank + 1)
        if doc_hash not in doc_map:
            doc_map[doc_hash] = (doc, keyword_score)

    # Sort by fused score
    fused = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [(doc_map[doc_hash][0], fused_score) for doc_hash, fused_score in fused]
