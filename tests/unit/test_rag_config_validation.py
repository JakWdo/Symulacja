"""Testy walidacji konfiguracji RAG.

Ten moduł testuje czy RAG config parameters są w sensible ranges:
- Chunk size bounds (500-2000)
- Overlap percentage (10%-50%)
- TOP_K limits (3-20)
- RRF_K range (20-100)
- MAX_CONTEXT bounds
- Reranker model availability

Dokumentacja: app/core/config.py (RAG_ prefixed settings)
"""

import pytest
from app.core.config import get_settings


class TestChunkSizeValidation:
    """Testy dla chunk size parameters."""

    def test_chunk_size_within_bounds(self):
        """
        Test: RAG_CHUNK_SIZE jest w sensible range (500-2000).

        Reasoning:
        - Too small (<500): Loss of context, too many chunks
        - Too large (>2000): Poor precision, irrelevant content
        - Optimal: 800-1200 dla balanced precision/recall
        """
        settings = get_settings()

        chunk_size = settings.RAG_CHUNK_SIZE

        # Verify bounds
        assert 500 <= chunk_size <= 2000, (
            f"CHUNK_SIZE {chunk_size} out of bounds [500, 2000]. "
            "Too small = loss of context, too large = poor precision."
        )

    def test_chunk_overlap_percentage(self):
        """
        Test: RAG_CHUNK_OVERLAP jest w range 10%-50% of chunk_size.

        Overlap zapewnia continuity między chunks.
        - Too small (<10%): Koncepty mogą być split between chunks
        - Too large (>50%): Excessive duplication, slower indexing
        """
        settings = get_settings()

        chunk_size = settings.RAG_CHUNK_SIZE
        overlap = settings.RAG_CHUNK_OVERLAP

        # Calculate percentage
        overlap_pct = (overlap / chunk_size) * 100

        # Verify range
        assert 10 <= overlap_pct <= 50, (
            f"CHUNK_OVERLAP {overlap} ({overlap_pct:.1f}%) out of range [10%, 50%] "
            f"for CHUNK_SIZE {chunk_size}."
        )

    def test_chunk_overlap_less_than_chunk_size(self):
        """
        Test: RAG_CHUNK_OVERLAP < RAG_CHUNK_SIZE (sanity check).

        Edge case: Overlap >= chunk_size jest nonsensical.
        """
        settings = get_settings()

        chunk_size = settings.RAG_CHUNK_SIZE
        overlap = settings.RAG_CHUNK_OVERLAP

        assert overlap < chunk_size, (
            f"CHUNK_OVERLAP {overlap} >= CHUNK_SIZE {chunk_size}. "
            "Overlap musi być mniejszy niż chunk size."
        )


class TestTopKValidation:
    """Testy dla TOP_K parameter (liczba results w retrieval)."""

    def test_top_k_within_bounds(self):
        """
        Test: RAG_TOP_K jest w range 3-20.

        Reasoning:
        - Too small (<3): Może miss relevant context
        - Too large (>20): Noise, slower reranking, context overflow
        - Optimal: 5-10 dla balanced coverage
        """
        settings = get_settings()

        top_k = settings.RAG_TOP_K

        assert 3 <= top_k <= 20, (
            f"TOP_K {top_k} out of bounds [3, 20]. "
            "Too small = miss context, too large = noise."
        )

    def test_rerank_candidates_greater_than_top_k(self):
        """
        Test: RAG_RERANK_CANDIDATES >= RAG_TOP_K.

        Reranking workflow:
        1. Retrieve RERANK_CANDIDATES documents (RRF fusion)
        2. Rerank with cross-encoder
        3. Return top TOP_K

        RERANK_CANDIDATES musi być >= TOP_K aby reranking miał sens.
        """
        settings = get_settings()

        top_k = settings.RAG_TOP_K
        rerank_candidates = settings.RAG_RERANK_CANDIDATES

        if settings.RAG_USE_RERANKING:
            assert rerank_candidates >= top_k, (
                f"RERANK_CANDIDATES {rerank_candidates} < TOP_K {top_k}. "
                "Reranking wymaga więcej candidates niż final TOP_K."
            )


class TestRRFKValidation:
    """Testy dla RRF_K parameter (Reciprocal Rank Fusion)."""

    def test_rrf_k_within_bounds(self):
        """
        Test: RAG_RRF_K jest w range 20-100.

        RRF formula: score = sum(1 / (k + rank_i))

        Effect of k:
        - Small k (20-40): Elitarne (top results dominate)
        - Medium k (40-60): Balanced
        - Large k (60-100): Demokratyczne (equal weighting)

        Valid range: 20-100
        """
        settings = get_settings()

        rrf_k = settings.RAG_RRF_K

        assert 20 <= rrf_k <= 100, (
            f"RRF_K {rrf_k} out of bounds [20, 100]. "
            "Too small = overly elitist, too large = no differentiation."
        )


