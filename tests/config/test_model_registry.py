"""
Tests for ModelRegistry - model fallback chain, configuration
"""

import pytest

from config import ModelRegistry, ModelConfig


class TestModelRegistry:
    """Test ModelRegistry functionality."""

    @pytest.fixture
    def registry(self):
        """Create ModelRegistry instance."""
        return ModelRegistry()

    def test_get_default_model(self, registry):
        """Test getting global default model."""
        model_config = registry.get_default()

        assert isinstance(model_config, ModelConfig)
        assert model_config.model == "gemini-2.5-flash"
        assert model_config.temperature == 0.7
        assert model_config.max_tokens == 6000
        assert model_config.timeout == 60
        assert model_config.retries == 3

    def test_get_domain_subdomain(self, registry):
        """Test getting domain-specific model (personas.orchestration)."""
        model_config = registry.get("personas", "orchestration")

        # Should get specific config for personas.orchestration
        assert model_config.model == "gemini-2.5-pro"
        assert model_config.temperature == 0.3  # Lower for analytical
        assert model_config.max_tokens == 8000
        assert model_config.timeout == 120

    def test_get_domain_subdomain_fallback_to_generation(self, registry):
        """Test fallback: personas.jtbd → defaults.chat."""
        model_config = registry.get("personas", "jtbd")

        # Should fallback to defaults.chat (no specific jtbd config)
        assert model_config.model == "gemini-2.5-flash"
        # Fallback to defaults.chat temperature since no jtbd or generation specific
        assert model_config.temperature in [0.7, 0.8]  # Either default or generation

    def test_get_unknown_domain_fallback_to_default(self, registry):
        """Test fallback: unknown.unknown → defaults.chat."""
        model_config = registry.get("unknown_domain", "unknown_subdomain")

        # Should fallback to defaults.chat
        assert model_config.model == "gemini-2.5-flash"
        assert model_config.temperature == 0.7

    def test_get_surveys_response(self, registry):
        """Test getting surveys.response model."""
        model_config = registry.get("surveys", "response")

        assert model_config.model == "gemini-2.5-flash"
        # Has timeout=30 in models.yaml
        assert model_config.timeout == 30

    def test_get_rag_graph(self, registry):
        """Test getting RAG graph model (very low temperature)."""
        model_config = registry.get("rag", "graph")

        assert model_config.model == "gemini-2.5-flash"
        assert model_config.temperature == 0.1  # Very low for Cypher

    def test_model_config_params_property(self, registry):
        """Test ModelConfig.params returns dict for build_chat_model()."""
        model_config = registry.get("personas", "orchestration")
        params = model_config.params

        assert isinstance(params, dict)
        assert "model" in params
        assert "temperature" in params
        assert "max_tokens" in params
        assert "timeout" in params

        # Should not include None values
        assert all(v is not None for v in params.values())

    def test_model_config_with_optional_params(self):
        """Test ModelConfig with optional top_p and top_k."""
        config = ModelConfig(
            model="test-model",
            temperature=0.5,
            max_tokens=1000,
            top_p=0.9,
            top_k=40
        )

        params = config.params

        assert params["top_p"] == 0.9
        assert params["top_k"] == 40

    def test_model_config_without_optional_params(self):
        """Test ModelConfig without top_p and top_k (default None)."""
        config = ModelConfig(
            model="test-model",
            temperature=0.5,
            max_tokens=1000
        )

        params = config.params

        # top_p and top_k should not be in params if None
        assert "top_p" not in params
        assert "top_k" not in params

    def test_fallback_chain_order(self, registry):
        """Test fallback chain priority order."""
        # 1. Specific subdomain (if exists)
        orchestration = registry.get("personas", "orchestration")
        assert orchestration.model == "gemini-2.5-pro"

        # 2. Fallback to defaults.chat when no specific config
        jtbd = registry.get("personas", "jtbd")
        assert jtbd.model == "gemini-2.5-flash"

        # 3. Global default
        unknown = registry.get("unknown", "unknown")
        assert unknown.model == "gemini-2.5-flash"  # From defaults.chat

    def test_focus_groups_discussion(self, registry):
        """Test focus_groups.discussion config."""
        model_config = registry.get("focus_groups", "discussion")

        assert model_config.model == "gemini-2.5-flash"
        assert model_config.temperature == 0.8  # More creative
        assert model_config.max_tokens == 2000

    def test_focus_groups_summarization(self, registry):
        """Test focus_groups.summarization config."""
        model_config = registry.get("focus_groups", "summarization")

        assert model_config.model == "gemini-2.5-pro"
        assert model_config.temperature == 0.2  # Low for analytical

    def test_validation_required_fields(self, registry):
        """Test validation checks for required fields."""
        # Registry should validate on init
        assert "defaults" in registry.config
        assert "chat" in registry.config["defaults"]
        assert "model" in registry.config["defaults"]["chat"]


class TestModelConfig:
    """Test ModelConfig dataclass."""

    def test_model_config_creation(self):
        """Test creating ModelConfig."""
        config = ModelConfig(
            model="gemini-2.5-flash",
            temperature=0.7,
            max_tokens=6000,
            timeout=60,
            retries=3
        )

        assert config.model == "gemini-2.5-flash"
        assert config.temperature == 0.7
        assert config.max_tokens == 6000
        assert config.timeout == 60
        assert config.retries == 3

    def test_model_config_defaults(self):
        """Test ModelConfig default values."""
        config = ModelConfig(model="test-model")

        assert config.temperature == 0.7
        assert config.max_tokens == 6000
        assert config.top_p is None
        assert config.top_k is None
        assert config.timeout == 60
        assert config.retries == 3

    def test_params_property_structure(self):
        """Test params property returns correct structure."""
        config = ModelConfig(
            model="test-model",
            temperature=0.5,
            max_tokens=2000
        )

        params = config.params

        assert params == {
            "model": "test-model",
            "temperature": 0.5,
            "max_tokens": 2000,
            "timeout": 60
        }
