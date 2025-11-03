"""
Tests for FeaturesLoader - Feature flags and performance configuration.
"""

import pytest
from unittest.mock import patch, MagicMock

from config.features_loader import (
    FeaturesConfig,
    RagFeatures,
    SegmentCacheFeatures,
    OrchestrationFeatures,
    PerformanceConfig,
    get_features_config,
)


class TestRagFeatures:
    """Test RAG feature flags loading and validation."""

    @pytest.fixture
    def features(self):
        """Get features config."""
        return get_features_config()

    def test_rag_enabled_default(self, features):
        """Test that RAG is enabled by default."""
        assert isinstance(features.rag, RagFeatures)
        assert features.rag.enabled is True

    def test_rag_node_properties_enabled(self, features):
        """Test that node properties extraction is enabled."""
        assert hasattr(features.rag, "node_properties_enabled")
        assert isinstance(features.rag.node_properties_enabled, bool)

    def test_rag_extract_summaries(self, features):
        """Test that summary extraction flag exists."""
        assert hasattr(features.rag, "extract_summaries")
        assert isinstance(features.rag.extract_summaries, bool)

    def test_rag_extract_key_facts(self, features):
        """Test that key facts extraction flag exists."""
        assert hasattr(features.rag, "extract_key_facts")
        assert isinstance(features.rag.extract_key_facts, bool)

    def test_rag_relationship_confidence(self, features):
        """Test that relationship confidence flag exists."""
        assert hasattr(features.rag, "relationship_confidence")
        assert isinstance(features.rag.relationship_confidence, bool)


class TestSegmentCacheFeatures:
    """Test segment cache feature flags."""

    @pytest.fixture
    def features(self):
        """Get features config."""
        return get_features_config()

    def test_segment_cache_enabled(self, features):
        """Test segment cache is enabled by default."""
        assert isinstance(features.segment_cache, SegmentCacheFeatures)
        assert features.segment_cache.enabled is True

    def test_segment_cache_ttl_days(self, features):
        """Test that TTL is set and reasonable."""
        assert hasattr(features.segment_cache, "ttl_days")
        assert isinstance(features.segment_cache.ttl_days, int)
        assert features.segment_cache.ttl_days > 0
        assert features.segment_cache.ttl_days <= 30  # Reasonable max TTL


class TestOrchestrationFeatures:
    """Test orchestration feature flags."""

    @pytest.fixture
    def features(self):
        """Get features config."""
        return get_features_config()

    def test_orchestration_enabled(self, features):
        """Test orchestration is enabled by default."""
        assert isinstance(features.orchestration, OrchestrationFeatures)
        assert features.orchestration.enabled is True

    def test_orchestration_timeout(self, features):
        """Test orchestration timeout is set and reasonable."""
        assert hasattr(features.orchestration, "timeout")
        assert isinstance(features.orchestration.timeout, int)
        assert features.orchestration.timeout > 0
        assert features.orchestration.timeout <= 120  # Max 2 minutes


class TestPerformanceConfig:
    """Test performance configuration."""

    @pytest.fixture
    def features(self):
        """Get features config."""
        return get_features_config()

    def test_performance_exists(self, features):
        """Test that performance config exists."""
        assert isinstance(features.performance, PerformanceConfig)

    def test_max_response_time_per_persona(self, features):
        """Test max response time is set correctly."""
        assert hasattr(features.performance, "max_response_time_per_persona")
        assert isinstance(features.performance.max_response_time_per_persona, int)
        assert features.performance.max_response_time_per_persona > 0
        assert features.performance.max_response_time_per_persona <= 10  # Reasonable max

    def test_max_focus_group_time(self, features):
        """Test max focus group time is set correctly."""
        assert hasattr(features.performance, "max_focus_group_time")
        assert isinstance(features.performance.max_focus_group_time, int)
        assert features.performance.max_focus_group_time > 0
        assert features.performance.max_focus_group_time <= 60  # Max 1 hour

    def test_consistency_error_threshold(self, features):
        """Test consistency error threshold is valid."""
        assert hasattr(features.performance, "consistency_error_threshold")
        assert isinstance(features.performance.consistency_error_threshold, float)
        assert 0.0 < features.performance.consistency_error_threshold <= 1.0

    def test_statistical_significance_threshold(self, features):
        """Test statistical significance threshold is valid."""
        assert hasattr(features.performance, "statistical_significance_threshold")
        assert isinstance(features.performance.statistical_significance_threshold, float)
        assert 0.0 < features.performance.statistical_significance_threshold <= 1.0

    def test_random_seed(self, features):
        """Test random seed is set for reproducibility."""
        assert hasattr(features.performance, "random_seed")
        # Can be int or None
        assert features.performance.random_seed is None or isinstance(features.performance.random_seed, int)