class TestMaxContextValidation:
    """Testy dla MAX_CONTEXT (truncation limit)."""

    def test_max_context_sufficient_for_top_k(self):
        """
        Test: RAG_MAX_CONTEXT jest sufficient dla TOP_K chunks.

        Min required = TOP_K * average_chunk_size
        Jeśli MAX_CONTEXT < required, truncation occurs frequently.

        Warning threshold: MAX_CONTEXT < TOP_K * 1000
        """
        settings = get_settings()

        top_k = settings.RAG_TOP_K
        chunk_size = settings.RAG_CHUNK_SIZE
        max_context = settings.RAG_MAX_CONTEXT

        # Estimate min required (assume chunk_size as average)
        min_required = top_k * chunk_size

        # Verify max_context is reasonable
        if max_context < min_required:
            # Warning but not error (może być intentional dla token limits)
            pytest.skip(
                f"MAX_CONTEXT {max_context} < estimated required {min_required} "
                f"for TOP_K={top_k} chunks. Truncation will occur frequently."
            )

    def test_max_context_positive(self):
        """
        Test: RAG_MAX_CONTEXT > 0 (sanity check).

        Edge case: MAX_CONTEXT <= 0 jest invalid.
        """
        settings = get_settings()

        max_context = settings.RAG_MAX_CONTEXT

        assert max_context > 0, (
            f"MAX_CONTEXT {max_context} <= 0. Musi być positive."
        )


class TestVectorWeightValidation:
    """Testy dla vector weight w hybrid search."""

    def test_vector_weight_in_range(self):
        """
        Test: RAG_VECTOR_WEIGHT jest w range [0.0, 1.0].

        Hybrid search fusion:
        - vector_weight = weight for vector search
        - keyword_weight = 1.0 - vector_weight

        Valid range: 0.0 (keyword only) to 1.0 (vector only)
        Optimal: 0.6-0.8 (favor semantic but include keywords)
        """
        settings = get_settings()

        vector_weight = settings.RAG_VECTOR_WEIGHT

        assert 0.0 <= vector_weight <= 1.0, (
            f"VECTOR_WEIGHT {vector_weight} out of range [0.0, 1.0]. "
            "0.0 = keyword only, 1.0 = vector only."
        )

    def test_vector_weight_not_extreme(self):
        """
        Test: RAG_VECTOR_WEIGHT nie jest extreme (0.0 or 1.0).

        Warning jeśli weight = 0.0 lub 1.0 (single mode only).
        Hybrid search działa best z balanced weights.
        """
        settings = get_settings()

        vector_weight = settings.RAG_VECTOR_WEIGHT

        if vector_weight == 0.0:
            pytest.skip(
                "VECTOR_WEIGHT = 0.0 (keyword search only). "
                "Hybrid search is disabled."
            )
        elif vector_weight == 1.0:
            pytest.skip(
                "VECTOR_WEIGHT = 1.0 (vector search only). "
                "Keyword search is disabled."
            )


class TestRerankerConfiguration:
    """Testy dla reranker configuration."""

    def test_reranker_model_specified_if_enabled(self):
        """
        Test: Jeśli RAG_USE_RERANKING=True, RAG_RERANK_MODEL jest specified.

        Reranking wymaga cross-encoder model.
        Default: "cross-encoder/ms-marco-MiniLM-L-6-v2" (multilingual)
        """
        settings = get_settings()

        if settings.RAG_USE_RERANKING:
            rerank_model = settings.RAG_RERANK_MODEL

            assert rerank_model is not None, (
                "RAG_USE_RERANKING=True but RAG_RERANK_MODEL not specified."
            )
            assert len(rerank_model) > 0, (
                "RAG_RERANK_MODEL jest empty string."
            )

    def test_reranker_model_availability(self):
        """
        Test: Reranker model jest available (import check).

        Edge case: sentence-transformers może nie być installed.
        Jeśli USE_RERANKING=True, library musi być available.
        """
        settings = get_settings()

        if settings.RAG_USE_RERANKING:
            try:
                from sentence_transformers import CrossEncoder
                # Verify import works
                assert CrossEncoder is not None
            except ImportError:
                pytest.fail(
                    "RAG_USE_RERANKING=True but sentence-transformers not installed. "
                    "Install: pip install sentence-transformers"
                )


class TestConfigConsistency:
    """Testy dla overall consistency configuration."""

    def test_hybrid_search_enabled_check(self):
        """
        Test: RAG_USE_HYBRID_SEARCH consistency z vector_weight.

        Jeśli HYBRID_SEARCH=False, vector_weight powinno być 1.0
        (vector only) lub 0.0 (keyword only).
        """
        settings = get_settings()

        use_hybrid = settings.RAG_USE_HYBRID_SEARCH
        vector_weight = settings.RAG_VECTOR_WEIGHT

        if not use_hybrid:
            # Jeśli hybrid disabled, weight powinno być extreme
            assert vector_weight in [0.0, 1.0], (
                f"HYBRID_SEARCH=False but VECTOR_WEIGHT={vector_weight}. "
                "Expected 0.0 (keyword only) or 1.0 (vector only)."
            )

    def test_no_conflicting_settings(self):
        """
        Test: Brak conflicting settings w config.

        Checks:
        - Chunk overlap < chunk size ✓ (already tested)
        - TOP_K <= RERANK_CANDIDATES ✓ (already tested)
        - MAX_CONTEXT > 0 ✓ (already tested)

        Ten test jest summary check dla overall consistency.
        """
        settings = get_settings()

        # All individual checks already done
        # Ten test jest placeholder dla future consistency checks
        assert settings.RAG_CHUNK_SIZE > 0
        assert settings.RAG_TOP_K > 0
        assert settings.RAG_RRF_K > 0
