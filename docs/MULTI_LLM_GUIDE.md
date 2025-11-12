# Multi-LLM Support - Przewodnik

System multi-LLM dla Sight Platform z automatycznym fallbackiem, cost routingiem i monitoringiem użycia.

## 🎯 Funkcjonalności

### 1. Multi-Provider Support

Obsługiwani dostawcy (w kolejności fallback):
- **Gemini** (Google) - Primary provider (najtańszy, dobry quality)
- **OpenAI** (GPT-4o, GPT-4o-mini) - Fallback 1
- **Anthropic** (Claude 3.5) - Fallback 2

### 2. Automatic Fallback

Jeśli primary provider nie działa (rate limit, API error, timeout):
```
Gemini → OpenAI → Anthropic
```

System automatycznie przełącza się na następny dostępny provider bez manual intervention.

### 3. Cost Routing

Automatyczny wybór najtańszego modelu dla danego task complexity:

| Task Complexity | Preferred Models | Use Cases |
|-----------------|------------------|-----------|
| **SIMPLE** | Gemini Flash → GPT-4o-mini → Claude Haiku | Formatowanie, klasyfikacja, proste odpowiedzi |
| **MEDIUM** | Gemini Flash → GPT-4o-mini → Claude Haiku | Generacja person, ankiety, dyskusje |
| **COMPLEX** | Gemini Pro → Claude Sonnet → GPT-4o | Orchestration, reasoning, analiza |

### 4. Usage Tracking

Automatyczne śledzenie:
- Tokeny input/output per provider
- Liczba requestów
- Szacowane koszty per provider
- Health status każdego providera

## 🚀 Quick Start

### Setup

1. **Install dependencies:**
   ```bash
   # Gemini (already installed)
   # No additional deps needed

   # OpenAI (optional)
   pip install -e ".[llm-providers]"

   # Anthropic (optional)
   pip install -e ".[llm-providers]"
   ```

2. **Set API keys:**
   ```bash
   # .env
   GOOGLE_API_KEY=your-gemini-key  # Required
   OPENAI_API_KEY=your-openai-key  # Optional (for fallback)
   ANTHROPIC_API_KEY=your-anthropic-key  # Optional (for fallback)
   ```

3. **Enable providers in config:**
   ```yaml
   # config/models.yaml
   providers:
     openai:
       enabled: true  # Set to true to enable OpenAI fallback
     anthropic:
       enabled: true  # Set to true to enable Anthropic fallback
   ```

### Basic Usage

```python
from app.services.shared.llm_router import get_llm_router, TaskComplexity

# Get router instance
router = get_llm_router()

# Simple task (will use cheapest model - Gemini Flash)
llm = router.get_chat_model(task_complexity=TaskComplexity.SIMPLE)
response = await llm.ainvoke("Classify this text: ...")

# Complex task (will use best model - Gemini Pro)
llm = router.get_chat_model(task_complexity=TaskComplexity.COMPLEX)
response = await llm.ainvoke("Analyze this complex scenario: ...")

# Preferred provider (override cost routing)
from app.services.shared.llm_router import LLMProvider

llm = router.get_chat_model(
    task_complexity=TaskComplexity.MEDIUM,
    preferred_provider=LLMProvider.OPENAI  # Force OpenAI
)
```

### Usage Tracking

```python
# Get usage summary
router = get_llm_router()
summary = router.get_usage_summary()

# Output:
# {
#   "gemini": {
#     "requests": 150,
#     "input_tokens": 45000,
#     "output_tokens": 30000,
#     "total_tokens": 75000,
#     "estimated_cost_usd": 0.0068
#   },
#   "openai": {
#     "requests": 10,
#     "input_tokens": 3000,
#     "output_tokens": 2000,
#     "total_tokens": 5000,
#     "estimated_cost_usd": 0.0017
#   }
# }
```

## 📊 Cost Comparison

### Cost per 1M tokens (as of 2024-11):

| Provider | Model | Input | Output | Use Case |
|----------|-------|--------|--------|----------|
| **Gemini** | Flash | $0.05 | $0.15 | 🏆 Najtańszy - default dla simple/medium |
| **Gemini** | Pro | $1.00 | $3.00 | Analytical tasks, complex reasoning |
| **OpenAI** | GPT-4o-mini | $0.15 | $0.60 | Fallback dla simple tasks |
| **OpenAI** | GPT-4o | $2.50 | $10.00 | Premium quality (expensive) |
| **Anthropic** | Claude Haiku | $0.80 | $4.00 | Fast, cost-effective |
| **Anthropic** | Claude Sonnet | $3.00 | $15.00 | Premium quality, best reasoning |

### Savings Example

**Scenario:** 1000 personas generated (simple task)
- Tokens: ~100k input, ~200k output per persona generation
- Total: 100M input, 200M output tokens

**Without cost routing (all Gemini Pro):**
- Input: 100M × $1 / 1M = $100
- Output: 200M × $3 / 1M = $600
- **Total: $700**

**With cost routing (Gemini Flash for simple tasks):**
- Input: 100M × $0.05 / 1M = $5
- Output: 200M × $0.15 / 1M = $30
- **Total: $35**

