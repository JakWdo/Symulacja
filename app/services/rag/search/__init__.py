"""Search modules dla hybrid RAG - keyword search, Lucene utils, RRF fusion."""

from .cache import (
    get_hybrid_search_cache_key,
    get_hybrid_cache,
    set_hybrid_cache,
    CACHE_TTL_SECONDS,
)
from .keyword_search import keyword_search, ensure_fulltext_index
from .lucene_utils import sanitize_lucene_query
from .fusion_algorithms import rrf_fusion
from .reranker import init_reranker, rerank_with_cross_encoder
from .graph_enrichment import (
    format_graph_context,
    find_related_graph_nodes,
    enrich_chunk_with_graph,
)
from .hybrid_search_service import PolishSocietyRAG

__all__ = [
    # Cache
    "get_hybrid_search_cache_key",
    "get_hybrid_cache",
    "set_hybrid_cache",
    "CACHE_TTL_SECONDS",
    # Keyword search
    "keyword_search",
    "ensure_fulltext_index",
    # Lucene utils
    "sanitize_lucene_query",
    # Fusion
    "rrf_fusion",
    # Reranking
    "init_reranker",
    "rerank_with_cross_encoder",
    # Graph enrichment
    "format_graph_context",
    "find_related_graph_nodes",
    "enrich_chunk_with_graph",
    # Main service
    "PolishSocietyRAG",
]
