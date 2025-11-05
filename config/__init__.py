"""
Config package - Centralized configuration system (Single Source of Truth).

Główne API:
    from config import prompts, models, rag, demographics, features, app

    # Prompts
    prompt = prompts.get("surveys.single_choice")
    rendered = prompt.render(question="...", options=[])

    # Models
    model_config = models.get("surveys", "response")
    llm = build_chat_model(**model_config.params)

    # RAG
    chunk_size = rag.chunking.chunk_size
    query = rag.queries.get("demographic_context")

    # Demographics
    locations = demographics.poland.locations
    age_groups = demographics.common.age_groups
    values = demographics.international.values

    # Features
    if features.rag.enabled:
        use_graph = features.rag.node_properties_enabled

    # App
    redis_config = app.redis
    db_url = app.database.url
"""

# ═══════════════════════════════════════════════════════════════════════════
# EXISTING LOADERS (Prompts, Models, RAG)
# ═══════════════════════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════════════════════
# NEW LOADERS (Demographics, Features, App)
# ═══════════════════════════════════════════════════════════════════════════

from config.demographics_loader import (
    DemographicsConfig,
    PolandDemographics,
    InternationalDemographics,
    CommonDemographics,
    get_demographics_config,
    demographics,
)

from config.features_loader import (
    FeaturesConfig,
    RagFeatures,
    SegmentCacheFeatures,
    OrchestrationFeatures,
    PerformanceConfig,
    get_features_config,
    features,
)

from config.app_loader import (
    AppConfig,
    RedisConfig,
    DatabaseConfig,
    Neo4jConfig,
    CeleryConfig,
    DocumentStorageConfig,
    GCPConfig,
    get_app_config,
    app,
)

# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    # Base loader
    "ConfigLoader",
    # Prompts
    "Prompt",
    "PromptRegistry",
    "get_prompt_registry",
    "prompts",
    # Models
    "ModelConfig",
    "ModelRegistry",
    "get_model_registry",
    "models",
    # RAG
    "RagConfig",
    "get_rag_config",
    "rag",
    # Demographics
    "DemographicsConfig",
    "PolandDemographics",
    "InternationalDemographics",
    "CommonDemographics",
    "get_demographics_config",
    "demographics",
    # Features
    "FeaturesConfig",
    "RagFeatures",
    "SegmentCacheFeatures",
    "OrchestrationFeatures",
    "PerformanceConfig",
    "get_features_config",
    "features",
    # App
    "AppConfig",
    "RedisConfig",
    "DatabaseConfig",
    "Neo4jConfig",
    "CeleryConfig",
    "DocumentStorageConfig",
    "GCPConfig",
    "get_app_config",
    "app",
]