**Savings: $665 (95% reduction!)**

## 🔄 Migration Guide

### Migracja z obecnego kodu (single provider)

**Before (legacy):**
```python
from app.services.shared.clients import build_chat_model
from config import models

model_config = models.get("personas", "generation")
llm = build_chat_model(**model_config.params)
response = await llm.ainvoke(messages)
```

**After (multi-LLM):**
```python
from app.services.shared.llm_router import get_llm_router, TaskComplexity

router = get_llm_router()
llm = router.get_chat_model(
    task_complexity=TaskComplexity.MEDIUM,
    temperature=0.9,  # Can still override params
    max_tokens=6000
)
response = await llm.ainvoke(messages)
```

### Migracja stopniowa (per-service)

1. **Start:** Dodaj multi-LLM jako opcjonalny
2. **Test:** Przetestuj na dev/staging z fallbackiem
3. **Monitor:** Sprawdź koszty i quality
4. **Migrate:** Stopniowo migruj serwisy

**Przykład:**
```python
# W service, dodaj flag
USE_MULTI_LLM = os.getenv("USE_MULTI_LLM", "false").lower() == "true"

if USE_MULTI_LLM:
    router = get_llm_router()
    llm = router.get_chat_model(task_complexity=TaskComplexity.MEDIUM)
else:
    # Legacy path
    llm = build_chat_model(model="gemini-2.5-flash")
```

## 🛠️ Advanced Features

### Custom Fallback Chain

```python
from app.services.shared.llm_router import LLMRouter, LLMProvider

# Custom chain: OpenAI → Anthropic (skip Gemini)
router = LLMRouter(
    fallback_chain=[LLMProvider.OPENAI, LLMProvider.ANTHROPIC]
)
```

### Disable Cost Routing

```python
# Always use primary provider, no cost optimization
router = LLMRouter(enable_cost_routing=False)
```

### Provider Health Check

```python
router = get_llm_router()

# Check if provider is available
if router.is_provider_available(LLMProvider.OPENAI):
    print("OpenAI is available")
else:
    print("OpenAI is unavailable (no API key or failed health check)")
```

### Manual Usage Tracking

```python
# Track usage after LLM call
usage = response.response_metadata.get("token_usage", {})
router.track_usage(
    provider=LLMProvider.GEMINI,
    input_tokens=usage.get("prompt_tokens", 0),
    output_tokens=usage.get("completion_tokens", 0)
)
```

## 🔍 Monitoring & Debugging

### Logs

LLM Router loguje wszystkie istotne eventy:
```
INFO: LLMRouter initialized with fallback chain: ['gemini', 'openai', 'anthropic']
INFO: Using gemini:gemini-2.5-flash for medium task
WARNING: Trying fallback to next provider
INFO: Fallback successful: using openai
ERROR: Fallback to anthropic failed: API key not found
```

### Health Dashboard

Dodaj endpoint do monitoringu:
```python
from fastapi import APIRouter
from app.services.shared.llm_router import get_llm_router

router = APIRouter()

@router.get("/admin/llm-status")
async def get_llm_status():
    llm_router = get_llm_router()
    return {
        "providers": {
            "gemini": llm_router.is_provider_available(LLMProvider.GEMINI),
            "openai": llm_router.is_provider_available(LLMProvider.OPENAI),
            "anthropic": llm_router.is_provider_available(LLMProvider.ANTHROPIC),
        },
        "usage": llm_router.get_usage_summary(),
        "health": llm_router.provider_health,
    }
```

## ⚠️ Best Practices

### 1. Always Set Task Complexity

```python
# ✅ Good
llm = router.get_chat_model(task_complexity=TaskComplexity.SIMPLE)

# ❌ Bad (defaults to MEDIUM, may be more expensive)
llm = router.get_chat_model()
```

### 2. Use Preferred Provider for Critical Tasks

```python
# For critical orchestration, force best model
llm = router.get_chat_model(
    task_complexity=TaskComplexity.COMPLEX,
    preferred_provider=LLMProvider.GEMINI,  # Ensure Gemini Pro
)
```

### 3. Monitor Costs Regularly

```python
# Log usage summary daily
import logging
logger = logging.getLogger(__name__)

router = get_llm_router()
summary = router.get_usage_summary()
logger.info(f"Daily LLM usage: {summary}")
```

### 4. Test Fallback Scenarios

```python
# Simulate provider failure in tests
router.provider_health[LLMProvider.GEMINI] = False
llm = router.get_chat_model(task_complexity=TaskComplexity.SIMPLE)
# Should automatically use OpenAI
```

## 📈 Roadmap

- [ ] Auto-retry with exponential backoff per provider
- [ ] Intelligent caching (avoid duplicate expensive calls)
- [ ] A/B testing framework (compare quality across providers)
- [ ] Cost alerts (notify when spending >threshold)
- [ ] Quality scoring (track response quality per provider)

## 🔗 Resources

- [Gemini Pricing](https://ai.google.dev/pricing)
- [OpenAI Pricing](https://openai.com/pricing)
- [Anthropic Pricing](https://www.anthropic.com/pricing)
- [LangChain Multi-Provider Guide](https://python.langchain.com/docs/integrations/chat/)
