"""
Config package - Centralized configuration system.

Główne API:
    from config import prompts, models, rag

    # Prompts
    prompt = prompts.get("surveys.single_choice")
    rendered = prompt.render(question="...", options=[])

    # Models
    model_config = models.get("surveys", "response")
    llm = build_chat_model(**model_config.params)

    # RAG
    chunk_size = rag.chunking.chunk_size
"""

from config.loader import (
    ConfigLoader,
    ModelConfig,
    ModelRegistry,
    Prompt,
    PromptRegistry,
    RagConfig,
    get_model_registry,
    get_prompt_registry,
    get_rag_config,
    models,
    prompts,
    rag,
)

__all__ = [
    "ConfigLoader",
    "Prompt",
    "PromptRegistry",
    "ModelConfig",
    "ModelRegistry",
    "RagConfig",
    "get_prompt_registry",
    "get_model_registry",
    "get_rag_config",
    "prompts",
    "models",
    "rag",
]
