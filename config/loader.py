"""
Config Loader - Centralized configuration management system.

Ten moduł dostarcza:
- ConfigLoader: Bazowy loader YAML z environment layering
- PromptRegistry: Cache promptów z versioning i hashing
- ModelRegistry: Fallback chain dla modeli (service → domain → global)
- RagConfig: Konfiguracja systemu RAG

Użycie:
    from config import prompts, models, rag

    # Prompts
    prompt = prompts.get("surveys.single_choice")
    rendered = prompt.render(question="...", options=[])

    # Models
    model_config = models.get("surveys", "response")
    llm = build_chat_model(**model_config.params)

    # RAG
    chunk_size = rag.chunking.chunk_size
    query = rag.queries.get("demographic_context")
"""

import hashlib
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Template, UndefinedError, StrictUndefined

# Import validators from separate module
from config.validators import (
    validate_prompt_structure,
    validate_prompt_placeholders,
    validate_models_config,
    validate_model_name,
)

logger = logging.getLogger(__name__)

# Config root directory (config/ w głównym folderze projektu)
CONFIG_ROOT = Path(__file__).parent.resolve()
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


# ═══════════════════════════════════════════════════════════════════════════════
# BASE CONFIG LOADER
# ═══════════════════════════════════════════════════════════════════════════════


class ConfigLoader:
    """
    Bazowy loader YAML z environment layering i walidacją.

    Precedence order (highest to lowest):
    1. Environment variables
    2. env/{environment}.yaml
    3. Base config file (app.yaml, models.yaml, etc.)
    4. Defaults in code
    """

    def __init__(self, config_root: Path | None = None):
        self.config_root = config_root or CONFIG_ROOT
        self.environment = ENVIRONMENT

    def load_yaml(self, path: str | Path) -> dict:
        """
        Load YAML file z obsługą błędów.

        Args:
            path: Ścieżka do pliku YAML (relative do config_root)

        Returns:
            Dict z zawartością YAML

        Raises:
            FileNotFoundError: Jeśli plik nie istnieje
            yaml.YAMLError: Jeśli parsing się nie udał
        """
        if isinstance(path, str):
            path = Path(path)

        if not path.is_absolute():
            path = self.config_root / path

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data or {}
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML {path}: {e}")
            raise

    def load_with_env_overrides(self, base_file: str, env_file: str | None = None) -> dict:
        """
        Load base config + env overrides.

        Args:
            base_file: Base config file (e.g., "models.yaml")
            env_file: Env-specific overrides (e.g., "env/production.yaml")
                     If None, uses "env/{environment}.yaml"

        Returns:
            Merged config dict
        """
        # Load base config
        base_config = self.load_yaml(base_file)

        # Try to load env overrides
        if env_file is None:
            env_file = f"env/{self.environment}.yaml"

        env_path = self.config_root / env_file
        if env_path.exists():
            env_config = self.load_yaml(env_file)
            base_config = self._deep_merge(base_config, env_config)
            logger.debug(f"Applied env overrides from {env_file}")

        return base_config

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """
        Deep merge override dict into base dict.

        Override values replace base values at all nesting levels.
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class Prompt:
    """
    Pojedynczy prompt template.

    Attributes:
        id: Unique prompt ID (e.g., "surveys.single_choice")
        version: Semantic version (e.g., "1.0.0")
        description: Human-readable description
        messages: Lista wiadomości (system/user/assistant)
        hash: SHA256 hash of normalized content (for versioning)
        variant: Optional variant name for A/B testing (e.g., "a", "b")
        weight: Optional weight for variant selection (default: 1.0)
    """
    id: str
    version: str
    description: str
    messages: list[dict[str, str]]
    hash: str = ""
    variant: str | None = None
    weight: float = 1.0

    def render(self, **variables) -> list[dict[str, str]]:
        """
        Render prompt z variables używając Jinja2 (custom delimiters ${var}).

        Args:
            **variables: Variables do substytu

