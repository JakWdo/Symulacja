"""
Features Loader - Feature flags and system configuration.

Ten moduł dostarcza:
- RagFeatures: Feature flags dla systemu RAG
- SegmentCacheFeatures: Konfiguracja segment-first cache
- PerformanceConfig: Progi wydajnościowe i timeouty
- FeaturesConfig: Singleton łączący wszystkie feature flags

Użycie:
    from config import features

    # RAG
    if features.rag.enabled:
        use_graph_rag = features.rag.node_properties_enabled

    # Segment Cache
    if features.segment_cache.enabled:
        ttl = features.segment_cache.ttl_days

    # Performance
    max_time = features.performance.max_response_time_per_persona
"""

import logging
from dataclasses import dataclass

from config.loader import ConfigLoader

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# DATACLASSES - FEATURE FLAGS
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class RagFeatures:
    """
    Feature flags dla systemu RAG (Retrieval-Augmented Generation).

    Attributes:
        enabled: Globalny toggle dla systemu RAG
        node_properties_enabled: Włącz właściwości węzłów w GraphRAG
        extract_summaries: Ekstraktuj podsumowania z dokumentów
        extract_key_facts: Ekstraktuj kluczowe fakty
        relationship_confidence: Dodaj confidence score do relacji
    """
    enabled: bool = True
    node_properties_enabled: bool = True
    extract_summaries: bool = True
    extract_key_facts: bool = True
    relationship_confidence: bool = True


@dataclass
class SegmentCacheFeatures:
    """
    Feature flags dla segment-first cache.

    Benefits: 3x szybsze, 60% mniej tokenów, lepsza spójność.
    Rollback: Ustaw enabled=False aby wrócić do per-persona RAG.

    Attributes:
        enabled: Włącz segment-first cache
        ttl_days: TTL cache w dniach (Redis)
    """
    enabled: bool = True
    ttl_days: int = 7


@dataclass
class OrchestrationFeatures:
    """
    Feature flags dla persona orchestration.

    Benefits:
    - Długie briefe (900-1200 chars) dla każdego demographic group
    - Graph RAG insights (3-5 insights per group)
    - Segment characteristics (4-6 kluczowych cech)
    - Allocation reasoning (dlaczego tyle person w grupie)

    Trade-off: ~10-20s latency z cachingiem (vs 2-5s basic generation)
    Rollback: Ustaw enabled=False aby wrócić do basic generation

    Attributes:
        enabled: Włącz persona orchestration z Gemini 2.5 Pro
        timeout: Orchestration timeout w sekundach
    """
    enabled: bool = True
    timeout: int = 90


@dataclass
class PerformanceConfig:
    """
    Konfiguracja wydajności i timeoutów.

    Attributes:
        max_response_time_per_persona: Maksymalny czas odpowiedzi persony (sekundy)
        max_focus_group_time: Maksymalny całkowity czas grupy fokusowej (sekundy)
        consistency_error_threshold: Próg błędu spójności (0.0-1.0)
        statistical_significance_threshold: Próg istotności statystycznej (p-value)
        random_seed: Seed dla reproducibility (None = losowy)
    """
    max_response_time_per_persona: int = 3
    max_focus_group_time: int = 30
    consistency_error_threshold: float = 0.05
    statistical_significance_threshold: float = 0.05
    random_seed: int | None = 42


# ═══════════════════════════════════════════════════════════════════════════
# FEATURES CONFIG
# ═══════════════════════════════════════════════════════════════════════════


class FeaturesConfig:
    """
    Centralny konfigurator feature flags i parametrów systemu.

    Ładuje: config/features.yaml

    Features:
    - Environment-aware (env/production.yaml może override'ować)
    - Typed dataclasses dla type safety
    - Fallback do sensownych defaultów
    """

    def __init__(self, features_file: str = "features.yaml"):
        self.loader = ConfigLoader()
        self.config = self.loader.load_with_env_overrides(features_file)

        # Load feature flags
        self.rag = self._load_rag()
        self.segment_cache = self._load_segment_cache()
        self.orchestration = self._load_orchestration()
        self.performance = self._load_performance()

    def _load_rag(self) -> RagFeatures:
        """
        Ładuje RAG feature flags.

        Returns:
            RagFeatures object z defaultami
        """
        rag_config = self.config.get("rag", {})

        return RagFeatures(
            enabled=rag_config.get("enabled", True),
            node_properties_enabled=rag_config.get("node_properties_enabled", True),
            extract_summaries=rag_config.get("extract_summaries", True),
            extract_key_facts=rag_config.get("extract_key_facts", True),
            relationship_confidence=rag_config.get("relationship_confidence", True),
        )

    def _load_segment_cache(self) -> SegmentCacheFeatures:
        """
        Ładuje segment cache feature flags.

        Returns:
            SegmentCacheFeatures object z defaultami
        """
        cache_config = self.config.get("segment_cache", {})

        return SegmentCacheFeatures(
            enabled=cache_config.get("enabled", True),
            ttl_days=cache_config.get("ttl_days", 7),
        )

    def _load_orchestration(self) -> OrchestrationFeatures:
        """
        Ładuje orchestration feature flags.

        Returns:
            OrchestrationFeatures object z defaultami
        """
        orch_config = self.config.get("orchestration", {})

        return OrchestrationFeatures(
            enabled=orch_config.get("enabled", True),
            timeout=orch_config.get("timeout", 90),
        )

    def _load_performance(self) -> PerformanceConfig:
        """
        Ładuje performance configuration.

        Returns:
            PerformanceConfig object z defaultami
        """
        perf_config = self.config.get("performance", {})

        return PerformanceConfig(
            max_response_time_per_persona=perf_config.get("max_response_time_per_persona", 3),
            max_focus_group_time=perf_config.get("max_focus_group_time", 30),
            consistency_error_threshold=perf_config.get("consistency_error_threshold", 0.05),
            statistical_significance_threshold=perf_config.get("statistical_significance_threshold", 0.05),
            random_seed=perf_config.get("random_seed", 42),
        )


# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

# Global features singleton (lazy-initialized on first access)
_features: FeaturesConfig | None = None


def get_features_config() -> FeaturesConfig:
    """
    Get global FeaturesConfig singleton.

    Returns:
        FeaturesConfig instance
    """
    global _features
    if _features is None:
        _features = FeaturesConfig()
        logger.debug("Initialized FeaturesConfig singleton")
    return _features


# Convenience export
features = get_features_config()
