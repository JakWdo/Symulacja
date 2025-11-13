"""
Config Validators - Validation logic for configuration files.

Separated from loader.py for better separation of concerns and testability.

Ten moduł zawiera:
- validate_prompt_structure(): Walidacja struktury promptu (required fields)
- validate_prompt_placeholders(): Walidacja czy wszystkie placeholders są provided
- validate_models_config(): Walidacja struktury config/models.yaml
- validate_yaml_structure(): Generic YAML schema validation
"""

import logging
from typing import Any

from jinja2 import Template, UndefinedError, StrictUndefined

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════


def validate_prompt_structure(data: dict, prompt_id: str) -> None:
    """
    Validate że prompt YAML ma required fields.

    Args:
        data: Parsed YAML dict
        prompt_id: Prompt ID (for error messages)

    Raises:
        ValueError: Jeśli brakuje required field
    """
    required = ["id", "version", "description", "messages"]
    for field in required:
        if field not in data:
            raise ValueError(f"Prompt {prompt_id} missing required field: {field}")

    # Validate messages structure
    if not isinstance(data["messages"], list):
        raise ValueError(f"Prompt {prompt_id}: 'messages' must be a list")

    for i, msg in enumerate(data["messages"]):
        if not isinstance(msg, dict):
            raise ValueError(f"Prompt {prompt_id}: message {i} must be a dict")
        if "role" not in msg or "content" not in msg:
            raise ValueError(f"Prompt {prompt_id}: message {i} missing 'role' or 'content'")
        if msg["role"] not in ["system", "user", "assistant"]:
            raise ValueError(
                f"Prompt {prompt_id}: message {i} has invalid role '{msg['role']}' "
                "(must be: system, user, assistant)"
            )


def validate_prompt_placeholders(messages: list[dict[str, str]], prompt_id: str, **variables) -> None:
    """
    Validate że wszystkie required placeholders w promptach są provided.

    Uses Jinja2 StrictUndefined to detect missing variables.

    Args:
        messages: List of message dicts (role + content)
        prompt_id: Prompt ID (for error messages)
        **variables: Variables to substitute

    Raises:
        ValueError: Jeśli brakuje required variable
    """
    for msg in messages:
        content = msg["content"]

        # Custom delimiters: ${var} instead of {{ var }}
        template = Template(
            content,
            variable_start_string="${",
            variable_end_string="}",
            undefined=StrictUndefined
        )

        try:
            # Try to render - will raise UndefinedError if missing variable
            template.render(**variables)
        except UndefinedError as e:
            raise ValueError(
                f"Missing required variable in prompt '{prompt_id}': {e}"
            )


def extract_prompt_placeholders(messages: list[dict[str, str]]) -> set[str]:
    """
    Extract all placeholder variables from prompt messages.

    Returns set of variable names (e.g., {"question", "options", "age"}).

    Args:
        messages: List of message dicts

    Returns:
        Set of placeholder variable names
    """
    import re

    placeholders = set()
    # Regex to match ${variable_name}
    pattern = r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}"

    for msg in messages:
        content = msg["content"]
        matches = re.findall(pattern, content)
        placeholders.update(matches)

    return placeholders


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════


def validate_models_config(config: dict) -> None:
    """
    Validate że models.yaml ma required structure.

    Required structure:
    - defaults.chat (with at least "model" field)
    - domains (optional, but if exists must be dict)

    Args:
        config: Parsed models.yaml dict

    Raises:
        ValueError: Jeśli struktura jest niepoprawna
    """
    # Check defaults.chat exists
    if "defaults" not in config:
        raise ValueError("models.yaml must have 'defaults' section")

    if "chat" not in config["defaults"]:
        raise ValueError("models.yaml must have 'defaults.chat' section")

    defaults_chat = config["defaults"]["chat"]

    # Check required fields in defaults.chat
    if not isinstance(defaults_chat, dict):
        raise ValueError("defaults.chat must be a dict")

    if "model" not in defaults_chat:
        raise ValueError("defaults.chat must have 'model' field")

    # Validate domains (if exists)
    if "domains" in config:
        if not isinstance(config["domains"], dict):
            raise ValueError("'domains' must be a dict")


