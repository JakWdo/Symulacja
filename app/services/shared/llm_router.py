"""
Multi-LLM Router z fallbackiem, cost routingiem i automatycznym switchingiem.
Obsługuje Gemini, OpenAI i Anthropic Claude z inteligentnym routingiem.
"""
import logging
import os
from enum import Enum
from typing import Any, Optional, Dict, List
from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Dostępni dostawcy LLM."""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class TaskComplexity(str, Enum):
    """Poziom złożoności zadania dla cost routingu."""
    SIMPLE = "simple"  # Proste zadania (formatowanie, klasyfikacja)
    MEDIUM = "medium"  # Średnie zadania (generacja person, odpowiedzi)
    COMPLEX = "complex"  # Złożone zadania (analiza, orchestration, reasoning)


@dataclass
class LLMProviderConfig:
    """Konfiguracja pojedynczego dostawcy LLM."""
    provider: LLMProvider
    model: str
    api_key_env: str
    cost_per_1k_tokens_input: float
    cost_per_1k_tokens_output: float
    max_tokens: int
    temperature: float = 0.7
    enabled: bool = True
    priority: int = 1  # Niższy = wyższy priorytet


# Konfiguracja kosztów (per 1k tokens) - update according to pricing
LLM_PROVIDER_CONFIGS: Dict[LLMProvider, Dict[str, LLMProviderConfig]] = {
    LLMProvider.GEMINI: {
        "flash": LLMProviderConfig(
            provider=LLMProvider.GEMINI,
            model="gemini-2.5-flash",
            api_key_env="GOOGLE_API_KEY",
            cost_per_1k_tokens_input=0.00005,  # $0.05 per 1M
            cost_per_1k_tokens_output=0.00015,  # $0.15 per 1M
            max_tokens=6000,
            priority=1,
        ),
        "pro": LLMProviderConfig(
            provider=LLMProvider.GEMINI,
            model="gemini-2.5-pro",
            api_key_env="GOOGLE_API_KEY",
            cost_per_1k_tokens_input=0.001,  # $1 per 1M
            cost_per_1k_tokens_output=0.003,  # $3 per 1M
            max_tokens=6000,
            priority=3,
        ),
    },
    LLMProvider.OPENAI: {
        "gpt-4o-mini": LLMProviderConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            api_key_env="OPENAI_API_KEY",
            cost_per_1k_tokens_input=0.00015,  # $0.15 per 1M
            cost_per_1k_tokens_output=0.0006,  # $0.60 per 1M
            max_tokens=6000,
            priority=2,
        ),
        "gpt-4o": LLMProviderConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
            api_key_env="OPENAI_API_KEY",
            cost_per_1k_tokens_input=0.0025,  # $2.5 per 1M
            cost_per_1k_tokens_output=0.010,  # $10 per 1M
            max_tokens=6000,
            priority=4,
        ),
    },
    LLMProvider.ANTHROPIC: {
        "claude-3-5-haiku": LLMProviderConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-5-haiku-20241022",
            api_key_env="ANTHROPIC_API_KEY",
            cost_per_1k_tokens_input=0.0008,  # $0.8 per 1M
            cost_per_1k_tokens_output=0.004,  # $4 per 1M
            max_tokens=6000,
            priority=2,
        ),
        "claude-3-5-sonnet": LLMProviderConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
            api_key_env="ANTHROPIC_API_KEY",
            cost_per_1k_tokens_input=0.003,  # $3 per 1M
            cost_per_1k_tokens_output=0.015,  # $15 per 1M
            max_tokens=6000,
            priority=5,
        ),
    },
}


class LLMRouter:
    """
    Router LLM z automatycznym fallbackiem i cost routingiem.

    Funkcjonalności:
    - Automatyczny fallback: Gemini → OpenAI → Anthropic
    - Cost routing: Preferuj tańsze modele dla prostych zadań
    - Provider health tracking: Przełącz na backup jeśli primary nie działa
    - Token usage tracking: Monitoruj koszty per provider
    """

    def __init__(
        self,
        fallback_chain: Optional[List[LLMProvider]] = None,
        enable_cost_routing: bool = True,
    ):
        """
        Initialize LLM Router.

        Args:
            fallback_chain: Lista dostawców w kolejności fallback (domyślnie: Gemini→OpenAI→Anthropic)
            enable_cost_routing: Czy włączyć automatyczny cost routing
        """
        self.fallback_chain = fallback_chain or [
            LLMProvider.GEMINI,
            LLMProvider.OPENAI,
            LLMProvider.ANTHROPIC,
        ]
        self.enable_cost_routing = enable_cost_routing

        # Provider health tracking
        self.provider_health: Dict[LLMProvider, bool] = {
            provider: True for provider in LLMProvider
        }

        # Token usage tracking (for cost monitoring)
        self.usage_stats: Dict[LLMProvider, Dict[str, int]] = {
            provider: {"input_tokens": 0, "output_tokens": 0, "requests": 0}
            for provider in LLMProvider
        }

        logger.info(
            f"LLMRouter initialized with fallback chain: {[p.value for p in self.fallback_chain]}"
        )

    def get_chat_model(
        self,
        *,
        task_complexity: TaskComplexity = TaskComplexity.MEDIUM,
        preferred_provider: Optional[LLMProvider] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **extra_params: Any,
    ) -> BaseChatModel:
        """
        Zwraca odpowiedni model LLM na podstawie task complexity i dostępności.

        Args:
            task_complexity: Złożoność zadania (simple/medium/complex)
            preferred_provider: Preferowany dostawca (jeśli None, użyj cost routing)
            temperature: Temperatura próbkująca (override)
            max_tokens: Limit tokenów (override)
            extra_params: Dodatkowe parametry dla modelu

        Returns:
            BaseChatModel: Instancja modelu LLM

        Raises:
            RuntimeError: Jeśli żaden dostawca nie jest dostępny
        """
        # Determine which provider to use
        if preferred_provider and self.is_provider_available(preferred_provider):
            provider = preferred_provider
        elif self.enable_cost_routing:
            provider = self._select_provider_by_cost(task_complexity)
        else:
            provider = self._select_provider_by_fallback()

        # Get model config
        model_config = self._get_model_config_for_complexity(provider, task_complexity)

        # Override params if provided
        if temperature is not None:
            model_config.temperature = temperature
        if max_tokens is not None:
            model_config.max_tokens = max_tokens

        # Build model
        try:
            model = self._build_model(model_config, **extra_params)
            logger.info(
                f"Using {model_config.provider.value}:{model_config.model} "
                f"for {task_complexity.value} task"
            )
            return model
        except Exception as e:
            logger.error(f"Failed to build model for {provider.value}: {e}")
            self.provider_health[provider] = False

            # Try fallback
            return self._try_fallback(task_complexity, temperature, max_tokens, **extra_params)

    def _select_provider_by_cost(self, task_complexity: TaskComplexity) -> LLMProvider:
        """Wybierz najtańszy dostępny provider dla danego task complexity."""
        # Dla simple tasks: preferuj najtańsze modele
        if task_complexity == TaskComplexity.SIMPLE:
            # Gemini Flash (najtańszy) → OpenAI GPT-4o-mini → Claude Haiku
            for provider in [LLMProvider.GEMINI, LLMProvider.OPENAI, LLMProvider.ANTHROPIC]:
                if self.is_provider_available(provider):
                    return provider

        # Dla complex tasks: preferuj najlepsze modele (quality over cost)
        elif task_complexity == TaskComplexity.COMPLEX:
            # Gemini Pro → Claude Sonnet → GPT-4o
            for provider in [LLMProvider.GEMINI, LLMProvider.ANTHROPIC, LLMProvider.OPENAI]:
                if self.is_provider_available(provider):
                    return provider

        # Dla medium tasks: balans cost/quality
        return self._select_provider_by_fallback()

    def _select_provider_by_fallback(self) -> LLMProvider:
        """Wybierz pierwszy dostępny provider z fallback chain."""
        for provider in self.fallback_chain:
            if self.is_provider_available(provider):
                return provider

        raise RuntimeError("No LLM providers available")

    def is_provider_available(self, provider: LLMProvider) -> bool:
        """Sprawdź czy provider jest dostępny (API key + health check)."""
        # Check if provider is healthy
        if not self.provider_health.get(provider, False):
            return False

        # Check if API key is set
        configs = LLM_PROVIDER_CONFIGS.get(provider, {})
        if not configs:
            return False

        # Check at least one model config has API key
        for config in configs.values():
            if config.enabled and os.getenv(config.api_key_env):
                return True

        return False

    def _get_model_config_for_complexity(
        self, provider: LLMProvider, complexity: TaskComplexity
    ) -> LLMProviderConfig:
        """Wybierz odpowiedni model dla danego providera i complexity."""
        configs = LLM_PROVIDER_CONFIGS[provider]

        # Dla Gemini
        if provider == LLMProvider.GEMINI:
            return configs["flash"] if complexity == TaskComplexity.SIMPLE else configs["pro"]

        # Dla OpenAI
        elif provider == LLMProvider.OPENAI:
            return configs["gpt-4o-mini"] if complexity == TaskComplexity.SIMPLE else configs["gpt-4o"]

        # Dla Anthropic
        elif provider == LLMProvider.ANTHROPIC:
            return configs["claude-3-5-haiku"] if complexity == TaskComplexity.SIMPLE else configs["claude-3-5-sonnet"]

        # Fallback
        return list(configs.values())[0]

    def _build_model(self, config: LLMProviderConfig, **extra_params: Any) -> BaseChatModel:
        """Zbuduj instancję modelu dla danego providera."""
        api_key = os.getenv(config.api_key_env)
        if not api_key:
            raise ValueError(f"API key not found for {config.provider.value}: {config.api_key_env}")

        # Gemini
        if config.provider == LLMProvider.GEMINI:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=config.model,
                google_api_key=api_key,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                max_retries=3,
                **extra_params,
            )

        # OpenAI
        elif config.provider == LLMProvider.OPENAI:
            try:
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=config.model,
                    openai_api_key=api_key,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    max_retries=3,
                    **extra_params,
                )
            except ImportError:
                raise ImportError(
                    "OpenAI support requires langchain-openai. "
                    "Install with: pip install -e '.[llm-providers]'"
                )

        # Anthropic
        elif config.provider == LLMProvider.ANTHROPIC:
            try:
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(
                    model=config.model,
                    anthropic_api_key=api_key,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    max_retries=3,
                    **extra_params,
                )
            except ImportError:
                raise ImportError(
                    "Anthropic support requires langchain-anthropic. "
                    "Install with: pip install -e '.[llm-providers]'"
                )

        raise ValueError(f"Unsupported provider: {config.provider}")

    def _try_fallback(
        self,
        task_complexity: TaskComplexity,
        temperature: Optional[float],
        max_tokens: Optional[int],
        **extra_params: Any,
    ) -> BaseChatModel:
        """Spróbuj fallback do następnego providera."""
        logger.warning("Trying fallback to next provider")

        for provider in self.fallback_chain:
            if self.is_provider_available(provider):
                try:
                    config = self._get_model_config_for_complexity(provider, task_complexity)
                    if temperature is not None:
                        config.temperature = temperature
                    if max_tokens is not None:
                        config.max_tokens = max_tokens

                    model = self._build_model(config, **extra_params)
                    logger.info(f"Fallback successful: using {provider.value}")
                    return model
                except Exception as e:
                    logger.error(f"Fallback to {provider.value} failed: {e}")
                    self.provider_health[provider] = False
                    continue

        raise RuntimeError("All LLM providers failed")

    def track_usage(
        self,
        provider: LLMProvider,
        input_tokens: int,
        output_tokens: int,
    ):
        """Śledź usage tokeny dla monitorowania kosztów."""
        self.usage_stats[provider]["input_tokens"] += input_tokens
        self.usage_stats[provider]["output_tokens"] += output_tokens
        self.usage_stats[provider]["requests"] += 1

    def get_usage_summary(self) -> Dict[str, Any]:
        """Zwróć podsumowanie usage i kosztów per provider."""
        summary = {}
        for provider, stats in self.usage_stats.items():
            configs = LLM_PROVIDER_CONFIGS.get(provider, {})
            if not configs:
                continue

            # Użyj pierwszego dostępnego config dla kosztów (uproszczenie)
            config = list(configs.values())[0]

            input_cost = (stats["input_tokens"] / 1000) * config.cost_per_1k_tokens_input
            output_cost = (stats["output_tokens"] / 1000) * config.cost_per_1k_tokens_output
            total_cost = input_cost + output_cost

            summary[provider.value] = {
                "requests": stats["requests"],
                "input_tokens": stats["input_tokens"],
                "output_tokens": stats["output_tokens"],
                "total_tokens": stats["input_tokens"] + stats["output_tokens"],
                "estimated_cost_usd": round(total_cost, 4),
            }

        return summary


# Global router instance (singleton)
_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """Zwróć globalną instancję LLM routera (singleton)."""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