class TestFeaturesConfigSingleton:
    """Test singleton pattern and caching."""

    def test_singleton_returns_same_instance(self):
        """Test that get_features_config() returns the same instance."""
        config1 = get_features_config()
        config2 = get_features_config()

        assert config1 is config2, "Singleton should return same instance"

    def test_singleton_caches_flags(self):
        """Test that feature flags are cached."""
        config1 = get_features_config()
        rag1 = config1.rag

        config2 = get_features_config()
        rag2 = config2.rag

        # Should be same object reference (cached)
        assert rag1 is rag2


class TestFeaturesConfigDefaults:
    """Test default values when config file is missing or incomplete."""

    @patch("config.features_loader.ConfigLoader.load_with_env_overrides")
    def test_missing_rag_section_uses_defaults(self, mock_load):
        """Test that missing RAG section uses default values."""
        mock_load.return_value = {}  # Empty config

        config = FeaturesConfig()

        assert config.rag.enabled is True
        assert config.rag.node_properties_enabled is True
        assert config.rag.extract_summaries is True

    @patch("config.features_loader.ConfigLoader.load_with_env_overrides")
    def test_missing_segment_cache_uses_defaults(self, mock_load):
        """Test that missing segment cache section uses defaults."""
        mock_load.return_value = {}

        config = FeaturesConfig()

        assert config.segment_cache.enabled is True
        assert config.segment_cache.ttl_days == 7

    @patch("config.features_loader.ConfigLoader.load_with_env_overrides")
    def test_missing_orchestration_uses_defaults(self, mock_load):
        """Test that missing orchestration section uses defaults."""
        mock_load.return_value = {}

        config = FeaturesConfig()

        assert config.orchestration.enabled is True
        assert config.orchestration.timeout == 90

    @patch("config.features_loader.ConfigLoader.load_with_env_overrides")
    def test_missing_performance_uses_defaults(self, mock_load):
        """Test that missing performance section uses defaults."""
        mock_load.return_value = {}

        config = FeaturesConfig()

        assert config.performance.max_response_time_per_persona == 3
        assert config.performance.max_focus_group_time == 30
        assert config.performance.consistency_error_threshold == 0.05
        assert config.performance.random_seed == 42

    @patch("config.features_loader.ConfigLoader.load_with_env_overrides")
    def test_partial_config_merges_with_defaults(self, mock_load):
        """Test that partial config merges with defaults."""
        mock_load.return_value = {
            "rag": {"enabled": False},  # Only override enabled
            "performance": {"random_seed": None}  # Only override seed
        }

        config = FeaturesConfig()

        # Overridden values
        assert config.rag.enabled is False
        assert config.performance.random_seed is None

        # Default values still present
        assert config.rag.node_properties_enabled is True
        assert config.performance.max_response_time_per_persona == 3


class TestDataclassDefaults:
    """Test that dataclass default values work correctly."""

    def test_rag_features_defaults(self):
        """Test RagFeatures default values."""
        rag = RagFeatures()

        assert rag.enabled is True
        assert rag.node_properties_enabled is True
        assert rag.extract_summaries is True
        assert rag.extract_key_facts is True
        assert rag.relationship_confidence is True

    def test_segment_cache_defaults(self):
        """Test SegmentCacheFeatures default values."""
        cache = SegmentCacheFeatures()

        assert cache.enabled is True
        assert cache.ttl_days == 7

    def test_orchestration_defaults(self):
        """Test OrchestrationFeatures default values."""
        orch = OrchestrationFeatures()

        assert orch.enabled is True
        assert orch.timeout == 90

    def test_performance_defaults(self):
        """Test PerformanceConfig default values."""
        perf = PerformanceConfig()

        assert perf.max_response_time_per_persona == 3
        assert perf.max_focus_group_time == 30
        assert perf.consistency_error_threshold == 0.05
        assert perf.statistical_significance_threshold == 0.05
        assert perf.random_seed == 42


class TestEnvironmentOverrides:
    """Test that environment-specific configs can override base config."""

    @patch("config.features_loader.ConfigLoader.load_with_env_overrides")
    def test_environment_can_override_flags(self, mock_load):
        """Test that environment config can override feature flags."""
        mock_load.return_value = {
            "rag": {"enabled": False},  # Production might disable RAG
            "orchestration": {"timeout": 60}  # Shorter timeout in prod
        }

        config = FeaturesConfig()

        assert config.rag.enabled is False
        assert config.orchestration.timeout == 60