def validate_model_name(model_name: str) -> None:
    """
    Validate że model name jest w poprawnym formacie.

    Currently supports:
    - Gemini: gemini-*
    - OpenAI: gpt-*
    - Anthropic: claude-*

    Args:
        model_name: Model name string

    Raises:
        ValueError: Jeśli format jest niepoprawny
    """
    if not model_name:
        raise ValueError("Model name cannot be empty")

    valid_prefixes = ["gemini-", "gpt-", "claude-", "command-", "llama-"]

    if not any(model_name.startswith(prefix) for prefix in valid_prefixes):
        logger.warning(
            f"Model '{model_name}' doesn't match known prefixes: {valid_prefixes}. "
            "This might be a custom model or typo."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# GENERIC YAML VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════


def validate_yaml_structure(data: dict, required_keys: list[str], config_name: str) -> None:
    """
    Generic YAML structure validation.

    Args:
        data: Parsed YAML dict
        required_keys: List of required top-level keys
        config_name: Config file name (for error messages)

    Raises:
        ValueError: Jeśli brakuje required keys
    """
    for key in required_keys:
        if key not in data:
            raise ValueError(f"{config_name} missing required key: {key}")


def validate_value_in_range(value: Any, min_val: float, max_val: float, field_name: str) -> None:
    """
    Validate że wartość jest w zakresie [min_val, max_val].

    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        field_name: Field name (for error messages)

    Raises:
        ValueError: Jeśli wartość poza zakresem
    """
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number, got {type(value)}")

    if value < min_val or value > max_val:
        raise ValueError(
            f"{field_name} must be in range [{min_val}, {max_val}], got {value}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# RAG CONFIG VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════


def validate_rag_retrieval_config(config: dict) -> None:
    """
    Validate RAG retrieval configuration.

    Args:
        config: Parsed retrieval.yaml dict

    Raises:
        ValueError: Jeśli konfiguracja jest niepoprawna
    """
    # Validate chunking
    if "chunking" in config:
        chunking = config["chunking"]
        if "chunk_size" in chunking:
            validate_value_in_range(chunking["chunk_size"], 100, 5000, "chunking.chunk_size")
        if "chunk_overlap" in chunking:
            validate_value_in_range(chunking["chunk_overlap"], 0, 1000, "chunking.chunk_overlap")

    # Validate retrieval
    if "retrieval" in config:
        retrieval = config["retrieval"]
        if "top_k" in retrieval:
            validate_value_in_range(retrieval["top_k"], 1, 100, "retrieval.top_k")
        if "vector_weight" in retrieval:
            validate_value_in_range(retrieval["vector_weight"], 0.0, 1.0, "retrieval.vector_weight")
        if "mode" in retrieval:
            valid_modes = ["vector", "hybrid", "hybrid+rerank"]
            if retrieval["mode"] not in valid_modes:
                raise ValueError(
                    f"retrieval.mode must be one of {valid_modes}, got '{retrieval['mode']}'"
                )


def validate_graph_transformer_config(config: dict) -> None:
    """
    Validate graph transformer configuration.

    Args:
        config: Parsed graph_transformer.yaml dict

    Raises:
        ValueError: Jeśli konfiguracja jest niepoprawna
    """
    # Validate allowed_nodes
    if "allowed_nodes" in config:
        if not isinstance(config["allowed_nodes"], list):
            raise ValueError("allowed_nodes must be a list")

    # Validate allowed_relationships
    if "allowed_relationships" in config:
        if not isinstance(config["allowed_relationships"], list):
            raise ValueError("allowed_relationships must be a list")
