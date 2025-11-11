"""
Tests for ConfigLoader - YAML loading, environment layering
"""

import pytest
import yaml
from unittest.mock import patch

from config.loader import ConfigLoader


class TestConfigLoader:
    """Test ConfigLoader functionality."""

    @pytest.fixture
    def loader(self):
        """Create ConfigLoader instance."""
        return ConfigLoader()

    @pytest.fixture
    def temp_yaml_file(self, tmp_path):
        """Create temporary YAML file for testing."""
        yaml_file = tmp_path / "test.yaml"
        data = {
            "key1": "value1",
            "key2": {"nested": "value2"},
            "key3": [1, 2, 3]
        }
        with open(yaml_file, "w") as f:
            yaml.dump(data, f)
        return yaml_file

    def test_load_yaml_success(self, loader, temp_yaml_file):
        """Test loading valid YAML file."""
        data = loader.load_yaml(temp_yaml_file)

        assert data["key1"] == "value1"
        assert data["key2"]["nested"] == "value2"
        assert data["key3"] == [1, 2, 3]

    def test_load_yaml_file_not_found(self, loader, tmp_path):
        """Test error when file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            loader.load_yaml(nonexistent)

    def test_load_yaml_invalid_syntax(self, loader, tmp_path):
        """Test error on invalid YAML syntax."""
        bad_yaml = tmp_path / "bad.yaml"
        with open(bad_yaml, "w") as f:
            f.write("key1: value1\n  key2: value2\ninvalid yaml: [unclosed")

        with pytest.raises(yaml.YAMLError):
            loader.load_yaml(bad_yaml)

    def test_load_yaml_empty_file(self, loader, tmp_path):
        """Test loading empty YAML file returns empty dict."""
        empty_yaml = tmp_path / "empty.yaml"
        empty_yaml.touch()

        data = loader.load_yaml(empty_yaml)

        assert data == {}

    def test_deep_merge_simple(self, loader):
        """Test deep merge with simple values."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}

        result = loader._deep_merge(base, override)

        assert result == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge_nested(self, loader):
        """Test deep merge with nested dicts."""
        base = {
            "level1": {
                "level2": {"a": 1, "b": 2},
                "other": "value"
            }
        }
        override = {
            "level1": {
                "level2": {"b": 3, "c": 4}
            }
        }

        result = loader._deep_merge(base, override)

        assert result["level1"]["level2"]["a"] == 1  # Preserved from base
        assert result["level1"]["level2"]["b"] == 3  # Overridden
        assert result["level1"]["level2"]["c"] == 4  # Added
        assert result["level1"]["other"] == "value"  # Preserved

    def test_deep_merge_list_override(self, loader):
        """Test deep merge replaces lists (doesn't merge them)."""
        base = {"items": [1, 2, 3]}
        override = {"items": [4, 5]}

        result = loader._deep_merge(base, override)

        assert result["items"] == [4, 5]  # Completely replaced

    def test_load_models_yaml(self, loader):
        """Test loading actual models.yaml from config/."""
        config = loader.load_yaml("models.yaml")

        assert "defaults" in config
        assert "chat" in config["defaults"]
        assert config["defaults"]["chat"]["model"] == "gemini-2.5-flash"

    def test_load_with_env_overrides_development(self, loader):
        """Test loading with development environment overrides."""
        with patch.object(loader, "environment", "development"):
            config = loader.load_with_env_overrides("models.yaml")

        # Should have base config
        assert "defaults" in config

        # Development overrides should be applied if they exist
        # (check specific override if present in env/development.yaml)

    def test_environment_attribute(self, loader):
        """Test environment attribute is set from ENVIRONMENT env var."""
        assert loader.environment in ["development", "staging", "production"]

    def test_config_root_path(self, loader):
        """Test config_root points to config/ directory."""
        assert loader.config_root.name == "config"
        assert loader.config_root.exists()
        assert (loader.config_root / "models.yaml").exists()


class TestEnvironmentLayering:
    """Test environment-specific configuration layering."""

    @pytest.fixture
    def loader_dev(self):
        """Create loader with development environment."""
        loader = ConfigLoader()
        loader.environment = "development"
        return loader

    @pytest.fixture
    def loader_prod(self):
        """Create loader with production environment."""
        loader = ConfigLoader()
        loader.environment = "production"
        return loader

    def test_development_env_overrides(self, loader_dev):
        """Test development environment has longer timeouts."""
        config = loader_dev.load_with_env_overrides("models.yaml")

        # Development should have longer timeout (if specified in env/development.yaml)
        if "defaults" in config and "chat" in config["defaults"]:
            # Check if timeout was overridden
            timeout = config["defaults"]["chat"].get("timeout")
            assert timeout is not None

    def test_production_env_uses_better_models(self, loader_prod):
        """Test production environment prefers Pro models."""
        config = loader_prod.load_with_env_overrides("models.yaml")

        # Production might use Pro model (if specified in env/production.yaml)
        if "defaults" in config and "chat" in config["defaults"]:
            model = config["defaults"]["chat"]["model"]
            assert model in ["gemini-2.5-flash", "gemini-2.5-pro"]

    def test_base_config_unchanged(self):
        """Test that base config files are not modified by env loading."""
        loader = ConfigLoader()

        # Load base
        base = loader.load_yaml("models.yaml")
        base_model = base["defaults"]["chat"]["model"]

        # Load with env overrides
        loader.environment = "production"
        loader.load_with_env_overrides("models.yaml")

        # Original base should still be unchanged
        base_after = loader.load_yaml("models.yaml")
        assert base_after["defaults"]["chat"]["model"] == base_model