cji

        Returns:
            Lista rendered messages

        Raises:
            ValueError: Jeśli brakuje required variable
        """
        rendered_messages = []

        for msg in self.messages:
            role = msg["role"]
            content = msg["content"]

            # Custom delimiters: ${var} instead of {{ var }}
            # Bezpieczne dla Cypher queries które używają {param}
            # StrictUndefined: throw error on missing variables
            template = Template(
                content,
                variable_start_string="${",
                variable_end_string="}",
                undefined=StrictUndefined
            )

            try:
                rendered_content = template.render(**variables)
                rendered_messages.append({"role": role, "content": rendered_content})
            except UndefinedError as e:
                raise ValueError(
                    f"Missing required variable in prompt '{self.id}': {e}"
                )

        return rendered_messages

    def compute_hash(self) -> str:
        """
        Compute SHA256 hash of normalized prompt content.

        Used for version detection - if hash changes, version should be bumped.
        """
        # Normalize: serialize messages as stable JSON
        import json
        normalized = json.dumps(self.messages, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


class PromptRegistry:
    """
    Registry wszystkich promptów z cache i versioning.

    Features:
    - Lazy loading z cache
    - SHA256 hashing dla version detection
    - Strict placeholder validation
    - Auto-bump versioning (via config_validate.py)
    - A/B testing z variants (weighted random selection)
    """

    def __init__(self, prompts_dir: Path | None = None):
        self.prompts_dir = prompts_dir or (CONFIG_ROOT / "prompts")
        self._cache: dict[str, Prompt] = {}
        self._variants_cache: dict[str, list[Prompt]] = {}  # ID → list of variants
        self.loader = ConfigLoader()

    def get(self, prompt_id: str, variant: str | None = None) -> Prompt:
        """
        Get prompt by ID (dot-separated path, e.g., "surveys.single_choice").

        Supports A/B testing: if variants exist, randomly selects based on weights.

        Args:
            prompt_id: Prompt ID (format: "domain.name")
            variant: Specific variant to load (if None, uses weighted random)

        Returns:
            Prompt object

        Raises:
            FileNotFoundError: Jeśli prompt nie istnieje
        """
        # If specific variant requested, load it
        if variant:
            cache_key = f"{prompt_id}:{variant}"
            if cache_key in self._cache:
                return self._cache[cache_key]

            # Try to load variant file
            parts = prompt_id.split(".")
            if len(parts) < 2:
                raise ValueError(f"Invalid prompt ID: {prompt_id} (expected 'domain.name')")

            domain = parts[0]
            name = ".".join(parts[1:])

            variant_file = self.prompts_dir / domain / f"{name}_variant_{variant}.yaml"
            if variant_file.exists():
                return self._load_prompt_file(variant_file, cache_key)
            else:
                # Fall back to default
                logger.warning(f"Variant {variant} not found for {prompt_id}, using default")

        # Check if we have variants for this prompt
        if prompt_id in self._variants_cache:
            return self._select_variant(prompt_id)

        # Try to find variants
        self._discover_variants(prompt_id)

        # If variants exist, select one
        if prompt_id in self._variants_cache:
            return self._select_variant(prompt_id)

        # No variants - load default
        if prompt_id in self._cache:
            return self._cache[prompt_id]

        # Parse ID: "surveys.single_choice" → prompts/surveys/single_choice.yaml
        parts = prompt_id.split(".")
        if len(parts) < 2:
            raise ValueError(f"Invalid prompt ID: {prompt_id} (expected 'domain.name')")

        domain = parts[0]
        name = ".".join(parts[1:])

        prompt_file = self.prompts_dir / domain / f"{name}.yaml"

        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_id} (path: {prompt_file})")

        return self._load_prompt_file(prompt_file, prompt_id)

    def _load_prompt_file(self, prompt_file: Path, cache_key: str) -> Prompt:
        """Load single prompt file and cache it."""
        data = self.loader.load_yaml(prompt_file)

        # Validate required fields (delegated to validators module)
        validate_prompt_structure(data, cache_key)

        # Create Prompt object
        prompt = Prompt(
            id=data["id"],
            version=data["version"],
            description=data["description"],
            messages=data["messages"],
            variant=data.get("variant"),
            weight=data.get("weight", 1.0)
        )

        # Compute hash
        prompt.hash = prompt.compute_hash()

        # Cache
        self._cache[cache_key] = prompt

        logger.debug(f"Loaded prompt: {cache_key} (v{prompt.version}, variant={prompt.variant}, hash={prompt.hash})")

        return prompt

    def _discover_variants(self, prompt_id: str):
        """Discover all variants for a prompt ID."""
        parts = prompt_id.split(".")
        domain = parts[0]
        name = ".".join(parts[1:])

        prompt_dir = self.prompts_dir / domain
        if not prompt_dir.exists():
            return

        # Find all variant files: {name}_variant_{x}.yaml
        import glob
        variant_files = list(prompt_dir.glob(f"{name}_variant_*.yaml"))

        if variant_files:
            variants = []
            for vf in variant_files:
                # Extract variant name from filename
                variant_name = vf.stem.split("_variant_")[-1]
                cache_key = f"{prompt_id}:{variant_name}"

                variant_prompt = self._load_prompt_file(vf, cache_key)
                variants.append(variant_prompt)

            # Also load default
            default_file = prompt_dir / f"{name}.yaml"
            if default_file.exists():
                default_prompt = self._load_prompt_file(default_file, prompt_id)
                variants.append(default_prompt)

            self._variants_cache[prompt_id] = variants
            logger.debug(f"Discovered {len(variants)} variants for {prompt_id}")

    def _select_variant(self, prompt_id: str) -> Prompt:
        """Select variant using weighted random selection."""
        import random

        variants = self._variants_cache[prompt_id]
        weights = [v.weight for v in variants]

        selected = random.choices(variants, weights=weights, k=1)[0]

        logger.debug(f"Selected variant '{selected.variant or 'default'}' for {prompt_id}")

        return selected

    def get_hash(self, prompt_id: str) -> str:
        """Get SHA256 hash of prompt content."""
        prompt = self.get(prompt_id)
        return prompt.hash

    def validate_placeholders(self, prompt_id: str, **variables) -> None:
        """
        Validate że wszystkie required placeholders są provided.

        Raises:
            ValueError: Jeśli brakuje required variable
        """
        prompt = self.get(prompt_id)
        # Delegated to validators module
        validate_prompt_placeholders(prompt.messages, prompt_id, **variables)


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class ModelConfig:
    """
    Konfiguracja modelu LLM.

    Attributes:
        model: Model name (e.g., "gemini-2.5-flash")
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum output tokens
        top_p: Nucleus sampling parameter
        top_k: Top-k sampling parameter
        timeout: Request timeout (seconds)
        retries: Number of retry attempts
    """
    model: str
    temperature: float = 0.7
    max_tokens: int = 6000
    top_p: float | None = None
    top_k: int | None = None
    timeout: int = 60
    retries: int = 3

    @property
    def params(self) -> dict[str, Any]:
        """Return dict of parameters for build_chat_model()."""
        params = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
        }

        if self.top_p is not None:
            params["top_p"] = self.top_p
        if self.top_k is not None:
            params["top_k"] = self.top_k

        return params


class ModelRegistry:
    """
    Registry modeli z fallback chain.

    Fallback order:
    1. Domain-specific override (e.g., domains.personas.orchestration)
    2. Domain defaults (e.g., domains.personas.generation)
    3. Global defaults (defaults.chat)

    Fallback behavior na missing model:
    - Fallback do defaults.chat.model + WARNING log
    - System działa (graceful degradation)
    """

    def __init__(self, models_file: str = "models.yaml"):
        self.loader = ConfigLoader()
        self.config = self.loader.load_with_env_overrides(models_file)
        # Delegated to validators module
        validate_models_config(self.config)

    def get(self, domain: str, subdomain: str | None = None) -> ModelConfig:
        """
        Get model config z fallback chain.

        Args:
            domain: Domain name (e.g., "personas", "surveys")
            subdomain: Subdomain name (e.g., "orchestration", "response")

        Returns:
            ModelConfig object

        Examples:
            >>> models.get("personas", "orchestration")
            ModelConfig(model="gemini-2.5-pro", temperature=0.3, ...)

            >>> models.get("surveys", "response")
            ModelConfig(model="gemini-2.5-flash", temperature=0.7, ...)
        """
        # Get defaults
        defaults = self.config["defaults"]["chat"]

        # Try domain.subdomain
        if subdomain and "domains" in self.config:
            domain_config = self.config["domains"].get(domain, {})
            subdomain_config = domain_config.get(subdomain)

            if subdomain_config:
                # Merge with defaults
                merged = {**defaults, **subdomain_config}
                return self._build_model_config(merged)

        # Try domain defaults
        if "domains" in self.config and domain in self.config["domains"]:
            # Check if domain has "generation" as default fallback
            domain_config = self.config["domains"][domain]
            if "generation" in domain_config:
                merged = {**defaults, **domain_config["generation"]}
                return self._build_model_config(merged)

        # Fallback to global defaults
        logger.info(
            f"No config for {domain}.{subdomain}, using defaults.chat"
        )
        return self._build_model_config(defaults)

    def _build_model_config(self, config: dict) -> ModelConfig:
        """Build ModelConfig from dict."""
        # Check if model exists (basic validation)
        model_name = config.get("model")
        if not model_name:
            logger.warning("Model name not specified, using default")
            model_name = self.config["defaults"]["chat"]["model"]

        # Validate model name format (delegated to validators module)
        validate_model_name(model_name)

        return ModelConfig(
            model=model_name,
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 6000),
            top_p=config.get("top_p"),
            top_k=config.get("top_k"),
            timeout=config.get("timeout", 60),
            retries=config.get("retries", 3),
        )

    def get_default(self) -> ModelConfig:
        """Get global default model config."""
        return self._build_model_config(self.config["defaults"]["chat"])


# ═══════════════════════════════════════════════════════════════════════════════
# RAG CONFIG
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class ChunkingConfig:
    """Chunking configuration."""
    chunk_size: int = 1000
    chunk_overlap: int = 300


@dataclass
class RetrievalConfig:
    """Retrieval configuration."""
    top_k: int = 8
    max_context_chars: int = 8000
    use_hybrid_search: bool = True
    vector_weight: float = 0.7
    rrf_k: int = 60
    mode: str = "vector"  # vector | hybrid | hybrid+rerank

    # Reranking
    use_reranking: bool = True
    rerank_candidates: int = 10
    rerank_threshold: int = 3
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"


@dataclass
class GraphTransformerConfig:
    """LLMGraphTransformer configuration."""
    allowed_nodes: list[str] = field(default_factory=list)
    allowed_relationships: list[str] = field(default_factory=list)
    node_properties: list[str] = field(default_factory=list)
    relationship_properties: list[str] = field(default_factory=list)
    additional_instructions: str = ""


class RagConfig:
    """
    RAG system configuration.

    Loads from:
    - config/rag/retrieval.yaml
    - config/rag/graph_transformer.yaml
    - config/rag/queries/*.cypher
    """

    def __init__(self):
        self.loader = ConfigLoader()
        self.rag_dir = CONFIG_ROOT / "rag"

        # Load configs
        self._load_retrieval()
        self._load_graph_transformer()
        self._load_queries()

    def _load_retrieval(self):
        """Load retrieval.yaml."""
        config = self.loader.load_yaml(self.rag_dir / "retrieval.yaml")

        # Chunking
        chunking = config.get("chunking", {})
        self.chunking = ChunkingConfig(
            chunk_size=chunking.get("chunk_size", 1000),
            chunk_overlap=chunking.get("chunk_overlap", 300),
        )

        # Retrieval
        retrieval = config.get("retrieval", {})
        reranking = retrieval.get("reranking", {})

        self.retrieval = RetrievalConfig(
            top_k=retrieval.get("top_k", 8),
            max_context_chars=retrieval.get("max_context_chars", 8000),
            use_hybrid_search=retrieval.get("use_hybrid_search", True),
            vector_weight=retrieval.get("vector_weight", 0.7),
            rrf_k=retrieval.get("rrf_k", 60),
            mode=retrieval.get("mode", "vector"),
            use_reranking=reranking.get("enabled", True),
            rerank_candidates=reranking.get("candidates", 10),
            rerank_threshold=retrieval.get("rerank_threshold", 3),
            reranker_model=reranking.get("model", "cross-encoder/ms-marco-MiniLM-L-6-v2"),
        )

    def _load_graph_transformer(self):
        """Load graph_transformer.yaml."""
        config = self.loader.load_yaml(self.rag_dir / "graph_transformer.yaml")

        self.graph_transformer = GraphTransformerConfig(
            allowed_nodes=config.get("allowed_nodes", []),
            allowed_relationships=config.get("allowed_relationships", []),
            node_properties=config.get("node_properties", []),
            relationship_properties=config.get("relationship_properties", []),
            additional_instructions=config.get("additional_instructions", ""),
        )

    def _load_queries(self):
        """Load named Cypher queries from rag/queries/*.cypher."""
        self.queries = {}

        queries_dir = self.rag_dir / "queries"
        if queries_dir.exists():
            for query_file in queries_dir.glob("*.cypher"):
                query_name = query_file.stem
                with open(query_file, "r", encoding="utf-8") as f:
                    self.queries[query_name] = f.read().strip()

        logger.debug(f"Loaded {len(self.queries)} Cypher queries")


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL SINGLETONS
# ═══════════════════════════════════════════════════════════════════════════════

# Global registries (lazy-initialized on first access)
_prompts: PromptRegistry | None = None
_models: ModelRegistry | None = None
_rag: RagConfig | None = None


def get_prompt_registry() -> PromptRegistry:
    """Get global PromptRegistry singleton."""
    global _prompts
    if _prompts is None:
        _prompts = PromptRegistry()
    return _prompts


def get_model_registry() -> ModelRegistry:
    """Get global ModelRegistry singleton."""
    global _models
    if _models is None:
        _models = ModelRegistry()
    return _models


def get_rag_config() -> RagConfig:
    """Get global RagConfig singleton."""
    global _rag
    if _rag is None:
        _rag = RagConfig()
    return _rag


# Convenience exports
prompts = get_prompt_registry()
models = get_model_registry()
rag = get_rag_config()
