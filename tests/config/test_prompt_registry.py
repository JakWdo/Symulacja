"""
Tests for PromptRegistry - prompt loading, rendering, versioning, hashing
"""

import pytest
from pathlib import Path

from config import PromptRegistry, Prompt


class TestPromptRegistry:
    """Test PromptRegistry functionality."""

    @pytest.fixture
    def registry(self):
        """Create PromptRegistry instance."""
        return PromptRegistry()

    def test_get_prompt_success(self, registry):
        """Test loading existing prompt."""
        prompt = registry.get("surveys.single_choice")

        assert isinstance(prompt, Prompt)
        assert prompt.id == "surveys.single_choice"
        assert prompt.version == "1.0.0"
        assert len(prompt.messages) == 2  # system + user
        assert prompt.hash  # Hash should be computed

    def test_get_prompt_cache(self, registry):
        """Test prompt caching - second get should use cache."""
        prompt1 = registry.get("surveys.single_choice")
        prompt2 = registry.get("surveys.single_choice")

        # Should be same object (from cache)
        assert prompt1 is prompt2

    def test_get_prompt_not_found(self, registry):
        """Test error when prompt doesn't exist."""
        with pytest.raises(FileNotFoundError):
            registry.get("nonexistent.prompt")

    def test_get_prompt_invalid_id_format(self, registry):
        """Test error on invalid ID format."""
        with pytest.raises(ValueError, match="expected 'domain.name'"):
            registry.get("invalid")

    def test_prompt_render_success(self, registry):
        """Test rendering prompt with variables."""
        prompt = registry.get("surveys.single_choice")

        rendered = prompt.render(
            persona_context="Test persona context",
            question="Test question?",
            description="Test description",
            options="- Option 1\n- Option 2"
        )

        assert len(rendered) == 2  # system + user
        assert rendered[0]["role"] == "system"
        assert rendered[1]["role"] == "user"

        # Check variables were substituted
        user_content = rendered[1]["content"]
        assert "Test persona context" in user_content
        assert "Test question?" in user_content
        assert "Option 1" in user_content

    def test_prompt_render_missing_variable(self, registry):
        """Test error when required variable is missing."""
        prompt = registry.get("surveys.single_choice")

        with pytest.raises(ValueError, match="Missing required variable"):
            prompt.render(
                persona_context="Test",
                question="Test?"
                # Missing: description, options
            )

    def test_prompt_hash_stability(self, registry):
        """Test that hash is stable for same content."""
        prompt1 = registry.get("surveys.single_choice")
        hash1 = prompt1.hash

        # Clear cache and reload
        registry._cache.clear()
        prompt2 = registry.get("surveys.single_choice")
        hash2 = prompt2.hash

        assert hash1 == hash2  # Hash should be identical

    def test_prompt_hash_changes_with_content(self):
        """Test that hash changes when content changes."""
        messages1 = [{"role": "system", "content": "Original content"}]
        messages2 = [{"role": "system", "content": "Changed content"}]

        prompt1 = Prompt(
            id="test.prompt",
            version="1.0.0",
            description="Test",
            messages=messages1
        )
        hash1 = prompt1.compute_hash()

        prompt2 = Prompt(
            id="test.prompt",
            version="1.0.0",
            description="Test",
            messages=messages2
        )
        hash2 = prompt2.compute_hash()

        assert hash1 != hash2

    def test_multiple_domain_prompts(self, registry):
        """Test loading prompts from different domains."""
        survey_prompt = registry.get("surveys.single_choice")
        persona_prompt = registry.get("personas.jtbd")
        rag_prompt = registry.get("rag.cypher_generation")

        assert survey_prompt.id.startswith("surveys.")
        assert persona_prompt.id.startswith("personas.")
        assert rag_prompt.id.startswith("rag.")

    def test_get_hash_method(self, registry):
        """Test get_hash convenience method."""
        hash_value = registry.get_hash("surveys.single_choice")

        assert isinstance(hash_value, str)
        assert len(hash_value) == 16  # SHA256[:16]

    def test_validate_placeholders_success(self, registry):
        """Test placeholder validation with all variables provided."""
        # Should not raise
        registry.validate_placeholders(
            "surveys.single_choice",
            persona_context="Test",
            question="Test?",
            description="Desc",
            options="Options"
        )

    def test_validate_placeholders_failure(self, registry):
        """Test placeholder validation fails with missing variables."""
        with pytest.raises(ValueError, match="Missing required variable"):
            registry.validate_placeholders(
                "surveys.single_choice",
                persona_context="Test"
                # Missing other required vars
            )


class TestPromptObject:
    """Test Prompt object methods."""

    def test_prompt_creation(self):
        """Test creating Prompt object."""
        prompt = Prompt(
            id="test.prompt",
            version="1.0.0",
            description="Test prompt",
            messages=[
                {"role": "system", "content": "System message"},
                {"role": "user", "content": "User ${variable}"}
            ]
        )

        assert prompt.id == "test.prompt"
        assert prompt.version == "1.0.0"
        assert len(prompt.messages) == 2

    def test_prompt_render_custom_delimiters(self):
        """Test rendering uses ${} delimiters (not Jinja2 default {{ }})."""
        prompt = Prompt(
            id="test.prompt",
            version="1.0.0",
            description="Test",
            messages=[
                {"role": "system", "content": "Value: ${my_var}"}
            ]
        )

        rendered = prompt.render(my_var="REPLACED")

        assert rendered[0]["content"] == "Value: REPLACED"

    def test_prompt_render_preserves_curly_braces(self):
        """Test that {param} (single braces) are preserved for Cypher."""
        prompt = Prompt(
            id="test.cypher",
            version="1.0.0",
            description="Test Cypher",
            messages=[
                {"role": "system", "content": "MATCH (n) WHERE n.id = {param} AND ${my_var}"}
            ]
        )

        rendered = prompt.render(my_var="condition")

        # {param} should be preserved, ${my_var} should be replaced
        assert "{param}" in rendered[0]["content"]
        assert "condition" in rendered[0]["content"]
        assert "${my_var}" not in rendered[0]["content"]

    def test_compute_hash_deterministic(self):
        """Test hash computation is deterministic."""
        messages = [
            {"role": "system", "content": "Test"},
            {"role": "user", "content": "Hello ${name}"}
        ]

        prompt = Prompt(
            id="test.prompt",
            version="1.0.0",
            description="Test",
            messages=messages
        )

        hash1 = prompt.compute_hash()
        hash2 = prompt.compute_hash()

        assert hash1 == hash2
